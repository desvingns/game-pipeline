"""Existing project and dual-tool installation behavior, retained fixtures."""
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
import uuid

os.environ.pop("PET_ARCHIVE_ROOT", None)  # pin the project-local archive
ROOT = Path(__file__).resolve().parents[1]
BASH = os.environ.get("GP_TEST_BASH", "bash")


class AdoptionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = ROOT / "out/adoption" / ("existing game " + uuid.uuid4().hex)
        cls.root.mkdir(parents=True)
        cls.originals = {
            "AGENTS.md": "# Existing project\nKeep domain/data/presentation/app.\n",
            "HANDOFF.md": "# State\nNo tasks have been started.\n",
            "project.godot": '[application]\nconfig/name="Existing"\n',
            "SPECS/backlog/TASK-1.md": "# TASK-1 — Preserve the task\n\n## Acceptance criteria\n1. It works.\n",
            "SPECS/INDEX.md": "# Board\n\n| [TASK-1](backlog/TASK-1.md) | BACKLOG |\n",
            "domain/rule.gd": "extends RefCounted\n",
            "data/.keep": "", "presentation/.keep": "", "app/.keep": "",
        }
        for name, body in cls.originals.items():
            path = cls.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body, encoding="utf-8", newline="\n")
        for tool in ("codex", "claude"):
            args = [BASH, str(ROOT / "bootstrap.sh"), "--adopt", "--tool=" + tool, "--prefix=gt",
                    "--project-name=Existing", "--package=com.example.existing", "--non-interactive", "--no-git", "--skip-memory", "--blender-assets"]
            proc = subprocess.run(args, cwd=cls.root, capture_output=True, text=True, encoding="utf-8", errors="replace",
                                  env={**os.environ, "GP_PYTHON": sys.executable, "MSYS2_ARG_CONV_EXCL": "*"})
            (cls.root / (tool + "-install.log")).write_text(proc.stdout + proc.stderr, encoding="utf-8")
            if proc.returncode:
                raise AssertionError(proc.stdout + proc.stderr)

    def test_original_game_and_board_preserved(self):
        for name, expected in self.originals.items():
            self.assertEqual(expected, (self.root / name).read_text(encoding="utf-8"))
        self.assertFalse((self.root / ".codex/specs").exists())
        self.assertFalse((self.root / ".claude/specs").exists())

    def test_adopts_architecture_and_root(self):
        config = json.loads((self.root / "pipeline/project.json").read_text())
        self.assertEqual(".", config["project_dir"])
        self.assertEqual("clean", config["architecture"]["profile"])
        self.assertEqual("domain", config["architecture"]["layers"]["domain"])
        self.assertTrue(config["art"]["blender"])

    def test_independent_model_policy_and_blender_module(self):
        policy = json.loads((self.root / "pipeline/model-policy.json").read_text())
        self.assertEqual(("claude-sonnet-5", "medium"), tuple(policy["claude"]["tiers"]["simple"].values()))
        self.assertEqual("claude-opus-5", policy["claude"]["tiers"]["expert"]["model"])
        developer = (self.root / ".claude/agents/gt-developer-godot.md").read_text(encoding="utf-8")
        self.assertIn("\nmodel: claude-sonnet-5\neffort: xhigh\n", developer)
        self.assertEqual("gpt-5.6-luna", policy["tiers"]["simple"]["model"])
        for tool in ("codex", "claude"):
            path = self.root / ("." + tool)
            self.assertTrue((path / "scripts/gt-mesh-build.sh").exists())
            self.assertTrue((path / "scripts/gp_3d.py").exists())
            self.assertFalse((path / "commands/gt-runtime/contract-3d.md").exists())

    def test_actual_installed_cli_finds_existing_task(self):
        for tool in ("codex", "claude"):
            proc = subprocess.run([BASH, str(self.root / ("." + tool) / "scripts/gt-work.sh"), "next"], cwd=self.root,
                                  capture_output=True, text=True, encoding="utf-8", errors="replace",
                                  env={**os.environ, "GP_PYTHON": sys.executable, "MSYS2_ARG_CONV_EXCL": "*"})
            self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
            self.assertEqual("TASK-1", json.loads(proc.stdout)["selected"]["id"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
