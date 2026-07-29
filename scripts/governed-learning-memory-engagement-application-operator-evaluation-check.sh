#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"

"$PYTHON_BIN" -m py_compile \
  scripts/lib/governed_learning_memory_engagement_application_operator_evaluation.py \
  scripts/lib/governed_learning_memory_continual_learning_pilot_authorization.py

"$PYTHON_BIN" - <<'PY'
from pathlib import Path
from scripts.lib.governed_learning_memory_engagement_application_operator_evaluation import (
    PASS_DECISION,
    SCENARIO_IDS,
    validate_evaluation_report_file,
)
from scripts.lib.governed_learning_memory_continual_learning_pilot_authorization import (
    CURRENT_AUTHORIZATION_ID,
    NEXT_AUTHORIZATION_ID,
    load_json,
    validate_aion225_closeout,
    validate_authorization_record,
    validate_continual_learning_pilot_authorization,
)

report = Path("examples/governed-learning-memory/engagement-application-operator-evaluation-report.json")
payload = validate_evaluation_report_file(report)
if payload["decision"] != PASS_DECISION or payload["evaluation_passed"] is not True:
    raise SystemExit("AION-227 evaluation decision mismatch")
if payload["scenario_count"] != 28 or tuple(payload["scenario_ids"]) != SCENARIO_IDS:
    raise SystemExit("AION-227 evaluation scenario mismatch")
if not all(item["result"] == "passed" for item in payload["scenario_results"]):
    raise SystemExit("AION-227 scenario result mismatch")
if not all(item["passed"] is True for item in payload["hard_gate_results"].values()):
    raise SystemExit("AION-227 hard gate result mismatch")
if payload["network_calls"] != 0 or payload["active_overlay_records_after_evaluation"] != 0:
    raise SystemExit("AION-227 evaluation side-effect mismatch")
if payload["authorization_closeout"]["authorization_transaction_id"] != CURRENT_AUTHORIZATION_ID:
    raise SystemExit("AION-227 authorization closeout id mismatch")
validate_aion225_closeout(payload["authorization_closeout"])
if payload["conditional_next_authorization"]["authorization_transaction_id"] != NEXT_AUTHORIZATION_ID:
    raise SystemExit("AION-227 conditional authorization id mismatch")
validate_authorization_record(
    load_json("examples/governed-learning-memory/continual-learning-pilot-authorization.json")
)
validate_continual_learning_pilot_authorization()
PY

./scripts/governed-learning-memory-engagement-application-operator-evaluation-no-go-regression.sh
./scripts/governed-learning-memory-engagement-application-no-go-regression.sh
./scripts/governed-learning-memory-engagement-application-check.sh
./scripts/governed-learning-memory-engagement-shadow-pilot-evidence-check.sh
AION_GLM_ENGAGEMENT_APPLICATION_RUNTIME_HOLD_SKIP_FULL_CHECK=1 \
  ./scripts/governed-learning-memory-engagement-application-runtime-hold.sh
./scripts/governed-learning-memory-continual-learning-pilot-authorization-check.sh
echo "governed learning memory engagement application operator evaluation PASS"
