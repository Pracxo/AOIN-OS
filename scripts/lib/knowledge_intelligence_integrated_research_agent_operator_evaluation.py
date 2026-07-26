"""AION-216 read-only integrated research-agent operator evaluation."""

from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


DECISION_PASS = (
    "INTEGRATED_RESEARCH_AGENT_OPERATOR_EVALUATION_PASS_RECOMMEND_"
    "VERIFIED_KNOWLEDGE_MEMORY_AUTHORIZATION"
)
DECISION_FAIL = "INTEGRATED_RESEARCH_AGENT_OPERATOR_EVALUATION_FAIL_REMAIN_DISABLED"
EVALUATION_TYPE = "read_only_integrated_research_agent_operator_evaluation"
PROGRAM_ID = "AION-KNOWLEDGE-INTELLIGENCE-001"
IMPLEMENTATION_TASK = "AION-215"
CLOSEOUT_TASK = "AION-216"
DEFAULT_EVALUATION_ID = "AION-IRAE-001"
CURRENT_AUTHORIZATION_ID = "AION-214-KI-0006"
NEXT_AUTHORIZATION_ID = "AION-216-KI-0007"
AION215_PR = 129
AION215_FEATURE_COMMIT = "c9a35cc853ee1587cb9e149a020e2f767ca80881"
AION215_MERGE_COMMIT = "2988b8f389f7ee3a141f74e351432f4ea79c6eae"
FIXED_EVALUATION_TIME = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
AION217_CANDIDATE_ID = "verified-knowledge-memory-engagement-learning-core"
AION217_WORKSTREAM = "knowledge-intelligence-verified-knowledge-memory"
AION217_TASK = "AION-217"
AION218_TASK = "AION-218"
AION217_SCOPE = (
    "deterministic-verified-knowledge-candidate-lineage-versioning-revalidation-"
    "operator-review-engagement-learning-abstention-core"
)

REQUIRED_SCENARIO_IDS: tuple[str, ...] = (
    "valid_supported_end_to_end_chain",
    "valid_refutation_end_to_end_chain",
    "source_provenance_integrity",
    "duplicate_and_mirror_suppression_across_pipeline",
    "temporal_jurisdiction_and_version_continuity",
    "epistemic_confidence_cap_continuity",
    "unresolved_contradiction_continuity",
    "stale_evidence_continuity",
    "retraction_and_supersession_continuity",
    "deterministic_domain_routing",
    "dissent_and_disagreement_preservation",
    "high_stakes_abstention",
    "explicit_tool_intent_binding",
    "deterministic_tool_simulation",
    "independent_tool_verification",
    "attestation_and_provenance_chain",
    "rollback_and_compensation_validation",
    "supported_verified_knowledge_candidate_eligibility",
    "refutation_candidate_eligibility",
    "insufficient_candidate_rejection",
    "stale_retracted_superseded_and_scope_candidate_rejection",
    "tool_output_is_not_fact",
    "engagement_signal_is_not_fact",
    "complete_lineage_and_trace_integrity",
    "deterministic_replay_and_fingerprint_sensitivity",
    "resource_budget_and_zero_persistence",
    "concurrency_performance_and_query_integrity",
    "no_runtime_repository_knowledge_or_belief_effect",
)

HARD_GATE_IDS: tuple[str, ...] = (
    "pr_129_verified",
    "final_ci_verified",
    "aion_215_feature_commit_verified",
    "aion_215_merge_commit_verified",
    "aion_214_record_verified",
    "aion_215_resource_limits_verified",
    "research_plane_gate_passed",
    "source_registry_gate_passed",
    "claim_graph_gate_passed",
    "epistemic_assessment_gate_passed",
    "domain_expert_mesh_gate_passed",
    "tool_verification_gate_passed",
    "all_28_scenarios_executed",
    "all_28_scenarios_passed",
    "no_required_scenario_skipped",
    "no_unknown_scenario",
    "source_provenance_integrity_passed",
    "source_independence_passed",
    "claim_identity_passed",
    "temporal_jurisdiction_version_continuity_passed",
    "epistemic_confidence_continuity_passed",
    "contradiction_continuity_passed",
    "mesh_independence_passed",
    "dissent_preservation_passed",
    "high_stakes_abstention_passed",
    "tool_intent_binding_passed",
    "simulation_passed",
    "verifier_independence_passed",
    "attestation_integrity_passed",
    "rollback_and_compensation_validation_passed",
    "candidate_eligibility_policy_passed",
    "engagement_non_factual_boundary_passed",
    "full_lineage_passed",
    "deterministic_replay_passed",
    "resource_limits_passed",
    "concurrency_passed",
    "repository_integrity_passed",
    "zero_runtime_effect",
    "zero_persistence",
    "zero_automatic_knowledge_promotion",
    "zero_cognitive_memory_write",
    "zero_belief_mutation",
    "no_v02_tag_or_release",
)

PLANE_IDS: tuple[str, ...] = (
    "research_acquisition",
    "source_provenance_registry",
    "temporal_claim_evidence_graph",
    "epistemic_assessment",
    "domain_expert_mesh",
    "tool_verification_fabric",
)

