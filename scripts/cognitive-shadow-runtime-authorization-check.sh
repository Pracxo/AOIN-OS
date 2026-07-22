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
  examples/cognitive-architecture/aion-198-shadow-runtime-authorization.json >/dev/null

"$PYTHON_BIN" scripts/lib/cognitive_architecture_governance.py \
  --repo-root "$ROOT_DIR" \
  --mode shadow-runtime-authorization

./scripts/cognitive-shadow-runtime-authorization-no-go-regression.sh

"$PYTHON_BIN" -m ruff check \
  scripts/lib/cognitive_architecture_governance.py \
  services/brain-api/tests/test_cognitive_integrated_evaluation_closeout_docs.py \
  services/brain-api/tests/test_cognitive_shadow_runtime_authorization_docs.py \
  services/brain-api/tests/test_cognitive_architecture_program_authorization_docs.py

if is_nested_gate_context; then
  echo "PASS: focused cognitive shadow-runtime authorization pytest deferred to outer gate"
else
  "$PYTHON_BIN" -m pytest \
    services/brain-api/tests/test_cognitive_shadow_runtime_authorization_docs.py \
    -q
fi

if is_nested_gate_context; then
  echo "PASS: inherited repository gates deferred to outer gate"
else
  ./scripts/cognitive-integrated-evaluation-check.sh
  ./scripts/cognitive-architecture-authorization-check.sh
  ./scripts/docs-check.sh
  ./scripts/final-docs-audit.sh
  ./scripts/verify-no-domain-drift.sh
  ./scripts/boundary-check.sh
  ./scripts/repo-health.sh
fi

cat <<'SUMMARY'
cognitive shadow-runtime authorization result:
- authorization=AION-198-CA-0008
- parent_evaluation=AION-CAE-001
- parent_task=AION-197
- parent_pr=108
- parent_merge_commit=770a195eae98de12a67370c790f2c7eb36e91aec
- authorized_task=AION-199
- implementation_branch=phase/cognitive-shadow-runtime
- scope=operator-invoked-local-offline-integrated-cognitive-shadow-runtime
- active_cognitive_implementation_authorization_count=1
- runtime_implementation_added=false
- production_cognitive_runtime_enabled=false
- network_access=false
- connector_access=false
- provider_access=false
- source_rewrite=false
- git_mutation=false
- approval_creation=false
- merge=false
- deployment=false
- model_weight_training=0
cognitive shadow-runtime authorization PASS
SUMMARY
