#!/usr/bin/env bash
# build-marketplace.sh — emit the Claude Code and Codex marketplace adapters.
#
# The generator templates remain canonical. This script creates one gp-dev plugin
# for each harness, the two marketplace catalogs, and a self-contained generator
# copy so a git-sourced plugin can bootstrap a fresh game without a checkout of
# the source repository. Existing generated trees are moved to archive/ before
# replacement; nothing is deleted.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION="$(tr -d '[:space:]' < "$ROOT/VERSION")"
COMMON="$ROOT/templates/common"
DIM3D="$ROOT/templates/dimensions/3d"
MARKET="$ROOT/templates/marketplace"

# shellcheck source=lib/render.sh
. "$ROOT/lib/render.sh"

DRY=0
CHECK=0
case "${1:-}" in
    "") ;;
    --dry-run) DRY=1 ;;
    --check) CHECK=1 ;;
    *) echo "usage: $0 [--dry-run|--check]" >&2; exit 2 ;;
esac

ARCHIVE_DIR=""
WORK=""

archive_existing() {
    local path="$1" rel dest
    [ -e "$path" ] || return 0
    [ -n "$ARCHIVE_DIR" ] || { echo "archive directory is not initialized" >&2; return 1; }
    rel="${path#"$ROOT"/}"
    dest="$ARCHIVE_DIR/previous/$rel"
    mkdir -p "$(dirname "$dest")"
    if [ -e "$dest" ]; then dest="$dest.$(date -u +%H%M%S)-$$"; fi
    mv "$path" "$dest"
}