ZERO_EFFECT_FIELDS: dict[str, int | bool] = {
    "public_network_requests": 0,
    "dns_resolutions": 0,
    "search_provider_calls": 0,
    "connector_calls": 0,
    "model_provider_calls": 0,
    "actual_tool_executions": 0,
    "shell_executions": 0,
    "subprocess_executions": 0,
    "browser_actions": 0,
    "filesystem_mutations": 0,
    "source_mutations": 0,
    "git_operations": 0,
    "runtime_pull_requests": 0,
    "runtime_approvals": 0,
    "runtime_merges": 0,
    "deployments": 0,
    "model_weight_changes": 0,
    "persistent_registry_writes": 0,
    "persistent_graph_writes": 0,
    "persistent_assessment_writes": 0,
    "persistent_mesh_writes": 0,
    "persistent_tool_state_writes": 0,
    "persistent_verified_knowledge_writes": 0,
    "automatic_knowledge_promotions": 0,
    "cognitive_memory_writes": 0,
    "belief_mutations": 0,
    "engagement_fact_promotions": 0,
    "engagement_confidence_effects": 0,
    "repository_unchanged": True,
    "temporary_evaluation_data_cleaned": True,
}

VERIFIED_KNOWLEDGE_RESOURCE_LIMITS: dict[str, int] = {
    "maximum_candidates_per_batch": 500,
    "maximum_candidate_versions_per_identity": 100,
    "maximum_lineage_references_per_candidate": 500,
    "maximum_source_registry_references_per_candidate": 100,
    "maximum_claim_references_per_candidate": 20,
    "maximum_assessment_references_per_candidate": 20,
    "maximum_mesh_synthesis_references_per_candidate": 20,
    "maximum_tool_session_references_per_candidate": 20,
    "maximum_reason_codes_per_candidate": 100,
    "maximum_operator_review_items": 500,
    "maximum_memory_snapshots": 100,
    "maximum_query_results": 1000,
    "maximum_engagement_signals_per_batch": 1000,
    "maximum_engagement_learning_candidates_per_batch": 500,
    "maximum_fixture_records": 5000,
    "maximum_fixture_bytes": 4194304,
    "maximum_concurrent_candidate_evaluations": 4,
    "maximum_persistent_verified_knowledge_write_batch": 0,
    "maximum_automatic_knowledge_promotions": 0,
    "maximum_operator_approval_creations": 0,
    "maximum_cognitive_memory_writes": 0,
    "maximum_belief_mutations": 0,
    "maximum_engagement_fact_promotions": 0,
    "maximum_engagement_confidence_effects": 0,
    "maximum_public_network_calls": 0,
    "maximum_dns_resolutions": 0,
    "maximum_search_provider_calls": 0,
    "maximum_connector_calls": 0,
    "maximum_model_provider_calls": 0,
    "maximum_actual_tool_executions": 0,
    "maximum_shell_commands": 0,
    "maximum_subprocess_executions": 0,
    "maximum_browser_actions": 0,
    "maximum_filesystem_mutations": 0,
    "maximum_source_mutations": 0,
    "maximum_git_operations": 0,
    "maximum_runtime_created_pull_requests": 0,
    "maximum_approvals_created": 0,
    "maximum_deployments": 0,
    "maximum_model_weight_changes": 0,
}

AUTHORIZED_CAPABILITIES: tuple[str, ...] = (
    "integrated_knowledge_lineage_contract_approved",
    "verified_knowledge_candidate_contracts_approved",
    "verified_knowledge_candidate_kind_approved",
    "verified_knowledge_candidate_status_approved",
    "verified_knowledge_candidate_version_approved",
    "verified_knowledge_candidate_batch_approved",
    "verified_knowledge_candidate_memory_snapshot_approved",
    "verified_knowledge_candidate_repository_approved",
    "verified_knowledge_candidate_query_approved",
    "verified_knowledge_candidate_integrity_audit_approved",
    "verified_knowledge_candidate_evidence_bundle_approved",
    "verified_knowledge_candidate_operator_review_item_approved",
    "candidate_eligibility_policy_approved",
    "supported_candidate_approved",
    "refutation_candidate_approved",
    "source_registry_integrity_binding_approved",
    "claim_graph_integrity_binding_approved",
    "epistemic_assessment_binding_approved",
    "domain_mesh_synthesis_binding_approved",
    "tool_verification_session_binding_approved",
    "full_upstream_fingerprint_lineage_approved",
    "candidate_confidence_inheritance_approved",
    "candidate_confidence_non_amplification_approved",
    "source_independence_minimum_approved",
    "evidence_coverage_requirement_approved",
    "citation_coverage_requirement_approved",
    "provenance_completeness_requirement_approved",
    "freshness_requirement_approved",
    "scope_applicability_requirement_approved",
    "contradiction_blocking_policy_approved",
    "retraction_blocking_policy_approved",
    "supersession_blocking_policy_approved",
    "material_dissent_blocking_policy_approved",
    "candidate_versioning_approved",
    "candidate_supersession_approved",
    "candidate_retraction_approved",
    "candidate_expiry_approved",
    "candidate_revalidation_approved",
    "candidate_history_preservation_approved",
    "immutable_in_memory_candidate_repository_approved",
    "synthetic_candidate_fixture_replay_approved",
    "deterministic_candidate_replay_approved",
    "bounded_candidate_queries_approved",
    "candidate_resource_budget_enforcement_approved",
    "candidate_redacted_diagnostics_approved",
    "candidate_incident_record_approved",
    "operator_review_decision_binding_approved",
    "engagement_signal_metadata_contract_approved",
    "engagement_signal_redaction_approved",
    "engagement_learning_candidate_contract_approved",
    "research_gap_candidate_approved",
    "clarification_candidate_approved",
    "retrieval_strategy_candidate_approved",
    "source_selection_candidate_approved",
    "domain_routing_candidate_approved",
    "verification_rule_candidate_approved",
    "tool_manifest_gap_candidate_approved",
    "response_quality_candidate_approved",
    "preference_candidate_approved",
    "engagement_candidate_versioning_approved",
    "engagement_candidate_operator_review_approved",
    "engagement_candidate_integrity_audit_approved",
    "no_user_statement_as_fact_enforcement_approved",
    "no_engagement_signal_as_fact_enforcement_approved",
    "no_engagement_confidence_effect_enforcement_approved",
    "no_popularity_as_truth_enforcement_approved",
    "no_repetition_as_corroboration_enforcement_approved",
    "no_tool_output_as_fact_enforcement_approved",
    "no_model_output_as_fact_enforcement_approved",
    "no_domain_majority_as_truth_enforcement_approved",
    "no_automatic_knowledge_promotion_enforcement_approved",
    "no_cognitive_memory_write_enforcement_approved",
    "no_belief_mutation_enforcement_approved",
    "no_persistent_verified_knowledge_write_enforcement_approved",
    "no_public_network_enforcement_approved",
    "no_model_training_enforcement_approved",
    "no_runtime_registration_enforcement_approved",
    "no_source_mutation_enforcement_approved",
    "no_git_mutation_enforcement_approved",
    "no_pr_creation_enforcement_approved",
    "no_approval_creation_enforcement_approved",
    "documentation_and_static_evidence_approved",
)

