"""Optional real Godot/Blender integration. Retains project, builds, logs, images.

Set GODOT_BIN and BLENDER_BIN, then python tests/test_fps_integration.py.
This fixture validates the generator integrations, not the quality of a full FPS.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from PIL import Image

os.environ.pop("PET_ARCHIVE_ROOT", None)  # pin the project-local archive
ROOT = Path(__file__).resolve().parents[1]
BASH = os.environ.get("GP_TEST_BASH", "bash")
ENV = {**os.environ, "GP_PYTHON": sys.executable, "MSYS2_ARG_CONV_EXCL": "*", "PYTHONUTF8": "1"}


def main():
    if not all(os.environ.get(name) for name in ("GODOT_BIN", "BLENDER_BIN")):
        raise SystemExit("Set GODOT_BIN and BLENDER_BIN to real executables")
    path = Path(tempfile.mkdtemp(prefix="fps-real-", dir=ROOT / "out"))
    (ROOT / "out/latest-fps-real.txt").write_text(str(path), encoding="utf-8")
    print("Real integration evidence:", path, flush=True)

    def command(args):
        return subprocess.run(args, cwd=path, env=ENV, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=360)

    result = command([BASH, str(ROOT / "bootstrap.sh"), "--preset=3d-fps-windows", "--tool=codex", "--prefix=fp", "--project-name=Integration", "--non-interactive", "--no-git"])
    if result.returncode:
        raise AssertionError(result.stdout + result.stderr)
    receipts = []

    def gate(name, *args, passed=True):
        result = command([BASH, str(path / ".codex/scripts" / ("fp-" + name + ".sh")), *args])
        if result.returncode or len(result.stdout.splitlines()) != 1:
            raise AssertionError(result.stdout + result.stderr)
        data = json.loads(result.stdout)
        receipts.append({"gate": name, "args": args, "result": data})
        (path / "integration-results.json").write_text(json.dumps(receipts, indent=2), encoding="utf-8")
        print(name, data.get("pass"), data.get("error_kind", ""), flush=True)
        if data["pass"] != passed:
            raise AssertionError(data)
        return data

    tools = gate("doctor")
    (path / "pipeline/toolchain.json").write_text(json.dumps({k: tools[k] for k in ("godot", "blender")}), encoding="utf-8")
    game = path / "game"
    game.mkdir()
    (game / "project.godot").write_text('''config_version=5
[application]
config/name="GP integration fixture"
run/main_scene="res://main.tscn"
[autoload]
GPExportQA="*res://tools/gates/export_bridge.gd"
[display]
window/size/viewport_width=1280
window/size/viewport_height=720
[rendering]
renderer/rendering_method="gl_compatibility"
''', encoding="utf-8")
    gate("fps-godot", "--init-harness")
    gate("runner-godot", passed=False)  # Empty suite/absent main scene cannot pass.
    gate("mesh-validate", "--all", passed=False)
    fixtures = ROOT / "tests/fixtures/fps"
    for source, target in (("rules.gd", "domain/rules.gd"), ("suite.gd", "tests/suite.gd"), ("replay.gd", "tests/gp_replay.gd"), ("main.gd", "main.gd")):
        dest = game / target
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(fixtures / source, dest)
    (game / "main.tscn").write_text('[gd_scene load_steps=2 format=3]\n[ext_resource type="Script" path="res://main.gd" id="1"]\n[node name="Main" type="Node3D"]\nscript = ExtResource("1")\n')
    (game / "tests/gp_suites.json").write_text('["res://tests/suite.gd"]')
    (game / "tests/gp_scenarios.json").write_text(json.dumps({name: "res://main.tscn" for name in ("smoke", "movement", "visual", "perf")}))
    recipe = path / "tools/blender/fixture.py"
    recipe.parent.mkdir(parents=True)
    shutil.copy2(fixtures / "recipe.py", recipe)
    spec = {"spec_version": 1, "id": "fixture", "kind": "prop", "source": "tools/blender/fixture.py", "dependencies": [], "seed": 4242,
            "creator": {"tool": "integration-test", "model": "not-applicable"},
            "size_m": {"min": [0.9]*3, "max": [1.1]*3}, "animations": [], "collision": "convex"}
    (path / "art/prompts/fixture.json").write_text(json.dumps(spec))
    gate("mesh-build", "--spec", "art/prompts/fixture.json", passed=False)
    # Synthetic approved test fixture; this does not approve a user's art direction.
    Image.new("RGB", (64, 64), (220, 100, 30)).save(path / "art/style/reference/fixture.png")
    gate("style-lock", "--lock")
    gate("mesh-build", "--spec", "art/prompts/fixture.json", "--timeout", "180")
    gate("mesh-validate", "--all")
    gate("runner-godot")
    gate("sim-godot", "--replay")
    for scenario in ("smoke", "movement", "visual", "perf"):
        gate("fps-godot", "--scenario", scenario)
    gate("fps-godot", "--scenario", "combat", passed=False)  # Not registered, no substitute.
    (game / "export_presets.cfg").write_text('''[preset.0]
name="Windows Desktop"
platform="Windows Desktop"
runnable=true
export_filter="all_resources"
include_filter="tests/*.json"
exclude_filter=""
export_path=""
[preset.0.options]
binary_format/architecture="x86_64"
binary_format/embed_pck=true
debug/export_console_wrapper=0
application/modify_resources=false
''', encoding="utf-8")
    gate("runner-godot", "--export", "--out", "build/package/fixture.exe")
    asset = game / "assets/models/fixture.glb"
    original = asset.read_bytes()
    asset.write_bytes(original + b"tampered")
    gate("mesh-validate", "--all", passed=False)
    asset.write_bytes(original)
    original_recipe = recipe.read_bytes()
    recipe.write_text(recipe.read_text() + "\n# source drift\n")
    gate("mesh-validate", "--all", passed=False)
    recipe.write_bytes(original_recipe)
    print("Real integration passed. Evidence:", path, flush=True)


if __name__ == "__main__":
    main()
