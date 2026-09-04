#!/usr/bin/env bash
# Install a thin personal entry point; project runtime is frozen by bootstrap.
set -euo pipefail
GP_SOURCE_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
SKILLS_ROOT="${CODEX_HOME:-$HOME/.codex}/skills"
for arg in "$@"; do
    case "$arg" in
        --skills-dir=*) SKILLS_ROOT="${arg#*=}" ;;
        --help) printf 'Usage: bash install-codex.sh [--skills-dir=/path/to/skills]\n'; exit 0 ;;
        *) printf 'Unknown argument: %s\n' "$arg" >&2; exit 1 ;;
    esac
done
[ -n "$SKILLS_ROOT" ] || { echo "Skills directory must not be empty." >&2; exit 1; }
mkdir -p "$SKILLS_ROOT"
DEST="$SKILLS_ROOT/gp-dev"
if [ -e "$DEST" ]; then
    mkdir -p "$SKILLS_ROOT/archive"
    BACKUP=$(mktemp -d "$SKILLS_ROOT/archive/gp-dev.XXXXXX")
    cp -R "$DEST" "$BACKUP/"
fi
mkdir -p "$DEST"
cp "$GP_SOURCE_ROOT/skills/gp-dev/SKILL.md" "$DEST/SKILL.md"
# A Windows Python/Codex process needs a native absolute path, not /d/...
if command -v cygpath >/dev/null 2>&1; then
    cygpath -m "$GP_SOURCE_ROOT" > "$DEST/generator-root.txt"
else
    printf '%s\n' "$GP_SOURCE_ROOT" > "$DEST/generator-root.txt"
fi
printf 'Installed gp-dev at %s\nInvoke $gp-dev in Codex to install or run a game pipeline.\n' "$DEST"