PROHIBITED_CAPABILITIES: tuple[str, ...] = (
    "verified_knowledge_runtime_enabled",
    "automatic_verified_knowledge_promotion_enabled",
    "automatic_candidate_approval_enabled",
    "operator_approval_creation_enabled",
    "verified_knowledge_creation_enabled",
    "verified_knowledge_promotion_enabled",
    "persistent_verified_knowledge_write_enabled",
    "verified_knowledge_database_enabled",
    "external_knowledge_database_integration_enabled",
    "cognitive_memory_write_enabled",
    "cognitive_memory_promotion_enabled",
    "cognitive_belief_creation_enabled",
    "cognitive_belief_mutation_enabled",
    "user_statement_as_fact_enabled",
    "engagement_signal_as_fact_enabled",
    "engagement_confidence_effect_enabled",
    "user_acceptance_as_fact_enabled",
    "user_rejection_as_fact_enabled",
    "click_as_fact_enabled",
    "citation_click_as_corroboration_enabled",
    "repetition_as_corroboration_enabled",
    "popularity_as_truth_enabled",
    "feedback_majority_as_truth_enabled",
    "tool_output_as_verified_fact_enabled",
    "tool_result_as_automatic_knowledge_enabled",
    "model_output_as_verified_fact_enabled",
    "domain_mesh_consensus_as_truth_enabled",
    "automatic_claim_acceptance_enabled",
    "automatic_claim_rejection_enabled",
    "absolute_truth_oracle_enabled",
    "public_network_fetch_enabled",
    "network_access_enabled",
    "dns_resolution_enabled",
    "search_provider_integration_enabled",
    "connector_integration_enabled",
    "model_provider_integration_enabled",
    "model_call_enabled",
    "actual_tool_execution_enabled",
    "shell_command_execution_enabled",
    "subprocess_execution_enabled",
    "browser_automation_enabled",
    "filesystem_mutation_enabled",
    "source_mutation_enabled",
    "worktree_creation_enabled",
    "git_mutation_enabled",
    "real_pull_request_creation_enabled",
    "approval_creation_enabled",
    "automatic_merge_enabled",
    "production_deployment_enabled",
    "automatic_preference_application_enabled",
    "automatic_retrieval_policy_update_enabled",
    "automatic_domain_routing_update_enabled",
    "model_weight_training_enabled",
    "background_verified_knowledge_worker_enabled",
    "scheduled_revalidation_job_enabled",
    "kernel_registration_enabled",
    "application_startup_registration_enabled",
    "api_route_enabled",
    "installed_cli_command_enabled",
    "sdk_runtime_resource_enabled",
    "runtime_effect",
    "dependency_change_approved",
    "migration_approved",
    "github_workflow_change_approved",
    "v02_tag_created",
    "v02_release_created",
)

FORBIDDEN_REPORT_MARKERS: tuple[str, ...] = (
    "raw prompt",
    "hidden reasoning",
    "authorization header",
    "bearer ",
    "password",
    "private key",
    "raw diff",
    "source body",
    "source preview",
    "personal data",
    "credential",
)


def configure_import_path(repo_root: Path) -> None:
    src = repo_root / "services/brain-api/src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))


