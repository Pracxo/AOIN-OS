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
"$PYTHON_BIN" -m json.tool \
  examples/cognitive-architecture/aion-201-local-offline-pilot-authorization.json >/dev/null

"$PYTHON_BIN" scripts/lib/cognitive_architecture_governance.py \
  --repo-root "$ROOT_DIR" \
  --mode local-offline-pilot-authorization

./scripts/cognitive-local-offline-pilot-authorization-no-go-regression.sh

"$PYTHON_BIN" -m ruff check \
  scripts/lib/cognitive_architecture_governance.py \
  services/brain-api/tests/test_cognitive_local_offline_pilot_authorization_docs.py \
  services/brain-api/tests/test_cognitive_shadow_runtime_evaluation_closeout.py \
  services/brain-api/tests/test_cognitive_shadow_runtime_authorization_docs.py \
  services/brain-api/tests/test_cognitive_integrated_evaluation_closeout_docs.py

if is_nested_gate_context; then
  echo "PASS: focused cognitive local-offline pilot authorization pytest deferred to outer gate"
else
  "$PYTHON_BIN" -m pytest \
    services/brain-api/tests/test_cognitive_local_offline_pilot_authorization_docs.py \
    -q
fi

if is_nested_gate_context; then
  echo "PASS: inherited repository gates deferred to outer gate"
else
  AION_AGGREGATE_GATE_RUNNING=1 ./scripts/cognitive-shadow-runtime-evaluation-check.sh
  AION_AGGREGATE_GATE_RUNNING=1 ./scripts/cognitive-shadow-runtime-check.sh
  AION_AGGREGATE_GATE_RUNNING=1 ./scripts/cognitive-shadow-runtime-authorization-check.sh
  AION_AGGREGATE_GATE_RUNNING=1 ./scripts/cognitive-integrated-evaluation-check.sh
  ./scripts/docs-check.sh
  ./scripts/final-docs-audit.sh
  ./scripts/verify-no-domain-drift.sh
  ./scripts/boundary-check.sh
  ./scripts/repo-health.sh
fi

cat <<'SUMMARY'
cognitive local-offline pilot authorization result:
- authorization=AION-201-CA-0009
- authorized_task=AION-202
- formal_closeout_task=AION-203
- parent_evaluation=AION-CSE-001
- aion199_implementation_commit=c1479e805ee95e11f7f2d8719607189ccbf9ed4b
- aion200_evaluation_fingerprint=4cb32ba5e5cfb0f0d78014aa2eb7bb959fe3c9a6e23d5a06740b578c3c8cc563
- environment=local_offline_operator_evaluation
- maximum_sessions=10
- maximum_cycles_per_session=100
- maximum_total_cycles=1000
- maximum_concurrency=2
- network_calls=0
- source_mutations=0
- git_operations=0
- real_prs=0
- approvals_created=0
- deployments=0
- production_exposure=0
- model_weight_changes=0
- pilot_executed=false
cognitive local-offline pilot authorization PASS
SUMMARY
