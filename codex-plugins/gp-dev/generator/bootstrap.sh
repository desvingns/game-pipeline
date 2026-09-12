#!/usr/bin/env bash
# bootstrap.sh — generate a game pipeline (agents + orchestrator + gates + art
# subsystem) from gp templates into the current directory.
#
# Usage: see docs/USAGE.md, or pass --help.
# Cross-platform: Linux, macOS, Windows Git Bash.

set -e

# ----- locate self & source libs -----------------------------------------
SCRIPT_PATH="${BASH_SOURCE[0]:-$0}"
TEMPLATES_ROOT=$(cd "$(dirname "$SCRIPT_PATH")" && pwd)
LIB_DIR="$TEMPLATES_ROOT/lib"

# shellcheck source=lib/detect.sh
. "$LIB_DIR/detect.sh"
# shellcheck source=lib/prompts.sh
. "$LIB_DIR/prompts.sh"
# shellcheck source=lib/render.sh
. "$LIB_DIR/render.sh"
. "$LIB_DIR/codex.sh"
. "$LIB_DIR/claude.sh"

# ----- parse args --------------------------------------------------------
ENGINE="godot"
TOOL="claude"
PREFIX=""
PROJECT_NAME=""
PROJECT_DESCRIPTION=""
PACKAGE=""
UI_LANG="en"
MEMORY_PATH=""
PRESET="2d-android"
GENRE=""
NETWORK="offline"
PROJECTION=""
STYLE_PROFILE=""
FORCE=0
DRY_RUN=0
SKIP_MEMORY=0
NON_INTERACTIVE=0
NO_GIT=0
ADOPT=0
BLENDER_ASSETS=0
PREVIEW=0

while [ $# -gt 0 ]; do
    case "$1" in
        --engine=*)              ENGINE="${1#*=}" ;;
        --tool=*)                TOOL="${1#*=}" ;;
        --prefix=*)              PREFIX="${1#*=}" ;;
        --project-name=*)        PROJECT_NAME="${1#*=}" ;;
        --project-description=*) PROJECT_DESCRIPTION="${1#*=}" ;;
        --package=*)             PACKAGE="${1#*=}" ;;
        --ui-lang=*)             UI_LANG="${1#*=}" ;;
        --memory-path=*)         MEMORY_PATH="${1#*=}" ;;
        --projection=*)          PROJECTION="${1#*=}" ;;
        --preset=*)              PRESET="${1#*=}" ;;
        --genre=*)               GENRE="${1#*=}" ;;
        --network=*)             NETWORK="${1#*=}" ;;
        --style-profile=*)       STYLE_PROFILE="${1#*=}" ;;
        --force)                 FORCE=1 ;;
        --dry-run)               DRY_RUN=1 ;;
        --skip-memory)           SKIP_MEMORY=1 ;;
        --non-interactive)       NON_INTERACTIVE=1 ;;
        --no-git)                NO_GIT=1 ;;
        --adopt)                 ADOPT=1 ;;
        --blender-assets)        BLENDER_ASSETS=1 ;;
        --preview)               PREVIEW=1 ;;
        --help|-h)               cat "$TEMPLATES_ROOT/docs/USAGE.md"; exit 0 ;;
        *) echo "Unknown flag: $1 (use --help)" >&2; exit 1 ;;
    esac
    shift
done

# ----- interactive prompts if required flags missing ---------------------
maybe_prompt() {
    local current="$1" name="$2" pattern="${3:-.+}"
    if [ -z "$current" ]; then
        if [ "$NON_INTERACTIVE" -eq 1 ]; then
            echo "Missing required: --${name}" >&2; exit 1
        fi
        prompt_required "$name" "$pattern"
    else
        printf '%s' "$current"
    fi
}

PREFIX=$(maybe_prompt "$PREFIX" "prefix" "^[a-z][a-z0-9_]{0,7}$")
PROJECT_NAME=$(maybe_prompt "$PROJECT_NAME" "project-name")
# Resolve only catalogue entries. Python is used as a JSON reader, never eval.
PRESET_PYTHON="${GP_PYTHON:-}"
if [ -z "$PRESET_PYTHON" ]; then
    for candidate in python3 python py; do
        if "$candidate" -c 'import sys' >/dev/null 2>&1; then PRESET_PYTHON="$candidate"; break; fi
    done