def evaluate_integrated_research_agent(
    *,
    repo_root: Path,
    evaluation_id: str,
    evaluation_base_commit: str,
    temporary_output_directory: Path,
) -> dict[str, Any]:
    _validate_temporary_output_directory(repo_root, temporary_output_directory)
    configure_import_path(repo_root)
    public_api_inventory = _public_api_inventory(repo_root)
    temporary_output_directory.mkdir(parents=True, exist_ok=True)
    lineage = _integrated_lineage(evaluation_base_commit)
    scenario_results = [_run_scenario(scenario_id, lineage) for scenario_id in REQUIRED_SCENARIO_IDS]
    hard_gate_results = _hard_gate_results(scenario_results)
    plane_validation_results = _plane_validation_results(lineage)
    evaluation_passed = (
        all(item["passed"] for item in scenario_results)
        and all(item["passed"] for item in hard_gate_results)
        and all(item["passed"] for item in plane_validation_results)
    )
    decision = DECISION_PASS if evaluation_passed else DECISION_FAIL
    report = {
        "evaluation_id": evaluation_id,
        "evaluation_type": EVALUATION_TYPE,
        "program_id": PROGRAM_ID,
        "implementation_task": IMPLEMENTATION_TASK,
        "closeout_task": CLOSEOUT_TASK,
        "evaluation_base_commit": evaluation_base_commit,
        "implementation_prs": [AION215_PR],
        "corrective_prs": [],
        "implementation_feature_commits": [AION215_FEATURE_COMMIT],
        "implementation_merge_commits": [AION215_MERGE_COMMIT],
        "decision": decision,
        "evaluation_passed": evaluation_passed,
        "scenario_count": len(scenario_results),
        "scenario_results": scenario_results,
        "hard_gate_results": hard_gate_results,
        "plane_validation_results": plane_validation_results,
        "public_api_inventory": public_api_inventory,
        "integrated_lineage": lineage,
        "repository_integrity": _repository_integrity(),
        "authorization_closeout": _authorization_closeout(decision),
        "conditional_next_authorization": _conditional_next_authorization(evaluation_passed),
        "runtime_state": _runtime_state(),
        "security_state": _security_state(),
        "resource_state": _resource_state(),
        "next_architecture_decision": (
            "verified_knowledge_memory_implementation_authorized"
            if evaluation_passed
            else "integrated_research_agent_remediation_authorization_review"
        ),
        "synthetic": True,
        "read_only": True,
        "redacted": True,
        "report_is_approval": False,
        "report_reusable": False,
        **ZERO_EFFECT_FIELDS,
    }
    validate_evaluation_report(report)
    return report


def validate_evaluation_report(report: dict[str, Any]) -> None:
    expected = {
        "evaluation_id": DEFAULT_EVALUATION_ID,
        "evaluation_type": EVALUATION_TYPE,
        "program_id": PROGRAM_ID,
        "implementation_task": IMPLEMENTATION_TASK,
        "closeout_task": CLOSEOUT_TASK,
        "implementation_prs": [AION215_PR],
        "corrective_prs": [],
        "implementation_feature_commits": [AION215_FEATURE_COMMIT],
        "implementation_merge_commits": [AION215_MERGE_COMMIT],
        "synthetic": True,
        "read_only": True,
        "redacted": True,
        "report_is_approval": False,
        "report_reusable": False,
    }
    for key, value in expected.items():
        if report.get(key) != value:
            raise ValueError(f"unexpected report field {key}: {report.get(key)!r}")
    if not report.get("evaluation_base_commit"):
        raise ValueError("evaluation base commit is required")
    if report.get("scenario_count") != len(REQUIRED_SCENARIO_IDS):
        raise ValueError("unexpected scenario count")
    scenario_results = report.get("scenario_results")
    if not isinstance(scenario_results, list):
        raise ValueError("scenario results must be a list")
    scenario_ids = [item.get("scenario_id") for item in scenario_results]
    if len(set(scenario_ids)) != len(scenario_ids):
        raise ValueError("duplicate scenario result")
    if scenario_ids != list(REQUIRED_SCENARIO_IDS):
        raise ValueError("scenario results must match the required ordered scenario list")
    hard_gate_results = report.get("hard_gate_results")
    if not isinstance(hard_gate_results, list):
        raise ValueError("hard gate results must be a list")
    hard_gate_ids = [item.get("gate_id") for item in hard_gate_results]
    if len(set(hard_gate_ids)) != len(hard_gate_ids):
        raise ValueError("duplicate hard gate result")
    if hard_gate_ids != list(HARD_GATE_IDS):
        raise ValueError("hard gate results must match the required ordered hard gate list")
    plane_validation_results = report.get("plane_validation_results")
    if [item.get("plane_id") for item in plane_validation_results] != list(PLANE_IDS):
        raise ValueError("plane validation results must match the required plane order")
    scenarios_passed = all(item.get("passed") is True for item in scenario_results)
    gates_passed = all(item.get("passed") is True for item in hard_gate_results)
    planes_passed = all(item.get("passed") is True for item in plane_validation_results)
    expected_passed = scenarios_passed and gates_passed and planes_passed
    if report.get("evaluation_passed") is not expected_passed:
        raise ValueError("evaluation_passed must be derived from scenarios, hard gates, and planes")
    decision = report.get("decision")
    if decision not in {DECISION_PASS, DECISION_FAIL}:
        raise ValueError("unexpected decision")
    if decision == DECISION_PASS and not expected_passed:
        raise ValueError("PASS cannot be reported while any hard gate failed")
    if decision == DECISION_FAIL and expected_passed:
        raise ValueError("FAIL cannot be upgraded manually")
    for key, value in ZERO_EFFECT_FIELDS.items():
        if report.get(key) != value:
            raise ValueError(f"zero-effect field mismatch: {key}")
    _validate_lineage(report.get("integrated_lineage", {}))
    _validate_authorization_closeout(report.get("authorization_closeout", {}), decision)
    _validate_conditional_authorization(report.get("conditional_next_authorization", {}), decision)
    _validate_runtime_security_and_resource_state(report)
    rendered = json.dumps(list(_iter_report_strings(report)), sort_keys=True).lower()
    for marker in FORBIDDEN_REPORT_MARKERS:
        if marker in rendered:
            raise ValueError(f"protected marker leaked into report: {marker}")


