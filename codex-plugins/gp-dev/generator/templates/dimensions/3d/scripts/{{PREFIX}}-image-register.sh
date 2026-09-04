#!/usr/bin/env bash
# Register generated images used by the 3D pipeline; emits one JSON line.
set -uo pipefail
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)
. "$SCRIPT_DIR/{{PREFIX}}-common.sh"
PYTHON=$(detect_gate_python || true)
[ -n "$PYTHON" ] || emit_error "python_missing" "Python 3 is required; set GP_PYTHON"
MSYS2_ARG_CONV_EXCL='*' "$PYTHON" "$(native_path "$SCRIPT_DIR/gp_mesh.py")" image "$@"
