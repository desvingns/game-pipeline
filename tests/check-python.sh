#!/usr/bin/env bash
# Portable Python invocation for repository checks (not installed runtime).
set -euo pipefail
GP_CHECK_PYTHON="${GP_PYTHON:-python}"
GP_CHECK_SCRIPT="$1"
shift
if command -v cygpath >/dev/null 2>&1; then GP_CHECK_SCRIPT=$(cygpath -m "$GP_CHECK_SCRIPT"); fi
exec "$GP_CHECK_PYTHON" "$GP_CHECK_SCRIPT" "$@"
