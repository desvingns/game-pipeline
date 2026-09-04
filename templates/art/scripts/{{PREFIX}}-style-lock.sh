#!/usr/bin/env bash
# {{PREFIX}}-style-lock.sh — freeze the approved reference sheet for {{PROJECT_NAME}}.
# Emits exactly one JSON line.
#
# Usage:
#   {{PREFIX}}-style-lock.sh --lock     # hash every reference image, write the manifest
#   {{PREFIX}}-style-lock.sh --verify   # check the frozen sheet still matches the manifest
#
# STYLE LOCK is the gate that makes a hundred separately generated assets belong
# to one game. After the human approves the reference sheet, its contents are
# hashed; every later generation records that hash in its provenance. When the
# sheet changes, previously generated assets stop being comparable — and this
# script is how that is noticed rather than silently absorbed.

set -uo pipefail

SHEET_DIR="art/style/reference"
MANIFEST="art/style/reference-manifest.json"
MODE=""

emit() { printf '%s\n' "$1"; exit 0; }
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)
. "$SCRIPT_DIR/{{PREFIX}}-common.sh"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --lock)   MODE="lock"; shift ;;
    --verify) MODE="verify"; shift ;;
    --sheet)  SHEET_DIR="${2:-}"; shift 2 || shift ;;
    *) emit_error "bad_usage" "unknown argument: $1" ;;
  esac
done
[ -n "$MODE" ] || emit_error "bad_usage" "pass --lock or --verify"
[ -d "$SHEET_DIR" ] || emit_error "sheet_missing" "no reference sheet directory at $SHEET_DIR"

# sha256 of stdin, portable across Git Bash, Linux and macOS.
sha256() {
  if command -v sha256sum >/dev/null 2>&1; then sha256sum | awk '{print $1}'
  elif command -v shasum >/dev/null 2>&1; then shasum -a 256 | awk '{print $1}'
  else return 1
  fi
}
printf '' | sha256 >/dev/null 2>&1 || emit_error "no_sha256" "neither sha256sum nor shasum is available"

FILES=$(find "$SHEET_DIR" -type f \( -name '*.png' -o -name '*.jpg' -o -name '*.webp' \) | LC_ALL=C sort)
[ -n "$FILES" ] || emit_error "sheet_empty" "no reference images under $SHEET_DIR"

ENTRIES=""
COUNT=0
while IFS= read -r f; do
  [ -n "$f" ] || continue
  h=$(sha256 < "$f") || emit_error "hash_failed" "could not hash $f"
  rel="${f#./}"
  [ -n "$ENTRIES" ] && ENTRIES="$ENTRIES,"
  ENTRIES="$ENTRIES{\"path\":\"$(json_escape "$rel")\",\"sha256\":\"$h\"}"
  COUNT=$((COUNT + 1))
done <<EOF
$FILES
EOF

# The sheet hash is the hash of the ordered per-file hashes: stable across
# machines, and changes if any image is added, removed or edited.
SHEET_HASH=$(printf '%s' "$ENTRIES" | sha256)

if [ "$MODE" = "lock" ]; then
  mkdir -p "$(dirname "$MANIFEST")"
  {
    printf '{\n'
    printf '  "manifest_version": 1,\n'
    printf '  "locked_utc": "%s",\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    printf '  "sheet_dir": "%s",\n' "$(json_escape "$SHEET_DIR")"
    printf '  "sheet_sha256": "%s",\n' "$SHEET_HASH"
    printf '  "files": [%s]\n' "$ENTRIES"
    printf '}\n'
  } > "$MANIFEST"
  emit "{\"pass\":true,\"mode\":\"lock\",\"files\":$COUNT,\"sheet_sha256\":\"$SHEET_HASH\",\"manifest\":\"$MANIFEST\"}"
fi

[ -f "$MANIFEST" ] || emit_error "not_locked" "no manifest at $MANIFEST — run --lock after the human approves the sheet"
RECORDED=$(grep -o '"sheet_sha256"[[:space:]]*:[[:space:]]*"[0-9a-f]*"' "$MANIFEST" | head -1 | sed -e 's|.*"\([0-9a-f]*\)"$|\1|')
if [ "$RECORDED" = "$SHEET_HASH" ]; then
  emit "{\"pass\":true,\"mode\":\"verify\",\"files\":$COUNT,\"sheet_sha256\":\"$SHEET_HASH\"}"
fi
emit "{\"pass\":false,\"mode\":\"verify\",\"error_kind\":\"sheet_drift\",\"files\":$COUNT,\"expected\":\"$RECORDED\",\"actual\":\"$SHEET_HASH\",\"errors\":[\"the reference sheet changed after STYLE LOCK; assets generated before and after are no longer comparable\"]}"
