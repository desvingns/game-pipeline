#!/usr/bin/env bash
# Derive native Codex adapters from the canonical rendered Markdown roles.
emit_codex_agents() {
    local dir="$1" file name tmp model effort sandbox
    for file in "$dir"/*.md; do
        [ -f "$file" ] || continue
        name=$(basename "$file" .md)
        model=gpt-5.6-sol; effort=xhigh; sandbox=workspace-write
        case "$name" in
            *-docs|*-backlog-discovery) model=gpt-5.6-luna ;;
            *-art-prompter|*-animator-*) model=gpt-6-astra; effort=high ;;
        esac
        case "$name" in *-reviewer-*|*-verifier-*|*-architect) sandbox=read-only ;; esac
        tmp="$file.tmp.$$"
        # Claude tool allowlists/model names are not Codex settings.
        awk 'BEGIN { front=0 } /^---$/ { front++; print; next }
             front == 1 && /^(tools|model):/ { next } { print }' "$file" > "$tmp"
        mv "$tmp" "$file"
        cat > "$dir/$name.toml" <<EOF
name = "$name"
description = "Game pipeline specialist: $name. Follow the corresponding role contract."
model = "$model"
model_reasoning_effort = "$effort"
sandbox_mode = "$sandbox"
developer_instructions = '''
Read $dir/$name.md from the game repository root and follow its role instructions.
The Markdown body is canonical; frontmatter is descriptive metadata.
Return exactly the structured payload required by that role.
Use Bash for shell commands, including on Windows. These are role defaults;
the assignment's model-policy selection overrides them. Do not delegate further.
'''
EOF
    done
}