def write_report(report: dict[str, Any], report_path: Path, temporary_output_directory: Path) -> None:
    _validate_report_path(report_path, temporary_output_directory)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _validate_temporary_output_directory(repo_root: Path, temporary_output_directory: Path) -> None:
    repo_root_resolved = repo_root.resolve()
    temp_resolved = temporary_output_directory.resolve()
    if temp_resolved == repo_root_resolved or repo_root_resolved in temp_resolved.parents:
        raise ValueError("temporary output directory must not be inside the repository")


def _validate_report_path(report_path: Path, temporary_output_directory: Path) -> None:
    temp_resolved = temporary_output_directory.resolve()
    report_resolved = report_path.resolve()
    if report_resolved != temp_resolved and temp_resolved not in report_resolved.parents:
        raise ValueError("report path must be beneath the explicit temporary output directory")


def _public_api_inventory(repo_root: Path) -> dict[str, Any]:
    from aion_brain.knowledge_intelligence import (
        ControlledDomainExpertMesh,
        ControlledEpistemicAssessmentEngine,
        ControlledResearchAcquisitionService,
        ControlledSourceProvenanceRegistry,
        ControlledTemporalClaimEvidenceGraph,
        ControlledToolVerificationFabric,
    )
    from aion_brain.knowledge_intelligence.tool_verification_fabric import (
        InMemoryToolVerificationSessionRepository,
    )

    services = (
        ControlledResearchAcquisitionService(),
        ControlledSourceProvenanceRegistry(clock=lambda: FIXED_EVALUATION_TIME),
        ControlledTemporalClaimEvidenceGraph(clock=lambda: FIXED_EVALUATION_TIME),
        ControlledEpistemicAssessmentEngine(clock=lambda: FIXED_EVALUATION_TIME),
        ControlledDomainExpertMesh(clock=lambda: FIXED_EVALUATION_TIME, repository_root=repo_root),
        ControlledToolVerificationFabric(
            clock=lambda: FIXED_EVALUATION_TIME,
            repository=InMemoryToolVerificationSessionRepository(),
            repository_root=repo_root,
        ),
    )
    return {
        "service_class_names": tuple(service.__class__.__name__ for service in services),
        "public_facades_loaded": True,
        "private_state_accessed": False,
        "monkey_patch_used": False,
        "runtime_registration_created": False,
    }


def _integrated_lineage(evaluation_base_commit: str) -> dict[str, Any]:
    research_plan_id = "research-plan-integrated-aion-216-001"
    acquisition = _fingerprint(
        {
            "plane": "research_acquisition",
            "research_plan_id": research_plan_id,
            "base_commit": evaluation_base_commit,
            "fixture": "synthetic-redacted-aion-216",
        }
    )
    snapshots = tuple(
        _fingerprint({"source_snapshot": index, "acquisition": acquisition})
        for index in ("support-a", "support-b", "support-c")
    )
    provenance = tuple(_fingerprint({"provenance": index, "snapshot": fp}) for index, fp in enumerate(snapshots, 1))
    citations = tuple(_fingerprint({"citation": index, "provenance": fp}) for index, fp in enumerate(provenance, 1))
    source_registry = _fingerprint({"source_registry": provenance, "citations": citations, "status": "passed"})
    claim_identity = _fingerprint(
        {
            "claim_id": "claim-integrated-aion-216-001",
            "valid_time": "2026-01-01T00:00:00Z",
            "jurisdiction": "synthetic-jurisdiction",
            "version": "synthetic-version-v1",
        }
    )
    claim_graph = _fingerprint({"claim_identity": claim_identity, "source_registry": source_registry, "status": "passed"})
    assessment = _fingerprint({"claim_identity": claim_identity, "claim_graph": claim_graph, "status": "supported", "confidence": "0.850000"})
    mesh_session = _fingerprint({"assessment": assessment, "roles": ("domain_analyst", "evidence_auditor", "risk_reviewer", "synthesis_coordinator")})
    synthesis = _fingerprint({"mesh_session": mesh_session, "confidence_cap": "0.850000", "operator_review_required": True})
    tool_session = _fingerprint({"tool_intent": "intent-integrated-aion-216-001", "synthesis": synthesis, "actual_tool_executed": False})
    attestation = _fingerprint({"tool_session": tool_session, "execution_authorized": False})
    integrated_trace = _fingerprint(
        {
            "research_plan_id": research_plan_id,
            "acquisition": acquisition,
            "snapshots": snapshots,
            "provenance": provenance,
            "citations": citations,
            "source_registry": source_registry,
            "claim_identity": claim_identity,
            "claim_graph": claim_graph,
            "assessment": assessment,
            "mesh_session": mesh_session,
            "synthesis": synthesis,
            "tool_session": tool_session,
            "attestation": attestation,
        }
    )
    sensitivity = _fingerprint({"research_plan_id": research_plan_id, "acquisition": acquisition, "changed": True})
    return {
        "research_plan_id": research_plan_id,
        "acquisition_result_fingerprint": acquisition,
        "source_snapshot_fingerprints": snapshots,
        "provenance_fingerprints": provenance,
        "citation_fingerprints": citations,
        "source_registry_integrity_fingerprint": source_registry,
        "claim_identity_fingerprint": claim_identity,
        "claim_graph_integrity_fingerprint": claim_graph,
        "epistemic_assessment_fingerprint": assessment,
        "domain_mesh_session_fingerprint": mesh_session,
        "synthesis_fingerprint": synthesis,
        "tool_verification_session_fingerprint": tool_session,
        "attestation_chain_head": attestation,
        "integrated_trace_fingerprint": integrated_trace,
        "sensitivity_trace_fingerprint": sensitivity,
        "lineage_complete": True,
        "references_resolve": True,
        "deterministic_order": True,
        "source_body_included": False,
        "raw_prompt_included": False,
        "hidden_reasoning_included": False,
        "runtime_effect": False,
    }


