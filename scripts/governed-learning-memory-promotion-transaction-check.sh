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
export AION_GLM_PROMOTION_TRANSACTION_CHECK_RUNNING=1

mode="${1:-feature}"
case "$mode" in
  feature|--feature)
    mode="feature"
    ;;
  merged-main|--merged-main)
    mode="merged-main"
    ;;
  *)
    echo "usage: $0 [feature|merged-main]" >&2
    exit 2
    ;;
esac

authorized_source=(
  services/brain-api/src/aion_brain/contracts/governed_learning_memory.py
  services/brain-api/src/aion_brain/governed_learning_memory/__init__.py
  services/brain-api/src/aion_brain/governed_learning_memory/promotion_requests.py
  services/brain-api/src/aion_brain/governed_learning_memory/approval_evidence.py
  services/brain-api/src/aion_brain/governed_learning_memory/eligibility_revalidation.py
  services/brain-api/src/aion_brain/governed_learning_memory/knowledge_identity.py
  services/brain-api/src/aion_brain/governed_learning_memory/version_planning.py
  services/brain-api/src/aion_brain/governed_learning_memory/memory_projection.py
  services/brain-api/src/aion_brain/governed_learning_memory/promotion_transactions.py
  services/brain-api/src/aion_brain/governed_learning_memory/rollback.py
  services/brain-api/src/aion_brain/governed_learning_memory/integrity.py
  services/brain-api/src/aion_brain/governed_learning_memory/evidence.py
)

for path in "${authorized_source[@]}"; do
  [[ -f "$path" ]] || {
    echo "ERROR: authorized source missing: $path" >&2
    exit 1
  }
done

"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
import os
from pathlib import Path

from scripts.lib.governed_learning_memory_local_persistence_authorization import (
    AION221_AUTHORIZATION_ID,
    AION222_FEATURE_COMMIT,
    AION222_MERGE_COMMIT,
    AION222_MERGED_AT,
    AION222_SOURCE_SCOPE,
    AION223_AUTHORIZATION_ID,
    PASS_DECISION,
    validate_local_persistence_authorization,
)

root = Path(os.environ["AION_REPO_ROOT"])
validate_local_persistence_authorization(root)
program = json.loads((root / "docs/governed-learning-memory/program-ledger.json").read_text(encoding="utf-8"))
auth = json.loads((root / "docs/governed-learning-memory/authorization-ledger.json").read_text(encoding="utf-8"))

