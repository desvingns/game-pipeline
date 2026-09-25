#!/usr/bin/env bash
# Deterministic regression tests; preserves fixtures and logs under out/.
set -euo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$ROOT"
# Default tests pin the project-local archive; shared-archive tests set their own root.
unset PET_ARCHIVE_ROOT
for script in bootstrap.sh install-codex.sh lib/*.sh tests/*.sh \
              templates/common/scripts/*.sh templates/art/scripts/*.sh templates/godot/scripts/*.sh; do
    bash -n "$script"
done
while IFS= read -r script; do bash -n "$script"; done < <(find templates/dimensions -name '*.sh' -type f)
"${GP_PYTHON:-python}" -m py_compile lib/claude_agents.py lib/claude_settings.py
export GP_TEST_BASH
GP_TEST_BASH=$(command -v bash)
if command -v cygpath >/dev/null 2>&1; then GP_TEST_BASH=$(cygpath -m "$GP_TEST_BASH"); fi
"${GP_PYTHON:-python}" tests/test_workflow.py
"${GP_PYTHON:-python}" tests/test_pipeline.py
"${GP_PYTHON:-python}" tests/test_fps.py
"${GP_PYTHON:-python}" tests/test_marketplace.py
"${GP_PYTHON:-python}" tests/test_adoption.py
bash tests/check-python.sh lib/check-parity.py
