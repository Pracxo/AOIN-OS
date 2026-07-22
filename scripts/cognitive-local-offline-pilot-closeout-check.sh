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
  examples/cognitive-architecture/aion-202-controlled-cognitive-pilot.json >/dev/null
"$PYTHON_BIN" -m json.tool \
  examples/cognitive-architecture/aion-203-cognitive-pilot-evaluation-closeout.json >/dev/null

"$PYTHON_BIN" scripts/lib/cognitive_architecture_governance.py \
  --repo-root "$ROOT_DIR" \
  --mode local-offline-pilot-closeout

./scripts/cognitive-local-offline-pilot-closeout-no-go-regression.sh

"$PYTHON_BIN" -m ruff check \
  scripts/lib/cognitive_architecture_governance.py \
  services/brain-api/tests/test_cognitive_local_offline_pilot_closeout_docs.py \
  services/brain-api/tests/test_cognitive_local_offline_pilot_docs.py \
  services/brain-api/tests/test_cognitive_local_offline_pilot_authorization_docs.py

if is_nested_gate_context; then
  echo "PASS: focused cognitive local-offline pilot closeout pytest deferred to outer gate"
else
  "$PYTHON_BIN" -m pytest \
    services/brain-api/tests/test_cognitive_local_offline_pilot_closeout_docs.py \
    services/brain-api/tests/test_cognitive_local_offline_pilot_docs.py \
    services/brain-api/tests/test_cognitive_local_offline_pilot_authorization_docs.py \
    -q
fi

if is_nested_gate_context; then
  echo "PASS: inherited repository gates deferred to outer gate"
else
  AION_AGGREGATE_GATE_RUNNING=1 ./scripts/cognitive-local-offline-pilot-check.sh
  AION_AGGREGATE_GATE_RUNNING=1 ./scripts/cognitive-shadow-runtime-evaluation-check.sh
  ./scripts/docs-check.sh
  ./scripts/final-docs-audit.sh
  ./scripts/verify-no-domain-drift.sh
  ./scripts/boundary-check.sh
  ./scripts/repo-health.sh
fi

cat <<'SUMMARY'
cognitive local-offline pilot closeout result:
- evaluation=AION-CASE-001
- decision=CONTROLLED_LOCAL_OFFLINE_PILOT_PASS_COMPLETE_COGNITIVE_ARCHITECTURE_PROGRAM
- closed_authorization=AION-201-CA-0009
- active_cognitive_implementation_authorization_count=0
- state_continuity_rate=1.0
- deterministic_replay_rate=1.0
- forbidden_side_effects=0
- policy_violations=0
- unauthorized_promotions=0
- repository_runtime_mutations=0
- temporary_local_pilot_state_cleaned=true
- production_cognitive_runtime_enabled=false
- network_access_enabled=false
- source_rewrite_runtime_enabled=false
- automatic_merge_enabled=false
- production_deployment_enabled=false
- model_weight_training_enabled=false
cognitive local-offline pilot closeout PASS
SUMMARY
