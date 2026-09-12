#!/usr/bin/env bash
# Shared board/workflow interface for Claude Code and Codex. One JSON line.
set -uo pipefail
GP_SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)
GP_RUNTIME_PYTHON="${GP_PYTHON:-}"
if [ -z "$GP_RUNTIME_PYTHON" ]; then
    for candidate in python3 python py; do
        if "$candidate" -c 'import sys; assert sys.version_info >= (3, 10)' >/dev/null 2>&1; then
            GP_RUNTIME_PYTHON="$candidate"; break
        fi
    done
fi
if [ -z "$GP_RUNTIME_PYTHON" ]; then
    printf '%s\n' '{"pass":false,"error_kind":"python_missing","errors":["Python 3.10+ is required; set GP_PYTHON"]}'
    exit 1
fi
GP_WORK_SOURCE="$GP_SCRIPT_DIR/gp_work.py"
if command -v cygpath >/dev/null 2>&1; then GP_WORK_SOURCE=$(cygpath -m "$GP_WORK_SOURCE"); fi
exec "$GP_RUNTIME_PYTHON" "$GP_WORK_SOURCE" "$@"
