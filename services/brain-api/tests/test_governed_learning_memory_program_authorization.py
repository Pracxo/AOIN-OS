from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PROGRAM_ID = "AION-GOVERNED-LEARNING-MEMORY-001"
PROGRAM_STATE = (
    "governed_learning_memory_promotion_transaction_core_implemented_"
    "write_disabled_pending_closeout"
)
AUTH_ID = "AION-221-GLM-0001"
CANDIDATE_ID = "approval-bound-knowledge-promotion-transaction-core"
WORKSTREAM = "governed-learning-memory-integration"
IMPLEMENTATION_TASK = "AION-222"
FORMAL_CLOSEOUT_TASK = "AION-223"
SCOPE = (
    "verified-candidate-operator-approval-provenance-revalidation-deduplication-"
    "conflict-supersession-rollback-dry-run-cognitive-memory-projection-core"
)
KI_DECISION = "CONTROLLED_PUBLIC_RESEARCH_PILOT_PASS_COMPLETE_KNOWLEDGE_INTELLIGENCE_PROGRAM"

AUTHORIZED_CAPABILITIES = {
    "knowledge_promotion_request_contract_approved",
    "promotion_candidate_binding_approved",
    "verified_candidate_lineage_binding_approved",
    "candidate_eligibility_revalidation_approved",
    "source_provenance_revalidation_approved",
    "claim_scope_revalidation_approved",
    "epistemic_confidence_revalidation_approved",
    "domain_dissent_revalidation_approved",
    "tool_attestation_revalidation_approved",
    "operator_approval_evidence_contract_approved",
    "approval_expiry_validation_approved",
    "approval_revocation_validation_approved",
    "separation_of_duties_policy_approved",
    "knowledge_identity_derivation_approved",
    "knowledge_version_plan_approved",
    "knowledge_supersession_plan_approved",
    "knowledge_retraction_plan_approved",
    "knowledge_expiry_plan_approved",
    "conflict_detection_approved",
    "duplicate_detection_approved",
    "memory_projection_plan_approved",
    "semantic_memory_projection_plan_approved",
    "episodic_memory_projection_plan_approved",
    "procedural_memory_projection_plan_approved",
    "belief_projection_candidate_plan_approved",
    "dry_run_promotion_transaction_approved",
    "idempotency_validation_approved",
    "rollback_plan_validation_approved",
    "compensation_plan_validation_approved",
    "in_memory_transaction_journal_approved",
    "promotion_integrity_audit_approved",
    "redacted_promotion_evidence_approved",
    "operator_review_item_approved",
    "synthetic_fixture_replay_approved",
    "bounded_exact_queries_approved",
    "documentation_and_static_evidence_approved",
}

PROHIBITED_CAPABILITIES = {
    "runtime_enabled",
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
    "engagement_factual_effect_enabled",
    "engagement_confidence_effect_enabled",
    "background_learning_enabled",
    "scheduled_learning_enabled",
    "runtime_source_rewrite_enabled",
    "source_mutation_enabled",
    "git_mutation_enabled",
    "real_pull_request_creation_enabled",
    "approval_creation_by_runtime_enabled",
    "automatic_merge_enabled",
    "production_deployment_enabled",
    "model_weight_training_enabled",
    "public_network_access_enabled",
    "search_provider_integration_enabled",
    "connector_integration_enabled",
    "model_provider_integration_enabled",
    "actual_tool_execution_enabled",
    "shell_command_execution_enabled",
    "subprocess_execution_enabled",
    "browser_automation_enabled",
    "api_route_enabled",
    "installed_cli_command_enabled",
    "kernel_registration_enabled",
    "application_startup_registration_enabled",
    "scheduler_enabled",
    "background_worker_enabled",
    "production_exposure",
    "v02_release_ready",
    "v02_tag_created",
    "v02_release_created",
}


def load_json(relative: str) -> dict[str, object]:
    return json.loads((REPO_ROOT / relative).read_text(encoding="utf-8"))


def test_aion_221_program_and_authorization_are_exact() -> None:
    program = load_json("docs/governed-learning-memory/program-ledger.json")
    auth = load_json("docs/governed-learning-memory/authorization-ledger.json")

    for payload in (program, auth):
        assert payload["program_id"] == PROGRAM_ID
        assert payload["program_name"] == "AION Governed Learning and Memory Integration Program"
        assert payload["program_state"] == PROGRAM_STATE
        assert payload["parent_program_ids"] == [
            "AION-COGNITIVE-ARCHITECTURE-001",
            "AION-KNOWLEDGE-INTELLIGENCE-001",
            "AION-SELF-IMPROVEMENT-001",
        ]
        assert payload["created_by_task"] == "AION-221"
        assert payload["final_planned_task"] == "AION-229"
        assert payload["active_glm_implementation_authorization_count"] == 1
        assert payload["active_glm_implementation_authorization"] == AUTH_ID
        assert payload["active_glm_implementation_task"] == IMPLEMENTATION_TASK
        assert payload["formal_closeout_task"] == FORMAL_CLOSEOUT_TASK
        assert payload["new_program_created"] is True

    assert auth["authorization_transaction_id"] == AUTH_ID
    assert auth["approval_record_id"] == AUTH_ID
    assert auth["candidate_id"] == CANDIDATE_ID
    assert auth["workstream"] == WORKSTREAM
    assert auth["implementation_task"] == IMPLEMENTATION_TASK
    assert auth["formal_closeout_task"] == FORMAL_CLOSEOUT_TASK
    assert auth["authorization_scope"] == SCOPE
    assert auth["authorization_transaction_approved"] is True
    assert auth["explicit_approval_record_approval"] is True
    assert auth["implementation_authorization_approved"] is True
    assert auth["implementation_go_status"] is True
    assert auth["implementation_no_go_status"] is False
    assert auth["authorization_active"] is True
    assert auth["authorization_consumed"] is False
    assert auth["authorization_expired"] is False
    assert auth["authorization_reusable"] is False


def test_authorized_and_prohibited_capabilities_are_explicit() -> None:
    auth = load_json("docs/governed-learning-memory/authorization-ledger.json")

    assert set(auth["authorized_capabilities"]) == AUTHORIZED_CAPABILITIES
    assert set(auth["prohibited_capabilities"]) == PROHIBITED_CAPABILITIES
    assert all(auth["authorized_capabilities"][key] is True for key in AUTHORIZED_CAPABILITIES)
    assert all(auth["prohibited_capabilities"][key] is False for key in PROHIBITED_CAPABILITIES)
