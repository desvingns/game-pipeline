#!/usr/bin/env bash
# Shared gate helpers. Source only: no output on its own.
json_escape() {
    local value="$1" control escaped i
    value="${value//\\/\\\\}"
    value="${value//\"/\\\"}"
    for ((i=1; i<32; i++)); do
        printf -v control '%b' "\\$(printf '%03o' "$i")"
        printf -v escaped '\\u%04x' "$i"
        value="${value//"$control"/$escaped}"
    done
    printf '%s' "$value"
}
emit_error() {
    printf '{"pass":false,"error_kind":"%s","errors":["%s"]}\n' \
        "$(json_escape "$1")" "$(json_escape "$2")"
    exit 0
}
positive_integer() { [[ "$1" =~ ^[1-9][0-9]{0,8}$ ]]; }
native_path() {
    if command -v cygpath >/dev/null 2>&1; then cygpath -m "$1"; else printf '%s\n' "$1"; fi
}
detect_gate_python() {
    local candidate
    if [ -n "${GP_PYTHON:-}" ]; then
        "$GP_PYTHON" -c 'import sys' >/dev/null 2>&1 || return 1
        printf '%s\n' "$GP_PYTHON"; return 0
    fi
    for candidate in python3 python py; do
        if "$candidate" -c 'import sys' >/dev/null 2>&1; then
            command -v "$candidate"; return 0
        fi
    done
    return 1
}
detect_gate_godot() {
    local candidate
    if [ -n "${GODOT_BIN:-}" ]; then
        [ -x "$GODOT_BIN" ] || return 1
        printf '%s\n' "$GODOT_BIN"; return 0
    fi
    for candidate in godot4 godot \
        /Applications/Godot.app/Contents/MacOS/Godot \
        /c/Program\ Files/Godot/Godot_v4*_console.exe \
        "${LOCALAPPDATA:-}/Programs/Godot/"Godot_v4*_console.exe; do
        if command -v "$candidate" >/dev/null 2>&1; then command -v "$candidate"; return 0; fi
    done
    return 1
}
