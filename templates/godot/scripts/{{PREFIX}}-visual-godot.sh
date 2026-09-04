#!/usr/bin/env bash
# {{PREFIX}}-visual-godot.sh — capture headless screenshots for {{PROJECT_NAME}}.
# Emits exactly one JSON line on stdout.
#
# Usage:
#   {{PREFIX}}-visual-godot.sh --scene res://scenes/battle.tscn --out shots/battle.png
#   {{PREFIX}}-visual-godot.sh --all            # every scene listed in the shot list
#
# This script only produces pixels. Judging them against the style bible is the
# art director's multimodal job — deliberately split, because "did the frame
# render" and "does the frame look right" fail for unrelated reasons and should
# never share a pass/fail bit.
#
# The project provides a capture harness at res://tools/gates/shot.tscn which
# accepts --scene and --out and prints one JSON line:
#   {"scene":"res://...","out":"shots/x.png","ok":true}
# A shot list at art/shots.txt (one "scene<TAB>out" pair per line) drives --all.

set -uo pipefail

PROJECT_DIR="${GP_PROJECT_DIR:-game}"
HARNESS="${GP_SHOT_HARNESS:-res://tools/gates/shot.tscn}"
SHOT_LIST="${GP_SHOT_LIST:-art/shots.txt}"
SCENE=""
OUT=""
ALL=0

emit_error() {
  printf '{"pass":false,"error_kind":"%s","errors":["%s"]}\n' "$1" "$2"
  exit 0
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --scene)   SCENE="${2:-}"; shift 2 || shift ;;
    --out)     OUT="${2:-}"; shift 2 || shift ;;
    --all)     ALL=1; shift ;;
    --project) PROJECT_DIR="${2:-}"; shift 2 || shift ;;
    *) emit_error "bad_usage" "unknown argument: $1" ;;
  esac
done

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
[ -f "$PROJECT_DIR/${HARNESS#res://}" ] || emit_error "harness_missing" "no capture harness at $HARNESS"

capture() {
  local scene="$1" out="$2"
  mkdir -p "$(dirname "$out")"
  "$GODOT" --headless --path "$PROJECT_DIR" "$HARNESS" -- \
      --scene="$scene" --out="$(pwd)/$out" >/dev/null 2>&1
  [ -s "$out" ]
}

SHOTS=""
FAILED=""
COUNT=0

add_result() {
  [ -n "$SHOTS" ] && SHOTS="$SHOTS,"
  SHOTS="$SHOTS{\"scene\":\"$1\",\"out\":\"$2\",\"ok\":$3}"
  COUNT=$((COUNT + 1))
  [ "$3" = "false" ] && FAILED="$FAILED $1"
}

if [ "$ALL" -eq 1 ]; then
  [ -f "$SHOT_LIST" ] || emit_error "shot_list_missing" "no shot list at $SHOT_LIST"
  while IFS=$'\t' read -r s o; do
    case "$s" in ''|'#'*) continue ;; esac
    if capture "$s" "$o"; then add_result "$s" "$o" true; else add_result "$s" "$o" false; fi
  done < "$SHOT_LIST"
else
  [ -n "$SCENE" ] || emit_error "bad_usage" "--scene is required without --all"
  [ -n "$OUT" ] || OUT="shots/$(basename "${SCENE%.tscn}").png"
  if capture "$SCENE" "$OUT"; then add_result "$SCENE" "$OUT" true; else add_result "$SCENE" "$OUT" false; fi
fi

if [ -n "$FAILED" ]; then
  printf '{"pass":false,"captured":%s,"shots":[%s],"errors":["no image produced for:%s"]}\n' \
    "$COUNT" "$SHOTS" "$FAILED"
else
  printf '{"pass":true,"captured":%s,"shots":[%s]}\n' "$COUNT" "$SHOTS"
fi
