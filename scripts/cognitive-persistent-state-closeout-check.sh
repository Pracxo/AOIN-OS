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
"$PYTHON_BIN" -m json.tool examples/cognitive-architecture/aion-185-persistent-state-evaluation.json >/dev/null
"$PYTHON_BIN" -m json.tool examples/cognitive-architecture/aion-185-world-model-authorization.json >/dev/null

"$PYTHON_BIN" scripts/lib/cognitive_architecture_governance.py \
  --repo-root "$ROOT_DIR" \
  --mode persistent-state-closeout

./scripts/cognitive-persistent-state-closeout-no-go-regression.sh

"$PYTHON_BIN" -m ruff check \
  scripts/lib/cognitive_architecture_governance.py \
  services/brain-api/tests/test_cognitive_architecture_program_authorization_docs.py \
  services/brain-api/tests/test_cognitive_persistent_state_closeout_authorization_docs.py

if is_nested_gate_context; then
  echo "PASS: focused cognitive persistent-state closeout pytest deferred to outer gate"
else
  "$PYTHON_BIN" -m pytest \
    services/brain-api/tests/test_cognitive_persistent_state.py \
    services/brain-api/tests/test_cognitive_persistent_state_repository.py \
    services/brain-api/tests/test_cognitive_persistent_state_no_runtime_effect.py \
    services/brain-api/tests/test_cognitive_architecture_program_authorization_docs.py \
    services/brain-api/tests/test_cognitive_persistent_state_closeout_authorization_docs.py \
    -q
fi

if is_nested_gate_context; then
  echo "PASS: inherited repository gates deferred to outer gate"
else
  ./scripts/docs-check.sh
  ./scripts/final-docs-audit.sh
  ./scripts/verify-no-domain-drift.sh
  ./scripts/boundary-check.sh
  ./scripts/repo-health.sh
fi

cat <<'SUMMARY'
cognitive persistent-state closeout result:
- evaluation=AION-PCSE-001
- closed_authorization=AION-183-CA-0001
- new_authorization=AION-185-CA-0002
- authorized_task=AION-186
- replay_equality=100%
- state_invariant_violations=0
- lost_committed_events=0
- duplicate_applied_events=0
- forbidden_side_effects=0
- runtime_effect=false
cognitive persistent-state closeout PASS
SUMMARY
