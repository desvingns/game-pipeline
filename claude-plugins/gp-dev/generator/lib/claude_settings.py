"""Merge project-scoped Claude Code permission rules for installed pipeline scripts.

Usage: claude_settings.py PROJECT_ROOT PREFIX ARCHIVE_DIR

Rules are added to .claude/settings.json; existing keys and rules are never removed.
Image generation keeps the default prompt (paid external API) and STYLE LOCK --lock
always asks (hard human gate). An existing file is archived before it changes.
"""
import json
from pathlib import Path
import shutil
import sys


def rules(root, prefix):
    allow, ask = [], []
    for script in sorted((root / ".claude/scripts").glob(prefix + "-*.sh")):
        name = script.stem[len(prefix) + 1:]
        command = "bash .claude/scripts/" + script.name
        if name in {"common", "art-gen"}:
            continue  # common is sourced; art-gen calls a paid external image API
        if name == "style-lock":
            allow.append(f"Bash({command} --verify *)")
            ask.append(f"Bash({command} *--lock*)")
        else:
            allow.append(f"Bash({command} *)")
    return allow, ask


def merge(root, prefix, archive):
    root, archive = Path(root), Path(archive)
    path = root / ".claude/settings.json"
    existing = path.is_file()
    allow, ask = rules(root, prefix)
    try:
        settings = json.loads(path.read_text(encoding="utf-8-sig")) if existing else {}
    except ValueError:
        settings = None
    permissions = settings.get("permissions", {}) if isinstance(settings, dict) else None
    if not isinstance(permissions, dict) or any(not isinstance(permissions.get(key, []), list) for key in ("allow", "ask")):
        print("Preserved unreadable .claude/settings.json; add these rules manually: "
              + json.dumps({"allow": allow, "ask": ask}), file=sys.stderr)
        return {"allow": [], "ask": []}
    added = {}
    for key, wanted in (("allow", allow), ("ask", ask)):
        current = permissions.get(key, [])
        added[key] = [rule for rule in wanted if rule not in current]
        if added[key]:
            permissions[key] = current + added[key]
    if added["allow"] or added["ask"]:
        if existing:
            backup = archive / ".claude/settings.json"
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, backup)
        settings["permissions"] = permissions
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(settings, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    return added


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    try:
        merge(*sys.argv[1:])
    except OSError as exc:
        sys.exit("claude settings: " + str(exc))
