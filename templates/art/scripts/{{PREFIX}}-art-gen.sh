#!/usr/bin/env bash
# {{PREFIX}}-art-gen.sh — provider adapter for {{PROJECT_NAME}}.
# Emits exactly one JSON line on stdout.
#
# Usage:
#   {{PREFIX}}-art-gen.sh --spec <prompt-spec.json> [--provider gemini|codex-native|manual]
#                         [--out-dir assets/inbox] [--register <path>] [--render-only]
#
# The provider defaults to the session's harness: a Claude session scripts the
# Gemini API, a Codex session renders the prompt for Codex Desktop's image_gen
# and waits for a human to bring the file back. Both paths write the same
# provenance record, which is the only thing downstream cares about.

set -uo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)
# The harness default is written in at bootstrap. Conditional markers live inside
# shell comments so this template stays valid bash before it is rendered — a
# template you cannot `bash -n` is a template whose syntax errors ship.
# <!-- tool:claude -->
DEFAULT_PROVIDER="gemini"
# <!-- /tool:claude -->
# <!-- tool:codex -->
DEFAULT_PROVIDER="codex-native"
# <!-- /tool:codex -->

# An explicit override wins, and a Claude default with no key falls back to the
# human path rather than failing: a missing key is a reason to hand the prompt to
# a person, not to stop the run.
PROVIDER="${GP_ART_PROVIDER:-$DEFAULT_PROVIDER}"
if [ "$PROVIDER" = "gemini" ] && [ -z "${GEMINI_API_KEY:-}" ]; then
  PROVIDER="manual"
fi
PASSTHROUGH=()
SPEC=""

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)
. "$SCRIPT_DIR/{{PREFIX}}-common.sh"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --spec)     SPEC="${2:-}"; PASSTHROUGH+=(--spec "${2:-}"); shift 2 || shift ;;
    --provider) PROVIDER="${2:-}"; shift 2 || shift ;;
    --out-dir|--register|--sheet-manifest|--operator|--attempt)
                PASSTHROUGH+=("$1" "${2:-}"); shift 2 || shift ;;
    --render-only) PASSTHROUGH+=(--render-only); shift ;;
    *) emit_error "bad_usage" "unknown argument: $1" ;;
  esac
done

[ -n "$SPEC" ] || emit_error "bad_usage" "--spec is required"
[ -f "$SPEC" ] || emit_error "spec_missing" "no such prompt-spec: $SPEC"

case "$PROVIDER" in
  gemini|codex-native|manual) ;;
  *) emit_error "bad_usage" "unknown provider: $PROVIDER" ;;
esac

PY=$(detect_gate_python || true)
[ -n "$PY" ] || emit_error "python_missing" "no python interpreter found (set GP_PYTHON)"

IMPL="$SCRIPT_DIR/{{PREFIX}}-art-gen.py"
[ -f "$IMPL" ] || emit_error "impl_missing" "generator implementation not found at $IMPL"
IMPL=$(native_path "$IMPL")

OUT=$("$PY" "$IMPL" --provider "$PROVIDER" "${PASSTHROUGH[@]}" 2>/dev/null)
[ -n "$OUT" ] || emit_error "generator_crashed" "the generator produced no output for $SPEC"
printf '%s\n' "$OUT"