fi
[ -n "$PRESET_PYTHON" ] || { echo "Python 3 is required to read preset JSON; set GP_PYTHON." >&2; exit 1; }
PRESET_SCRIPT="$LIB_DIR/preset.py"
PRESET_ROOT="$TEMPLATES_ROOT"
if command -v cygpath >/dev/null 2>&1; then
    PRESET_SCRIPT=$(cygpath -m "$PRESET_SCRIPT"); PRESET_ROOT=$(cygpath -m "$PRESET_ROOT")
fi
PRESET_VALUES=$("$PRESET_PYTHON" "$PRESET_SCRIPT" "$PRESET_ROOT" "$PRESET" "$GENRE" "$NETWORK") || exit 1
while IFS='=' read -r key value; do
    value="${value%$'\r'}"
    case "$key" in
        DIMENSION|PLATFORM|ART_PIPELINE|GENRE|NETWORK|DEFAULT_STYLE|DEFAULT_PROJECTION|EXPORT_PRESET|EXPORT_EXT)
            printf -v "$key" '%s' "$value" ;;
        *) echo "Invalid preset key." >&2; exit 1 ;;
    esac
done <<< "$PRESET_VALUES"
[ -n "$STYLE_PROFILE" ] || STYLE_PROFILE="$DEFAULT_STYLE"
[ -n "$PROJECTION" ] || PROJECTION="$DEFAULT_PROJECTION"
if [ "$PLATFORM" = android ]; then
    PACKAGE=$(maybe_prompt "$PACKAGE" "package" "^[a-z]+(\.[a-z][a-z0-9_]*)+$")
fi
[ -z "$PROJECT_DESCRIPTION" ] && PROJECT_DESCRIPTION="(One-sentence game description — replace this placeholder.)"

# ----- validate ----------------------------------------------------------
[[ "$PREFIX" =~ ^[a-z][a-z0-9_]{0,7}$ ]] || { echo "Invalid prefix: use 1-8 lowercase letters, digits or underscores, starting with a letter." >&2; exit 1; }
if [ -n "$PACKAGE" ]; then
    [[ "$PACKAGE" =~ ^[a-z]+(\.[a-z][a-z0-9_]*)+$ ]] || { echo "Invalid Android package id." >&2; exit 1; }
fi
if [ "$DIMENSION" = 3d ]; then
    [ "$STYLE_PROFILE" = stylized-3d ] && [ "$PROJECTION" = perspective-fps ] || {
        echo "3D requires stylized-3d and perspective-fps profiles." >&2; exit 1;
    }
elif [ "$STYLE_PROFILE" = stylized-3d ] || [ "$PROJECTION" = perspective-fps ]; then
    echo "3D art/projection cannot be installed into a 2D preset." >&2; exit 1
fi
for value in "$PROJECT_NAME" "$PROJECT_DESCRIPTION" "$MEMORY_PATH" "$UI_LANG"; do
    case "$value" in *$'\n'*|*$'\r'*) echo "Arguments must be single-line values." >&2; exit 1 ;; esac
done
for value in "$STYLE_PROFILE" "$PROJECTION"; do
    [[ "$value" =~ ^[a-z0-9][a-z0-9-]*$ ]] || { echo "Invalid profile id." >&2; exit 1; }
done
case "$PREFIX" in
    init|clear|help|model|config|cost|review|security-review|loop|schedule|simplify)
        echo "Prefix '$PREFIX' conflicts with a built-in command — pick another." >&2; exit 1 ;;
esac
case "$ENGINE" in
    godot) ;;
    *) echo "Unsupported engine: $ENGINE (only 'godot' in v$(tr -d '[:space:]' < "$TEMPLATES_ROOT/VERSION"))." >&2; exit 1 ;;
esac
case "$TOOL" in
    claude|codex) ;;
    *) echo "Unsupported tool: $TOOL (claude|codex)." >&2; exit 1 ;;
esac
if [ ! -f "$TEMPLATES_ROOT/profiles/style/$STYLE_PROFILE.json" ]; then
    echo "Unknown style profile: $STYLE_PROFILE" >&2
    echo "Available: $(ls "$TEMPLATES_ROOT/profiles/style" | sed 's/\.json$//' | tr '\n' ' ')" >&2
    exit 1
fi
if [ ! -f "$TEMPLATES_ROOT/profiles/projection/$PROJECTION.json" ]; then
    echo "Unknown projection profile: $PROJECTION" >&2
    echo "Available: $(ls "$TEMPLATES_ROOT/profiles/projection" | sed 's/\.json$//' | tr '\n' ' ')" >&2
    exit 1
