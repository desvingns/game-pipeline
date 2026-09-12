"""Static checks for the dual-harness game-pipeline marketplace packages."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()


class MarketplaceTests(unittest.TestCase):
    def test_catalogs_reference_existing_plugins(self):
        claude = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
        codex = json.loads((ROOT / ".agents/plugins/marketplace.json").read_text(encoding="utf-8"))
        self.assertEqual(claude["name"], "game-pipeline")
        self.assertEqual(codex["name"], "game-pipeline")
        self.assertEqual(claude["plugins"][0]["name"], "gp-dev")
        self.assertEqual(codex["plugins"][0]["name"], "gp-dev")
        self.assertEqual(claude["plugins"][0]["source"], "./claude-plugins/gp-dev")
        self.assertEqual(codex["plugins"][0]["source"]["path"], "./codex-plugins/gp-dev")
        self.assertTrue((ROOT / "claude-plugins/gp-dev/.claude-plugin/plugin.json").is_file())
        self.assertTrue((ROOT / "codex-plugins/gp-dev/.codex-plugin/plugin.json").is_file())

    def test_manifests_and_runtime_fallbacks(self):
        for rel, manifest_name in (
            ("claude-plugins/gp-dev", ".claude-plugin/plugin.json"),
            ("codex-plugins/gp-dev", ".codex-plugin/plugin.json"),
        ):
            root = ROOT / rel
            manifest = json.loads((root / manifest_name).read_text(encoding="utf-8"))
            self.assertEqual(manifest["name"], "gp-dev")
            self.assertEqual(manifest["version"], VERSION)
            self.assertTrue(manifest["skills"] == "./skills/")
            self.assertTrue((root / "skills/gp-dev/SKILL.md").is_file())
            self.assertTrue((root / "scripts/gp-bootstrap.sh").is_file())
            self.assertTrue((root / "generator/bootstrap.sh").is_file())
            if root.name == "gp-dev" and "claude-plugins" in root.parts:
                runtime = root / "commands/gp-runtime"
                self.assertTrue((root / "commands/gp.md").is_file())
            else:
                runtime = root / "skills/gp-dev/references/runtime"
                self.assertTrue((runtime / "router.md").is_file())
            for dimension in ("2d", "3d"):
                self.assertTrue((runtime / dimension / "manifest.tsv").is_file())
                self.assertTrue((runtime / dimension / "build.md").is_file())

    def test_adapters_have_no_render_markers(self):
        for package in (ROOT / "claude-plugins/gp-dev", ROOT / "codex-plugins/gp-dev"):
            for path in package.rglob("*"):
                if not path.is_file() or "generator" in path.parts:
                    continue
                if path.suffix not in {".md", ".json", ".tsv"}:
                    continue
                body = path.read_text(encoding="utf-8")
                self.assertNotIn("{{", body, path)
                self.assertNotIn("<!-- engine:", body, path)
                self.assertNotIn("<!-- tool:", body, path)
                self.assertNotIn("<!-- if ", body, path)

    def test_bundled_generator_has_expected_contract(self):
        for package in (ROOT / "claude-plugins/gp-dev", ROOT / "codex-plugins/gp-dev"):
            generator = package / "generator"
            self.assertEqual((generator / "VERSION").read_text(encoding="utf-8").strip(), VERSION)
            self.assertTrue((generator / "lib/preset.py").is_file())
            self.assertTrue((generator / "profiles/presets/2d-android.json").is_file())
            self.assertTrue((generator / "profiles/presets/3d-fps-windows.json").is_file())
            self.assertTrue((generator / "templates/dimensions/3d/scripts/gp_3d.py").is_file())

    def test_chain_is_codex_marketplace_behavior(self):
        codex = (ROOT / "codex-plugins/gp-dev/skills/gp-dev/SKILL.md").read_text(encoding="utf-8")
        router = (ROOT / "codex-plugins/gp-dev/skills/gp-dev/references/runtime/router.md").read_text(encoding="utf-8")
        claude = (ROOT / "claude-plugins/gp-dev/skills/gp-dev/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("--feature --next --chain", codex)
        self.assertIn("create_thread", codex)
        self.assertIn("empty transcript", codex)
        self.assertIn("--chain", router)
        self.assertIn("chain_unsupported_in_claude", claude)
        self.assertNotIn("create_thread", claude)
        claude_runtime = (ROOT / "claude-plugins/gp-dev/commands/gp-runtime/2d/contract-work.md").read_text(encoding="utf-8")
        codex_runtime = (ROOT / "codex-plugins/gp-dev/skills/gp-dev/references/runtime/2d/contract-work.md").read_text(encoding="utf-8")
        self.assertIn("create_thread", codex_runtime)
        self.assertNotIn("create_thread", claude_runtime)


if __name__ == "__main__":
    unittest.main(verbosity=2)
