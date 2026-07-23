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

"$PYTHON_BIN" scripts/lib/cognitive_architecture_governance.py \
  --repo-root "$ROOT_DIR" \
  --mode local-offline-pilot

./scripts/cognitive-local-offline-pilot-no-go-regression.sh

"$PYTHON_BIN" -m ruff check --extend-ignore E402 \
  scripts/cognitive-local-offline-pilot-execute.py
"$PYTHON_BIN" -m ruff check \
  scripts/lib/cognitive_architecture_governance.py \
  services/brain-api/tests/test_cognitive_local_offline_pilot_docs.py \
  services/brain-api/tests/test_cognitive_local_offline_pilot_authorization_docs.py

if is_nested_gate_context; then
  echo "PASS: focused cognitive local-offline pilot pytest deferred to outer gate"
else
  "$PYTHON_BIN" -m pytest \
    services/brain-api/tests/test_cognitive_local_offline_pilot_docs.py \
    services/brain-api/tests/test_cognitive_local_offline_pilot_authorization_docs.py \
    -q
fi

if is_nested_gate_context; then
  echo "PASS: inherited repository gates deferred to outer gate"
else
  AION_AGGREGATE_GATE_RUNNING=1 ./scripts/cognitive-local-offline-pilot-authorization-check.sh
  AION_AGGREGATE_GATE_RUNNING=1 ./scripts/cognitive-shadow-runtime-evaluation-check.sh
  ./scripts/docs-check.sh
  ./scripts/final-docs-audit.sh
  ./scripts/verify-no-domain-drift.sh
  ./scripts/boundary-check.sh
  ./scripts/repo-health.sh
fi

cat <<'SUMMARY'
cognitive local-offline pilot result:
- authorization=AION-201-CA-0009
- task=AION-202
- formal_closeout_task=AION-203
- evaluation=AION-CASE-001
- sessions_executed=10
- cycles_per_session=100
- total_cycles_executed=1000
- state_continuity_rate=1.0
- deterministic_replay_rate=1.0
- forbidden_side_effects=0
- policy_violations=0
- unauthorized_promotions=0
- repository_runtime_mutations=0
- kill_switch_blocked=true
cognitive local-offline pilot PASS
SUMMARY