fi

if [ "$NO_GIT" -ne 1 ] && ! is_git_repo .; then
    echo "Warning: current directory is not a git repo." >&2
    echo "  The pipeline still bootstraps, but nothing can be committed or pushed." >&2
fi

# ----- derive vars -------------------------------------------------------
SANITISED_CWD=$(sanitise_path "$(pwd)")
DEST_ROOT=$(pwd)
TODAY=$(date +%Y-%m-%d)
GP_VERSION=$(tr -d '[:space:]' < "$TEMPLATES_ROOT/VERSION")
case "$TOOL" in
    claude) AGENT_DIR=".claude"; ROOT_DOC="CLAUDE.md"; INVOCATION="/$PREFIX"
            [ -n "$MEMORY_PATH" ] || MEMORY_PATH="$HOME/.claude/projects/$SANITISED_CWD/memory" ;;
    codex)  AGENT_DIR=".codex"; ROOT_DOC="AGENTS.md"; INVOCATION="\$${PREFIX//_/-}"
            [ -n "$MEMORY_PATH" ] || MEMORY_PATH="$DEST_ROOT/.ai/memory" ;;
esac
SKILL_NAME="${PREFIX//_/-}"
case "$MEMORY_PATH" in /*|[A-Za-z]:/*) ;; *) MEMORY_PATH="$DEST_ROOT/$MEMORY_PATH" ;; esac
if command -v cygpath >/dev/null 2>&1; then MEMORY_PATH=$(cygpath -m "$MEMORY_PATH"); fi

# ----- preflight ---------------------------------------------------------
# Profile switches require a deliberate migration in a fresh game directory.
# Otherwise old scripts, frozen art and append-only memory would contradict it.
for stamp in .codex/.gp-version .claude/.gp-version; do
    if [ -f "$stamp" ]; then
        old_preset=$(sed -n 's/^preset: //p' "$stamp")
        old_genre=$(sed -n 's/^genre: //p' "$stamp")
        old_network=$(sed -n 's/^network: //p' "$stamp")
        [ -n "$old_preset" ] || old_preset=2d-android
        [ -n "$old_genre" ] || old_genre=strategy
        [ -n "$old_network" ] || old_network=offline
        if [ "$old_preset/$old_genre/$old_network" != "$PRESET/$GENRE/$NETWORK" ]; then
            echo "Preset/genre/network migration requires a fresh target directory; --force only upgrades the same configuration." >&2; exit 2
        fi
    fi
done
if [ "$FORCE" -ne 1 ] && [ "$DRY_RUN" -ne 1 ] && [ "$ADOPT" -ne 1 ] && [ "$PREVIEW" -ne 1 ]; then
    for path in "$AGENT_DIR" "$ROOT_DOC" CLAUDE.md STATE.md ROADMAP.md DOCUMENTATION.md art ".agents/skills/$SKILL_NAME"; do
        if [ -e "$path" ]; then
            echo "Existing $path — use --force to overwrite." >&2; exit 2
        fi
    done
fi

# ----- dry-run preview ---------------------------------------------------
if [ "$DRY_RUN" -eq 1 ]; then
    echo "DRY RUN — would create:"
    echo "  $AGENT_DIR/agents/$PREFIX-{architect,game-designer,level-designer,economy,docs}.md"
    echo "  $AGENT_DIR/agents/$PREFIX-{art-director,art-prompter,asset-integrator}.md"
    echo "  $AGENT_DIR/agents/$PREFIX-{developer,animator,tester,runner,reviewer,verifier}-$ENGINE.md"
    echo "  $AGENT_DIR/commands/$PREFIX.md"
    echo "  $AGENT_DIR/commands/$PREFIX-runtime/*.md   (lazy-loaded mode runbooks)"
    if [ "$TOOL" = codex ]; then
        echo "  .agents/skills/$SKILL_NAME/SKILL.md       (invoke $INVOCATION)"
        echo "  .codex/agents/$PREFIX-*.toml             (native specialist adapters)"
        echo "  ./AGENTS.md                             (Codex project instructions)"
    fi
    echo "  $AGENT_DIR/scripts/$PREFIX-*.sh + *.py     (gate scripts)"
    echo "  SPECS/{backlog,done}/                   (shared board; discovered before first feature)"
    echo "  pipeline/project.json + model-policy.json (preserved project configuration)"
    echo "  Existing SPECS, game source, root documents and project configuration are preserved."
    if [ "$ADOPT" -eq 1 ]; then
        GP_WORK_SOURCE="$TEMPLATES_ROOT/templates/common/scripts/gp_work.py"
        GP_WORK_TARGET="$DEST_ROOT"
        if command -v cygpath >/dev/null 2>&1; then
            GP_WORK_SOURCE=$(cygpath -m "$GP_WORK_SOURCE"); GP_WORK_TARGET=$(cygpath -m "$GP_WORK_TARGET")
        fi
        "$PRESET_PYTHON" "$GP_WORK_SOURCE" --root "$GP_WORK_TARGET" adopt
    fi
    echo "  art/cards/{backlog,active,done}/           (art board)"
    echo "  art/style/profiles/*.json + art/schemas/*.json"
    echo "  art/style/reference/  art/prompts/  assets/inbox/"
    echo "  ./CLAUDE.md ./STATE.md ./ROADMAP.md ./DOCUMENTATION.md"
    [ "$SKIP_MEMORY" -ne 1 ] && echo "  $MEMORY_PATH/MEMORY.md + memos"
    echo ""
    echo "Vars resolved:"
    echo "  engine=$ENGINE tool=$TOOL prefix=$PREFIX package=$PACKAGE ui-lang=$UI_LANG"
    echo "  preset=$PRESET dimension=$DIMENSION platform=$PLATFORM genre=$GENRE network=$NETWORK"
    echo "  style-profile=$STYLE_PROFILE projection=$PROJECTION agent-dir=$AGENT_DIR"
    [ "$DIMENSION" != 3d ] || echo "  3D overlay: Blender tools, FPS roles, QA harness templates, Windows gates"
    exit 0
fi

[ "$DEST_ROOT" != "$TEMPLATES_ROOT" ] || { echo "Run bootstrap from a game repository, not the generator itself." >&2; exit 2; }
# Build in isolation: --force must never render existing user files or boards.
# Keep staging and overwritten versions in archive/; nothing is deleted.
mkdir -p archive/gp-bootstrap
STAGE=$(mktemp -d "$DEST_ROOT/archive/gp-bootstrap/run.XXXXXX")
mkdir -p "$STAGE/generated" "$STAGE/previous"
cd "$STAGE/generated"

# ----- build vars file for render_file ----------------------------------
VARS_FILE="$STAGE/render-vars.txt"
cat > "$VARS_FILE" <<EOF
PREFIX=$PREFIX
PROJECT_NAME=$PROJECT_NAME
PROJECT_DESCRIPTION=$PROJECT_DESCRIPTION
PACKAGE=$PACKAGE
ENGINE=$ENGINE
UI_LANGUAGE=$UI_LANG
MEMORY_PATH=$MEMORY_PATH
TODAY=$TODAY
GP_VERSION=$GP_VERSION
AGENT_DIR=$AGENT_DIR
STYLE_PROFILE=$STYLE_PROFILE
PROJECTION_PROFILE=$PROJECTION
ROOT_DOC=$ROOT_DOC
INVOCATION=$INVOCATION
SKILL_NAME=$SKILL_NAME
PRESET=$PRESET
DIMENSION=$DIMENSION
PLATFORM=$PLATFORM
ART_PIPELINE=$ART_PIPELINE
GENRE=$GENRE
NETWORK=$NETWORK
EXPORT_PRESET=$EXPORT_PRESET
EXPORT_EXT=$EXPORT_EXT
EOF

# ----- copy phase --------------------------------------------------------
mkdir -p "$AGENT_DIR/agents" "$AGENT_DIR/commands/$PREFIX-runtime" \
         "$AGENT_DIR/scripts" \
         art/style/profiles art/style/reference art/prompts art/schemas \
         art/cards assets/inbox

# 1. Agents: engine-neutral, art subsystem, engine-specific.
for src in "$TEMPLATES_ROOT"/templates/common/agents/*.md \
           "$TEMPLATES_ROOT"/templates/art/agents/*.md \
           "$TEMPLATES_ROOT"/templates/"$ENGINE"/agents/*.md; do
    [ -f "$src" ] || continue
    if [ "$DIMENSION" = 3d ] && [ -f "$TEMPLATES_ROOT/templates/dimensions/3d/agents/$(basename "$src")" ]; then
        src="$TEMPLATES_ROOT/templates/dimensions/3d/agents/$(basename "$src")"
    fi
    cp "$src" "$AGENT_DIR/agents/$(basename "$src")"
done

# 2. Orchestrator + lazily-loaded runbooks.
cp "$TEMPLATES_ROOT/templates/common/commands/{{PREFIX}}.md" "$AGENT_DIR/commands/{{PREFIX}}.md"
for src in "$TEMPLATES_ROOT"/templates/common/commands/runtime/*; do
    [ -f "$src" ] || continue
    if [ "$DIMENSION" = 3d ] && [ "$(basename "$src")" = contract-art.md ]; then continue; fi
    if [ "$DIMENSION" = 3d ] && [ -f "$TEMPLATES_ROOT/templates/dimensions/3d/runtime/$(basename "$src")" ]; then
        src="$TEMPLATES_ROOT/templates/dimensions/3d/runtime/$(basename "$src")"
    fi
    cp "$src" "$AGENT_DIR/commands/$PREFIX-runtime/$(basename "$src")"
done

# 3. Board reference. Never create SPECS before the discovery agent has inspected
# an absent board. Code cards are shared by both tools, not installed per-tool.
mkdir -p pipeline
cp "$TEMPLATES_ROOT/templates/common/specs/README.md" pipeline/spec-board.md
cp "$TEMPLATES_ROOT/templates/common/pipeline/model-policy.json" pipeline/model-policy.json
mkdir -p pipeline/schemas
cp "$TEMPLATES_ROOT"/schemas/work-*.schema.json pipeline/schemas/
for board in backlog active done; do
    mkdir -p "art/cards/$board"
    touch "art/cards/$board/.gitkeep"
done

# 4. Gate scripts: art subsystem + engine.
for src in "$TEMPLATES_ROOT"/templates/common/scripts/* \
           "$TEMPLATES_ROOT"/templates/art/scripts/* \
           "$TEMPLATES_ROOT"/templates/"$ENGINE"/scripts/*; do
    [ -f "$src" ] || continue
    base=$(basename "$src")
    if [ "$DIMENSION" = 3d ]; then
        case "$base" in
            *art-gen*|*asset-validate*|*sim-godot*|*visual-godot*) continue ;;
        esac
        if [ -f "$TEMPLATES_ROOT/templates/dimensions/3d/scripts/$base" ]; then
            src="$TEMPLATES_ROOT/templates/dimensions/3d/scripts/$base"
        fi
    fi
    cp "$src" "$AGENT_DIR/scripts/$base"
    chmod +x "$AGENT_DIR/scripts/$base"
done

# Dimension-specific additions are installed only for the selected target.
if [ "$DIMENSION" = 3d ]; then
    for src in "$TEMPLATES_ROOT"/templates/dimensions/3d/scripts/*; do
        [ -f "$src" ] || continue
        case "$src" in *.sh|*.py) cp "$src" "$AGENT_DIR/scripts/" ;; esac
    done
    for src in "$TEMPLATES_ROOT"/templates/dimensions/3d/runtime/*.md; do
        [ -f "$src" ] && cp "$src" "$AGENT_DIR/commands/$PREFIX-runtime/"
    done
    cp "$TEMPLATES_ROOT/profiles/genres/$GENRE.md" "$AGENT_DIR/commands/$PREFIX-runtime/genre.md"
    cp "$TEMPLATES_ROOT/profiles/network/$NETWORK.md" "$AGENT_DIR/commands/$PREFIX-runtime/network.md"
    mkdir -p pipeline/harness pipeline/blender
    for src in "$TEMPLATES_ROOT"/templates/dimensions/3d/harness/*; do
        [ -f "$src" ] || continue
        case "$src" in *.gd|*.cfg) cp "$src" pipeline/harness/ ;; esac
    done
    for src in "$TEMPLATES_ROOT"/templates/dimensions/3d/blender/*.py; do
        [ -f "$src" ] && cp "$src" pipeline/blender/
    done
    cp "$TEMPLATES_ROOT/profiles/qa/fps.json" pipeline/qa-contract.json
    if [ "$NETWORK" != offline ]; then
        # Additive network requirements; never silently treat offline bots as peers.
        "$PRESET_PYTHON" -c 'import json; from pathlib import Path; p=Path("pipeline/qa-contract.json"); d=json.loads(p.read_text()); d["scenarios"]["network"]=["two_process_peers","connect","replicate","authority","disconnect","rejoin"]; p.write_text(json.dumps(d,indent=2)+"\n")'
    fi
fi
# Blender asset production is independent from the game's dimension. 2D games
# may build meshes/pre-render sources without receiving FPS/world instructions.
if [ "$DIMENSION" = 2d ] && [ "$BLENDER_ASSETS" -eq 1 ]; then
    mkdir -p pipeline/blender
    cp "$TEMPLATES_ROOT"/templates/dimensions/3d/blender/*.py pipeline/blender/
    cp "$TEMPLATES_ROOT/templates/dimensions/3d/scripts/gp_mesh.py" "$AGENT_DIR/scripts/"
    cp "$TEMPLATES_ROOT/templates/dimensions/3d/scripts/gp_3d.py" "$AGENT_DIR/scripts/"
    for mesh_script in "$TEMPLATES_ROOT"/templates/dimensions/3d/scripts/*mesh*.sh; do
        cp "$mesh_script" "$AGENT_DIR/scripts/"
    done
    cp "$TEMPLATES_ROOT/profiles/style/stylized-3d.json" art/style/profiles/
    cp "$TEMPLATES_ROOT"/schemas/mesh-*.json art/schemas/
fi
mkdir -p pipeline
cat > pipeline/profile.json <<EOF
{"profile_version":1,"preset":"$PRESET","dimension":"$DIMENSION","platform":"$PLATFORM","art_pipeline":"$ART_PIPELINE","genre":"$GENRE","network":"$NETWORK","style":"$STYLE_PROFILE","projection":"$PROJECTION"}
EOF

# 5. Profiles and schemas are FROZEN into the project, not referenced from the
#    generator. A game must keep building the same way after gp moves on.
cp "$TEMPLATES_ROOT/profiles/style/$STYLE_PROFILE.json" "art/style/profiles/$STYLE_PROFILE.json"
cp "$TEMPLATES_ROOT/profiles/projection/$PROJECTION.json" "art/style/profiles/$PROJECTION.json"
for src in "$TEMPLATES_ROOT"/schemas/*.json; do
    if [ "$DIMENSION" = 2d ]; then
        case "$(basename "$src")" in mesh-*) continue ;; work-*) continue ;; esac
    else
        case "$(basename "$src")" in mesh-*) ;; *) continue ;; esac
    fi
    cp "$src" "art/schemas/$(basename "$src")"
done

# 6. Root docs (.tmpl -> strip extension).
for src in "$TEMPLATES_ROOT"/templates/common/root/*.md.tmpl; do
    if [ "$DIMENSION" = 3d ] && [ -f "$TEMPLATES_ROOT/templates/dimensions/3d/root/$(basename "$src")" ]; then
        src="$TEMPLATES_ROOT/templates/dimensions/3d/root/$(basename "$src")"
    fi
    base=$(basename "$src" .tmpl)
    [ "$base" != CLAUDE.md ] || base="$ROOT_DOC"
    cp "$src" "./$base"
done
if [ "$TOOL" = codex ]; then
    mkdir -p ".agents/skills/$SKILL_NAME"
    cp "$TEMPLATES_ROOT/templates/codex/SKILL.md.tmpl" ".agents/skills/$SKILL_NAME/SKILL.md"
    printf '# Claude adapter\n\n@AGENTS.md\n' > CLAUDE.md
fi

# ----- render phase: placeholders ---------------------------------------
# An array, not a string: a project directory may contain spaces, and word
# splitting a path list is the classic way a generator half-renders a tree.
RENDER_TARGETS=(
    "$AGENT_DIR"/agents/*.md
    "$AGENT_DIR"/commands/*.md
    "$AGENT_DIR"/commands/*/*.md
    pipeline/spec-board.md
    "$AGENT_DIR"/scripts/*
    ./CLAUDE.md ./AGENTS.md ./STATE.md ./ROADMAP.md ./DOCUMENTATION.md
    ".agents/skills/$SKILL_NAME/SKILL.md"
    pipeline/harness/* pipeline/blender/*
)

for f in "${RENDER_TARGETS[@]}"; do
    [ -f "$f" ] || continue
    render_file "$f" "$VARS_FILE"
done

# ----- render phase: conditional blocks ---------------------------------
ALL_ENGINES="godot unity"
ALL_TOOLS="claude codex"
strip_conditionals() {
    local f="$1" e t
    for e in $ALL_ENGINES; do
        if [ "$e" = "$ENGINE" ]; then strip_engine_markers "$f" "$e"; else strip_engine_block "$f" "$e"; fi
    done
    for t in $ALL_TOOLS; do
        if [ "$t" = "$TOOL" ]; then strip_tool_markers "$f" "$t"; else strip_tool_block "$f" "$t"; fi
    done
    for d in 2d 3d; do
        if [ "$d" = "$DIMENSION" ]; then strip_engine_markers "$f" "$d"; else strip_engine_block "$f" "$d"; fi
    done
    if [ "$UI_LANG" = "en" ]; then
        strip_if_block "$f" "UI_LANGUAGE != en"
    else
        strip_if_block "$f" "UI_LANGUAGE == en"
    fi
    strip_if_markers "$f"
}

for f in "${RENDER_TARGETS[@]}"; do
    [ -f "$f" ] || continue
    strip_conditionals "$f"
done

# ----- rename files: {{PREFIX}} in basename -----------------------------
# After content rendering, so file contents already carry the real prefix.
for f in "$AGENT_DIR"/agents/*.md "$AGENT_DIR"/commands/*.md "$AGENT_DIR"/scripts/*; do
    [ -f "$f" ] || continue
    base=$(basename "$f")
    case "$base" in
        *'{{PREFIX}}'*)
            new_base="${base//\{\{PREFIX\}\}/$PREFIX}"
            mv "$f" "$(dirname "$f")/$new_base"
            ;;
    esac
done

# Native adapters are derived from rendered, tool-neutral role bodies.
if [ "$TOOL" = codex ]; then emit_codex_agents "$AGENT_DIR/agents"; fi
# A preserved project policy, not the template, decides the pinned Claude tiers.
if [ "$TOOL" = claude ]; then
    CLAUDE_POLICY_ROOT="$STAGE/generated"
    [ ! -f "$DEST_ROOT/pipeline/model-policy.json" ] || CLAUDE_POLICY_ROOT="$DEST_ROOT"
    emit_claude_agents "$AGENT_DIR/agents" "$PREFIX" "$ENGINE" "$AGENT_DIR/scripts/gp_work.py" "$CLAUDE_POLICY_ROOT"
fi
for f in "$AGENT_DIR"/scripts/*.sh; do chmod +x "$f"; done

# Concrete reviewable upgrade diff, without deploying generated runtime files.
# Rendering is retained under archive; --dry-run remains the no-write outline.
if [ "$PREVIEW" -eq 1 ]; then
    GP_PREVIEW_SCRIPT="$STAGE/generated/$AGENT_DIR/scripts/gp_work.py"
    GP_PREVIEW_ROOT="$DEST_ROOT"
    GP_PREVIEW_STAGE="$STAGE/generated"
    if command -v cygpath >/dev/null 2>&1; then
        GP_PREVIEW_SCRIPT=$(cygpath -m "$GP_PREVIEW_SCRIPT")
        GP_PREVIEW_ROOT=$(cygpath -m "$GP_PREVIEW_ROOT")
        GP_PREVIEW_STAGE=$(cygpath -m "$GP_PREVIEW_STAGE")
    fi
    "$PRESET_PYTHON" "$GP_PREVIEW_SCRIPT" --root "$GP_PREVIEW_ROOT" upgrade-preview --generated "$GP_PREVIEW_STAGE"
    exit 0
fi

# Deploy only files generated by this run. Preserve project state and frozen art.
while IFS= read -r -d '' f; do
    rel="${f#./}"
    dst="$DEST_ROOT/$rel"
    if [ -f "$dst" ]; then
        case "$rel" in
            STATE.md|ROADMAP.md|DOCUMENTATION.md|art/*|SPECS/*|*/specs/*|pipeline/profile.json|pipeline/project.json|pipeline/model-policy.json|pipeline/qa-contract.json|pipeline/toolchain.json) continue ;;
            AGENTS.md|CLAUDE.md)
                if ! grep -qE 'Generated by game-pipeline|^# Claude adapter$' "$dst"; then
                    echo "Preserved existing $rel; see archive/gp-bootstrap/$(basename "$STAGE")/generated/$rel for pipeline instructions." >&2
                    continue
                fi ;;
        esac
        mkdir -p "$STAGE/previous/$(dirname "$rel")"
        cp "$dst" "$STAGE/previous/$rel"
    fi
    mkdir -p "$(dirname "$dst")"
    cp "$f" "$dst"
done < <(find . -type f -print0)
# Empty working directories are part of the bootstrap contract too.
while IFS= read -r -d '' d; do mkdir -p "$DEST_ROOT/${d#./}"; done < <(find . -type d -print0)
cd "$DEST_ROOT"
# Project-scoped allow rules for the pipeline's own scripts: merged, never replaced.
if [ "$TOOL" = claude ]; then merge_claude_settings "$DEST_ROOT" "$PREFIX" "$STAGE/previous"; fi
GP_WORK_SOURCE="$DEST_ROOT/$AGENT_DIR/scripts/gp_work.py"
GP_WORK_TARGET="$DEST_ROOT"
if command -v cygpath >/dev/null 2>&1; then
    GP_WORK_SOURCE=$(cygpath -m "$GP_WORK_SOURCE"); GP_WORK_TARGET=$(cygpath -m "$GP_WORK_TARGET")
fi
"$PRESET_PYTHON" "$GP_WORK_SOURCE" --root "$GP_WORK_TARGET" adopt --apply

# ----- memory phase -----------------------------------------------------
if [ "$SKIP_MEMORY" -ne 1 ]; then
    mkdir -p "$MEMORY_PATH"
    for src in "$TEMPLATES_ROOT"/templates/common/memory/*.md.tmpl \
               "$TEMPLATES_ROOT"/templates/"$ENGINE"/memory/*.md.tmpl; do
        [ -f "$src" ] || continue
        if [ "$DIMENSION" = 3d ] && [ -f "$TEMPLATES_ROOT/templates/dimensions/3d/memory/$(basename "$src")" ]; then
            src="$TEMPLATES_ROOT/templates/dimensions/3d/memory/$(basename "$src")"
        fi
        dst="$MEMORY_PATH/$(basename "$src" .tmpl)"
        [ -f "$dst" ] && continue   # memory is append-only; never overwrite
        cp "$src" "$dst"
        render_file "$dst" "$VARS_FILE"
        strip_conditionals "$dst"
    done
    touch "$MEMORY_PATH/MEMORY.md"
    for f in "$MEMORY_PATH"/*.md; do
            [ -f "$f" ] || continue
            [ "$(basename "$f")" = "MEMORY.md" ] && continue
            desc=$(grep -m1 '^description:' "$f" | sed -e 's/^description: *//' -e 's/^"//' -e 's/"$//')
            [ -z "$desc" ] && desc="(no description)"
            if ! grep -Fq "($(basename "$f"))" "$MEMORY_PATH/MEMORY.md"; then
                printf '\n- [%s](%s)\n' "$desc" "$(basename "$f")" >> "$MEMORY_PATH/MEMORY.md"
            fi
    done
