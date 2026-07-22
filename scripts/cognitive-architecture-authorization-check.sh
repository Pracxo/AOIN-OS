#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"

is_nested_gate_context() {
  [[ -n "${PYTEST_CURRENT_TEST:-}" ]] && return 0
  [[ "${AION_AGGREGATE_GATE_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_CHECK_RUNNING:-}" == "1" ]] && return 0
  return 1
}

"$PYTHON_BIN" -m json.tool docs/cognitive-architecture/program-ledger.json >/dev/null
"$PYTHON_BIN" -m json.tool docs/cognitive-architecture/authorization-ledger.json >/dev/null
"$PYTHON_BIN" -m json.tool examples/cognitive-architecture/aion-183-program-authorization.json >/dev/null

"$PYTHON_BIN" scripts/lib/cognitive_architecture_governance.py \
  --repo-root "$ROOT_DIR" \
  --mode authorization

./scripts/cognitive-architecture-no-go-regression.sh

if is_nested_gate_context; then
  echo "PASS: focused cognitive architecture pytest deferred to outer gate"
else
  "$PYTHON_BIN" -m pytest \
    services/brain-api/tests/test_cognitive_architecture_program_authorization_docs.py \
    -q
fi

if is_nested_gate_context; then
  echo "PASS: inherited repository gates deferred to outer gate"
else
  ./scripts/docs-check.sh
  ./scripts/final-docs-audit.sh
  ./scripts/verify-no-domain-drift.sh
  ./scripts/boundary-check.sh
fi

read -r ACTIVE_AUTHORIZATION ACTIVE_AUTHORIZATION_COUNT PROGRAM_STATE <<SUMMARY_FIELDS
$("$PYTHON_BIN" - <<'PY'
import json
from pathlib import Path

program = json.loads(Path("docs/cognitive-architecture/program-ledger.json").read_text())
print(
    program["active_cognitive_implementation_authorization"] or "none",
    program["active_cognitive_implementation_authorization_count"],
    program["program_state"],
)
PY
)
SUMMARY_FIELDS

cat <<SUMMARY
cognitive architecture authorization result:
- program_id=AION-COGNITIVE-ARCHITECTURE-001
- closed_authorization=AION-183-CA-0001
- active_authorization=$ACTIVE_AUTHORIZATION
- program_state=$PROGRAM_STATE
- active implementation authorization count=$ACTIVE_AUTHORIZATION_COUNT
- production cognitive runtime disabled
- network access, connector access, provider access, source rewrite, runtime Git mutation, approval creation, merge, deployment, canary, and model-weight training disabled
cognitive architecture authorization PASS
SUMMARY
