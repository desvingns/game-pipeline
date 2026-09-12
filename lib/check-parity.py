"""Check bundled generator bytes against canonical sources, without mutation."""
import hashlib
import json
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[1]
files = [root / name for name in ("bootstrap.sh", "VERSION", "AGENTS.md")]
files.extend(root / "docs" / name for name in ("USAGE.md", "3D-WINDOWS.md", "WORKFLOW.md"))
for folder in ("lib", "profiles", "schemas", "templates"):
    files.extend(p for p in (root / folder).rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc")
errors = []
for package in ("claude-plugins/gp-dev", "codex-plugins/gp-dev"):
    for path in files:
        relative = path.relative_to(root)
        bundled = root / package / "generator" / relative
        if not bundled.is_file() or hashlib.sha256(path.read_bytes()).digest() != hashlib.sha256(bundled.read_bytes()).digest():
            errors.append(str(Path(package) / "generator" / relative))
print(json.dumps({"pass": not errors, "checked_files": len(files) * 2, "mismatches": errors}))
sys.exit(1 if errors else 0)
