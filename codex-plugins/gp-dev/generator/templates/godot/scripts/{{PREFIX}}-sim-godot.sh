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

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)
. "$SCRIPT_DIR/{{PREFIX}}-common.sh"

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
for value in "$RUNS" "$SEEDS" "$WAVES"; do
  positive_integer "$value" || emit_error "bad_usage" "runs, seeds and waves must be positive integers"
done
[[ "$SEED" =~ ^(0|[1-9][0-9]{0,8})$ ]] || emit_error "bad_usage" "seed must be a nonnegative integer"
[ "$MODE" != replay ] || [ "$RUNS" -ge 2 ] || emit_error "bad_usage" "replay requires at least two runs"
[ -n "$MODE" ] || emit_error "bad_usage" "pass --replay or --balance"
[ -f "$PROJECT_DIR/project.godot" ] || emit_error "project_missing" "no project.godot under $PROJECT_DIR"

GODOT=$(detect_gate_godot || true)
[ -n "$GODOT" ] || emit_error "godot_not_found" "no Godot 4 executable found; set GODOT_BIN to pin one"

HARNESS_FILE="$PROJECT_DIR/${HARNESS#res://}"
[ -f "$HARNESS_FILE" ] || emit_error "harness_missing" "no simulation harness at $HARNESS (expected $HARNESS_FILE)"
PY=$(detect_gate_python || true)
[ -n "$PY" ] || emit_error "python_missing" "Python is needed to validate simulation JSON"

run_once() {
  # The harness prints one JSON line; engine chatter goes to stderr and is
  # dropped. Taking the LAST json-looking line keeps stray prints harmless.
  local raw
  raw=$(MSYS2_ARG_CONV_EXCL='res://' "$GODOT" --headless --path "$PROJECT_DIR" "$HARNESS" -- \
      --seed="$1" --waves="$WAVES" 2>/dev/null) || return 1
  printf '%s\n' "$raw" | "$PY" -c '
import json, re, sys
try:
    lines = [line for line in sys.stdin.read().splitlines() if line.lstrip().startswith("{")]
    if len(lines) != 1: raise ValueError("expected one harness payload")
    data = json.loads(lines[0])
    if type(data.get("seed")) is not int or data["seed"] != int(sys.argv[1]): raise ValueError("seed")
    if not isinstance(data.get("hash"), str) or not re.fullmatch(r"[a-zA-Z0-9_-]+", data["hash"]): raise ValueError("hash")
    if type(data.get("waves_survived")) is not int or not 0 <= data["waves_survived"] <= int(sys.argv[2]): raise ValueError("waves")
    if data.get("result") not in ("win", "loss"): raise ValueError("result")
    print(json.dumps(data, separators=(",", ":")))
except (ValueError, TypeError, KeyError):
    sys.exit(1)
' "$1" "$WAVES"
}

field() { printf '%s' "$1" | grep -o "\"$2\"[[:space:]]*:[[:space:]]*\"\?[^,\"}]*" | sed -e "s|.*:[[:space:]]*\"\?||"; }

if [ "$MODE" = "replay" ]; then
  FIRST=""
  HASHES=""
  i=1
  while [ "$i" -le "$RUNS" ]; do
    LINE=$(run_once "$SEED") || emit_error "harness_failed" "simulation process failed on run $i"
    [ -n "$LINE" ] || emit_error "harness_silent" "run $i produced no JSON line"
    H=$(field "$LINE" hash)
    [[ "$H" =~ ^[a-zA-Z0-9_-]+$ ]] || emit_error "harness_contract" "run $i did not report a valid hash"
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
  LINE=$(run_once $((SEED + i))) || emit_error "harness_failed" "simulation process failed on seed $i"
  [ -n "$LINE" ] || emit_error "harness_silent" "seed $i produced no JSON line"
  if [ -n "$LINE" ]; then
    TOTAL=$((TOTAL + 1))
    RESULT=$(field "$LINE" result)
    case "$RESULT" in win) WINS=$((WINS + 1)) ;; loss) ;; *) emit_error "harness_contract" "seed $i has invalid result" ;; esac
    W=$(field "$LINE" waves_survived)
    [[ "$W" =~ ^(0|[1-9][0-9]{0,8})$ ]] || emit_error "harness_contract" "seed $i has invalid waves_survived"
    SUM_WAVES=$((SUM_WAVES + W))
  fi
  i=$((i + 1))
done
[ "$TOTAL" -gt 0 ] || emit_error "harness_silent" "no run produced a JSON line"

RATE=$((WINS * 100 / TOTAL))
AVG=$((SUM_WAVES / TOTAL))
LO="${GP_WINRATE_MIN:-35}"
HI="${GP_WINRATE_MAX:-75}"
[[ "$LO" =~ ^[0-9]{1,3}$ && "$HI" =~ ^[0-9]{1,3}$ ]] || emit_error "bad_usage" "invalid win-rate corridor"
LO=$((10#$LO)); HI=$((10#$HI))
[ "$LO" -le "$HI" ] && [ "$HI" -le 100 ] || emit_error "bad_usage" "corridor must be within 0-100"
PASS=true
ERRORS=""
if [ "$RATE" -lt "$LO" ] || [ "$RATE" -gt "$HI" ]; then
  PASS=false
  ERRORS="\"win rate ${RATE}% is outside the ${LO}-${HI}% corridor\""
fi
printf '{"pass":%s,"mode":"balance","seeds":%s,"win_rate_pct":%s,"avg_waves_survived":%s,"corridor":"%s-%s","errors":[%s]}\n' \
  "$PASS" "$TOTAL" "$RATE" "$AVG" "$LO" "$HI" "$ERRORS"