state = "implemented_deterministic_approval_bound_dry_run_in_memory_persistent_write_disabled"
required_true = [
    "governed_learning_memory_program_authorized",
    "knowledge_promotion_transaction_core_authorized",
    "knowledge_promotion_transaction_core_implemented",
    "candidate_revalidation_available",
    "operator_approval_evidence_validation_available",
    "separation_of_duties_validation_available",
    "knowledge_identity_derivation_available",
    "knowledge_duplicate_detection_available",
    "knowledge_conflict_detection_available",
    "knowledge_version_planning_available",
    "knowledge_supersession_planning_available",
    "knowledge_retraction_planning_available",
    "knowledge_expiry_planning_available",
    "semantic_memory_projection_planning_available",
    "episodic_memory_projection_planning_available",
    "procedural_memory_projection_planning_available",
    "belief_candidate_projection_planning_available",
    "rollback_plan_validation_available",
    "compensation_plan_validation_available",
    "promotion_integrity_audit_available",
    "in_memory_transaction_journal_available",
    "synthetic_fixture_replay_available",
    "bounded_exact_queries_available",
    "local_append_only_knowledge_store_authorized",
    "operator_invoked_local_persistence_authorized",
]
required_false = [
    "actual_knowledge_promotion_enabled",
    "persistent_knowledge_write_enabled",
    "persistent_verified_knowledge_write_enabled",
    "knowledge_database_enabled",
    "cognitive_memory_write_enabled",
    "semantic_memory_write_enabled",
    "episodic_memory_write_enabled",
    "procedural_memory_write_enabled",
    "cognitive_belief_creation_enabled",
    "cognitive_belief_mutation_enabled",
    "automatic_candidate_approval_enabled",
    "automatic_knowledge_promotion_enabled",
    "automatic_memory_ingestion_enabled",
    "automatic_engagement_learning_application_enabled",
    "runtime_enabled",
    "production_exposure",
    "runtime_effect",
    "background_persistent_knowledge_write_enabled",
    "production_persistent_knowledge_write_enabled",
    "approval_creation_by_runtime_enabled",
    "approval_decision_by_runtime_enabled",
    "network_access_enabled",
    "shell_command_execution_enabled",
    "subprocess_execution_enabled",
    "source_mutation_enabled",
    "git_mutation_enabled",
]
implemented_state = "governed_learning_memory_local_append_only_persistence_implemented_operator_invoked_isolated_pending_closeout"
engagement_authorized_state = "governed_learning_memory_engagement_application_authorized_not_implemented"
implemented_states = {implemented_state, engagement_authorized_state}
for label, payload in (("program", program), ("authorization", auth)):
    if payload.get("program_state") == engagement_authorized_state:
        if payload["authorization_transaction_id"] != "AION-225-GLM-0003":
            raise SystemExit(f"{label} current authorization mismatch")
        if payload["active_glm_implementation_task"] != "AION-226":
            raise SystemExit(f"{label} active task mismatch")
        if payload["formal_closeout_task"] != "AION-227":
            raise SystemExit(f"{label} closeout task mismatch")
    else:
        if payload["authorization_transaction_id"] != AION223_AUTHORIZATION_ID:
            raise SystemExit(f"{label} current authorization mismatch")
        if payload["active_glm_implementation_task"] != "AION-224":
            raise SystemExit(f"{label} active task mismatch")
        if payload["formal_closeout_task"] != "AION-225":
            raise SystemExit(f"{label} closeout task mismatch")
    if payload["knowledge_promotion_transaction_core_state"] != state:
        raise SystemExit(f"{label} implementation state mismatch")
    for key in required_true:
        if payload.get(key) is not True:
            raise SystemExit(f"{label} expected true: {key}")
    for key in required_false:
        if payload.get(key) is not False:
            raise SystemExit(f"{label} expected false: {key}")
    if payload.get("program_state") in implemented_states:
        for key in [
            "local_append_only_knowledge_store_implemented",
            "operator_invoked_local_persistence_available",
            "synthetic_local_persistence_pilot_completed",
        ]:
            if payload.get(key) is not True:
                raise SystemExit(f"{label} expected true: {key}")
    else:
        for key in [
            "local_append_only_knowledge_store_implemented",
            "operator_invoked_local_persistence_available",
        ]:
            if payload.get(key) is not False:
                raise SystemExit(f"{label} expected false: {key}")
    if payload["aion_221_delivery"]["pull_requests"] != [137]:
        raise SystemExit(f"{label} AION-221 PR reconciliation mismatch")
    if payload["aion_221_delivery"]["merge_commits"] != ["ecb1e8ce8560ac06040cd297bfc26ff2ad020273"]:
        raise SystemExit(f"{label} AION-221 merge reconciliation mismatch")
    expected_delivery = {
        "task_id": "AION-222",
        "branch": "phase/governed-learning-memory-promotion-transaction-core",
        "feature_commits": [AION222_FEATURE_COMMIT],
        "pull_requests": [138],
        "merge_commits": [AION222_MERGE_COMMIT],
        "ci_result": "pass",
        "completion_timestamp": AION222_MERGED_AT,
        "authorization_transaction": AION221_AUTHORIZATION_ID,
        "authorization_state": "consumed_by_AION-222_closed_by_AION-223",
        "next_task": "AION-223",
        "runtime_state": "promotion_transaction_core_implemented_dry_run_in_memory_write_disabled",
        "evaluation_id": "AION-GLMPE-001",
        "evaluation_decision": PASS_DECISION,
    }
    delivery = payload["aion_222_delivery"]
    for key, expected in expected_delivery.items():
        if delivery.get(key) != expected:
            raise SystemExit(f"{label} AION-222 delivery {key} mismatch")

