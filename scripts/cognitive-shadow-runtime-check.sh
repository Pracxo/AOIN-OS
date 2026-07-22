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
  examples/cognitive-architecture/aion-199-cognitive-shadow-runtime.json >/dev/null

"$PYTHON_BIN" scripts/lib/cognitive_architecture_governance.py \
  --repo-root "$ROOT_DIR" \
  --mode shadow-runtime

./scripts/cognitive-shadow-runtime-no-go-regression.sh

"$PYTHON_BIN" -m ruff check \
  scripts/lib/cognitive_architecture_governance.py \
  services/brain-api/src/aion_brain/contracts/cognitive_runtime.py \
  services/brain-api/src/aion_brain/cognitive_runtime \
  services/brain-api/tests/test_cognitive_shadow_runtime.py \
  services/brain-api/tests/test_cognitive_shadow_runtime_no_runtime_effect.py \
  services/brain-api/tests/test_cognitive_shadow_runtime_authorization_docs.py \
  services/brain-api/tests/test_cognitive_integrated_evaluation_closeout_docs.py

if is_nested_gate_context; then
  echo "PASS: focused cognitive shadow-runtime pytest deferred to outer gate"
else
  "$PYTHON_BIN" -m pytest \
    services/brain-api/tests/test_cognitive_shadow_runtime.py \
    services/brain-api/tests/test_cognitive_shadow_runtime_no_runtime_effect.py \
    -q
fi

if is_nested_gate_context; then
  echo "PASS: inherited repository gates deferred to outer gate"
else
  AION_AGGREGATE_GATE_RUNNING=1 ./scripts/cognitive-shadow-runtime-authorization-check.sh
  AION_AGGREGATE_GATE_RUNNING=1 ./scripts/cognitive-integrated-evaluation-check.sh
  ./scripts/docs-check.sh
  ./scripts/final-docs-audit.sh
  ./scripts/verify-no-domain-drift.sh
  ./scripts/boundary-check.sh
  ./scripts/repo-health.sh
fi

cat <<'SUMMARY'
cognitive shadow-runtime result:
- authorization=AION-198-CA-0008
- implementation_task=AION-199
- closeout_task=AION-200
- evaluation=AION-CSE-001
- scope=operator-invoked-local-offline-integrated-cognitive-shadow-runtime
- explicit_python_api=true
- operator_invoked=true
- local_offline=true
- production_cognitive_runtime_enabled=false
- api_route_added=false
- kernel_registration_added=false
- startup_registration_added=false
- scheduler_started=false
- background_loop_added=false
- cli_installation_added=false
- operator_review_required=true
- action_execution_performed=false
- network_calls=0
- connector_calls=0
- model_provider_calls=0
- source_rewrite=false
- git_mutation=false
- approval_creation=0
- merge_operations=0
- deployment_operations=0
- model_weight_training=0
cognitive shadow-runtime PASS
SUMMARY
