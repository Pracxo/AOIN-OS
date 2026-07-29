#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"

"$PYTHON_BIN" - <<'PY'
from scripts.lib.governed_learning_memory_engagement_application import (
    EngagementApplicationCheckError,
    validate_pilot_evidence,
)

try:
    validate_pilot_evidence()
except EngagementApplicationCheckError as exc:
    raise SystemExit(f"ERROR: {exc}") from exc
PY
echo "governed learning memory engagement shadow pilot evidence PASS"
