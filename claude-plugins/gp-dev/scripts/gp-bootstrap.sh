#!/usr/bin/env bash
# Resolve the generator bundled with this plugin and forward every argument.
set -euo pipefail
PLUGIN_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec bash "$PLUGIN_ROOT/generator/bootstrap.sh" "$@"
