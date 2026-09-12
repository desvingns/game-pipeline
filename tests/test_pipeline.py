"""Observable bootstrap/gate regressions; no network or real Godot required."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import py_compile
import re
import subprocess
import sys
import tempfile
import tomllib
import unittest

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
BASH = os.environ.get("GP_TEST_BASH", "bash")
OUT = ROOT / "out"
OUT.mkdir(exist_ok=True)
RUN = Path(tempfile.mkdtemp(prefix="regression-", dir=OUT))
ENV = dict(os.environ, GP_PYTHON=sys.executable, MSYS2_ARG_CONV_EXCL="*")


def command(args, cwd, env=None):
    return subprocess.run(args, cwd=cwd, env={**ENV, **(env or {})},
                          capture_output=True, text=True, encoding="utf-8", errors="replace")


def bootstrap(cwd, tool="codex", *extra):
    return command([BASH, str(ROOT / "bootstrap.sh"), "--tool=" + tool,
                    "--prefix=td", "--project-name=Demo: quoted & useful", "--package=com.demo.td",
                    "--style-profile=flat-vector", "--non-interactive", "--no-git", *extra], cwd)


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


class PipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.projects = {}
        for tool in ("codex", "claude"):
            cwd = RUN / (tool + " project with spaces")
            cwd.mkdir()
            result = bootstrap(cwd, tool, "--memory-path=" + str(cwd / "memory"))
            (RUN / (tool + "-bootstrap.log")).write_text(result.stdout + result.stderr, encoding="utf-8")
            if result.returncode:
                raise AssertionError(result.stdout + result.stderr)
            cls.projects[tool] = cwd
        cls.cwd = cls.projects["codex"]
        cls.scripts = cls.cwd / ".codex/scripts"
        cls.fake = RUN / "fake-godot.sh"
        cls.fake.write_text('''#!/usr/bin/env bash
mode="${FAKE_MODE:-ok}"
for arg in "$@"; do
  case "$arg" in
    --seed=*) seed="${arg#*=}" ;;
    --out=*) out="${arg#*=}" ;;
    --headless) headless=1 ;;
  esac
done
case "$mode" in
  crash) printf '{"seed":4242,"hash":"same","waves_survived":10,"result":"win"}\\n'; exit 1 ;;
  malformed) printf '{"seed":4242,"hash":"same","waves_survived":10,"result":"win",}\\n'; exit 0 ;;
esac
if [ -n "${out:-}" ]; then
  [ "${headless:-0}" -eq 0 ] || exit 13
  printf 'fresh capture' > "$out"; exit 0
fi
if [ -n "${seed:-}" ]; then
  [ "$mode" != partial ] || [ "$seed" != 4244 ] || exit 0
  result=win
  [ $((seed % 2)) -ne 0 ] || result=loss
  printf '{"seed":%s,"hash":"same","waves_survived":10,"result":"%s"}\\n' "$seed" "$result"
fi
''', encoding="utf-8", newline="\n")
        cls.fake.chmod(0o755)
        (cls.cwd / "game/tools/gates").mkdir(parents=True)
        for f in ("project.godot", "tools/gates/sim_harness.tscn", "tools/gates/shot.tscn"):
            (cls.cwd / "game" / f).write_text("fixture", encoding="utf-8")

    def gate(self, name, *args, env=None):
        result = command([BASH, str(self.scripts / ("td-" + name + ".sh")), *args], self.cwd,
                         {"GODOT_BIN": str(self.fake), **(env or {})})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(result.stdout.splitlines()), 1, result.stdout + result.stderr)
        return json.loads(result.stdout)

    def test_01_render_and_native_adapters(self):
        for tool, cwd in self.projects.items():
            for p in [*(cwd / ("." + tool)).rglob("*"), *(cwd / "art").rglob("*")]:
                if p.is_file():
                    text = p.read_text(encoding="utf-8")
                    self.assertNotRegex(text, r"\{\{[^}]+\}\}|<!-- (?:engine:|tool:|if )")
                    if p.suffix == ".py":
                        py_compile.compile(str(p), doraise=True)
            for p in (cwd / "art").rglob("*.json"):
                json.loads(p.read_text(encoding="utf-8"))
        cwd = self.cwd
        self.assertIn("# AGENTS.md", (cwd / "AGENTS.md").read_text(encoding="utf-8"))
        self.assertIn("name: td", (cwd / ".agents/skills/td/SKILL.md").read_text())
        adapters = list((cwd / ".codex/agents").glob("*.toml"))
        self.assertEqual(len(adapters), 15)
        for p in adapters:
            data = tomllib.loads(p.read_text(encoding="utf-8"))
            self.assertEqual(data["name"], p.stem)
            self.assertIn(data["model"], {"gpt-5.6-luna", "gpt-5.6-sol", "gpt-6-astra"})
            self.assertIn(data["model_reasoning_effort"], {"xhigh", "high"})
            role = cwd / ".codex/agents" / (p.stem + ".md")
            self.assertTrue(role.is_file())
            self.assertNotIn("model: claude", role.read_text(encoding="utf-8"))
        for p in (cwd / ".codex/scripts").glob("*.sh"):
            self.assertTrue(os.access(p, os.X_OK))
        codex_router = (self.projects["codex"] / ".codex/commands/td.md").read_text(encoding="utf-8")
        codex_contract = (self.projects["codex"] / ".codex/commands/td-runtime/contract-work.md").read_text(encoding="utf-8")
        claude_contract = (self.projects["claude"] / ".claude/commands/td-runtime/contract-work.md").read_text(encoding="utf-8")
        self.assertIn("--chain", codex_router)
        self.assertIn("create_thread", codex_contract)
        self.assertNotIn("create_thread", claude_contract)

    def test_01_claude_frontmatter_matches_runtime_policy(self):
        project = self.projects["claude"]
        spec = importlib.util.spec_from_file_location("claude_work", project / ".claude/scripts/gp_work.py")
        work = importlib.util.module_from_spec(spec)
        previous, sys.dont_write_bytecode = sys.dont_write_bytecode, True
        try:  # keep the generated fixture free of __pycache__
            spec.loader.exec_module(work)
        finally:
            sys.dont_write_bytecode = previous
        policy = work.policy(project)
        roles = sorted((project / ".claude/agents").glob("*.md"))
        self.assertEqual(len(roles), 15)
        for path in roles:
            text = path.read_text(encoding="utf-8")
            role = path.stem.removeprefix("td-").removesuffix("-godot")
            setting = work.claude_role_setting(policy, role)
            self.assertIn(f"\nmodel: {setting['model']}\neffort: {setting['reasoning']}\n", text.split("---")[1])
            self.assertEqual(1, text.count("\nmodel:"))
            self.assertEqual(setting["reasoning"], work.route(project, {"tool": "claude", "role": role})["reasoning"])
            front = text.split("---")[1]
            turns = work.claude_role_max_turns(policy, role)
            if turns:
                self.assertIn(f"\nmaxTurns: {turns}\n", front)
            else:
                self.assertNotIn("maxTurns:", front)
            if role in work.READ_ONLY:
                tools = re.search(r"^tools: (.*)$", front, re.M).group(1)
                self.assertLessEqual({name.strip() for name in tools.split(",")}, {"Read", "Glob", "Grep"})
        self.assertEqual(8, work.claude_role_max_turns(policy, "runner"))
        self.assertIn("\nmodel: claude-sonnet-5\neffort: medium\n", (project / ".claude/agents/td-docs.md").read_text(encoding="utf-8"))
        self.assertIn("\nmodel: claude-opus-5\neffort: xhigh\n", (project / ".claude/agents/td-art-prompter.md").read_text(encoding="utf-8"))

    def test_01_claude_project_permissions(self):
        self.assertFalse((self.projects["codex"] / ".claude/settings.json").exists())
        settings = json.loads((self.projects["claude"] / ".claude/settings.json").read_text(encoding="utf-8"))
        allow, ask = settings["permissions"]["allow"], settings["permissions"]["ask"]
        for name in ("work", "runner-godot", "sim-godot", "visual-godot", "asset-validate"):
            self.assertIn(f"Bash(bash .claude/scripts/td-{name}.sh *)", allow)
        self.assertIn("Bash(bash .claude/scripts/td-style-lock.sh --verify *)", allow)
        self.assertEqual(["Bash(bash .claude/scripts/td-style-lock.sh *--lock*)"], ask)
        self.assertFalse([rule for rule in allow if "art-gen" in rule or "common" in rule or "--lock" in rule])

    def test_02_claude_force_pins_preserved_policy(self):
        cwd = self.projects["claude"]
        path = cwd / "pipeline/model-policy.json"
        policy = json.loads(path.read_text(encoding="utf-8"))
        policy["claude"]["role_tiers"]["developer"] = "expert"
        path.write_text(json.dumps(policy), encoding="utf-8")
        settings_path = cwd / ".claude/settings.json"
        custom = {"env": {"GP_SHOT_RENDERER": "gl_compatibility"},
                  "permissions": {"allow": ["Bash(make *)"], "deny": ["Bash(git push *)"]}}
        settings_path.write_text(json.dumps(custom), encoding="utf-8")
        result = bootstrap(cwd, "claude", "--force", "--memory-path=" + str(cwd / "memory"))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(policy, json.loads(path.read_text(encoding="utf-8")))
        developer = (cwd / ".claude/agents/td-developer-godot.md").read_text(encoding="utf-8")
        self.assertIn("\nmodel: claude-opus-5\neffort: xhigh\n", developer)
        self.assertEqual(1, developer.count("\nmodel:"))
        merged = json.loads(settings_path.read_text(encoding="utf-8"))
        self.assertEqual(custom["env"], merged["env"])
        self.assertEqual(["Bash(git push *)"], merged["permissions"]["deny"])
        self.assertEqual("Bash(make *)", merged["permissions"]["allow"][0])
        self.assertEqual(1, merged["permissions"]["allow"].count("Bash(bash .claude/scripts/td-work.sh *)"))
        self.assertTrue(list((cwd / "archive/gp-bootstrap").glob("*/previous/.claude/settings.json")))
        spec = importlib.util.spec_from_file_location("claude_settings", ROOT / "lib/claude_settings.py")
        helper = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(helper)
        self.assertEqual({"allow": [], "ask": []}, helper.merge(cwd, "td", RUN / "unused-archive"))
        self.assertFalse((RUN / "unused-archive").exists())

    def test_02_force_preserves_user_work_and_memory(self):
        preserved = {
            "STATE.md": "User state {{LITERAL}}\n",
            "AGENTS.md": "# Custom user instructions\n",
            ".codex/agents/custom.md": "Keep {{PREFIX}} literally\n",
            ".codex/specs/active/user.md": "User spec\n",
            "art/style/profiles/flat-vector.json": (self.cwd / "art/style/profiles/flat-vector.json").read_text(),
            "memory/MEMORY.md": "# Curated notes\n- custom entry\n",
        }
        for rel, contents in preserved.items():
            p = self.cwd / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(contents, encoding="utf-8")
        result = bootstrap(self.cwd, "codex", "--force", "--memory-path=" + str(self.cwd / "memory"))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for rel, contents in preserved.items():
            actual = (self.cwd / rel).read_text(encoding="utf-8")
            if rel == "memory/MEMORY.md":
                self.assertTrue(actual.startswith(contents))
            else:
                self.assertEqual(actual, contents)
        self.assertTrue(list((self.cwd / "archive/gp-bootstrap").glob("*/previous/.codex/commands/td.md")))

    def test_03_invalid_input_fails_before_writes(self):
        cwd = RUN / "invalid"
        cwd.mkdir()
        for arg in ("--prefix=../bad", "--package=bad", "--project-name=line\nbreak", "--style-profile=../bad"):
            result = bootstrap(cwd, "codex", arg)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(list(cwd.iterdir()), [])

    def test_04_errors_are_json_even_with_control_characters(self):
        for name in ("runner-godot", "sim-godot", "visual-godot", "art-gen", "asset-validate", "style-lock"):
            result = self.gate(name, 'unknown"\\path\tline\nnext')
            self.assertFalse(result["pass"])
            self.assertEqual(result["error_kind"], "bad_usage")

    def test_05_runner_requires_tests(self):
        result = self.gate("runner-godot")
        self.assertFalse(result["pass"])
        self.assertEqual(result["error_kind"], "test_harness_missing")

    def test_06_replay_checks_runs_process_and_json(self):
        for runs in ("0", "1", "nope", "-1"):
            self.assertFalse(self.gate("sim-godot", "--replay", "--runs", runs)["pass"])
        for mode in ("crash", "malformed"):
            self.assertFalse(self.gate("sim-godot", "--replay", env={"FAKE_MODE": mode})["pass"])
        self.assertTrue(self.gate("sim-godot", "--replay")["pass"])
        self.assertTrue(self.gate("sim-godot", "--balance", "--seeds", "2")["pass"])
        self.assertFalse(self.gate("sim-godot", "--balance", "--seeds", "2", env={"FAKE_MODE": "partial"})["pass"])

    def test_07_stale_screenshot_and_empty_list_do_not_pass(self):
        shot = self.cwd / "shots/stale.png"
        shot.parent.mkdir(exist_ok=True)
        shot.write_bytes(b"old capture")
        self.assertFalse(self.gate("visual-godot", "--scene", "res://battle.tscn", "--out", "shots/stale.png", env={"FAKE_MODE": "crash"})["pass"])
        self.assertTrue(list((self.cwd / "archive/gp-shots").glob("*/stale.png")))
        (self.cwd / "art/shots.txt").write_text("# empty\n")
        self.assertFalse(self.gate("visual-godot", "--all")["pass"])
        self.assertTrue(self.gate("visual-godot", "--scene", "res://battle.tscn", "--out", str(shot))["pass"])

    def test_08_art_vertical_contract(self):
        ref = self.cwd / "art/style/reference/ref.png"
        Image.new("RGBA", (64, 64), (240, 200, 80, 255)).save(ref)
        self.assertTrue(self.gate("style-lock", "--lock")["pass"])
        spec = {"spec_version": 1, "id": "sample", "operation": "generate", "style_profile": "flat-vector",
                "tier": "B", "use_case": "test fixture", "asset_type": "tower", "subject": "test shape",
                "style_medium": "flat", "canvas": {"width": 64, "height": 64, "background": "transparent"},
                "constraints": ["flat"], "avoid": ["outline"], "reference_images": ["art/style/reference/ref.png"]}
        spec_path = self.cwd / "art/prompts/sample.json"
        write_json(spec_path, spec)
        self.assertEqual(self.gate("art-gen", "--spec", "art/prompts/sample.json")["action"], "human_in_the_loop")
        raw = self.cwd / "raw.png"
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        ImageDraw.Draw(img).rectangle((16, 16, 47, 47), fill=(240, 200, 80, 255))
        img.save(raw)
        self.assertTrue(self.gate("art-gen", "--spec", "art/prompts/sample.json", "--register", "raw.png")["pass"])
        prov_path = self.cwd / "assets/inbox/sample.provenance.json"
        prov = json.loads(prov_path.read_text())
        self.assertEqual(prov["operator"], "codex-desktop")
        args = ("--image", "assets/inbox/sample.png", "--profile", "flat-vector")
        self.assertFalse(self.gate("asset-validate", *args)["pass"])
        write_json(self.cwd / "art/style/palette.json", ["#f0c850"])
        result = self.gate("asset-validate", *args)
        self.assertTrue(result["pass"], result)
        bad = copy.deepcopy(prov)
        bad["prompt_spec_sha256"] = "0" * 64
        write_json(prov_path, bad)
        self.assertFalse(self.gate("asset-validate", *args)["pass"])
        write_json(prov_path, prov)
        Image.new("RGBA", (64, 64), (0, 0, 0, 0)).save(self.cwd / "assets/inbox/sample.png")
        self.assertFalse(self.gate("asset-validate", *args)["pass"])
        img.save(self.cwd / "assets/inbox/sample.png")
        ref.write_bytes(b"drift")
        self.assertFalse(self.gate("style-lock", "--verify")["pass"])
        self.assertFalse(self.gate("art-gen", "--spec", "art/prompts/sample.json")["pass"])
        self.assertFalse(self.gate("asset-validate", *args)["pass"])
        spec["id"] = "../../escaped"
        write_json(spec_path, spec)
        self.assertEqual(self.gate("art-gen", "--spec", "art/prompts/sample.json")["error_kind"], "spec_invalid")

    def test_09_personal_installer(self):
        dest = RUN / "personal skills"
        result = command([BASH, str(ROOT / "install-codex.sh"), "--skills-dir=" + str(dest)], ROOT)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue((dest / "gp-dev/SKILL.md").is_file())
        self.assertEqual(Path((dest / "gp-dev/generator-root.txt").read_text().strip()), ROOT)


if __name__ == "__main__":
    print("Regression artifacts:", RUN, flush=True)
    unittest.main(verbosity=2)
