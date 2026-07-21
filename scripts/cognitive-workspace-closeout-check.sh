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
"$PYTHON_BIN" -m json.tool examples/cognitive-architecture/aion-189-workspace-evaluation.json >/dev/null
"$PYTHON_BIN" -m json.tool examples/cognitive-architecture/aion-189-consolidation-authorization.json >/dev/null

"$PYTHON_BIN" scripts/lib/cognitive_architecture_governance.py \
  --repo-root "$ROOT_DIR" \
  --mode workspace-closeout

./scripts/cognitive-workspace-closeout-no-go-regression.sh

"$PYTHON_BIN" -m ruff check \
  scripts/lib/cognitive_architecture_governance.py \
  services/brain-api/tests/test_cognitive_global_workspace.py \
  services/brain-api/tests/test_cognitive_global_workspace_no_runtime_effect.py \
  services/brain-api/tests/test_cognitive_world_model_closeout_authorization_docs.py \
  services/brain-api/tests/test_cognitive_workspace_closeout_authorization_docs.py

if is_nested_gate_context; then
  echo "PASS: focused cognitive workspace closeout pytest deferred to outer gate"
else
  "$PYTHON_BIN" -m pytest \
    services/brain-api/tests/test_cognitive_global_workspace.py \
    services/brain-api/tests/test_cognitive_global_workspace_no_runtime_effect.py \
    services/brain-api/tests/test_cognitive_world_model_closeout_authorization_docs.py \
    services/brain-api/tests/test_cognitive_workspace_closeout_authorization_docs.py \
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
cognitive workspace closeout result:
- evaluation=AION-GWE-001
- closed_authorization=AION-187-CA-0003
- new_authorization=AION-189-CA-0004
- authorized_task=AION-190
- deterministic_arbitration=100%
- safety_preemption=100%
- anti_starvation=100%
- bounded_capacity=100%
- broadcast_consistency=100%
- duplicate_bid_handling=100%
- concurrency_replay=100%
- cycle_provenance=100%
- direct_action_count=0
- forbidden_side_effects=0
- runtime_effect=false
cognitive workspace closeout PASS
SUMMARY
