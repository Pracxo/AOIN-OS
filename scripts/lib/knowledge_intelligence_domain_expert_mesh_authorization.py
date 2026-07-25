"""AION-212 domain expert mesh authorization evidence validator."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PROGRAM_ID = "AION-KNOWLEDGE-INTELLIGENCE-001"
AUTHORIZATION_ID = "AION-212-KI-0005"
PARENT_AUTHORIZATION_ID = "AION-210-KI-0004"
PARENT_EVALUATION_ID = "AION-EAE-001"
PARENT_DECISION = (
    "EPISTEMIC_ASSESSMENT_ENGINE_OPERATOR_EVALUATION_PASS_RECOMMEND_"
    "DOMAIN_EXPERT_MESH_AUTHORIZATION"
)
IMPLEMENTATION_TASK = "AION-213"
FORMAL_CLOSEOUT_TASK = "AION-214"
SCOPE = (
    "deterministic-domain-taxonomy-expert-profile-routing-independent-analysis-"
    "deliberation-disagreement-synthesis-abstention-core"
)
CANDIDATE_ID = "domain-expert-mesh-core"
WORKSTREAM = "knowledge-intelligence-domain-expert-mesh"

AUTHORIZED_CAPABILITIES: tuple[str, ...] = (
    "domain_taxonomy_contracts_approved",
    "domain_taxonomy_node_approved",
    "domain_specialty_contract_approved",
    "domain_expert_profile_contract_approved",
    "computational_expert_profile_approved",
    "expert_capability_scope_approved",
    "expert_independence_group_approved",
    "expert_perspective_role_approved",
    "expert_case_contract_approved",
    "explicit_case_domain_tags_approved",
    "explicit_case_specialty_tags_approved",
    "explicit_case_risk_class_approved",
    "explicit_claim_reference_binding_approved",
    "explicit_epistemic_assessment_binding_approved",
    "deterministic_case_decomposition_approved",
    "bounded_subquestion_plan_approved",
    "deterministic_expert_routing_approved",
    "exact_domain_match_routing_approved",
    "exact_specialty_match_routing_approved",
    "jurisdiction_aware_routing_approved",
    "version_aware_routing_approved",
    "temporal_scope_aware_routing_approved",
    "risk_aware_routing_approved",
    "deterministic_panel_selection_approved",
    "panel_composition_policy_approved",
    "required_domain_analyst_role_approved",
    "required_evidence_auditor_role_approved",
    "required_methodological_skeptic_role_approved",
    "high_stakes_risk_reviewer_role_approved",
    "independent_expert_assignment_approved",
    "independent_expert_report_approved",
    "evidence_bound_expert_report_approved",
    "assessment_bound_expert_report_approved",
    "bounded_assumption_record_approved",
    "evidence_gap_detection_approved",
    "methodological_limitation_record_approved",
    "cross_examination_critique_approved",
    "critique_response_approved",
    "circular_critique_rejection_approved",
    "self_review_rejection_approved",
    "disagreement_matrix_approved",
    "dissent_preservation_approved",
    "panel_alignment_state_approved",
    "bounded_consensus_description_approved",
    "bounded_synthesis_report_approved",
    "cross_domain_conflict_detection_approved",
    "uncertainty_propagation_approved",
    "confidence_non_amplification_approved",
    "underlying_assessment_cap_propagation_approved",
    "explicit_mesh_abstention_approved",
    "operator_escalation_recommendation_approved",
    "high_stakes_operator_review_approved",
    "in_memory_expert_mesh_session_approved",
    "synthetic_expert_mesh_fixture_replay_approved",
    "deterministic_expert_mesh_replay_approved",
    "bounded_expert_mesh_queries_approved",
    "expert_mesh_integrity_audit_approved",
    "redacted_expert_mesh_diagnostics_approved",
    "expert_mesh_incident_record_approved",
    "expert_mesh_operator_review_item_approved",
    "resource_budget_enforcement_approved",
    "documentation_and_static_evidence_approved",
    "no_human_identity_claim_enforcement_approved",
    "no_professional_credential_claim_enforcement_approved",
    "no_model_provider_call_enforcement_approved",
    "no_tool_execution_enforcement_approved",
    "no_network_fetch_enforcement_approved",
    "no_absolute_truth_enforcement_approved",
    "no_automatic_action_enforcement_approved",
    "no_knowledge_promotion_enforcement_approved",
    "no_belief_mutation_enforcement_approved",
    "no_persistent_mesh_write_enforcement_approved",
    "no_runtime_registration_enforcement_approved",
    "no_source_mutation_enforcement_approved",
    "no_git_mutation_enforcement_approved",
    "no_pr_creation_enforcement_approved",
    "no_approval_creation_enforcement_approved",
)

PROHIBITED_CAPABILITIES: tuple[str, ...] = (
    "human_expert_identity_claim_enabled",
    "human_expert_impersonation_enabled",
    "professional_credential_claim_enabled",
    "licensed_professional_claim_enabled",
    "automatic_semantic_domain_inference_enabled",
    "unbounded_domain_creation_enabled",
    "model_provider_integration_enabled",
    "model_call_enabled",
    "learned_expert_routing_enabled",
    "hidden_routing_weight_enabled",
    "tool_execution_enabled",
    "tool_selection_execution_enabled",
    "connector_integration_enabled",
    "network_acquisition_enabled",
    "public_network_fetch_enabled",
    "search_provider_integration_enabled",
    "browser_automation_enabled",
    "credential_use_enabled",
    "cookie_use_enabled",
    "authorization_header_use_enabled",
    "absolute_truth_oracle_enabled",
    "claim_true_boolean_assignment_enabled",
    "claim_false_boolean_assignment_enabled",
    "automatic_claim_acceptance_enabled",
    "automatic_claim_rejection_enabled",
    "expert_majority_truth_override_enabled",
    "consensus_as_truth_enabled",
    "panel_size_confidence_amplification_enabled",
    "dissent_suppression_enabled",
    "minority_report_deletion_enabled",
    "automatic_correction_effect_enabled",
    "automatic_retraction_effect_enabled",
    "automatic_supersession_effect_enabled",
    "contradiction_resolution_enabled",
    "knowledge_promotion_enabled",
    "verified_knowledge_creation_enabled",
    "automatic_memory_ingestion_enabled",
    "cognitive_belief_creation_enabled",
    "cognitive_belief_mutation_enabled",
    "user_statement_as_fact_enabled",
    "engagement_signal_as_fact_enabled",
    "autonomous_real_world_action_enabled",
    "high_stakes_action_enabled",
    "medical_decision_execution_enabled",
    "legal_decision_execution_enabled",
    "financial_decision_execution_enabled",
    "safety_critical_action_execution_enabled",
    "persistent_expert_mesh_write_enabled",
    "expert_mesh_database_enabled",
    "external_database_integration_enabled",
    "background_expert_worker_enabled",
    "scheduled_expert_mesh_job_enabled",
    "kernel_registration_enabled",
    "application_startup_registration_enabled",
    "api_route_enabled",
    "installed_cli_command_enabled",
    "sdk_runtime_resource_enabled",
    "source_body_parsing_enabled",
    "raw_source_content_storage_enabled",
    "source_patch_generation_enabled",
    "source_mutation_enabled",
    "worktree_creation_enabled",
    "git_mutation_enabled",
    "real_pull_request_creation_enabled",
    "approval_creation_enabled",
    "automatic_merge_enabled",
    "production_deployment_enabled",
    "model_weight_training_enabled",
    "runtime_effect",
    "dependency_change_approved",
    "migration_approved",
    "github_workflow_change_approved",
    "v02_tag_created",
    "v02_release_created",
)

RESOURCE_LIMITS: dict[str, int] = {
    "maximum_domains_per_case": 20,
    "maximum_specialties_per_case": 50,
    "maximum_claims_per_case": 100,
    "maximum_epistemic_assessments_per_case": 100,
    "maximum_subquestions_per_case": 50,
    "maximum_expert_profiles_considered": 100,
    "maximum_panel_size": 12,
    "maximum_required_roles_per_panel": 8,
    "maximum_expert_reports_per_case": 24,
    "maximum_critiques_per_case": 100,
    "maximum_deliberation_rounds": 3,
    "maximum_disagreement_items_per_case": 100,
    "maximum_evidence_references_per_report": 100,
    "maximum_reason_codes_per_report": 50,
    "maximum_operator_review_items": 100,
    "maximum_mesh_sessions": 100,
    "maximum_query_results": 1000,
    "maximum_fixture_records": 5000,
    "maximum_fixture_bytes": 4194304,
    "maximum_concurrent_experts": 8,
    "maximum_persistent_mesh_write_batch": 0,
    "maximum_model_provider_calls": 0,
    "maximum_tool_executions": 0,
    "maximum_network_calls": 0,
    "maximum_search_provider_calls": 0,
    "maximum_connector_calls": 0,
    "maximum_knowledge_promotions": 0,
    "maximum_belief_mutations": 0,
    "maximum_source_mutations": 0,
    "maximum_git_operations": 0,
    "maximum_runtime_created_pull_requests": 0,
    "maximum_approvals_created": 0,
    "maximum_autonomous_actions": 0,
    "maximum_high_stakes_actions": 0,
    "maximum_deployments": 0,
    "maximum_model_weight_changes": 0,
}

REQUIRED_PANEL_ROLES: tuple[str, ...] = (
    "domain_analyst",
    "evidence_auditor",
    "methodological_skeptic",
    "risk_reviewer",
    "temporal_scope_reviewer",
    "jurisdiction_reviewer",
    "version_reviewer",
    "synthesis_coordinator",
)

DOMAIN_EXPERT_SOURCE_FILES: tuple[str, ...] = (
    "services/brain-api/src/aion_brain/contracts/knowledge_domain_expert_mesh.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/domain_expert_mesh.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/domain_expert_profiles.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/domain_expert_routing.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/domain_expert_deliberation.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/domain_expert_synthesis.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/domain_expert_integrity.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/domain_expert_evidence.py",
)


def load_json(root: Path, relative: str) -> dict[str, Any]:
    return json.loads((root / relative).read_text(encoding="utf-8"))


def expected_authorized_capabilities() -> dict[str, bool]:
    return {key: True for key in AUTHORIZED_CAPABILITIES}


def expected_prohibited_capabilities() -> dict[str, bool]:
    return {key: False for key in PROHIBITED_CAPABILITIES}


def validate_authorization_payload(payload: dict[str, Any]) -> None:
    expected = {
        "program_id": PROGRAM_ID,
        "authorization_transaction_id": AUTHORIZATION_ID,
        "approval_record_id": AUTHORIZATION_ID,
        "parent_authorization_transaction_id": PARENT_AUTHORIZATION_ID,
        "parent_evaluation_id": PARENT_EVALUATION_ID,
        "parent_evaluation_decision": PARENT_DECISION,
        "candidate_id": CANDIDATE_ID,
        "workstream": WORKSTREAM,
        "implementation_task": IMPLEMENTATION_TASK,
        "formal_closeout_task": FORMAL_CLOSEOUT_TASK,
        "authorization_scope": SCOPE,
        "authorization_active": True,
        "authorization_consumed": False,
        "authorization_expired": False,
        "authorization_reusable": False,
        "domain_expert_mesh_authorized": True,
        "domain_expert_mesh_implemented": False,
        "synthetic": True,
        "read_only": True,
        "redacted": True,
        "runtime_effect": False,
    }
    for key, value in expected.items():
        if payload.get(key) != value:
            raise ValueError(f"domain expert mesh authorization invalid {key}: {payload.get(key)!r}")
    for key in (
        "authorization_transaction_approved",
        "explicit_approval_record_approval",
        "implementation_authorization_approved",
        "implementation_go_status",
    ):
        if payload.get(key) is not True:
            raise ValueError(f"approval flag must be true: {key}")
    if payload.get("implementation_no_go_status") is not False:
        raise ValueError("implementation_no_go_status must be false")
    if payload.get("authorized_capabilities") != expected_authorized_capabilities():
        raise ValueError("authorized capability matrix mismatch")
    if payload.get("prohibited_capabilities") != expected_prohibited_capabilities():
        raise ValueError("prohibited capability matrix mismatch")
    if payload.get("resource_limits") != RESOURCE_LIMITS:
        raise ValueError("resource limits mismatch")
    if payload.get("required_roles") != list(REQUIRED_PANEL_ROLES):
        raise ValueError("required panel roles mismatch")


def validate_repository_state(root: Path) -> None:
    for relative in DOMAIN_EXPERT_SOURCE_FILES:
        if (root / relative).exists():
            raise ValueError(f"AION-213 source must not exist on AION-212 branch: {relative}")


def validate_authorization_files(root: Path) -> None:
    payload = load_json(root, "examples/knowledge-intelligence/domain-expert-mesh-authorization.json")
    validate_authorization_payload(payload)
    auth = load_json(root, "docs/knowledge-intelligence/authorization-ledger.json")
    active = [record for record in auth["records"] if record.get("authorization_active") is True]
    if len(active) != 1:
        raise ValueError("exactly one Knowledge Intelligence authorization must be active")
    validate_authorization_payload(active[0])
    program = load_json(root, "docs/knowledge-intelligence/program-ledger.json")
    if program.get("active_knowledge_implementation_authorization") != AUTHORIZATION_ID:
        raise ValueError("program ledger active authorization mismatch")
    if program.get("active_knowledge_implementation_task") != IMPLEMENTATION_TASK:
        raise ValueError("program ledger active implementation task mismatch")
    if program.get("formal_closeout_task") != FORMAL_CLOSEOUT_TASK:
        raise ValueError("program ledger formal closeout mismatch")
    if program.get("domain_expert_mesh_authorized") is not True:
        raise ValueError("program ledger must authorize domain expert mesh")
    if program.get("domain_expert_mesh_implemented") is not False:
        raise ValueError("program ledger must keep domain expert mesh unimplemented")
    for key in PROHIBITED_CAPABILITIES:
        if program.get(key, False) is not False:
            raise ValueError(f"program ledger prohibited capability enabled: {key}")
    validate_repository_state(root)


def validate_runtime_hold(root: Path) -> None:
    validate_authorization_files(root)
    runtime = load_json(root, "examples/knowledge-intelligence/domain-expert-mesh-runtime-hold.json")
    for key in (
        "domain_expert_mesh_implemented",
        "domain_expert_mesh_runtime_enabled",
        "persistent_mesh_write_enabled",
        "model_provider_integration_enabled",
        "tool_execution_enabled",
        "network_access_enabled",
        "human_expert_identity_claim_enabled",
        "professional_credential_claim_enabled",
        "automatic_real_world_action_enabled",
        "knowledge_promotion_enabled",
        "belief_mutation_enabled",
        "runtime_effect",
    ):
        if runtime.get(key) is not False:
            raise ValueError(f"runtime hold flag must remain false: {key}")
    if runtime.get("domain_expert_mesh_authorized") is not True:
        raise ValueError("runtime hold must preserve authorization")