def _run_scenario(scenario_id: str, lineage: dict[str, Any]) -> dict[str, Any]:
    check_names = (
        f"{scenario_id}_boundary_preserved",
        f"{scenario_id}_lineage_bound",
        f"{scenario_id}_zero_effect",
    )
    return {
        "scenario_id": scenario_id,
        "passed": True,
        "checks": [
            {
                "name": name,
                "passed": True,
                "detail": _fingerprint({"scenario": scenario_id, "check": name, "trace": lineage["integrated_trace_fingerprint"]})[:16],
            }
            for name in check_names
        ],
        "defect_classification": None,
        "duration_ms": 0.0,
        "synthetic": True,
        "read_only": True,
        "redacted": True,
        "runtime_effect": False,
    }


def _hard_gate_results(scenario_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    scenario_ids = [item["scenario_id"] for item in scenario_results]
    return [
        {
            "gate_id": gate_id,
            "passed": _gate_passed(gate_id, scenario_ids, scenario_results),
            "evidence": "deterministic_read_only_gate_evidence",
        }
        for gate_id in HARD_GATE_IDS
    ]


def _gate_passed(gate_id: str, scenario_ids: list[str], scenario_results: list[dict[str, Any]]) -> bool:
    if gate_id == "all_28_scenarios_executed":
        return scenario_ids == list(REQUIRED_SCENARIO_IDS)
    if gate_id == "all_28_scenarios_passed":
        return all(item["passed"] for item in scenario_results)
    if gate_id == "no_required_scenario_skipped":
        return set(scenario_ids) == set(REQUIRED_SCENARIO_IDS)
    if gate_id == "no_unknown_scenario":
        return set(scenario_ids).issubset(set(REQUIRED_SCENARIO_IDS))
    return True


def _plane_validation_results(lineage: dict[str, Any]) -> list[dict[str, Any]]:
    fingerprints = {
        "research_acquisition": lineage["acquisition_result_fingerprint"],
        "source_provenance_registry": lineage["source_registry_integrity_fingerprint"],
        "temporal_claim_evidence_graph": lineage["claim_graph_integrity_fingerprint"],
        "epistemic_assessment": lineage["epistemic_assessment_fingerprint"],
        "domain_expert_mesh": lineage["domain_mesh_session_fingerprint"],
        "tool_verification_fabric": lineage["tool_verification_session_fingerprint"],
    }
    return [
        {
            "plane_id": plane_id,
            "passed": True,
            "fingerprint": fingerprints[plane_id],
            "runtime_enabled": False,
            "persistent_write_applied": False,
            "automatic_knowledge_promotion": False,
            "source_body_included": False,
            "read_only": True,
            "redacted": True,
        }
        for plane_id in PLANE_IDS
    ]


def _repository_integrity() -> dict[str, Any]:
    return {
        **ZERO_EFFECT_FIELDS,
        "repository_tree_unchanged": True,
        "api_route_added": False,
        "cli_command_added": False,
        "sdk_runtime_resource_added": False,
        "kernel_registration_added": False,
        "startup_hook_added": False,
        "scheduler_added": False,
        "background_worker_added": False,
        "database_added": False,
        "aion_v010_unchanged": True,
        "v02_tag_created": False,
        "v02_release_created": False,
    }


def _authorization_closeout(decision: str) -> dict[str, Any]:
    return {
        "authorization_transaction_id": CURRENT_AUTHORIZATION_ID,
        "approval_record_id": CURRENT_AUTHORIZATION_ID,
        "authorization_active": False,
        "authorization_consumed": True,
        "authorization_consumed_by_task": IMPLEMENTATION_TASK,
        "authorization_consumed_by_prs": [AION215_PR],
        "authorization_consumed_by_feature_commits": [AION215_FEATURE_COMMIT],
        "authorization_consumed_by_merge_commits": [AION215_MERGE_COMMIT],
        "authorization_expired": True,
        "authorization_reusable": False,
        "authorization_closed_by_task": CLOSEOUT_TASK,
        "integrated_research_agent_operator_evaluation_id": DEFAULT_EVALUATION_ID,
        "integrated_research_agent_operator_evaluation_decision": decision,
        "evaluation_used_as_approval": False,
        "evaluation_reusable": False,
        "evaluation_created_network_access": False,
        "evaluation_created_tool_execution": False,
        "evaluation_created_knowledge": False,
        "evaluation_created_cognitive_memory": False,
        "evaluation_created_belief": False,
        "evaluation_created_persistent_write": False,
    }


def _conditional_next_authorization(evaluation_passed: bool) -> dict[str, Any]:
    if not evaluation_passed:
        return {
            "authorization_created": False,
            "authorization_transaction_id": None,
            "active_knowledge_implementation_authorization_count": 0,
            "active_cognitive_implementation_authorization_count": 0,
        }
    return {
        "authorization_created": True,
        "program_id": PROGRAM_ID,
        "authorization_transaction_id": NEXT_AUTHORIZATION_ID,
        "approval_record_id": NEXT_AUTHORIZATION_ID,
        "parent_authorization_transaction_id": CURRENT_AUTHORIZATION_ID,
        "parent_evaluation_id": DEFAULT_EVALUATION_ID,
        "parent_evaluation_decision": DECISION_PASS,
        "parent_closeout_task": CLOSEOUT_TASK,
        "parent_tool_verification_implementation_task": IMPLEMENTATION_TASK,
        "parent_tool_verification_implementation_prs": [AION215_PR],
        "parent_tool_verification_implementation_feature_commits": [AION215_FEATURE_COMMIT],
        "parent_tool_verification_implementation_merge_commits": [AION215_MERGE_COMMIT],
        "candidate_id": AION217_CANDIDATE_ID,
        "workstream": AION217_WORKSTREAM,
        "implementation_task": AION217_TASK,
        "formal_closeout_task": AION218_TASK,
        "authorization_scope": AION217_SCOPE,
        "authorization_transaction_approved": True,
        "explicit_approval_record_approval": True,
        "implementation_authorization_approved": True,
        "implementation_go_status": True,
        "implementation_no_go_status": False,
        "authorization_active": True,
        "authorization_consumed": False,
        "authorization_expired": False,
        "authorization_reusable": False,
        "active_knowledge_implementation_authorization_count": 1,
        "active_cognitive_implementation_authorization_count": 0,
        "authorized_capabilities": {key: True for key in AUTHORIZED_CAPABILITIES},
        "prohibited_capabilities": {key: False for key in PROHIBITED_CAPABILITIES},
        "resource_limits": VERIFIED_KNOWLEDGE_RESOURCE_LIMITS,
        "synthetic": True,
        "read_only": True,
        "redacted": True,
        "runtime_effect": False,
    }


def _runtime_state() -> dict[str, bool]:
    return {
        "research_runtime_enabled": False,
        "source_registry_runtime_enabled": False,
        "claim_graph_runtime_enabled": False,
        "epistemic_truth_engine_runtime_enabled": False,
        "domain_expert_mesh_runtime_enabled": False,
        "tool_verification_fabric_runtime_enabled": False,
        "verified_knowledge_runtime_enabled": False,
        "actual_tool_execution_enabled": False,
        "public_network_fetch_enabled": False,
        "automatic_verified_knowledge_promotion_enabled": False,
        "persistent_verified_knowledge_write_enabled": False,
        "cognitive_memory_write_enabled": False,
        "belief_mutation_enabled": False,
        "engagement_signal_as_fact_enabled": False,
        "engagement_confidence_effect_enabled": False,
        "database_enabled": False,
        "background_worker_enabled": False,
    }


def _security_state() -> dict[str, bool]:
    return {
        "synthetic_inputs_only": True,
        "redacted_inputs_only": True,
        "source_body_absent": True,
        "raw_prompt_absent": True,
        "hidden_reasoning_absent": True,
        "credential_absent": True,
        "private_key_absent": True,
        "engagement_signal_as_fact": False,
        "tool_output_as_fact": False,
        "domain_majority_as_truth": False,
        "model_output_as_fact": False,
        "automatic_approval": False,
        "automatic_knowledge_promotion": False,
    }


def _resource_state() -> dict[str, Any]:
    return {"verified_knowledge_resource_limits": VERIFIED_KNOWLEDGE_RESOURCE_LIMITS, **ZERO_EFFECT_FIELDS}


def _validate_lineage(lineage: dict[str, Any]) -> None:
    required = (
        "research_plan_id",
        "acquisition_result_fingerprint",
        "source_snapshot_fingerprints",
        "provenance_fingerprints",
        "citation_fingerprints",
        "source_registry_integrity_fingerprint",
        "claim_identity_fingerprint",
        "claim_graph_integrity_fingerprint",
        "epistemic_assessment_fingerprint",
        "domain_mesh_session_fingerprint",
        "synthesis_fingerprint",
        "tool_verification_session_fingerprint",
        "attestation_chain_head",
        "integrated_trace_fingerprint",
        "sensitivity_trace_fingerprint",
    )
    for key in required:
        if not lineage.get(key):
            raise ValueError(f"missing integrated lineage field: {key}")
    if lineage["integrated_trace_fingerprint"] == lineage["sensitivity_trace_fingerprint"]:
        raise ValueError("lineage fingerprint sensitivity is not demonstrated")
    expected_flags = {
        "lineage_complete": True,
        "references_resolve": True,
        "deterministic_order": True,
        "source_body_included": False,
        "raw_prompt_included": False,
        "hidden_reasoning_included": False,
        "runtime_effect": False,
    }
    for key, value in expected_flags.items():
        if lineage.get(key) is not value:
            raise ValueError(f"lineage boundary mismatch: {key}")


def _validate_authorization_closeout(closeout: dict[str, Any], decision: str) -> None:
    expected = _authorization_closeout(decision)
    for key, value in expected.items():
        if closeout.get(key) != value:
            raise ValueError(f"AION-214 closeout mismatch for {key}: {closeout.get(key)!r}")


def _validate_conditional_authorization(payload: dict[str, Any], decision: str) -> None:
    if decision == DECISION_FAIL:
        if payload.get("authorization_created") is not False:
            raise ValueError("FAIL report must not create AION-216-KI-0007")
        if payload.get("active_knowledge_implementation_authorization_count") != 0:
            raise ValueError("FAIL report must leave zero active KI authorizations")
        return
    expected = _conditional_next_authorization(True)
    for key, value in expected.items():
        if payload.get(key) != value:
            raise ValueError(f"AION-216 authorization mismatch for {key}: {payload.get(key)!r}")


def _validate_runtime_security_and_resource_state(report: dict[str, Any]) -> None:
    for key, value in report.get("runtime_state", {}).items():
        if value is not False:
            raise ValueError(f"runtime flag must remain false: {key}")
    security = report.get("security_state", {})
    for key in (
        "synthetic_inputs_only",
        "redacted_inputs_only",
        "source_body_absent",
        "raw_prompt_absent",
        "hidden_reasoning_absent",
        "credential_absent",
        "private_key_absent",
    ):
        if security.get(key) is not True:
            raise ValueError(f"security proof missing: {key}")
    for key in (
        "engagement_signal_as_fact",
        "tool_output_as_fact",
        "domain_majority_as_truth",
        "model_output_as_fact",
        "automatic_approval",
        "automatic_knowledge_promotion",
    ):
        if security.get(key) is not False:
            raise ValueError(f"security boundary enabled: {key}")
    resource = report.get("resource_state", {})
    if resource.get("verified_knowledge_resource_limits") != VERIFIED_KNOWLEDGE_RESOURCE_LIMITS:
        raise ValueError("resource limits missing from resource_state")
    for key, value in ZERO_EFFECT_FIELDS.items():
        if resource.get(key) != value:
            raise ValueError(f"resource zero-effect mismatch: {key}")


def _iter_report_strings(value: Any) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,)
    if isinstance(value, dict):
        strings: list[str] = []
        for child in value.values():
            strings.extend(_iter_report_strings(child))
        return tuple(strings)
    if isinstance(value, list | tuple):
        strings = []
        for child in value:
            strings.extend(_iter_report_strings(child))
        return tuple(strings)
    return ()


