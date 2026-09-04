#!/usr/bin/env bash
# lib/detect.sh — OS / git / Godot / Python detection helpers.
# Sourced by bootstrap.sh and by the generated gate scripts; not executed standalone.

# detect_os -> "linux" | "macos" | "windows" | "unknown"
detect_os() {
    case "$(uname -s)" in
        Linux*)               echo "linux"   ;;
        Darwin*)              echo "macos"   ;;
        MINGW*|MSYS*|CYGWIN*) echo "windows" ;;
        *)                    echo "unknown" ;;
    esac
}

# is_git_repo [dir]
is_git_repo() {
    git -C "${1:-.}" rev-parse --git-dir >/dev/null 2>&1
}

# detect_godot -> prints the first Godot 4 executable found, returns 0; else returns 1.
#
# Order matters: an explicit GODOT_BIN always wins, so a project can pin an exact
# engine version without touching the scripts. Prefer a headless/console build on
# Windows — the plain `Godot_v4.x.exe` detaches from the console and a gate would
# hang waiting for output that never arrives.
detect_godot() {
    if [ -n "${GODOT_BIN:-}" ] && [ -x "${GODOT_BIN}" ]; then
        echo "$GODOT_BIN"
        return 0
    fi
    local candidates=(
        godot4
        godot
        /usr/local/bin/godot4
        /usr/local/bin/godot
        /Applications/Godot.app/Contents/MacOS/Godot
        "$HOME"/bin/godot4
        "$HOME"/bin/godot
        "/c/Program Files/Godot/Godot_v4"*_console.exe
        "/c/Program Files/Godot/Godot_v4"*.exe
        "${LOCALAPPDATA:-}"/Programs/Godot/Godot_v4*_console.exe
        "${LOCALAPPDATA:-}"/Programs/Godot/Godot_v4*.exe
    )
    local c
    for c in "${candidates[@]}"; do
        if command -v "$c" >/dev/null 2>&1; then
            command -v "$c"
            return 0
        fi
        if [ -x "$c" ]; then
            echo "$c"
            return 0
        fi
    done
    return 1
}

# detect_python -> prints a python interpreter that can import PIL, else returns 1.
#
# The art gates need Pillow. An interpreter without it is useless to us, so the
# import is part of the detection rather than a later surprise inside the gate.
detect_python() {
    if [ -n "${GP_PYTHON:-}" ] && "$GP_PYTHON" -c "import PIL" >/dev/null 2>&1; then
        echo "$GP_PYTHON"
        return 0
    fi
    local c
    for c in python3 python py; do
        if command -v "$c" >/dev/null 2>&1 && "$c" -c "import PIL" >/dev/null 2>&1; then
            command -v "$c"
            return 0
        fi
    done
    return 1
}

# sanitise_path <path>
# Claude Code memory-path convention: replace : / \ with -
# "C:\proj\foo" -> "C--proj-foo" ; "/home/user/foo" -> "-home-user-foo"
sanitise_path() {
    printf '%s' "$1" | tr ':/\\' '---'
}

# script_dir <invocation-path>
# Cross-platform `dirname $(readlink -f $0)`. macOS lacks `readlink -f`.
script_dir() {
    local src="$1"
    if readlink -f "$src" >/dev/null 2>&1; then
        dirname "$(readlink -f "$src")"
    else
        ( cd "$(dirname "$src")" && pwd )
    fi
}