records = {
    record["authorization_transaction_id"]: record
    for record in auth["records"]
    if "authorization_transaction_id" in record
}
closed = records.get(AION221_AUTHORIZATION_ID)
if not closed:
    raise SystemExit("AION-221 authorization record missing")
if closed.get("authorization_active") is not False:
    raise SystemExit("AION-221 authorization still active")
if closed.get("authorization_consumed") is not True:
    raise SystemExit("AION-221 authorization not consumed")
if closed.get("authorization_consumed_by_task") != "AION-222":
    raise SystemExit("AION-221 consumed-by task mismatch")
if closed.get("authorization_consumed_by_prs") != [138]:
    raise SystemExit("AION-221 consumed-by PR mismatch")
if closed.get("authorization_consumed_by_feature_commits") != [AION222_FEATURE_COMMIT]:
    raise SystemExit("AION-221 consumed-by feature commit mismatch")
if closed.get("authorization_consumed_by_merge_commits") != [AION222_MERGE_COMMIT]:
    raise SystemExit("AION-221 consumed-by merge commit mismatch")
if closed.get("authorization_closed_by_task") != "AION-223":
    raise SystemExit("AION-221 closeout task mismatch")

current = records.get(AION223_AUTHORIZATION_ID)
if not current:
    raise SystemExit("AION-223 authorization record missing")
if current.get("authorization_active") is True:
    if current.get("authorization_consumed") is not False:
        raise SystemExit("AION-223 authorization is already consumed")
elif current.get("authorization_active") is False:
    if (
        current.get("authorization_consumed") is not True
        or current.get("authorization_expired") is not True
        or current.get("authorization_consumed_by_task") != "AION-224"
        or current.get("authorization_consumed_by_prs") != [140]
        or current.get("authorization_closed_by_task") != "AION-225"
    ):
        raise SystemExit("AION-223 closeout mismatch")
else:
    raise SystemExit("AION-223 authorization active flag mismatch")
if current.get("implementation_approved", False) is not False:
    raise SystemExit("AION-223 implementation approval must remain false")
if current.get("runtime_enabled", False) is not False:
    raise SystemExit("AION-223 runtime must remain disabled")
if current.get("runtime_state") != "authorized_not_implemented":
    raise SystemExit("AION-223 runtime state mismatch")
if current.get("implementation_task") != "AION-224":
    raise SystemExit("AION-223 implementation task mismatch")

for relative in AION222_SOURCE_SCOPE:
    if not (root / relative).exists():
        raise SystemExit(f"AION-222 authorized source missing: {relative}")

example_dir = root / "examples/governed-learning-memory"
for path in sorted(example_dir.glob("*.json")):
    json.loads(path.read_text(encoding="utf-8"))
if not (root / "docs/adr/0186-approval-bound-knowledge-promotion-transaction-core.md").exists():
    raise SystemExit("ADR 0186 missing")
if "0186-approval-bound-knowledge-promotion-transaction-core.md" not in (root / "docs/adr/README.md").read_text(encoding="utf-8"):
    raise SystemExit("ADR 0186 not indexed")
PY

"$PYTHON_BIN" -m py_compile services/brain-api/src/aion_brain/contracts/governed_learning_memory.py services/brain-api/src/aion_brain/governed_learning_memory/*.py
"$PYTHON_BIN" -m pytest services/brain-api/tests/test_governed_learning_memory_*.py -q

./scripts/governed-learning-memory-promotion-transaction-no-go-regression.sh "$mode"
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/governed-learning-memory-program-no-go-regression.sh "$mode"
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/governed-learning-memory-program-authorization-check.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/knowledge-intelligence-program-complete-check.sh
aion_confirm_immutable_v01_tag_history >/dev/null

echo "governed learning memory promotion transaction PASS"
