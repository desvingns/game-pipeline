#!/usr/bin/env bash
# {{PREFIX}}-sim-godot.sh — determinism and balance gate for {{PROJECT_NAME}}.
# Emits exactly one JSON line on stdout.
#
# Usage:
#   {{PREFIX}}-sim-godot.sh --replay --seed 4242 [--runs 2]
#   {{PREFIX}}-sim-godot.sh --balance [--seeds 20] [--waves 30]
#
# --replay  runs the headless simulation harness twice with the same seed and
#           compares the reported state hash. Any divergence means something in
#           the simulation reached for wall-clock time, iteration order over an
#           unordered container, floating-point drift, or a node from the render
#           layer. This gate is the reason simulation must stay engine-free.
#
# --balance runs many seeds and reports the win-rate curve per wave, so tuning
#           is judged against numbers rather than against a feeling.
#
# The harness is a headless Godot scene the project provides at
# res://tools/gates/sim_harness.tscn. It must print exactly one JSON line of its
# own: {"seed":N,"hash":"...","waves_survived":N,"result":"win|loss"}.

set -uo pipefail

PROJECT_DIR="${GP_PROJECT_DIR:-game}"
HARNESS="${GP_SIM_HARNESS:-res://tools/gates/sim_harness.tscn}"
MODE=""
SEED=4242
RUNS=2
SEEDS=20
WAVES=30

emit_error() {
  printf '{"pass":false,"error_kind":"%s","errors":["%s"]}\n' "$1" "$2"
  exit 0
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --replay)  MODE="replay"; shift ;;
    --balance) MODE="balance"; shift ;;
    --seed)    SEED="${2:-}"; shift 2 || shift ;;
    --runs)    RUNS="${2:-}"; shift 2 || shift ;;
    --seeds)   SEEDS="${2:-}"; shift 2 || shift ;;
    --waves)   WAVES="${2:-}"; shift 2 || shift ;;
    --project) PROJECT_DIR="${2:-}"; shift 2 || shift ;;
    *) emit_error "bad_usage" "unknown argument: $1" ;;
  esac
done
[ -n "$MODE" ] || emit_error "bad_usage" "pass --replay or --balance"
[ -f "$PROJECT_DIR/project.godot" ] || emit_error "project_missing" "no project.godot under $PROJECT_DIR"

GODOT=""
if [ -n "${GODOT_BIN:-}" ] && [ -x "${GODOT_BIN}" ]; then
  GODOT="$GODOT_BIN"
else
  for c in godot4 godot; do
    command -v "$c" >/dev/null 2>&1 && { GODOT=$(command -v "$c"); break; }
  done
fi
[ -n "$GODOT" ] || emit_error "godot_not_found" "no Godot 4 executable found; set GODOT_BIN to pin one"

HARNESS_FILE="$PROJECT_DIR/${HARNESS#res://}"
[ -f "$HARNESS_FILE" ] || emit_error "harness_missing" "no simulation harness at $HARNESS (expected $HARNESS_FILE)"

run_once() {
  # The harness prints one JSON line; engine chatter goes to stderr and is
  # dropped. Taking the LAST json-looking line keeps stray prints harmless.
  "$GODOT" --headless --path "$PROJECT_DIR" "$HARNESS" -- \
      --seed="$1" --waves="$WAVES" 2>/dev/null | grep -o '{.*}' | tail -1
}

field() { printf '%s' "$1" | grep -o "\"$2\"[[:space:]]*:[[:space:]]*\"\?[^,\"}]*" | sed -e "s|.*:[[:space:]]*\"\?||"; }

if [ "$MODE" = "replay" ]; then
  FIRST=""
  HASHES=""
  i=1
  while [ "$i" -le "$RUNS" ]; do
    LINE=$(run_once "$SEED")
    [ -n "$LINE" ] || emit_error "harness_silent" "run $i produced no JSON line"
    H=$(field "$LINE" hash)
    [ -n "$H" ] || emit_error "harness_contract" "run $i did not report a hash"
    [ -n "$HASHES" ] && HASHES="$HASHES,"
    HASHES="$HASHES\"$H\""
    [ -z "$FIRST" ] && FIRST="$H"
    if [ "$H" != "$FIRST" ]; then
      printf '{"pass":false,"mode":"replay","seed":%s,"runs":%s,"hashes":[%s],"errors":["replay diverged: the simulation is not deterministic for this seed"]}\n' \
        "$SEED" "$RUNS" "$HASHES"
      exit 0
    fi
    i=$((i + 1))
  done
  printf '{"pass":true,"mode":"replay","seed":%s,"runs":%s,"hash":"%s"}\n' "$SEED" "$RUNS" "$FIRST"
  exit 0
fi

# ----- balance ------------------------------------------------------------
WINS=0
TOTAL=0
SUM_WAVES=0
i=1
while [ "$i" -le "$SEEDS" ]; do
  LINE=$(run_once $((SEED + i)))
  if [ -n "$LINE" ]; then
    TOTAL=$((TOTAL + 1))
    [ "$(field "$LINE" result)" = "win" ] && WINS=$((WINS + 1))
    W=$(field "$LINE" waves_survived)
    case "$W" in ''|*[!0-9]*) W=0 ;; esac
    SUM_WAVES=$((SUM_WAVES + W))
  fi
  i=$((i + 1))
done
[ "$TOTAL" -gt 0 ] || emit_error "harness_silent" "no run produced a JSON line"

RATE=$((WINS * 100 / TOTAL))
AVG=$((SUM_WAVES / TOTAL))
LO="${GP_WINRATE_MIN:-35}"
HI="${GP_WINRATE_MAX:-75}"
PASS=true
ERRORS=""
if [ "$RATE" -lt "$LO" ] || [ "$RATE" -gt "$HI" ]; then
  PASS=false
  ERRORS="\"win rate ${RATE}% is outside the ${LO}-${HI}% corridor\""
fi
printf '{"pass":%s,"mode":"balance","seeds":%s,"win_rate_pct":%s,"avg_waves_survived":%s,"corridor":"%s-%s","errors":[%s]}\n' \
  "$PASS" "$TOTAL" "$RATE" "$AVG" "$LO" "$HI" "$ERRORS"
