#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
source "$ROOT_DIR/scripts/lib/immutable-tags.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"

PYTHONPATH="$ROOT_DIR/scripts/lib:$ROOT_DIR/services/brain-api/src:${PYTHONPATH:-}" "$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
import os
from pathlib import Path

from governed_learning_memory_program_final_evaluation import (
    AUTHORIZATION_ID,
    CAPABILITY_MATRIX,
    EVALUATION_ID,
    PASS_DECISION,
    validate_evaluation_report,
)

root = Path(os.environ["AION_REPO_ROOT"])
program = json.loads((root / "docs/governed-learning-memory/program-ledger.json").read_text(encoding="utf-8"))
auth = json.loads((root / "docs/governed-learning-memory/authorization-ledger.json").read_text(encoding="utf-8"))
report = json.loads((root / "examples/governed-learning-memory/program-final-evaluation-report.json").read_text(encoding="utf-8"))
matrix = json.loads((root / "examples/governed-learning-memory/program-final-capability-matrix.json").read_text(encoding="utf-8"))

validate_evaluation_report(report)

required = {
    "program_state": "governed_learning_memory_program_complete",
    "governed_learning_memory_program_complete": True,
    "governed_learning_memory_program_evaluation_id": EVALUATION_ID,
    "governed_learning_memory_program_evaluation_decision": PASS_DECISION,
    "active_glm_implementation_authorization_count": 0,
    "active_glm_implementation_authorization": None,
    "active_glm_implementation_task": None,
    "formal_closeout_task": None,
    "new_glm_implementation_authorization_created": False,
    "next_glm_implementation_authorization": None,
    "next_glm_implementation_task": None,
    "final_planned_task": "AION-229",
    "final_completed_task": "AION-229",
    "production_runtime_authorized": False,
    "repeat_live_pilot_authorized": False,
    "active_continual_learning_execution_authorization": False,
    "operator_invoked_continual_learning_pilot_available": False,
    "v02_release_ready": False,
}
for label, payload in (("program", program), ("authorization", auth)):
    for key, value in required.items():
        if payload.get(key) != value:
            raise SystemExit(f"{label} mismatch {key}: {payload.get(key)!r}")
    for key in (
        "background_continual_learning_enabled",
        "scheduled_continual_learning_enabled",
        "unbounded_autonomous_loop_enabled",
        "automatic_cycle_continuation_enabled",
        "automatic_source_discovery_enabled",
        "web_crawler_enabled",
        "automatic_candidate_approval_enabled",
        "automatic_knowledge_promotion_enabled",
        "automatic_persistence_enabled",
        "retained_pilot_store_enabled",
        "production_memory_write_enabled",
        "production_policy_mutation_enabled",
        "cognitive_memory_write_enabled",
        "actual_belief_creation_enabled",
        "actual_belief_mutation_enabled",
        "self_rewrite_enabled",
        "runtime_source_rewrite_enabled",
        "model_weight_training_enabled",
        "production_exposure",
        "runtime_enabled",
        "v02_tag_created",
        "v02_release_created",
    ):
        if payload.get(key) is not False:
            raise SystemExit(f"{label} prohibited flag enabled: {key}")
if auth.get("active_authorizations") != []:
    raise SystemExit("active GLM authorization list is not empty")
closed = next(item for item in auth["records"] if item.get("authorization_transaction_id") == AUTHORIZATION_ID)
expected_closed = {
    "authorization_active": False,
    "authorization_consumed": True,
    "authorization_expired": True,
    "authorization_reusable": False,
    "authorization_consumed_by_task": "AION-228",
    "authorization_consumed_by_prs": [145],
    "authorization_consumed_by_feature_commits": [
        "07c146fe574a967266a2f2ad8b4473f51daf935d"
    ],
    "authorization_consumed_by_merge_commits": [
        "0fc95c345c1f8daada58a5b45e6f3b1fdd33d9e0"
    ],
    "authorization_closed_by_task": "AION-229",
    "program_final_evaluation_id": EVALUATION_ID,
    "program_final_evaluation_decision": PASS_DECISION,
}
for key, value in expected_closed.items():
    if closed.get(key) != value:
        raise SystemExit(f"authorization closeout mismatch {key}: {closed.get(key)!r}")
if matrix.get("capability_matrix") != CAPABILITY_MATRIX:
    raise SystemExit("final capability matrix mismatch")
delivery = program.get("aion_229_delivery", {})
for key in ("pull_requests", "merge_commits", "feature_commits"):
    if not delivery.get(key):
        raise SystemExit(f"AION-229 delivery missing {key}")
if delivery.get("ci_result") != "pass":
    raise SystemExit("AION-229 primary CI is not reconciled as pass")
PY

aion_confirm_immutable_v01_tag_history >/dev/null
if git tag --list 'v0.2*' 'aion-v0.2*' | rg -n '.+'; then
  echo "ERROR: v0.2 tag exists" >&2
  exit 1
fi
if command -v gh >/dev/null 2>&1; then
  if gh release view v0.2 >/dev/null 2>&1 || gh release view aion-v0.2 >/dev/null 2>&1; then
    echo "ERROR: v0.2 release exists" >&2
    exit 1
  fi
fi

echo "governed learning memory program complete PASS"
