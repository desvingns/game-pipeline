#!/usr/bin/env bash
# {{PREFIX}}-runner-godot.sh — build + test gate for {{PROJECT_NAME}}.
# Emits exactly one JSON line on stdout. All engine noise goes to a log file.
#
# Usage:
#   {{PREFIX}}-runner-godot.sh                 # import + unit tests
#   {{PREFIX}}-runner-godot.sh --export        # also export the Android APK
#   {{PREFIX}}-runner-godot.sh --scope res://sim   # run one test directory only
#
# Output (pass):
#   {"pass":true,"import":"ok","tests":"38 passed / 0 failed","export":"skipped"}
# Output (environment):
#   {"pass":false,"error_kind":"godot_not_found","errors":["..."]}
#
# Environment problems are reported as error_kind, never as a failing test run.
# Confusing "the engine is not installed" with "the game is broken" is how a
# pipeline learns to distrust its own gates.

set -uo pipefail

PROJECT_DIR="${GP_PROJECT_DIR:-game}"
EXPORT=0
SCOPE=""
EXPORT_PRESET="${GP_EXPORT_PRESET:-Android}"
LOG_DIR="${TMPDIR:-/tmp}/{{PREFIX}}-runner-$$"

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)
. "$SCRIPT_DIR/{{PREFIX}}-common.sh"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --export)  EXPORT=1; shift ;;
    --scope)   SCOPE="${2:-}"; shift 2 || shift ;;
    --project) PROJECT_DIR="${2:-}"; shift 2 || shift ;;
    *) emit_error "bad_usage" "unknown argument: $1" ;;
  esac
done

[ -f "$PROJECT_DIR/project.godot" ] || emit_error "project_missing" "no project.godot under $PROJECT_DIR"

# ----- engine -------------------------------------------------------------
GODOT=$(detect_gate_godot || true)
[ -n "$GODOT" ] || emit_error "godot_not_found" "no Godot 4 executable found; set GODOT_BIN to pin one"

mkdir -p "$LOG_DIR"
# Retain logs for diagnosis; never delete evidence.


# ----- import -------------------------------------------------------------
# A cold checkout has no .godot/ cache; every later step needs it, and an import
# failure is the cheapest possible signal that a .tscn or .tres is malformed.
if ! "$GODOT" --headless --path "$PROJECT_DIR" --import > "$LOG_DIR/import.log" 2>&1; then
  DETAIL=$(grep -iE 'error|failed' "$LOG_DIR/import.log" | head -3)
  printf '{"pass":false,"import":"failed","tests":"skipped","export":"skipped","errors":["%s"]}\n' \
    "$(json_escape "$DETAIL")"
  exit 0
fi

# ----- unit tests ---------------------------------------------------------
TESTS="skipped"
TEST_PASS=1
GDUNIT="$PROJECT_DIR/addons/gdUnit4/runtest.sh"
TEST_PATH="${SCOPE:-res://tests}"

if [ -f "$GDUNIT" ]; then
  if ( cd "$PROJECT_DIR" && MSYS2_ARG_CONV_EXCL='res://' GODOT_BIN="$GODOT" bash addons/gdUnit4/runtest.sh -a "$TEST_PATH" ) \
       > "$LOG_DIR/tests.log" 2>&1; then
    TEST_PASS=1
  else
    TEST_PASS=0
  fi
  SUMMARY=$(grep -iE '[0-9]+ *(tests?|failed|passed)' "$LOG_DIR/tests.log" | tail -1)
  TESTS="${SUMMARY:-see log}"
else
  emit_error "test_harness_missing" "gdUnit4 is missing at $GDUNIT; tests did not run"
fi

# ----- export -------------------------------------------------------------
EXPORT_RESULT="skipped"
EXPORT_PASS=1
if [ "$EXPORT" -eq 1 ]; then
  OUT_APK="${GP_APK_OUT:-build/{{PREFIX}}.apk}"
  mkdir -p "$(dirname "$OUT_APK")"
  if [ -e "$OUT_APK" ]; then
    mkdir -p archive/gp-exports
    previous=$(mktemp -d archive/gp-exports/run.XXXXXX)
    mv "$OUT_APK" "$previous/"
  fi
  if "$GODOT" --headless --path "$PROJECT_DIR" --export-release "$EXPORT_PRESET" \
       "$(cd "$(dirname "$OUT_APK")" && pwd)/$(basename "$OUT_APK")" \
       > "$LOG_DIR/export.log" 2>&1 && [ -f "$OUT_APK" ]; then
    EXPORT_RESULT="$OUT_APK"
  else
    EXPORT_PASS=0
    EXPORT_RESULT="failed"
  fi
fi

PASS=true
ERRORS=""
[ "$TEST_PASS" -eq 0 ] && { PASS=false; ERRORS="\"unit tests failed\""; }
if [ "$EXPORT_PASS" -eq 0 ]; then
  PASS=false
  DETAIL=$(json_escape "$(grep -iE 'error|failed' "$LOG_DIR/export.log" | head -2)")
  [ -n "$ERRORS" ] && ERRORS="$ERRORS,"
  ERRORS="$ERRORS\"export failed: $DETAIL\""
fi

printf '{"pass":%s,"import":"ok","tests":"%s","export":"%s","errors":[%s]}\n' \
  "$PASS" "$(json_escape "$TESTS")" "$(json_escape "$EXPORT_RESULT")" "$ERRORS"
