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
"$PYTHON_BIN" -m json.tool examples/cognitive-architecture/aion-184-persistent-state.json >/dev/null

"$PYTHON_BIN" scripts/lib/cognitive_architecture_governance.py \
  --repo-root "$ROOT_DIR" \
  --mode persistent-state

./scripts/cognitive-persistent-state-no-go-regression.sh

"$PYTHON_BIN" -m ruff check \
  services/brain-api/src/aion_brain/contracts/cognitive_state.py \
  services/brain-api/src/aion_brain/cognitive_architecture \
  services/brain-api/tests/test_cognitive_persistent_state.py \
  services/brain-api/tests/test_cognitive_persistent_state_repository.py \
  services/brain-api/tests/test_cognitive_persistent_state_no_runtime_effect.py

if is_nested_gate_context; then
  echo "PASS: focused cognitive persistent-state pytest deferred to outer gate"
else
  "$PYTHON_BIN" -m pytest \
    services/brain-api/tests/test_cognitive_persistent_state.py \
    services/brain-api/tests/test_cognitive_persistent_state_repository.py \
    services/brain-api/tests/test_cognitive_persistent_state_no_runtime_effect.py \
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
cognitive persistent-state result:
- authorization=AION-183-CA-0001
- implementation_task=AION-184
- contracts=immutable
- repository=append-only in-memory and explicit local SQLite
- replay=deterministic
- checkpoint_restore=hash-verified
- retention=explicit
- runtime_effect=false
- api_route_added=false
- kernel_registration_added=false
- network_calls=0
cognitive persistent-state PASS
SUMMARY
