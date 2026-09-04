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

# ----- parse args --------------------------------------------------------
ENGINE="godot"
TOOL="claude"
PREFIX=""
PROJECT_NAME=""
PROJECT_DESCRIPTION=""
PACKAGE=""
UI_LANG="en"
MEMORY_PATH=""
PROJECTION="top-down-34"
STYLE_PROFILE="cel-shaded-outline"
FORCE=0
DRY_RUN=0
SKIP_MEMORY=0
NON_INTERACTIVE=0
NO_GIT=0

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
        --style-profile=*)       STYLE_PROFILE="${1#*=}" ;;
        --force)                 FORCE=1 ;;
        --dry-run)               DRY_RUN=1 ;;
        --skip-memory)           SKIP_MEMORY=1 ;;
        --non-interactive)       NON_INTERACTIVE=1 ;;
        --no-git)                NO_GIT=1 ;;
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
PACKAGE=$(maybe_prompt "$PACKAGE" "package" "^[a-z]+(\.[a-z][a-z0-9_]*)+$")
[ -z "$PROJECT_DESCRIPTION" ] && PROJECT_DESCRIPTION="(One-sentence game description — replace this placeholder.)"

# ----- validate ----------------------------------------------------------
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
[ -z "$MEMORY_PATH" ] && MEMORY_PATH="$HOME/.claude/projects/$SANITISED_CWD/memory"
TODAY=$(date +%Y-%m-%d)
GP_VERSION=$(tr -d '[:space:]' < "$TEMPLATES_ROOT/VERSION")
case "$TOOL" in
    claude) AGENT_DIR=".claude" ;;
    codex)  AGENT_DIR=".codex"  ;;
esac

# ----- preflight ---------------------------------------------------------
if [ "$FORCE" -ne 1 ]; then
    for path in "$AGENT_DIR" CLAUDE.md STATE.md ROADMAP.md DOCUMENTATION.md art; do
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
    echo "  $AGENT_DIR/scripts/$PREFIX-*.sh + *.py     (gate scripts)"
    echo "  $AGENT_DIR/specs/{backlog,active,done}/    (code board)"
    echo "  art/cards/{backlog,active,done}/           (art board)"
    echo "  art/style/profiles/*.json + art/schemas/*.json"
    echo "  art/style/reference/  art/prompts/  assets/inbox/"
    echo "  ./CLAUDE.md ./STATE.md ./ROADMAP.md ./DOCUMENTATION.md"
    [ "$SKIP_MEMORY" -ne 1 ] && echo "  $MEMORY_PATH/MEMORY.md + memos"
    echo ""
    echo "Vars resolved:"
    echo "  engine=$ENGINE tool=$TOOL prefix=$PREFIX package=$PACKAGE ui-lang=$UI_LANG"
    echo "  style-profile=$STYLE_PROFILE projection=$PROJECTION agent-dir=$AGENT_DIR"
    exit 0
fi

# ----- build vars file for render_file ----------------------------------
VARS_FILE=$(mktemp)
trap 'rm -f "$VARS_FILE"' EXIT
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
EOF

# ----- copy phase --------------------------------------------------------
mkdir -p "$AGENT_DIR/agents" "$AGENT_DIR/commands/$PREFIX-runtime" \
         "$AGENT_DIR/scripts" "$AGENT_DIR/specs" \
         art/style/profiles art/style/reference art/prompts art/schemas \
         art/cards assets/inbox

