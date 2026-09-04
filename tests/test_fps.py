"""3D generator and fail-closed gate contracts; preserves all evidence."""
import contextlib
import importlib
import json
import os
from pathlib import Path
import py_compile
import struct
import subprocess
import sys
import tempfile
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASH = os.environ.get("GP_TEST_BASH", "bash")
OUT = ROOT / "out"
OUT.mkdir(exist_ok=True)
RUN = Path(tempfile.mkdtemp(prefix="fps-regression-", dir=OUT))
ENV = {**os.environ, "GP_PYTHON": sys.executable, "MSYS2_ARG_CONV_EXCL": "*", "PYTHONUTF8": "1"}


def command(args, cwd, env=None):
    return subprocess.run(args, cwd=cwd, env={**ENV, **(env or {})}, capture_output=True,
                          text=True, encoding="utf-8", errors="replace")


def install(path, tool="codex", *args):
    return command([BASH, str(ROOT / "bootstrap.sh"), "--preset=3d-fps-windows", "--prefix=fp",
                    "--project-name=FPS fixture", "--tool=" + tool, "--non-interactive", "--no-git", *args], path)


@contextlib.contextmanager
def cwd(path):
    old = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old)


def glb(path, normal=1.0, advertised_max=99):
    points = [(0., 0., 0.), (1., 0., 0.), (0., 1., 0.)]
    blob = b"".join(struct.pack("<fff", *p) for p in points)
    blob += b"".join(struct.pack("<fff", 0., 0., normal) for _ in points)
    data = {"asset": {"version": "2.0"}, "buffers": [{"byteLength": len(blob)}],
            "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": 36},
                            {"buffer": 0, "byteOffset": 36, "byteLength": 36}],
            "accessors": [{"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3", "min": [0, 0, 0], "max": [advertised_max]*3},
                          {"bufferView": 1, "componentType": 5126, "count": 3, "type": "VEC3"}],
            "materials": [{"pbrMetallicRoughness": {"baseColorFactor": [1, 1, 1, 1]}}],
            "meshes": [{"primitives": [{"attributes": {"POSITION": 0, "NORMAL": 1}, "material": 0}]}],
            "nodes": [{"mesh": 0}], "scenes": [{"nodes": [0]}], "scene": 0}
    encoded = json.dumps(data).encode()
    encoded += b" " * (-len(encoded) % 4)
    raw = struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(encoded) + 8 + len(blob))
    raw += struct.pack("<II", len(encoded), 0x4E4F534A) + encoded
    raw += struct.pack("<II", len(blob), 0x004E4942) + blob
    path.write_bytes(raw)


class FPSTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.projects = {}
        for tool in ("codex", "claude"):
            path = RUN / (tool + " FPS space")
            path.mkdir()
            args = ("--genre=horde", "--network=coop") if tool == "claude" else ()
            result = install(path, tool, *args)
            if result.returncode:
                raise AssertionError(result.stdout + result.stderr)
            cls.projects[tool] = path
        cls.project = cls.projects["codex"]
        cls.scripts = cls.project / ".codex/scripts"
        sys.path.insert(0, str(cls.scripts))
        cls.runtime = importlib.import_module("gp_3d")
        cls.mesh = importlib.import_module("gp_mesh")

    def gate(self, script, *args, env=None):
        result = command([BASH, str(self.scripts / ("fp-" + script + ".sh")), *args], self.project, env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(result.stdout.splitlines()), 1, result.stdout + result.stderr)
        return json.loads(result.stdout)

    def test_selected_composition_and_native_adapters(self):
        for tool, path in self.projects.items():
            root = path / ("." + tool)
            for file in [*root.rglob("*"), *(path / "pipeline").rglob("*"), path / "AGENTS.md" if tool == "codex" else path / "CLAUDE.md"]:
                if not file.is_file() or file.suffix == ".pyc":
                    continue
                text = file.read_text(encoding="utf-8")
                self.assertNotRegex(text, r"\{\{[^}]+\}\}|<!-- (?:engine:|tool:|if )")
                if file.suffix == ".py":
                    py_compile.compile(str(file), doraise=True)
            self.assertEqual(len(list((root / "agents").glob("*.md"))), 14)
            for file in (root / "agents").glob("*.md"):
                self.assertNotIn("model:", file.read_text())
                self.assertNotIn("Skeleton2D", file.read_text())
            self.assertFalse((root / "scripts/fp-art-gen.sh").exists())
            for file in (root / "agents").glob("*.toml"):
                self.assertNotIn("model", tomllib.loads(file.read_text()))
            manifest = (root / "commands/fp-runtime/manifest.tsv").read_text()
            self.assertIn("build\t--build\tbuild.md", manifest)
        contract = json.loads((self.projects["claude"] / "pipeline/qa-contract.json").read_text())
        self.assertIn("two_process_peers", contract["scenarios"]["network"])
        self.assertNotIn("network", json.loads((self.project / "pipeline/qa-contract.json").read_text())["scenarios"])

    def test_bad_preset_combinations_and_migrations_make_no_writes(self):
        empty = RUN / "invalid"
        empty.mkdir()
        for arg in ("--preset=../bad", "--genre=strategy", "--network=bad", "--projection=iso-2to1", "--style-profile=painterly"):
            result = install(empty, "codex", arg)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(list(empty.iterdir()), [])
        stamp = self.project / ".codex/.gp-version"
        old = stamp.read_bytes()
        for args in (("--preset=2d-android", "--package=com.test.game"), ("--genre=tactical",), ("--network=competitive",)):
            result = install(self.project, "codex", "--force", *args)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(stamp.read_bytes(), old)

    def test_errors_and_missing_evidence_are_not_passes(self):
        for name in ("runner-godot", "fps-godot", "sim-godot", "mesh-build", "mesh-validate", "image-register", "doctor"):
            data = self.gate(name, 'unknown"\nvalue')
            self.assertFalse(data["pass"])
            self.assertEqual(data["error_kind"], "bad_usage")
        self.assertEqual(self.gate("runner-godot")["error_kind"], "project_missing")
        self.assertEqual(self.gate("mesh-validate", "--all")["error_kind"], "assets_missing")
        self.assertEqual(self.gate("sim-godot", "--runs", "1")["error_kind"], "bad_usage")

    def test_qa_identity_required_checks_and_finite_metrics(self):
        data = {"schema_version": 1, "run_id": "test", "scenario": "smoke", "seed": 4242, "pass": True,
                "checks": [{"id": key, "pass": True, "observed": "fixture observed"} for key in ("main_scene_loaded", "player_spawned", "hud_visible")]}
        with cwd(self.project):
            self.runtime.validate_qa(data, "smoke", "test", 4242)
            for field, value in (("run_id", "stale"), ("seed", 1), ("checks", []), ("pass", "true")):
                with self.assertRaises(self.runtime.GateError):
                    self.runtime.validate_qa({**data, field: value}, "smoke", "test", 4242)
            broken = json.loads(json.dumps(data))
            broken["checks"].append(broken["checks"][0])
            with self.assertRaises(self.runtime.GateError):
                self.runtime.validate_qa(broken, "smoke", "test", 4242)
            for output in ('GP_QA_RESULT={"fps":NaN}', 'GP_QA_RESULT={}\nGP_QA_RESULT={}', 'GP_QA_RESULT=bad'):
                with self.assertRaises(self.runtime.GateError):
                    self.runtime.payload(output, "GP_QA_RESULT=")

    def test_real_binary_geometry_not_advertised_bounds(self):
        path = RUN / "triangle.glb"
        spec = {"kind": "prop", "size_m": {"min": [0.9, 0.9, 0], "max": [1.1, 1.1, 0.1]}, "animations": [], "collision": "none"}
        profile = json.loads((ROOT / "profiles/style/stylized-3d.json").read_text())
        glb(path)
        actual = self.mesh.inspect_glb(path, spec, profile)
        self.assertEqual(actual["triangles"], 1)
        self.assertEqual(actual["size_m"], [1, 1, 0])
        with self.assertRaises(ValueError):
            self.mesh.inspect_glb(path, {**spec, "animations": ["idle"]}, profile)
        with self.assertRaises(ValueError):
            self.mesh.inspect_glb(path, {**spec, "collision": "convex"}, profile)
        profile["budgets"]["prop"]["triangles"] = 0
        with self.assertRaises(ValueError):
            self.mesh.inspect_glb(path, spec, profile)
        glb(path, normal=float("nan"))
        with self.assertRaises(ValueError):
            self.mesh.inspect_glb(path, spec, profile)

    def test_timeout_and_crash_after_payload_fail(self):
        with self.assertRaises(self.runtime.GateError) as caught:
            self.runtime.run_process([sys.executable, "-c", "import time; time.sleep(10)"], RUN / "timeout.log", 0.2)
        self.assertEqual(caught.exception.kind, "process_timeout")
        with self.assertRaises(self.runtime.GateError):
            self.runtime.run_process([sys.executable, "-c", "print('GP_TEST_RESULT={}'); raise SystemExit(1)"], RUN / "crash.log", 10)

    def test_network_requires_distinct_fresh_peer_receipts(self):
        project = self.projects["claude"]
        with cwd(project):
            required = json.loads(Path("pipeline/qa-contract.json").read_text())["scenarios"]["network"]
            data = {"schema_version": 1, "scenario": "network", "run_id": "peer-contract-fixture", "seed": 4242, "pass": True,
                    "checks": [{"id": key, "pass": True, "observed": "protocol fixture"} for key in required]}
            with self.assertRaises(self.runtime.GateError):
                self.runtime.validate_qa(data, "network", data["run_id"], 4242)
            Path("out/peer-contract").mkdir(parents=True, exist_ok=True)
            data["peers"] = []
            for number in (1, 2):
                log = Path("out/peer-contract") / (str(number) + ".log")
                log.write_text("GP_PEER_READY=" + data["run_id"], encoding="utf-8")
                data["peers"].append({"pid": number, "run_id": data["run_id"], "log": log.as_posix()})
            self.runtime.validate_qa(data, "network", data["run_id"], 4242)
            data["peers"][1]["pid"] = 1
            with self.assertRaises(self.runtime.GateError):
                self.runtime.validate_qa(data, "network", data["run_id"], 4242)
            data["peers"][1]["pid"] = 2
            Path(data["peers"][1]["log"]).write_text("GP_PEER_READY=old-run", encoding="utf-8")
            with self.assertRaises(self.runtime.GateError):
                self.runtime.validate_qa(data, "network", data["run_id"], 4242)

    def test_harness_install_preserves_existing_game_files(self):
        game = self.project / "custom game"
        (game / "tools/gates").mkdir(parents=True)
        (game / "project.godot").write_text("fixture")
        user = game / "tools/gates/qa_host.gd"
        user.write_text("user-owned harness")
        result = self.gate("fps-godot", "--init-harness", "--project", "custom game")
        self.assertTrue(result["pass"])
        self.assertEqual(user.read_text(), "user-owned harness")
        self.assertEqual(json.loads((game / "tests/gp_suites.json").read_text()), [])


if __name__ == "__main__":
    print("FPS regression evidence:", RUN, flush=True)
    unittest.main(verbosity=2)
