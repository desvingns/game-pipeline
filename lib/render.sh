#!/usr/bin/env bash
# lib/render.sh — placeholder replacement and conditional-block trimming.
# Sourced by bootstrap.sh. Vendored from claude-mobile-pipeline and adapted:
# the platform axis (android|ios) is replaced by an engine axis (godot|...).
#
# Cross-platform principle: never use `sed -i` (incompatible between GNU sed
# and BSD sed). Always write to a tmp file and `mv`.

# replace_placeholder <file> <key> <value>
# Replaces all `{{KEY}}` occurrences in <file> with <value>.
replace_placeholder() {
    local file="$1" key="$2" value="$3"
    local tmp="${file}.tmp.$$"
    local escaped
    escaped=$(printf '%s' "$value" | sed -e 's/[\&|]/\\&/g')
    sed -e "s|{{${key}}}|${escaped}|g" "$file" > "$tmp" && mv "$tmp" "$file"
}

# replace_in_filename <file> <key> <value>
# Renames <file> if its basename contains `{{KEY}}`. Echoes the resulting path.
replace_in_filename() {
    local file="$1" key="$2" value="$3"
    local dir base new_base
    dir=$(dirname "$file")
    base=$(basename "$file")
    new_base="${base//\{\{${key}\}\}/${value}}"
    if [ "$new_base" != "$base" ]; then
        mv "$file" "$dir/$new_base"
        printf '%s' "$dir/$new_base"
    else
        printf '%s' "$file"
    fi
}

# strip_engine_block <file> <engine>
# Deletes `<!-- engine:X --> ... <!-- /engine:X -->` blocks (markers included).
#
# Two passes, deliberately:
#   1. `s|...|...|g`  collapses inline blocks that open and close on one line.
#   2. `/A/,/B/d`     deletes multi-line ranges, safe only after pass 1.
# This avoids the GNU/BSD sed range pitfall where `/A/,/B/` starts scanning for
# B on the line AFTER A matched, so an inline open+close would swallow
# everything down to the next close. The greedy `.*` in pass 1 means two inline
# blocks on one line merge into one match — author at most one per line.
strip_engine_block() {
    local file="$1" engine="$2"
    local tmp="${file}.tmp.$$"
    sed -e "s|<!-- engine:${engine} -->.*<!-- /engine:${engine} -->||g" \
        -e "/<!-- engine:${engine} -->/,/<!-- \/engine:${engine} -->/d" \
        "$file" > "$tmp" && mv "$tmp" "$file"
}

# strip_engine_markers <file> <engine>
# Removes only the marker text and keeps the wrapped content, for the selected
# engine. Replaces the marker substring rather than deleting the line, so inline
# content on the same line survives.
strip_engine_markers() {
    local file="$1" engine="$2"
    local tmp="${file}.tmp.$$"
    sed -e "s|<!-- engine:${engine} -->||g" \
        -e "s|<!-- /engine:${engine} -->||g" \
        "$file" > "$tmp" && mv "$tmp" "$file"
}

# strip_tool_block <file> <tool>
# Deletes `<!-- tool:X --> ... <!-- /tool:X -->` for an unselected harness.
strip_tool_block() {
    local file="$1" tool="$2"
    local tmp="${file}.tmp.$$"
    sed -e "s|<!-- tool:${tool} -->.*<!-- /tool:${tool} -->||g" \
        -e "/<!-- tool:${tool} -->/,/<!-- \/tool:${tool} -->/d" \
        "$file" > "$tmp" && mv "$tmp" "$file"
}

# strip_tool_markers <file> <tool>
strip_tool_markers() {
    local file="$1" tool="$2"
    local tmp="${file}.tmp.$$"
    sed -e "s|<!-- tool:${tool} -->||g" \
        -e "s|<!-- /tool:${tool} -->||g" \
        "$file" > "$tmp" && mv "$tmp" "$file"
}

# strip_if_block <file> <condition>
# Removes `<!-- if CONDITION -->...<!-- /if -->`. Condition is a literal string.
strip_if_block() {
    local file="$1" condition="$2"
    local tmp="${file}.tmp.$$"
    sed -e "s|<!-- if ${condition} -->.*<!-- /if -->||g" \
        -e "/<!-- if ${condition} -->/,/<!-- \/if -->/d" \
        "$file" > "$tmp" && mv "$tmp" "$file"
}

# strip_if_markers <file>
# Removes leftover `<!-- if ... -->` / `<!-- /if -->` text after the false
# branches have been deleted by strip_if_block.
strip_if_markers() {
    local file="$1"
    local tmp="${file}.tmp.$$"
    sed -E -e 's|<!-- if [^>]* -->||g' -e 's|<!-- /if -->||g' \
        "$file" > "$tmp" && mv "$tmp" "$file"
}

# render_file <file> <vars_file>
# Applies replace_placeholder for each `KEY=value` line in <vars_file>.
render_file() {
    local file="$1" vars_file="$2"
    local key value
    while IFS='=' read -r key value; do
        case "$key" in
            ''|'#'*) continue ;;
        esac
        replace_placeholder "$file" "$key" "$value"
    done < "$vars_file"
}