# 1. Agents: engine-neutral, art subsystem, engine-specific.
for src in "$TEMPLATES_ROOT"/templates/common/agents/*.md \
           "$TEMPLATES_ROOT"/templates/art/agents/*.md \
           "$TEMPLATES_ROOT"/templates/"$ENGINE"/agents/*.md; do
    [ -f "$src" ] || continue
    cp "$src" "$AGENT_DIR/agents/$(basename "$src")"
done

# 2. Orchestrator + lazily-loaded runbooks.
cp "$TEMPLATES_ROOT/templates/common/commands/{{PREFIX}}.md" "$AGENT_DIR/commands/{{PREFIX}}.md"
for src in "$TEMPLATES_ROOT"/templates/common/commands/runtime/*; do
    [ -f "$src" ] || continue
    cp "$src" "$AGENT_DIR/commands/$PREFIX-runtime/$(basename "$src")"
done

# 3. Boards.
cp "$TEMPLATES_ROOT/templates/common/specs/README.md" "$AGENT_DIR/specs/README.md"
for board in backlog active done; do
    mkdir -p "$AGENT_DIR/specs/$board" "art/cards/$board"
    touch "$AGENT_DIR/specs/$board/.gitkeep" "art/cards/$board/.gitkeep"
done

# 4. Gate scripts: art subsystem + engine.
for src in "$TEMPLATES_ROOT"/templates/art/scripts/* \
           "$TEMPLATES_ROOT"/templates/"$ENGINE"/scripts/*; do
    [ -f "$src" ] || continue
    base=$(basename "$src")
    cp "$src" "$AGENT_DIR/scripts/$base"
    chmod +x "$AGENT_DIR/scripts/$base"
done

# 5. Profiles and schemas are FROZEN into the project, not referenced from the
#    generator. A game must keep building the same way after gp moves on.
cp "$TEMPLATES_ROOT/profiles/style/$STYLE_PROFILE.json" "art/style/profiles/$STYLE_PROFILE.json"
cp "$TEMPLATES_ROOT/profiles/projection/$PROJECTION.json" "art/style/profiles/$PROJECTION.json"
for src in "$TEMPLATES_ROOT"/schemas/*.json; do
    cp "$src" "art/schemas/$(basename "$src")"
done

# 6. Root docs (.tmpl -> strip extension).
for src in "$TEMPLATES_ROOT"/templates/common/root/*.md.tmpl; do
    cp "$src" "./$(basename "$src" .tmpl)"
done

# ----- render phase: placeholders ---------------------------------------
# An array, not a string: a project directory may contain spaces, and word
# splitting a path list is the classic way a generator half-renders a tree.
RENDER_TARGETS=(
    "$AGENT_DIR"/agents/*.md
    "$AGENT_DIR"/commands/*.md
    "$AGENT_DIR"/commands/*/*.md
    "$AGENT_DIR"/specs/*.md
    "$AGENT_DIR"/scripts/*
    ./CLAUDE.md ./STATE.md ./ROADMAP.md ./DOCUMENTATION.md
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

# ----- memory phase -----------------------------------------------------
if [ "$SKIP_MEMORY" -ne 1 ]; then
    mkdir -p "$MEMORY_PATH"
    for src in "$TEMPLATES_ROOT"/templates/common/memory/*.md.tmpl \
               "$TEMPLATES_ROOT"/templates/"$ENGINE"/memory/*.md.tmpl; do
        [ -f "$src" ] || continue
        dst="$MEMORY_PATH/$(basename "$src" .tmpl)"
        [ -f "$dst" ] && continue   # memory is append-only; never overwrite
        cp "$src" "$dst"
        render_file "$dst" "$VARS_FILE"
        strip_conditionals "$dst"
    done
    {
        for f in "$MEMORY_PATH"/*.md; do
            [ -f "$f" ] || continue
            [ "$(basename "$f")" = "MEMORY.md" ] && continue
            desc=$(grep -m1 '^description:' "$f" | sed -e 's/^description: *//' -e 's/^"//' -e 's/"$//')
            [ -z "$desc" ] && desc="(no description)"
            echo "- [$desc]($(basename "$f"))"
        done
    } > "$MEMORY_PATH/MEMORY.md"
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
echo "  Prefix:      $PREFIX (use /$PREFIX)"
echo "  Style:       $STYLE_PROFILE"
echo "  Projection:  $PROJECTION"
echo "  UI language: $UI_LANG"
echo "  Memory:      $MEMORY_PATH"
echo ""
echo "  Created: $agent_count agents, $script_count gate scripts, 4 root docs, $memory_count memory files"
echo ""
echo "Next steps:"
echo "  1. Put a Godot 4 project under game/ (project.godot), or let the first"
echo "     --feature run scaffold it."
echo "  2. Run /$PREFIX --style   — build the style bible and lock the reference"
echo "     sheet. Everything visual is downstream of it; starting art or scenes"
echo "     first produces work that has to be redone."
echo "  3. Run /$PREFIX --design <the core loop>."