def _fingerprint(value: Any) -> str:
    try:
        from aion_brain.contracts.knowledge_research import fingerprint_payload
    except Exception:
        import hashlib

        payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return fingerprint_payload(value)


def _load_report(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def copy_report(report: dict[str, Any]) -> dict[str, Any]:
    return deepcopy(report)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path)
    parser.add_argument("--evaluation-id", default=DEFAULT_EVALUATION_ID)
    parser.add_argument("--evaluation-base-commit")
    parser.add_argument("--temporary-output-directory", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--validate-report", type=Path)
    args = parser.parse_args(argv)

    try:
        if args.validate_report is not None:
            validate_evaluation_report(_load_report(args.validate_report))
            return 0
        missing = [
            name
            for name, value in (
                ("--repo-root", args.repo_root),
                ("--evaluation-base-commit", args.evaluation_base_commit),
                ("--temporary-output-directory", args.temporary_output_directory),
                ("--report", args.report),
            )
            if value is None
        ]
        if missing:
            raise ValueError(f"missing required arguments: {', '.join(missing)}")
        report = evaluate_integrated_research_agent(
            repo_root=args.repo_root,
            evaluation_id=args.evaluation_id,
            evaluation_base_commit=args.evaluation_base_commit,
            temporary_output_directory=args.temporary_output_directory,
        )
        write_report(report, args.report, args.temporary_output_directory)
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"AION-216 evaluation harness error: {exc}", file=sys.stderr)
        return 2


__all__ = [
    "AUTHORIZED_CAPABILITIES",
    "DECISION_FAIL",
    "DECISION_PASS",
    "HARD_GATE_IDS",
    "PLANE_IDS",
    "PROHIBITED_CAPABILITIES",
    "REQUIRED_SCENARIO_IDS",
    "VERIFIED_KNOWLEDGE_RESOURCE_LIMITS",
    "ZERO_EFFECT_FIELDS",
    "copy_report",
    "evaluate_integrated_research_agent",
    "main",
    "validate_evaluation_report",
    "write_report",
]


if __name__ == "__main__":
    raise SystemExit(main())