fi

# ----- version stamp ----------------------------------------------------
cat > "$AGENT_DIR/.gp-version" <<EOF
version: $GP_VERSION
generated: $TODAY
engine: $ENGINE
tool: $TOOL
prefix: $PREFIX
package: $PACKAGE
ui-lang: $UI_LANG
style-profile: $STYLE_PROFILE
projection: $PROJECTION
preset: $PRESET
genre: $GENRE
network: $NETWORK
EOF

# ----- report -----------------------------------------------------------
agent_count=$(find "$AGENT_DIR/agents" -name '*.md' | wc -l | tr -d ' ')
script_count=$(find "$AGENT_DIR/scripts" -type f | wc -l | tr -d ' ')
memory_count=$([ "$SKIP_MEMORY" -eq 1 ] && echo 0 || find "$MEMORY_PATH" -name '*.md' | wc -l | tr -d ' ')

echo ""
echo "gp v$GP_VERSION bootstrap complete."
echo ""
echo "  Engine:      $ENGINE"
echo "  Harness:     $TOOL ($AGENT_DIR)"
echo "  Prefix:      $PREFIX (use $INVOCATION)"
echo "  Preset:      $PRESET / $GENRE / $NETWORK"
echo "  Style:       $STYLE_PROFILE"
echo "  Projection:  $PROJECTION"
echo "  UI language: $UI_LANG"
echo "  Memory:      $MEMORY_PATH"
echo ""
echo "  Created: $agent_count agents, $script_count gate scripts, 4 root docs, $memory_count memory files"
echo ""
echo "Next steps:"
echo "  Complete a game brief with $INVOCATION --build <brief>."
echo "  1. Put a Godot 4 project under game/ (project.godot), or let the first"
echo "     --feature run scaffold it."
echo "  2. Run $INVOCATION --style   — build the style bible and lock the reference"
echo "     sheet. Everything visual is downstream of it; starting art or scenes"
echo "     first produces work that has to be redone."
echo "  3. Run $INVOCATION --design <the core loop>."