copy_tree() {
    local src="$1" dst="$2" f rel
    [ -d "$src" ] || return 0
    while IFS= read -r -d '' f; do
        rel="${f#"$src"/}"
        case "$rel" in
            */__pycache__/*|__pycache__/*|*.pyc) continue ;;
        esac
        mkdir -p "$dst/$(dirname "$rel")"
        cp "$f" "$dst/$rel"
    done < <(find "$src" -type f -print0)
}

copy_file() {
    local src="$1" dst="$2"
    mkdir -p "$(dirname "$dst")"
    cp "$src" "$dst"
}

write_vars() {
    local tool="$1" agent_dir root_doc invocation
    if [ "$tool" = claude ]; then
        agent_dir=.claude; root_doc=CLAUDE.md; invocation=/gp
    else
        agent_dir=.codex; root_doc=AGENTS.md; invocation='\$gp-dev'
    fi
    printf '%s\n' \
        "PREFIX=gp" \
        "PROJECT_NAME=the game repository" \
        "PROJECT_DESCRIPTION=the approved game brief" \
        "PACKAGE=not applicable" \
        "ENGINE=godot" \
        "UI_LANGUAGE=en" \
        "MEMORY_PATH=.ai/memory" \
        "TODAY=marketplace" \
        "GP_VERSION=$VERSION" \
        "AGENT_DIR=$agent_dir" \
        "ROOT_DOC=$root_doc" \
        "INVOCATION=$invocation" \
        "SKILL_NAME=gp-dev" \
        "PRESET=selected-preset" \
        "DIMENSION=selected-dimension" \
        "PLATFORM=selected-platform" \
        "ART_PIPELINE=selected-art-pipeline" \
        "GENRE=selected-genre" \
        "NETWORK=selected-network" \
        "EXPORT_PRESET=selected-export" \
        "EXPORT_EXT=selected-package"
}

render_markdown() {
    local src="$1" dst="$2" tool="$3" vars="$4"
    mkdir -p "$(dirname "$dst")"
    cp "$src" "$dst"
    render_file "$dst" "$vars"
    if [ "$tool" = claude ]; then
        strip_tool_block "$dst" codex
        strip_tool_markers "$dst" claude
    else
        strip_tool_block "$dst" claude
        strip_tool_markers "$dst" codex
    fi
}

write_plugin_manifest() {
    local file="$1"
    mkdir -p "$(dirname "$file")"
    cat > "$file" <<EOF
{
  "name": "gp-dev",
  "version": "$VERSION",
  "description": "Godot 2D Android and Blender-based 3D Windows FPS game pipeline.",
  "author": {
    "name": "Kirill Shavrin",
    "email": "desvingns@gmail.com",
    "url": "https://github.com/desvingns"
  },
  "homepage": "https://github.com/desvingns/game-pipeline",
  "repository": "https://github.com/desvingns/game-pipeline",
  "license": "MIT",
  "keywords": ["games", "godot", "blender", "3d", "fps", "windows", "android", "pipeline"],
  "skills": "./skills/",
  "interface": {
    "displayName": "Game Pipeline",
    "shortDescription": "Build Godot 2D and 3D games with deterministic gates",
    "longDescription": "Bootstrap and run a single AI-first game workflow for Godot 4: 2D Android games or Blender-based 3D Windows FPS games, with style lock, asset provenance, replay, QA, performance and export gates.",
    "developerName": "Kirill Shavrin",
    "category": "Developer Tools",
    "capabilities": ["Interactive", "Write"],
    "defaultPrompt": [
      "Bootstrap a Godot 2D Android game through Game Pipeline",
      "Build a Blender-based 3D Windows FPS",
      "Run the selected Game Pipeline gates"
    ],
    "brandColor": "#0F766E"
  }
}
EOF
}

write_marketplaces() {
    cat > "$ROOT/.claude-plugin/marketplace.json" <<EOF
{
  "name": "game-pipeline",
  "owner": {
    "name": "Kirill Shavrin",
    "email": "desvingns@gmail.com"
  },
  "metadata": {
    "description": "Reusable Godot game pipeline for 2D Android and 3D Windows FPS projects. The gp-dev plugin bootstraps and routes one production workflow.",
    "version": "$VERSION"
  },
  "plugins": [
    {
      "name": "gp-dev",
      "source": "./claude-plugins/gp-dev",
      "description": "Game Pipeline front door for Godot 2D Android and Blender-based 3D Windows FPS games: bootstrap, build, style lock, art provenance, deterministic gates and export.",
      "category": "internal",
      "tags": ["games", "godot", "blender", "3d", "fps", "windows", "android", "pipeline"]
    }
  ]
}
EOF
    cat > "$ROOT/.agents/plugins/marketplace.json" <<EOF
{
  "name": "game-pipeline",
  "interface": {
    "displayName": "Game Pipeline"
  },
  "plugins": [
    {
      "name": "gp-dev",
      "source": {
        "source": "local",
        "path": "./codex-plugins/gp-dev"
      },
      "policy": {
        "installation": "AVAILABLE",
        "authentication": "ON_INSTALL"
      },
      "category": "Developer Tools"
    }
  ]
}
EOF
}

copy_generator() {
    local dst="$1" dir
    mkdir -p "$dst/generator"
    copy_file "$ROOT/bootstrap.sh" "$dst/generator/bootstrap.sh"
    copy_file "$ROOT/VERSION" "$dst/generator/VERSION"
    for dir in lib profiles schemas templates; do copy_tree "$ROOT/$dir" "$dst/generator/$dir"; done
    mkdir -p "$dst/generator/docs"
    copy_file "$ROOT/docs/USAGE.md" "$dst/generator/docs/USAGE.md"
    copy_file "$ROOT/docs/3D-WINDOWS.md" "$dst/generator/docs/3D-WINDOWS.md"
    chmod +x "$dst/generator/bootstrap.sh"
}

write_wrapper() {
    local dst="$1"
    mkdir -p "$(dirname "$dst")"
    cat > "$dst" <<'EOF'
#!/usr/bin/env bash
# Resolve the generator bundled with this plugin and forward every argument.
set -euo pipefail
PLUGIN_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec bash "$PLUGIN_ROOT/generator/bootstrap.sh" "$@"
EOF
    chmod +x "$dst"
}

build_runtime() {
    local dst="$1" tool="$2" dimension="$3" vars="$4" f base
    for f in "$COMMON"/commands/runtime/*.md; do
        [ -f "$f" ] || continue
        base="$(basename "$f")"
        if [ "$dimension" = 3d ] && [ "$base" = contract-art.md ]; then continue; fi
        render_markdown "$f" "$dst/$base" "$tool" "$vars"
        if [ "$dimension" = 2d ]; then
            strip_engine_block "$dst/$base" 3d
            strip_engine_markers "$dst/$base" 2d
        else
            strip_engine_block "$dst/$base" 2d
            strip_engine_markers "$dst/$base" 3d
        fi
    done
    if [ "$dimension" = 3d ]; then
        for f in "$DIM3D"/runtime/*.md; do
            [ -f "$f" ] || continue
            base="$(basename "$f")"
            render_markdown "$f" "$dst/$base" "$tool" "$vars"
            if [ "$dimension" = 2d ]; then
                strip_engine_block "$dst/$base" 3d
                strip_engine_markers "$dst/$base" 2d
            else
                strip_engine_block "$dst/$base" 2d
                strip_engine_markers "$dst/$base" 3d
            fi
        done
    fi
    cp "$COMMON/commands/runtime/manifest.tsv" "$dst/manifest.tsv"
}

build_plugin() {
    local tool="$1" dst="$2" vars="$3"
    mkdir -p "$dst"
    if [ "$tool" = claude ]; then
        write_plugin_manifest "$dst/.claude-plugin/plugin.json"
        render_markdown "$MARKET/gp.md.tmpl" "$dst/commands/gp.md" claude "$vars"
        render_markdown "$MARKET/SKILL.md.tmpl" "$dst/skills/gp-dev/SKILL.md" claude "$vars"
        build_runtime "$dst/commands/gp-runtime/2d" claude 2d "$vars"
        build_runtime "$dst/commands/gp-runtime/3d" claude 3d "$vars"
    else
        write_plugin_manifest "$dst/.codex-plugin/plugin.json"
        render_markdown "$MARKET/SKILL.md.tmpl" "$dst/skills/gp-dev/SKILL.md" codex "$vars"
        render_markdown "$MARKET/gp.md.tmpl" "$dst/skills/gp-dev/references/runtime/router.md" codex "$vars"
        build_runtime "$dst/skills/gp-dev/references/runtime/2d" codex 2d "$vars"
        build_runtime "$dst/skills/gp-dev/references/runtime/3d" codex 3d "$vars"
    fi
    copy_generator "$dst"
    write_wrapper "$dst/scripts/gp-bootstrap.sh"
}

validate_output() {
    local path="$1" tool="$2" manifest runtime dimension
    if [ "$tool" = claude ]; then manifest="$path/.claude-plugin/plugin.json"; else manifest="$path/.codex-plugin/plugin.json"; fi
    [ -f "$manifest" ] || { echo "marketplace-check: missing $manifest" >&2; return 1; }
    [ -f "$path/scripts/gp-bootstrap.sh" ] || { echo "marketplace-check: missing bootstrap wrapper" >&2; return 1; }
    [ -f "$path/generator/bootstrap.sh" ] || { echo "marketplace-check: missing bundled generator" >&2; return 1; }
    if [ "$tool" = claude ]; then runtime="$path/commands/gp-runtime"; else runtime="$path/skills/gp-dev/references/runtime"; fi
    for dimension in 2d 3d; do
        [ -f "$runtime/$dimension/manifest.tsv" ] || {
            echo "marketplace-check: missing runtime manifest: $runtime/$dimension/manifest.tsv" >&2
            return 1
        }
    done
}

if [ "$CHECK" = 1 ]; then
    python3 - "$ROOT/.claude-plugin/marketplace.json" "$ROOT/.agents/plugins/marketplace.json" <<'PY'
import json, sys
for path in sys.argv[1:]:
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
    assert data["name"] == "game-pipeline"
    assert data["plugins"][0]["name"] == "gp-dev"
print("marketplace-check: catalogs valid")
PY
    validate_output "$ROOT/claude-plugins/gp-dev" claude
    validate_output "$ROOT/codex-plugins/gp-dev" codex
    exit 0
fi

if [ "$DRY" = 0 ]; then
    stamp="$(date -u +%Y%m%dT%H%M%SZ)-$$"
    ARCHIVE_DIR="$ROOT/archive/marketplace/$stamp"
    WORK="$ARCHIVE_DIR/work"
    mkdir -p "$WORK"
    archive_existing "$ROOT/claude-plugins/gp-dev"
    archive_existing "$ROOT/codex-plugins/gp-dev"
fi

if [ "$DRY" = 1 ]; then
    echo "build-marketplace: dry-run (gp-dev Claude + Codex, v$VERSION)"
    echo "  would write .claude-plugin/marketplace.json"
    echo "  would write .agents/plugins/marketplace.json"
    echo "  would write claude-plugins/gp-dev and codex-plugins/gp-dev"
    exit 0
fi

mkdir -p "$ROOT/claude-plugins/gp-dev" "$ROOT/codex-plugins/gp-dev"
CLAUDE_VARS="$WORK/claude-vars.txt"
CODEX_VARS="$WORK/codex-vars.txt"
write_vars claude > "$CLAUDE_VARS"
write_vars codex > "$CODEX_VARS"
build_plugin claude "$ROOT/claude-plugins/gp-dev" "$CLAUDE_VARS"
build_plugin codex "$ROOT/codex-plugins/gp-dev" "$CODEX_VARS"
write_marketplaces
validate_output "$ROOT/claude-plugins/gp-dev" claude
validate_output "$ROOT/codex-plugins/gp-dev" codex
echo "build-marketplace: wrote gp-dev Claude + Codex adapters, v$VERSION (archive: ${ARCHIVE_DIR#"$ROOT"/})"
