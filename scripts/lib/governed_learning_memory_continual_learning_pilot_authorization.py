"""AION-227 controlled local continual-learning pilot authorization checks."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from scripts.lib.governed_learning_memory_engagement_application_operator_evaluation import (
    AION226_FEATURE_COMMIT,
    AION226_MERGE_COMMIT,
    AION226_PR,
    AION227_CORRECTIVE_FEATURE_COMMITS,
    AION227_CORRECTIVE_MERGE_COMMITS,
    AION227_CORRECTIVE_PRS,
    EVALUATION_ID,
    PASS_DECISION,
    validate_evaluation_report_file,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PROGRAM_ID = "AION-GOVERNED-LEARNING-MEMORY-001"
CURRENT_AUTHORIZATION_ID = "AION-225-GLM-0003"
NEXT_AUTHORIZATION_ID = "AION-227-GLM-0004"
IMPLEMENTATION_TASK = "AION-228"
FORMAL_CLOSEOUT_TASK = "AION-229"
AION226_COMPLETION_TIMESTAMP = "2026-07-29T11:06:17Z"
AION227_PARENT_MAIN_COMMIT = "8156661dae57b6e141f094ee9e6650a710765635"
PROGRAM_STATE = (
    "governed_learning_memory_controlled_local_continual_learning_pilot_"
    "implemented_completed_pending_final_closeout"
)
ENGAGEMENT_APPLICATION_STATE = (
    "implemented_deterministic_operator_approved_non_factual_in_memory_shadow_only"
)
AUTHORIZATION_SCOPE = (
    "operator-invoked-bounded-engagement-intake-explicit-public-https-research-"
    "verified-knowledge-promotion-temporary-local-persistence-shadow-adaptation-"
    "cross-cycle-outcome-evaluation-rollback-cleanup-audit-pilot-core"
)
PARENT_IMPLEMENTATION_PRS = [AION226_PR, *AION227_CORRECTIVE_PRS]
PARENT_FEATURE_COMMITS = [AION226_FEATURE_COMMIT, *AION227_CORRECTIVE_FEATURE_COMMITS]
PARENT_MERGE_COMMITS = [AION226_MERGE_COMMIT, *AION227_CORRECTIVE_MERGE_COMMITS]

FUTURE_AION228_SOURCE_SCOPE: tuple[str, ...] = (
    "services/brain-api/src/aion_brain/contracts/governed_continual_learning.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/continual_learning_authorization.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/continual_learning_cycle.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/continual_learning_intake.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/continual_learning_research.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/continual_learning_knowledge_pipeline.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/continual_learning_persistence.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/continual_learning_shadow.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/continual_learning_outcome.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/continual_learning_integrity.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/continual_learning_evidence.py",
)
AION228_OPTIONAL_EXISTING_SCOPE: tuple[str, ...] = (
    "services/brain-api/src/aion_brain/governed_learning_memory/__init__.py",
)
AION228_UNINSTALLED_OPERATOR_RUNNER = (
    "scripts/governed-learning-memory-controlled-local-continual-learning-run.py"
)

AUTHORIZED_CAPABILITIES: tuple[str, ...] = (
    "continual_learning_cycle_contract_approved",
    "explicit_cycle_authorization_envelope_approved",
    "operator_invoked_cycle_approved",
    "bounded_multi_cycle_session_approved",
    "deterministic_cycle_state_machine_approved",
    "immutable_cycle_stage_receipts_approved",
    "cycle_idempotency_approved",
    "explicit_cycle_checkpoint_approved",
    "cycle_resume_from_explicit_checkpoint_approved",
    "engagement_signal_intake_approved",
    "engagement_candidate_intake_approved",
    "engagement_non_factual_validation_approved",
    "read_only_local_knowledge_context_approved",
    "research_gap_selection_approved",
    "explicit_research_plan_approved",
    "explicit_url_allowlist_approved",
    "explicit_domain_allowlist_approved",
    "operator_invoked_bounded_public_https_approved",
    "existing_public_dns_transport_composition_approved",
    "existing_public_https_transport_composition_approved",
    "existing_source_provenance_pipeline_approved",
    "existing_temporal_claim_graph_pipeline_approved",
    "existing_epistemic_assessment_pipeline_approved",
    "existing_domain_expert_mesh_pipeline_approved",
    "existing_tool_verification_pipeline_approved",
    "verified_knowledge_candidate_pipeline_approved",
    "promotion_transaction_planning_approved",
    "existing_promotion_approval_validation_approved",
    "temporary_isolated_local_store_approved",
    "dual_approved_temporary_local_persistence_approved",
    "cross_cycle_local_knowledge_read_approved",
    "engagement_shadow_application_composition_approved",
    "engagement_overlay_approval_validation_approved",
    "baseline_counterfactual_comparison_approved",
    "cycle_outcome_evaluation_approved",
    "cycle_abstention_approved",
    "cycle_rollback_approved",
    "cycle_cleanup_approved",
    "cycle_integrity_audit_approved",
    "redacted_cycle_evidence_approved",
    "cycle_operator_review_item_approved",
    "controlled_live_pilot_approved",
    "deterministic_fixture_replay_approved",
    "documentation_and_static_evidence_approved",
)
PROHIBITED_CAPABILITIES: tuple[str, ...] = (
    "background_continual_learning_enabled",
    "scheduled_continual_learning_enabled",
    "unbounded_autonomous_loop_enabled",
    "automatic_cycle_continuation_enabled",
    "automatic_source_discovery_enabled",
    "web_crawler_enabled",
    "search_provider_integration_enabled",
    "connector_integration_enabled",
    "model_provider_integration_enabled",
    "general_network_access_enabled",
    "unrestricted_public_network_access_enabled",
    "automatic_candidate_approval_enabled",
    "automatic_knowledge_promotion_enabled",
    "automatic_local_persistence_enabled",
    "single_actor_persistence_enabled",
    "retained_pilot_store_enabled",
    "production_persistent_knowledge_write_enabled",
    "production_memory_repository_write_enabled",
    "production_engagement_application_enabled",
    "persistent_engagement_overlay_write_enabled",
    "production_policy_mutation_enabled",
    "production_retrieval_policy_mutation_enabled",
    "production_source_selection_mutation_enabled",
    "production_domain_routing_mutation_enabled",
    "production_verification_rule_mutation_enabled",
    "production_tool_manifest_mutation_enabled",
    "production_response_policy_mutation_enabled",
    "engagement_signal_as_fact_enabled",
    "engagement_confidence_effect_enabled",
    "engagement_knowledge_effect_enabled",
    "engagement_source_independence_effect_enabled",
    "cognitive_memory_write_enabled",
    "actual_belief_creation_enabled",
    "actual_belief_mutation_enabled",
    "self_rewrite_enabled",
    "runtime_source_rewrite_enabled",
    "model_weight_training_enabled",
    "source_mutation_enabled",
    "git_mutation_enabled",
    "real_pull_request_creation_enabled",
    "runtime_approval_creation_enabled",
    "automatic_merge_enabled",
    "production_deployment_enabled",
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
)
RESOURCE_LIMITS: dict[str, int] = {
    "maximum_live_pilot_sessions": 1,
    "maximum_cycles_per_live_pilot": 3,
    "maximum_synthetic_test_sessions": 20,
    "maximum_engagement_signals_per_cycle": 100,
    "maximum_engagement_candidates_per_cycle": 25,
    "maximum_research_gap_candidates_per_cycle": 10,
    "maximum_research_plans_per_cycle": 3,
    "maximum_queries_per_research_plan": 10,
    "maximum_explicit_source_urls_per_cycle": 20,
    "maximum_domains_per_cycle": 10,
    "maximum_source_candidates_per_cycle": 25,
    "maximum_dns_resolutions_per_cycle": 100,
    "maximum_public_https_requests_per_cycle": 50,
    "maximum_source_fetches_per_cycle": 25,
    "maximum_redirects_per_fetch": 3,
    "maximum_concurrency": 4,
    "maximum_timeout_seconds_per_request": 20,
    "maximum_wall_clock_seconds_per_cycle": 1800,
    "maximum_total_live_pilot_seconds": 7200,
    "maximum_response_bytes_per_source": 5242880,
    "maximum_transfer_bytes_per_cycle": 52428800,
    "maximum_source_snapshots_per_cycle": 50,
    "maximum_claim_specs_per_cycle": 50,
    "maximum_verified_candidates_per_cycle": 25,
    "maximum_promotion_plans_per_cycle": 25,
    "maximum_promotion_approval_records_per_transaction": 4,
    "maximum_temporary_local_persistence_transactions_per_cycle": 5,
    "maximum_knowledge_versions_written_per_cycle": 25,
    "maximum_projection_records_written_per_cycle": 100,
    "maximum_engagement_shadow_applications_per_cycle": 25,
    "maximum_counterfactual_cases_per_cycle": 250,
    "maximum_operator_review_items_per_cycle": 100,
    "maximum_cycle_checkpoints": 10,
    "maximum_cycle_evidence_bytes": 10485760,
    "maximum_retained_database_files": 0,
    "maximum_retained_wal_files": 0,
    "maximum_retained_shm_files": 0,
    "maximum_retained_backup_files": 0,
    "maximum_retained_manifest_files": 0,
    "maximum_operator_local_store_transactions": 0,
    "maximum_background_cycles": 0,
    "maximum_scheduled_cycles": 0,
    "maximum_automatic_cycle_continuations": 0,
    "maximum_automatic_source_discoveries": 0,
    "maximum_crawler_requests": 0,
    "maximum_search_provider_calls": 0,
    "maximum_connector_calls": 0,
    "maximum_model_provider_calls": 0,
    "maximum_automatic_candidate_approvals": 0,
    "maximum_automatic_knowledge_promotions": 0,
    "maximum_automatic_persistence_transactions": 0,
    "maximum_production_memory_writes": 0,
    "maximum_production_policy_mutations": 0,
    "maximum_cognitive_memory_writes": 0,
    "maximum_actual_belief_creations": 0,
    "maximum_actual_belief_mutations": 0,
    "maximum_persistent_engagement_overlay_writes": 0,
    "maximum_source_mutations": 0,
    "maximum_git_operations": 0,
    "maximum_runtime_created_pull_requests": 0,
    "maximum_runtime_created_approvals": 0,
    "maximum_deployments": 0,
    "maximum_model_weight_changes": 0,
}
CYCLE_STATES: tuple[str, ...] = (
    "drafted",
    "authorized",
    "engagement_intake_validated",
    "research_gap_selected",
    "research_planned",
    "research_acquired",
    "evidence_assessed",
    "verified_candidate_reviewed",
    "promotion_planned",
    "persistence_approval_validated",
    "temporarily_persisted",
    "shadow_application_planned",
    "shadow_application_evaluated",
    "cycle_completed",
    "abstained",
    "rolled_back",
    "failed",
)


class ContinualLearningAuthorizationError(ValueError):
    """Raised when AION-227 authorization evidence is inconsistent."""


def load_json(relative: str, root: Path = REPO_ROOT) -> dict[str, Any]:
    return json.loads((root / relative).read_text(encoding="utf-8"))


def fail(message: str) -> None:
    raise ContinualLearningAuthorizationError(message)


def record_by_id(records: list[Mapping[str, Any]], authorization_id: str) -> Mapping[str, Any]:
    for record in records:
        if record.get("authorization_transaction_id") == authorization_id:
            return record
    fail(f"authorization record missing: {authorization_id}")


def require_true(payload: Mapping[str, Any], keys: tuple[str, ...], label: str) -> None:
    for key in keys:
        if payload.get(key) is not True:
            fail(f"{label} expected true: {key}")


def require_false(payload: Mapping[str, Any], keys: tuple[str, ...], label: str) -> None:
    for key in keys:
        if payload.get(key) is not False:
            fail(f"{label} expected false: {key}")


def validate_evaluation_report(root: Path = REPO_ROOT) -> dict[str, Any]:
    report = validate_evaluation_report_file(
        root / "examples/governed-learning-memory/engagement-application-operator-evaluation-report.json"
    )
    if report["decision"] != PASS_DECISION or report["evaluation_passed"] is not True:
        fail("AION-227 evaluation must be exact PASS")
    if report["scenario_count"] != 28:
        fail("AION-227 scenario count mismatch")
    if report["validation_results"].get("corrective_prs") != list(AION227_CORRECTIVE_PRS):
        fail("AION-227 corrective PR reconciliation mismatch")
    if report["implementation_prs"] != PARENT_IMPLEMENTATION_PRS:
        fail("AION-227 implementation PR reconciliation mismatch")
    return report


def validate_authorization_record(record: Mapping[str, Any]) -> None:
    expected = {
        "program_id": PROGRAM_ID,
        "authorization_transaction_id": NEXT_AUTHORIZATION_ID,
        "approval_record_id": NEXT_AUTHORIZATION_ID,
        "parent_authorization_transaction_id": CURRENT_AUTHORIZATION_ID,
        "parent_evaluation_id": EVALUATION_ID,
        "parent_evaluation_decision": PASS_DECISION,
        "parent_closeout_task": "AION-227",
        "parent_implementation_task": "AION-226",
        "parent_implementation_prs": PARENT_IMPLEMENTATION_PRS,
        "parent_implementation_feature_commits": PARENT_FEATURE_COMMITS,
        "parent_implementation_merge_commits": PARENT_MERGE_COMMITS,
        "parent_main_commit": AION227_PARENT_MAIN_COMMIT,
        "candidate_id": "operator-approved-controlled-local-continual-learning-pilot-core",
        "workstream": "governed-learning-memory-controlled-local-continual-learning",
        "implementation_task": IMPLEMENTATION_TASK,
        "formal_closeout_task": FORMAL_CLOSEOUT_TASK,
        "authorization_scope": AUTHORIZATION_SCOPE,
    }
    for key, value in expected.items():
        if record.get(key) != value:
            fail(f"AION-227 authorization {key} mismatch")
    require_true(
        record,
        (
            "authorization_transaction_approved",
            "explicit_approval_record_approval",
            "implementation_authorization_approved",
            "implementation_go_status",
            "authorization_active",
            "sole_active_glm_authorization",
            "controlled_local_continual_learning_pilot_implemented",
            "operator_invoked_continual_learning_pilot_available",
        ),
        "AION-227 authorization",
    )
    require_false(
        record,
        (
            "implementation_no_go_status",
            "authorization_consumed",
            "authorization_expired",
            "authorization_reusable",
            "runtime_effect",
        ),
        "AION-227 authorization",
    )
    if record.get("authorized_capabilities") != {key: True for key in AUTHORIZED_CAPABILITIES}:
        fail("authorized AION-228 capabilities mismatch")
    if record.get("prohibited_capabilities") != {key: False for key in PROHIBITED_CAPABILITIES}:
        fail("prohibited AION-228 capabilities mismatch")
    if record.get("resource_limits") != RESOURCE_LIMITS:
        fail("AION-228 resource limit mismatch")
    if tuple(record.get("future_authorized_source_scope", ())) != (
        *FUTURE_AION228_SOURCE_SCOPE,
        *AION228_OPTIONAL_EXISTING_SCOPE,
    ):
        fail("AION-228 future source scope mismatch")


def validate_aion225_closeout(record: Mapping[str, Any]) -> None:
    expected = {
        "authorization_transaction_id": CURRENT_AUTHORIZATION_ID,
        "approval_record_id": CURRENT_AUTHORIZATION_ID,
        "authorization_active": False,
        "authorization_consumed": True,
        "authorization_consumed_by_task": "AION-226",
        "authorization_consumed_by_prs": PARENT_IMPLEMENTATION_PRS,
        "authorization_consumed_by_feature_commits": PARENT_FEATURE_COMMITS,
        "authorization_consumed_by_merge_commits": PARENT_MERGE_COMMITS,
        "authorization_expired": True,
        "authorization_reusable": False,
        "authorization_closed_by_task": "AION-227",
        "engagement_application_operator_evaluation_id": EVALUATION_ID,
        "engagement_application_operator_evaluation_decision": PASS_DECISION,
        "evaluation_used_as_continual_learning_cycle_approval": False,
        "evaluation_reusable": False,
        "evaluation_created_network_session": False,
        "evaluation_created_local_store": False,
        "evaluation_applied_overlay": False,
        "evaluation_created_production_effect": False,
    }
    for key, value in expected.items():
        if record.get(key) != value:
            fail(f"AION-225 closeout {key} mismatch")


def validate_ledgers(root: Path = REPO_ROOT) -> tuple[dict[str, Any], dict[str, Any]]:
    program = load_json("docs/governed-learning-memory/program-ledger.json", root)
    auth = load_json("docs/governed-learning-memory/authorization-ledger.json", root)
    for label, payload in (("program", program), ("authorization", auth)):
        if payload.get("program_id") != PROGRAM_ID:
            fail(f"{label} program id mismatch")
        expected = {
            "program_state": PROGRAM_STATE,
            "engagement_application_operator_evaluation_passed": True,
            "engagement_application_operator_evaluation_id": EVALUATION_ID,
            "engagement_application_operator_evaluation_decision": PASS_DECISION,
            "active_glm_implementation_authorization_count": 1,
            "active_glm_implementation_authorization": NEXT_AUTHORIZATION_ID,
            "active_glm_implementation_task": IMPLEMENTATION_TASK,
            "formal_closeout_task": FORMAL_CLOSEOUT_TASK,
            "new_glm_implementation_authorization_created": True,
            "controlled_local_continual_learning_pilot_authorized": True,
            "controlled_local_continual_learning_pilot_implemented": True,
            "operator_invoked_continual_learning_pilot_authorized": True,
            "operator_invoked_continual_learning_pilot_available": True,
            "deterministic_continual_learning_simulation_available": True,
            "controlled_live_pilot_completed": True,
            "controlled_live_pilot_cycle_count": 3,
            "operator_invoked_bounded_public_https_cycle_authorized": True,
            "temporary_isolated_local_store_cycle_authorized": True,
            "engagement_shadow_cycle_authorized": True,
            "engagement_learning_application_implemented": True,
            "engagement_learning_application_state": ENGAGEMENT_APPLICATION_STATE,
            "production_exposure": False,
            "v02_release_ready": False,
            "v02_tag_created": False,
            "v02_release_created": False,
        }
        for key, value in expected.items():
            if payload.get(key) != value:
                fail(f"{label} {key} mismatch")
        require_false(payload, PROHIBITED_CAPABILITIES, label)
        if payload.get("authorized_capabilities") != {key: True for key in AUTHORIZED_CAPABILITIES}:
            fail(f"{label} authorized capability projection mismatch")
        if payload.get("resource_limits") != RESOURCE_LIMITS:
            fail(f"{label} resource limit projection mismatch")
        delivery = payload.get("aion_226_delivery")
        if not isinstance(delivery, Mapping):
            fail(f"{label} AION-226 delivery missing")
        if (
            delivery.get("pull_requests") != PARENT_IMPLEMENTATION_PRS
            or delivery.get("feature_commits") != PARENT_FEATURE_COMMITS
            or delivery.get("merge_commits") != PARENT_MERGE_COMMITS
            or delivery.get("ci_result") != "pass"
            or delivery.get("completion_timestamp") != AION226_COMPLETION_TIMESTAMP
            or delivery.get("authorization_state") != "consumed_by_AION-226_closed_by_AION-227"
            or delivery.get("runtime_state")
            != "engagement_learning_application_implemented_in_memory_shadow_only"
            or delivery.get("evaluation_id") != EVALUATION_ID
            or delivery.get("evaluation_decision") != PASS_DECISION
        ):
            fail(f"{label} AION-226 delivery reconciliation mismatch")
        aion227_delivery = payload.get("aion_227_delivery")
        if not isinstance(aion227_delivery, Mapping):
            fail(f"{label} AION-227 delivery missing")
        if (
            aion227_delivery.get("pull_requests") != [144]
            or aion227_delivery.get("feature_commits")
            != [
                "b29e7f80ab82b03cb5363ffc9daf629159f804ee",
                "36279d736fbca06e041477c17d7e825c9b0a33b0",
            ]
            or aion227_delivery.get("merge_commits")
            != ["7a505f1afa30b3732d1e1955ed6983b14ba4b5b8"]
            or aion227_delivery.get("ci_result") != "pass"
            or aion227_delivery.get("completion_timestamp") != "2026-07-29T17:20:10Z"
            or aion227_delivery.get("authorization_transaction") != NEXT_AUTHORIZATION_ID
            or aion227_delivery.get("next_task") != IMPLEMENTATION_TASK
        ):
            fail(f"{label} AION-227 delivery reconciliation mismatch")
        aion228_delivery = payload.get("aion_228_delivery")
        if not isinstance(aion228_delivery, Mapping):
            fail(f"{label} AION-228 delivery missing")
        if (
            aion228_delivery.get("authorization_transaction") != NEXT_AUTHORIZATION_ID
            or aion228_delivery.get("next_task") != FORMAL_CLOSEOUT_TASK
            or aion228_delivery.get("ci_result") != "pending"
            or aion228_delivery.get("runtime_state")
            != "controlled_local_continual_learning_pilot_implemented_completed_pending_final_closeout"
        ):
            fail(f"{label} AION-228 delivery reconciliation mismatch")
    if auth.get("active_authorizations") != [NEXT_AUTHORIZATION_ID]:
        fail("authorization ledger active authorizations mismatch")
    records = auth.get("records")
    if not isinstance(records, list):
        fail("authorization records missing")
    validate_aion225_closeout(record_by_id(records, CURRENT_AUTHORIZATION_ID))
    validate_authorization_record(record_by_id(records, NEXT_AUTHORIZATION_ID))
    for closeout in (program, auth):
        closeouts = closeout.get("authorization_closeout_records")
        if not isinstance(closeouts, list):
            fail("authorization closeout records missing")
        validate_aion225_closeout(record_by_id(closeouts, CURRENT_AUTHORIZATION_ID))
    return program, auth


def validate_examples(root: Path = REPO_ROOT) -> None:
    validate_authorization_record(
        load_json("examples/governed-learning-memory/continual-learning-pilot-authorization.json", root)
    )
    runtime_hold = load_json(
        "examples/governed-learning-memory/continual-learning-runtime-hold.json", root
    )
    require_true(
        runtime_hold,
        (
            "controlled_local_continual_learning_pilot_authorized",
            "controlled_local_continual_learning_pilot_implemented",
            "operator_invoked_continual_learning_pilot_available",
            "deterministic_continual_learning_simulation_available",
            "controlled_live_pilot_completed",
            "no_active_overlay",
            "pilot_operator_invocation_required",
        ),
        "runtime hold",
    )
    require_false(
        runtime_hold,
        (
            "background_continual_learning_enabled",
            "scheduled_continual_learning_enabled",
            "automatic_cycle_continuation_enabled",
            "automatic_knowledge_promotion_enabled",
            "production_exposure",
        ),
        "runtime hold",
    )
    if runtime_hold.get("controlled_live_pilot_cycle_count") != 3:
        fail("runtime hold live pilot cycle count mismatch")


def validate_aion228_source_scope(root: Path = REPO_ROOT) -> None:
    for relative in FUTURE_AION228_SOURCE_SCOPE:
        if not (root / relative).exists():
            fail(f"AION-228 source missing after implementation: {relative}")
    if not (root / AION228_UNINSTALLED_OPERATOR_RUNNER).exists():
        fail("AION-228 uninstalled runner missing after implementation")


def validate_continual_learning_pilot_authorization(root: Path = REPO_ROOT) -> None:
    validate_evaluation_report(root)
    validate_ledgers(root)
    validate_examples(root)
    validate_aion228_source_scope(root)


def main() -> int:
    try:
        validate_continual_learning_pilot_authorization()
    except ContinualLearningAuthorizationError as exc:
        print(f"ERROR: {exc}")
        return 1
    print("governed learning memory continual learning pilot authorization validator PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
