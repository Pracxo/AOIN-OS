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

root = Path(os.environ["AION_REPO_ROOT"])
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
]
for label, payload in (("program", program), ("authorization", auth)):
    if payload["authorization_transaction_id"] != "AION-221-GLM-0001":
        raise SystemExit(f"{label} authorization mismatch")
    if payload["active_glm_implementation_task"] != "AION-222":
        raise SystemExit(f"{label} active task mismatch")
    if payload["formal_closeout_task"] != "AION-223":
        raise SystemExit(f"{label} closeout task mismatch")
    if payload["knowledge_promotion_transaction_core_state"] != state:
        raise SystemExit(f"{label} implementation state mismatch")
    for key in required_true:
        if payload.get(key) is not True:
            raise SystemExit(f"{label} expected true: {key}")
    for key in required_false:
        if payload.get(key) is not False:
            raise SystemExit(f"{label} expected false: {key}")
    if payload["aion_221_delivery"]["pull_requests"] != [137]:
        raise SystemExit(f"{label} AION-221 PR reconciliation mismatch")
    if payload["aion_221_delivery"]["merge_commits"] != ["ecb1e8ce8560ac06040cd297bfc26ff2ad020273"]:
        raise SystemExit(f"{label} AION-221 merge reconciliation mismatch")

limits = program["resource_limits"]
expected_limits = {
    "maximum_promotion_requests_per_batch": 100,
    "maximum_candidates_per_request": 100,
    "maximum_lineage_references_per_candidate": 500,
    "maximum_source_references_per_candidate": 100,
    "maximum_claim_references_per_candidate": 20,
    "maximum_assessment_references_per_candidate": 20,
    "maximum_mesh_references_per_candidate": 20,
    "maximum_tool_session_references_per_candidate": 20,
    "maximum_approval_evidence_records_per_transaction": 4,
    "maximum_projection_records_per_transaction": 100,
    "maximum_versions_per_knowledge_identity": 100,
    "maximum_rollback_steps_per_transaction": 50,
    "maximum_compensation_steps_per_transaction": 50,
    "maximum_operator_review_items": 100,
    "maximum_in_memory_transactions": 1000,
    "maximum_query_results": 1000,
    "maximum_fixture_records": 5000,
    "maximum_fixture_bytes": 4194304,
    "maximum_concurrency": 4,
    "maximum_persistent_knowledge_writes": 0,
    "maximum_persistent_verified_knowledge_writes": 0,
    "maximum_cognitive_memory_writes": 0,
    "maximum_semantic_memory_writes": 0,
    "maximum_episodic_memory_writes": 0,
    "maximum_procedural_memory_writes": 0,
    "maximum_belief_creations": 0,
    "maximum_belief_mutations": 0,
    "maximum_automatic_knowledge_promotions": 0,
    "maximum_automatic_candidate_approvals": 0,
    "maximum_engagement_fact_promotions": 0,
    "maximum_engagement_confidence_effects": 0,
    "maximum_network_calls": 0,
    "maximum_search_provider_calls": 0,
    "maximum_connector_calls": 0,
    "maximum_model_provider_calls": 0,
    "maximum_actual_tool_executions": 0,
    "maximum_shell_commands": 0,
    "maximum_subprocess_executions": 0,
    "maximum_browser_actions": 0,
    "maximum_source_mutations": 0,
    "maximum_git_operations": 0,
    "maximum_runtime_created_pull_requests": 0,
    "maximum_runtime_created_approvals": 0,
    "maximum_deployments": 0,
    "maximum_model_weight_changes": 0,
}
for key, expected in expected_limits.items():
    if limits.get(key) != expected:
        raise SystemExit(f"resource limit mismatch: {key}: {limits.get(key)!r}")

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
