"""AION-214 tool verification authorization evidence validator."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PROGRAM_ID = "AION-KNOWLEDGE-INTELLIGENCE-001"
AUTHORIZATION_ID = "AION-214-KI-0006"
PARENT_AUTHORIZATION_ID = "AION-212-KI-0005"
EVALUATION_ID = "AION-DEME-001"
PASS_DECISION = (
    "DOMAIN_EXPERT_MESH_OPERATOR_EVALUATION_PASS_RECOMMEND_"
    "TOOL_VERIFICATION_FABRIC_AUTHORIZATION"
)
IMPLEMENTATION_TASK = "AION-215"
FORMAL_CLOSEOUT_TASK = "AION-216"
SCOPE = (
    "deterministic-tool-manifest-intent-plan-simulation-verification-"
    "attestation-effect-evidence-rollback-abstention-core"
)
CANDIDATE_ID = "deterministic-tool-verification-fabric-core"
WORKSTREAM = "knowledge-intelligence-tool-verification-fabric"
AUTHORIZED_PROGRAM_STATE = "tool_verification_fabric_authorized_not_implemented"
IMPLEMENTED_PROGRAM_STATE = (
    "tool_verification_fabric_implemented_persistent_write_disabled_pending_closeout"
)
VERIFIED_KNOWLEDGE_AUTHORIZED_PROGRAM_STATE = (
    "verified_knowledge_memory_authorized_not_implemented"
)
VERIFIED_KNOWLEDGE_IMPLEMENTED_PROGRAM_STATE = (
    "verified_knowledge_memory_implemented_persistent_write_disabled_pending_closeout"
)
IMPLEMENTED_FABRIC_STATE = (
    "implemented_deterministic_simulation_verification_attestation_persistent_write_disabled"
)

AUTHORIZED_CAPABILITIES: tuple[str, ...] = (
    "tool_manifest_contracts_approved",
    "tool_capability_registry_approved",
    "tool_operation_classification_approved",
    "tool_risk_classification_approved",
    "tool_input_schema_contract_approved",
    "tool_output_schema_contract_approved",
    "tool_permission_envelope_approved",
    "tool_intent_contract_approved",
    "explicit_case_binding_approved",
    "explicit_claim_binding_approved",
    "explicit_epistemic_assessment_binding_approved",
    "explicit_domain_mesh_synthesis_binding_approved",
    "deterministic_tool_candidate_enumeration_approved",
    "deterministic_tool_selection_approved",
    "deterministic_tool_plan_approved",
    "bounded_tool_step_plan_approved",
    "tool_precondition_contract_approved",
    "tool_postcondition_contract_approved",
    "tool_expected_effect_contract_approved",
    "tool_forbidden_effect_contract_approved",
    "tool_idempotency_contract_approved",
    "tool_dry_run_simulation_approved",
    "synthetic_tool_adapter_approved",
    "local_fixture_tool_adapter_approved",
    "deterministic_output_canonicalization_approved",
    "output_artifact_fingerprinting_approved",
    "verification_rule_registry_approved",
    "independent_verifier_profile_approved",
    "dual_verification_policy_approved",
    "verification_finding_contract_approved",
    "verification_abstention_approved",
    "tool_attestation_chain_approved",
    "tool_result_provenance_approved",
    "tool_effect_comparison_approved",
    "rollback_plan_validation_approved",
    "compensation_plan_validation_approved",
    "operator_review_required_approved",
    "in_memory_tool_verification_session_approved",
    "synthetic_tool_fixture_replay_approved",
    "deterministic_tool_replay_approved",
    "bounded_tool_verification_queries_approved",
    "tool_verification_integrity_audit_approved",
    "redacted_tool_verification_diagnostics_approved",
    "tool_verification_incident_record_approved",
    "tool_verification_operator_review_item_approved",
    "resource_budget_enforcement_approved",
    "documentation_and_static_evidence_approved",
    "no_actual_tool_execution_enforcement_approved",
    "no_shell_execution_enforcement_approved",
    "no_subprocess_execution_enforcement_approved",
    "no_network_fetch_enforcement_approved",
    "no_dns_resolution_enforcement_approved",
    "no_browser_automation_enforcement_approved",
    "no_connector_call_enforcement_approved",
    "no_model_provider_call_enforcement_approved",
    "no_filesystem_mutation_enforcement_approved",
    "no_source_mutation_enforcement_approved",
    "no_git_mutation_enforcement_approved",
    "no_pr_creation_enforcement_approved",
    "no_approval_creation_enforcement_approved",
    "no_deployment_enforcement_approved",
    "no_autonomous_action_enforcement_approved",
    "no_high_stakes_action_enforcement_approved",
    "no_knowledge_promotion_enforcement_approved",
    "no_belief_mutation_enforcement_approved",
    "no_persistent_tool_state_enforcement_approved",
    "no_runtime_registration_enforcement_approved",
)

PROHIBITED_CAPABILITIES: tuple[str, ...] = (
    "actual_tool_execution_enabled",
    "shell_command_execution_enabled",
    "subprocess_execution_enabled",
    "filesystem_mutation_enabled",
    "network_access_enabled",
    "network_acquisition_enabled",
    "dns_resolution_enabled",
    "browser_automation_enabled",
    "connector_integration_enabled",
    "search_provider_integration_enabled",
    "model_provider_integration_enabled",
    "model_call_enabled",
    "credential_use_enabled",
    "cookie_use_enabled",
    "authorization_header_use_enabled",
    "source_body_parsing_enabled",
    "raw_source_content_storage_enabled",
    "tool_output_as_verified_fact_enabled",
    "tool_result_as_automatic_knowledge_enabled",
    "automatic_claim_acceptance_enabled",
    "automatic_claim_rejection_enabled",
    "absolute_truth_oracle_enabled",
    "autonomous_real_world_action_enabled",
    "high_stakes_action_enabled",
    "medical_action_execution_enabled",
    "legal_action_execution_enabled",
    "financial_action_execution_enabled",
    "safety_critical_action_execution_enabled",
    "source_patch_generation_enabled",
    "source_mutation_enabled",
    "worktree_creation_enabled",
    "git_mutation_enabled",
    "real_pull_request_creation_enabled",
    "approval_creation_enabled",
    "automatic_merge_enabled",
    "production_deployment_enabled",
    "knowledge_promotion_enabled",
    "verified_knowledge_creation_enabled",
    "automatic_memory_ingestion_enabled",
    "cognitive_belief_creation_enabled",
    "cognitive_belief_mutation_enabled",
    "persistent_tool_state_write_enabled",
    "tool_state_database_enabled",
    "external_database_integration_enabled",
    "background_tool_worker_enabled",
    "scheduled_tool_job_enabled",
    "kernel_registration_enabled",
    "application_startup_registration_enabled",
    "api_route_enabled",
    "installed_cli_command_enabled",
    "sdk_runtime_resource_enabled",
    "model_weight_training_enabled",
    "runtime_effect",
    "dependency_change_approved",
    "migration_approved",
    "github_workflow_change_approved",
    "v02_tag_created",
    "v02_release_created",
)

RESOURCE_LIMITS: dict[str, int] = {
    "maximum_tool_manifests": 500,
    "maximum_tool_candidates_per_plan": 100,
    "maximum_tool_steps_per_plan": 50,
    "maximum_manifest_bytes": 131072,
    "maximum_input_schema_bytes": 65536,
    "maximum_output_schema_bytes": 65536,
    "maximum_plan_bytes": 1048576,
    "maximum_preconditions_per_step": 50,
    "maximum_postconditions_per_step": 50,
    "maximum_expected_effects_per_step": 50,
    "maximum_forbidden_effects_per_step": 50,
    "maximum_verification_rules_per_step": 100,
    "maximum_verifiers_per_step": 8,
    "maximum_output_artifacts_per_step": 100,
    "maximum_evidence_references_per_step": 100,
    "maximum_attestations_per_session": 500,
    "maximum_rollback_steps_per_plan": 50,
    "maximum_compensation_steps_per_plan": 50,
    "maximum_simulated_sessions": 100,
    "maximum_query_results": 1000,
    "maximum_fixture_records": 5000,
    "maximum_fixture_bytes": 4194304,
    "maximum_concurrent_plans": 4,
    "maximum_concurrent_verifiers": 8,
    "maximum_persistent_tool_state_write_batch": 0,
    "maximum_actual_tool_executions": 0,
    "maximum_shell_commands": 0,
    "maximum_subprocess_executions": 0,
    "maximum_network_calls": 0,
    "maximum_dns_resolutions": 0,
    "maximum_browser_actions": 0,
    "maximum_connector_calls": 0,
    "maximum_search_provider_calls": 0,
    "maximum_model_provider_calls": 0,
    "maximum_filesystem_mutations": 0,
    "maximum_source_mutations": 0,
    "maximum_git_operations": 0,
    "maximum_runtime_created_pull_requests": 0,
    "maximum_approvals_created": 0,
    "maximum_autonomous_actions": 0,
    "maximum_high_stakes_actions": 0,
    "maximum_deployments": 0,
    "maximum_knowledge_promotions": 0,
    "maximum_belief_mutations": 0,
    "maximum_model_weight_changes": 0,
}

OPERATION_CLASSES: tuple[str, ...] = (
    "pure_compute",
    "deterministic_parser",
    "deterministic_validator",
    "local_fixture_read",
    "filesystem_read",
    "external_read",
    "external_write",
    "system_command",
    "browser",
    "connector",
    "model_provider",
    "source_write",
    "git_write",
    "deployment",
    "privileged",
)
RISK_CLASSES: tuple[str, ...] = ("minimal", "low", "moderate", "high", "critical")
VERIFICATION_STATUSES: tuple[str, ...] = (
    "planned",
    "simulation_passed",
    "simulation_failed",
    "verification_passed",
    "verification_failed",
    "inconclusive",
    "blocked",
    "abstained",
)
EFFECT_TYPES: tuple[str, ...] = (
    "read",
    "compute",
    "parse",
    "validate",
    "create",
    "update",
    "delete",
    "transmit",
    "execute",
    "approve",
    "merge",
    "deploy",
    "train",
)
VERIFIER_ROLES: tuple[str, ...] = (
    "schema_verifier",
    "policy_verifier",
    "effect_verifier",
    "provenance_verifier",
    "determinism_verifier",
    "safety_verifier",
    "rollback_verifier",
    "resource_verifier",
)

AION215_SOURCE_FILES: tuple[str, ...] = (
    "services/brain-api/src/aion_brain/contracts/knowledge_tool_verification.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/tool_verification_fabric.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/tool_manifests.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/tool_planning.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/tool_simulation.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/tool_verification.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/tool_attestation.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/tool_effects.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/tool_integrity.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/tool_evidence.py",
)
AION215_UPDATE_FILES: tuple[str, ...] = (
    "services/brain-api/src/aion_brain/knowledge_intelligence/__init__.py",
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
        "parent_evaluation_id": EVALUATION_ID,
        "parent_evaluation_decision": PASS_DECISION,
        "candidate_id": CANDIDATE_ID,
        "workstream": WORKSTREAM,
        "implementation_task": IMPLEMENTATION_TASK,
        "formal_closeout_task": FORMAL_CLOSEOUT_TASK,
        "authorization_scope": SCOPE,
        "authorization_active": True,
        "authorization_consumed": False,
        "authorization_expired": False,
        "authorization_reusable": False,
        "tool_verification_fabric_authorized": True,
        "synthetic": True,
        "read_only": True,
        "redacted": True,
        "runtime_effect": False,
    }
    for key, value in expected.items():
        if payload.get(key) != value:
            raise ValueError(f"tool verification authorization invalid {key}: {payload.get(key)!r}")
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
    implemented = payload.get("tool_verification_fabric_implemented")
    if implemented is True:
        if payload.get("tool_verification_fabric_state") != IMPLEMENTED_FABRIC_STATE:
            raise ValueError("tool verification fabric implemented state mismatch")
        if payload.get("tool_verification_fabric_runtime_enabled") is not False:
            raise ValueError("tool verification runtime must remain disabled")
    elif implemented is False:
        if payload.get("tool_verification_fabric_state") not in {
            None,
            "authorized_not_implemented",
        }:
            raise ValueError("tool verification authorized state mismatch")
    else:
        raise ValueError("tool verification implementation flag must be boolean")
    if payload.get("authorized_capabilities") != expected_authorized_capabilities():
        raise ValueError("authorized capability matrix mismatch")
    if payload.get("prohibited_capabilities") != expected_prohibited_capabilities():
        raise ValueError("prohibited capability matrix mismatch")
    if payload.get("resource_limits") != RESOURCE_LIMITS:
        raise ValueError("resource limits mismatch")
    if tuple(payload.get("operation_classes", ())) != OPERATION_CLASSES:
        raise ValueError("operation classes mismatch")
    if tuple(payload.get("risk_classes", ())) != RISK_CLASSES:
        raise ValueError("risk classes mismatch")
    if tuple(payload.get("verification_statuses", ())) != VERIFICATION_STATUSES:
        raise ValueError("verification statuses mismatch")
    if tuple(payload.get("effect_types", ())) != EFFECT_TYPES:
        raise ValueError("effect types mismatch")
    if tuple(payload.get("verifier_roles", ())) != VERIFIER_ROLES:
        raise ValueError("verifier roles mismatch")
    if tuple(payload.get("future_aion215_create_paths", ())) != AION215_SOURCE_FILES:
        raise ValueError("future AION-215 source-create scope mismatch")
    if tuple(payload.get("future_aion215_update_paths", ())) != AION215_UPDATE_FILES:
        raise ValueError("future AION-215 update scope mismatch")
    for key in PROHIBITED_CAPABILITIES:
        if payload.get(key, False) is not False:
            raise ValueError(f"prohibited capability enabled: {key}")


def validate_evaluation_report(root: Path) -> dict[str, Any]:
    report = load_json(
        root,
        "examples/knowledge-intelligence/domain-expert-mesh-operator-evaluation-report.json",
    )
    if report.get("evaluation_id") != EVALUATION_ID:
        raise ValueError("AION-DEME-001 report missing")
    if report.get("decision") != PASS_DECISION or report.get("evaluation_passed") is not True:
        raise ValueError("AION-DEME-001 exact PASS decision missing")
    if report.get("scenario_count") != 28 or len(report.get("scenario_results", [])) != 28:
        raise ValueError("AION-DEME-001 scenario count mismatch")
    if any(item.get("passed") is not True for item in report.get("scenario_results", [])):
        raise ValueError("AION-DEME-001 contains a failed scenario")
    if any(item.get("passed") is not True for item in report.get("hard_gate_results", [])):
        raise ValueError("AION-DEME-001 contains a failed hard gate")
    closeout = report.get("authorization_closeout", {})
    if closeout.get("authorization_transaction_id") != PARENT_AUTHORIZATION_ID:
        raise ValueError("AION-212-KI-0005 closeout missing from report")
    if closeout.get("authorization_active") is not False:
        raise ValueError("AION-212-KI-0005 must be inactive in report")
    next_auth = report.get("conditional_next_authorization", {})
    if next_auth.get("authorization_transaction_id") != AUTHORIZATION_ID:
        raise ValueError("AION-214-KI-0006 missing from report")
    for key, value in report.get("repository_integrity", {}).items():
        if key == "repository_unchanged":
            if value is not True:
                raise ValueError("repository_unchanged must be true")
        elif isinstance(value, int) and not isinstance(value, bool) and value != 0:
            raise ValueError(f"repository integrity effect must remain zero: {key}")
    return report


def validate_authorization_files(root: Path) -> None:
    report = validate_evaluation_report(root)
    example = load_json(root, "examples/knowledge-intelligence/tool-verification-authorization.json")
    validate_authorization_payload(example)
    if example.get("parent_evaluation_decision") != report["decision"]:
        raise ValueError("tool authorization parent decision mismatch")

    auth = load_json(root, "docs/knowledge-intelligence/authorization-ledger.json")
    program = load_json(root, "docs/knowledge-intelligence/program-ledger.json")
    for label, payload in (("authorization", auth), ("program", program)):
        if payload.get("program_state") not in {
            AUTHORIZED_PROGRAM_STATE,
            IMPLEMENTED_PROGRAM_STATE,
            VERIFIED_KNOWLEDGE_AUTHORIZED_PROGRAM_STATE,
            VERIFIED_KNOWLEDGE_IMPLEMENTED_PROGRAM_STATE,
        }:
            raise ValueError(f"{label} ledger program state mismatch")
        if payload.get("active_knowledge_implementation_authorization_count") != 1:
            raise ValueError(f"{label} active authorization count mismatch")
        if payload.get("program_state") in {
            VERIFIED_KNOWLEDGE_AUTHORIZED_PROGRAM_STATE,
            VERIFIED_KNOWLEDGE_IMPLEMENTED_PROGRAM_STATE,
        }:
            if payload.get("active_knowledge_implementation_authorization") != "AION-216-KI-0007":
                raise ValueError(f"{label} active verified-knowledge authorization mismatch")
            if payload.get("active_knowledge_implementation_task") != "AION-217":
                raise ValueError(f"{label} active verified-knowledge task mismatch")
            if payload.get("formal_closeout_task") != "AION-218":
                raise ValueError(f"{label} verified-knowledge closeout task mismatch")
        else:
            if payload.get("active_knowledge_implementation_authorization") != AUTHORIZATION_ID:
                raise ValueError(f"{label} active authorization mismatch")
            if payload.get("active_knowledge_implementation_task") != IMPLEMENTATION_TASK:
                raise ValueError(f"{label} active task mismatch")
            if payload.get("formal_closeout_task") != FORMAL_CLOSEOUT_TASK:
                raise ValueError(f"{label} closeout task mismatch")
        if payload.get("domain_expert_mesh_operator_evaluation_decision") != PASS_DECISION:
            raise ValueError(f"{label} evaluation decision mismatch")
        if payload.get("tool_verification_fabric_authorized") is not True:
            raise ValueError(f"{label} tool verification authorization missing")
        if payload.get("program_state") in {
            IMPLEMENTED_PROGRAM_STATE,
            VERIFIED_KNOWLEDGE_AUTHORIZED_PROGRAM_STATE,
            VERIFIED_KNOWLEDGE_IMPLEMENTED_PROGRAM_STATE,
        }:
            if payload.get("tool_verification_fabric_implemented") is not True:
                raise ValueError(f"{label} tool verification implementation missing")
            if payload.get("tool_verification_fabric_state") != IMPLEMENTED_FABRIC_STATE:
                raise ValueError(f"{label} tool verification state mismatch")
            if payload.get("tool_verification_fabric_runtime_enabled") is not False:
                raise ValueError(f"{label} tool verification runtime must remain disabled")
        elif payload.get("tool_verification_fabric_implemented") is not False:
            raise ValueError(f"{label} tool verification implementation must be false")
        for key in PROHIBITED_CAPABILITIES:
            if payload.get(key, False) is not False:
                raise ValueError(f"{label} prohibited capability enabled: {key}")

    active = [record for record in auth["records"] if record.get("authorization_active") is True]
    if len(active) != 1:
        raise ValueError("exactly one Knowledge Intelligence authorization must be active")
    if active[0].get("authorization_transaction_id") == AUTHORIZATION_ID:
        validate_authorization_payload(active[0])
    elif (
        active[0].get("authorization_transaction_id") != "AION-216-KI-0007"
        or auth.get("program_state")
        not in {
            VERIFIED_KNOWLEDGE_AUTHORIZED_PROGRAM_STATE,
            VERIFIED_KNOWLEDGE_IMPLEMENTED_PROGRAM_STATE,
        }
    ):
        raise ValueError("unexpected active Knowledge Intelligence authorization")

    closed = [
        record
        for record in auth["records"]
        if record.get("authorization_transaction_id") == PARENT_AUTHORIZATION_ID
    ]
    if len(closed) != 1:
        raise ValueError("AION-212-KI-0005 record missing")
    parent = closed[0]
    for key, expected in {
        "authorization_active": False,
        "authorization_consumed": True,
        "authorization_expired": True,
        "authorization_reusable": False,
        "authorization_closed_by_task": "AION-214",
        "authorization_consumed_by_task": "AION-213",
        "domain_expert_mesh_operator_evaluation_id": EVALUATION_ID,
        "domain_expert_mesh_operator_evaluation_decision": PASS_DECISION,
        "evaluation_used_as_approval": False,
        "evaluation_reusable": False,
    }.items():
        if parent.get(key) != expected:
            raise ValueError(f"AION-212 closeout mismatch for {key}: {parent.get(key)!r}")
    if parent.get("authorization_consumed_by_prs") != [127]:
        raise ValueError("AION-212 closeout PR evidence mismatch")

    tool_records = [
        record
        for record in auth["records"]
        if record.get("authorization_transaction_id") == AUTHORIZATION_ID
    ]
    if len(tool_records) != 1:
        raise ValueError("AION-214-KI-0006 record missing")
    if auth.get("program_state") in {
        VERIFIED_KNOWLEDGE_AUTHORIZED_PROGRAM_STATE,
        VERIFIED_KNOWLEDGE_IMPLEMENTED_PROGRAM_STATE,
    }:
        tool_record = tool_records[0]
        for key, expected in {
            "authorization_active": False,
            "authorization_consumed": True,
            "authorization_expired": True,
            "authorization_reusable": False,
            "authorization_closed_by_task": "AION-216",
            "authorization_consumed_by_task": "AION-215",
        }.items():
            if tool_record.get(key) != expected:
                raise ValueError(f"AION-214 closeout mismatch for {key}: {tool_record.get(key)!r}")
        if tool_record.get("authorization_consumed_by_prs") != [129]:
            raise ValueError("AION-214 closeout PR evidence mismatch")
        if tool_record.get("authorization_consumed_by_feature_commits") != [
            "c9a35cc853ee1587cb9e149a020e2f767ca80881"
        ]:
            raise ValueError("AION-214 closeout feature commit evidence mismatch")
        if tool_record.get("authorization_consumed_by_merge_commits") != [
            "2988b8f389f7ee3a141f74e351432f4ea79c6eae"
        ]:
            raise ValueError("AION-214 closeout merge commit evidence mismatch")
    validate_repository_state(root)


def validate_repository_state(root: Path) -> None:
    program = load_json(root, "docs/knowledge-intelligence/program-ledger.json")
    implemented = program.get("program_state") in {
        IMPLEMENTED_PROGRAM_STATE,
        VERIFIED_KNOWLEDGE_AUTHORIZED_PROGRAM_STATE,
        VERIFIED_KNOWLEDGE_IMPLEMENTED_PROGRAM_STATE,
    }
    for relative in AION215_SOURCE_FILES:
        exists = (root / relative).exists()
        if implemented and not exists:
            raise ValueError(f"AION-215 source missing after implementation: {relative}")
        if not implemented and exists:
            raise ValueError(f"AION-215 source is not authorized on AION-214: {relative}")
    for evidence_root in ("docs", "examples", "operator-console-static", "scripts"):
        for relative in (root / evidence_root).rglob("*"):
            if not relative.is_file():
                continue
            if relative.suffix.lower() in {".db", ".sqlite", ".sqlite3", ".jsonl", ".tool-state"}:
                raise ValueError(f"tool persistence file detected: {relative.relative_to(root)}")


def validate_runtime_hold(root: Path) -> None:
    validate_authorization_files(root)
    runtime = load_json(root, "examples/knowledge-intelligence/tool-verification-runtime-hold.json")
    for key in (
        "actual_tool_execution_enabled",
        "shell_command_execution_enabled",
        "subprocess_execution_enabled",
        "network_access_enabled",
        "dns_resolution_enabled",
        "browser_automation_enabled",
        "connector_integration_enabled",
        "model_provider_integration_enabled",
        "persistent_tool_state_write_enabled",
        "tool_state_database_enabled",
        "autonomous_real_world_action_enabled",
        "knowledge_promotion_enabled",
        "cognitive_belief_mutation_enabled",
        "runtime_effect",
    ):
        if runtime.get(key) is not False:
            raise ValueError(f"runtime hold flag must remain false: {key}")
    if runtime.get("tool_verification_fabric_authorized") is not True:
        raise ValueError("tool verification authorization must be recorded")
    if runtime.get("tool_verification_fabric_implemented") is not True:
        raise ValueError("tool verification implementation must be recorded")
    if runtime.get("tool_verification_fabric_state") != IMPLEMENTED_FABRIC_STATE:
        raise ValueError("tool verification implementation state mismatch")
    if runtime.get("tool_verification_fabric_runtime_enabled") is not False:
        raise ValueError("tool verification runtime must remain disabled")
