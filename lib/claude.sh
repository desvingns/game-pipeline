#!/usr/bin/env bash
# Pin Claude Code model/effort in the canonical rendered Markdown roles.
# Claude Code accepts a per-spawn model, but reads effort only from agent
# frontmatter, so every role carries its default tier from the effective policy.
emit_claude_agents() {
    local dir="$1" prefix="$2" engine="$3" work="$4" policy_root="$5" helper
    helper="$LIB_DIR/claude_agents.py"
    if command -v cygpath >/dev/null 2>&1; then
        helper=$(cygpath -m "$helper"); dir=$(cygpath -m "$dir")
        work=$(cygpath -m "$work"); policy_root=$(cygpath -m "$policy_root")
    fi
    "$PRESET_PYTHON" "$helper" "$dir" "$prefix" "$engine" "$work" "$policy_root"
}

# Merge project-scoped permission rules for the installed pipeline scripts into
# .claude/settings.json. Existing keys and rules are kept; a changed file is archived.
merge_claude_settings() {
    local root="$1" prefix="$2" archive="$3" helper
    helper="$LIB_DIR/claude_settings.py"
    if command -v cygpath >/dev/null 2>&1; then
        helper=$(cygpath -m "$helper"); root=$(cygpath -m "$root"); archive=$(cygpath -m "$archive")
    fi
    "$PRESET_PYTHON" "$helper" "$root" "$prefix" "$archive"
}
