from __future__ import annotations

import copy
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PROGRAM_ID = "AION-KNOWLEDGE-INTELLIGENCE-001"
CLAIM_GRAPH_AUTH_ID = "AION-208-KI-0003"
EPISTEMIC_AUTH_ID = "AION-210-KI-0004"
EVALUATION_ID = "AION-TCGE-001"
DECISION = (
    "TEMPORAL_CLAIM_EVIDENCE_GRAPH_OPERATOR_EVALUATION_PASS_RECOMMEND_"
    "EPISTEMIC_TRUTH_ENGINE_AUTHORIZATION"
)
SCOPE = (
    "deterministic-evidence-corroboration-contradiction-freshness-source-"
    "independence-confidence-assessment-core"
)
RESOURCE_LIMITS = {
    "maximum_claims_per_assessment_batch": 500,
    "maximum_evidence_bindings_per_claim": 100,
    "maximum_source_registry_references_per_claim": 50,
    "maximum_citation_references_per_claim": 50,
    "maximum_lineage_groups_per_claim": 20,
    "maximum_relation_edges_per_claim": 100,
    "maximum_reason_codes_per_assessment": 50,
    "maximum_operator_review_items": 500,
    "maximum_epistemic_assessments": 500,
    "maximum_confidence_calculations": 500,
    "maximum_benchmark_cases": 1000,
    "maximum_query_results": 1000,
    "maximum_fixture_records": 5000,
    "maximum_fixture_bytes": 4194304,
    "maximum_concurrent_assessments": 4,
    "maximum_persistent_assessment_write_batch": 0,
    "maximum_source_body_bytes": 0,
    "maximum_automatic_claim_extractions": 0,
    "maximum_absolute_truth_decisions": 0,
    "maximum_automatic_claim_acceptances": 0,
    "maximum_automatic_claim_rejections": 0,
    "maximum_contradiction_resolutions": 0,
    "maximum_knowledge_promotions": 0,
    "maximum_belief_mutations": 0,
    "maximum_network_calls": 0,
    "maximum_search_provider_calls": 0,
    "maximum_connector_calls": 0,
    "maximum_model_provider_calls": 0,
    "maximum_source_mutations": 0,
    "maximum_git_operations": 0,
    "maximum_runtime_created_pull_requests": 0,
    "maximum_approvals_created": 0,
    "maximum_deployments": 0,
    "maximum_model_weight_changes": 0,
}
AUTHORIZED_KEYS = set(
    [
        "epistemic_assessment_contracts_approved",
        "claim_assessment_status_approved",
        "evidence_sufficiency_evaluation_approved",
        "evidence_coverage_calculation_approved",
        "citation_coverage_calculation_approved",
        "provenance_completeness_calculation_approved",
        "source_independence_counting_approved",
        "independent_support_counting_approved",
        "independent_opposition_counting_approved",
        "duplicate_evidence_suppression_approved",
        "mirror_evidence_suppression_approved",
        "source_quality_metadata_evaluation_approved",
        "valid_time_applicability_evaluation_approved",
        "transaction_time_evaluation_approved",
        "temporal_freshness_evaluation_approved",
        "jurisdiction_applicability_evaluation_approved",
        "version_applicability_evaluation_approved",
        "correction_relation_evaluation_approved",
        "retraction_relation_evaluation_approved",
        "supersession_relation_evaluation_approved",
        "structural_conflict_evaluation_approved",
        "unresolved_contradiction_preservation_approved",
        "deterministic_epistemic_scorecard_approved",
        "bounded_numeric_confidence_approved",
        "confidence_band_approved",
        "confidence_cap_rules_approved",
        "explicit_abstention_approved",
        "epistemic_reason_code_registry_approved",
        "assessment_provenance_approved",
        "assessment_explanation_evidence_approved",
        "in_memory_assessment_batch_approved",
        "synthetic_assessment_fixture_replay_approved",
        "deterministic_assessment_replay_approved",
        "bounded_assessment_queries_approved",
        "assessment_integrity_audit_approved",
        "redacted_assessment_diagnostics_approved",
        "epistemic_incident_record_approved",
        "epistemic_operator_review_item_approved",
        "resource_budget_enforcement_approved",
        "documentation_and_static_evidence_approved",
        "no_absolute_truth_oracle_enforcement_approved",
        "no_automatic_claim_acceptance_enforcement_approved",
        "no_automatic_claim_rejection_enforcement_approved",
        "no_automatic_correction_effect_enforcement_approved",
        "no_automatic_retraction_effect_enforcement_approved",
        "no_knowledge_promotion_enforcement_approved",
        "no_belief_mutation_enforcement_approved",
        "no_persistent_assessment_write_enforcement_approved",
        "no_network_fetch_enforcement_approved",
        "no_runtime_registration_enforcement_approved",
        "no_source_mutation_enforcement_approved",
        "no_git_mutation_enforcement_approved",
        "no_pr_creation_enforcement_approved",
        "no_approval_creation_enforcement_approved",
    ]
)
PROHIBITED_KEYS = set(
    [
        "absolute_truth_oracle_enabled",
        "claim_true_boolean_assignment_enabled",
        "claim_false_boolean_assignment_enabled",
        "automatic_claim_acceptance_enabled",
        "automatic_claim_rejection_enabled",
        "automatic_claim_extraction_enabled",
        "source_body_parsing_enabled",
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
        "persistent_assessment_write_enabled",
        "assessment_database_enabled",
        "external_database_integration_enabled",
        "network_acquisition_enabled",
        "public_network_fetch_enabled",
        "search_provider_integration_enabled",
        "connector_integration_enabled",
        "model_provider_integration_enabled",
        "background_assessment_worker_enabled",
        "scheduled_assessment_job_enabled",
        "kernel_registration_enabled",
        "application_startup_registration_enabled",
        "api_route_enabled",
        "installed_cli_command_enabled",
        "sdk_runtime_resource_enabled",
        "credential_use_enabled",
        "cookie_use_enabled",
        "authorization_header_use_enabled",
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
    ]
)
STATUS_VALUES = [
    "supported",
    "contradicted",
    "mixed",
    "insufficient_evidence",
    "stale",
    "superseded",
    "retracted",
    "scope_mismatch",
    "unknown",
]
CONFIDENCE_BANDS = ["very_low", "low", "medium", "high", "very_high"]
FRESHNESS_STATUS_VALUES = ["current", "ageing", "stale", "superseded", "retracted", "unknown"]
SCOPE_APPLICABILITY_VALUES = [
    "applicable",
    "partially_applicable",
    "not_applicable",
    "insufficient_scope",
]
CONTRADICTION_STATUS_VALUES = [
    "none_detected",
    "unresolved",
    "material",
    "scope_separated",
    "insufficient_evidence",
]
CAPS = {
    "zero_independent_evidence_groups": {"maximum_confidence": 0.2},
    "one_independent_evidence_group": {"maximum_confidence": 0.6},
    "only_unknown_or_community_unverified_evidence": {"maximum_confidence": 0.5},
    "missing_citation_coverage": {"maximum_confidence": 0.45},
    "incomplete_provenance": {"maximum_confidence": 0.5},
    "stale_evidence": {"maximum_confidence": 0.5},
    "unresolved_material_opposition": {"status": "mixed", "maximum_confidence": 0.65},
    "scope_mismatch": {"status": "scope_mismatch", "maximum_confidence": 0.2},
    "insufficient_explicit_scope": {"status": "insufficient_evidence"},
    "applicable_retraction": {"status": "retracted"},
    "applicable_supersession_without_current_support": {"status": "superseded"},
    "broken_source_registry_or_graph_integrity": {"status": "unknown", "confidence": 0},
}
THREATS = [
    "authority bias",
    "source-class treated as truth",
    "duplicated evidence amplification",
    "mirrored-source amplification",
    "circular citation",
    "provenance spoofing",
    "citation spoofing",
    "lineage spoofing",
    "independence-group spoofing",
    "stale evidence",
    "superseded evidence",
    "retracted evidence",
    "correction ignored",
    "jurisdiction mismatch",
    "version mismatch",
    "temporal mismatch",
    "missing scope",
    "selective evidence omission",
    "opposition suppression",
    "confidence inflation",
    "confidence underflow masking",
    "hard-cap bypass",
    "score-weight tampering",
    "hidden score weights",
    "manual FAIL-to-PASS conversion",
    "assessment used as approval",
    "user statement treated as fact",
    "engagement treated as fact",
    "unresolved contradiction hidden",
    "source body leakage",
    "claim text leakage into diagnostics",
    "raw prompt leakage",
    "persistent assessment write",
    "database creation",
    "network acquisition",
    "background mutation",
    "knowledge-promotion bypass",
    "cognitive-belief mutation",
    "authorization reuse",
]


def read_json(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text())


def read_text(relative: str) -> str:
    return (ROOT / relative).read_text()


def auth_records() -> list[dict]:
    return read_json("docs/knowledge-intelligence/authorization-ledger.json")["records"]


def authorization_record(auth_id: str) -> dict:
    matches = [
        record for record in auth_records() if record.get("authorization_transaction_id") == auth_id
    ]
    assert len(matches) == 1
    return matches[0]


def active_authorization_record() -> dict:
    active = [record for record in auth_records() if record.get("authorization_active") is True]
    assert len(active) == 1
    return active[0]


def evaluation_report() -> dict:
    return read_json("examples/knowledge-intelligence/claim-graph-operator-evaluation-report.json")


def validate_epistemic_authorization(record: dict) -> None:
    assert record["program_id"] == PROGRAM_ID
    assert record["authorization_transaction_id"] == EPISTEMIC_AUTH_ID
    assert record["approval_record_id"] == EPISTEMIC_AUTH_ID
    assert record["parent_authorization_transaction_id"] == CLAIM_GRAPH_AUTH_ID
    assert record["parent_evaluation_id"] == EVALUATION_ID
    assert record["parent_evaluation_decision"] == DECISION
    assert record["parent_closeout_task"] == "AION-210"
    assert record["parent_claim_graph_implementation_task"] == "AION-209"
    assert record["parent_claim_graph_implementation_prs"] == [121]
    assert record["parent_claim_graph_implementation_feature_commits"] == [
        "0a84080c83f87eef94b5191c432021776c6a336a",
        "d50252c84a0a02b75317c7d2051eaee4fb9dc54c",
    ]
    assert record["parent_claim_graph_implementation_merge_commits"] == [
        "f9e2438a49aae458983fc57cee5c12b5ef0ab856"
    ]
    assert record["candidate_id"] == "epistemic-truth-engine-core"
    assert record["workstream"] == "knowledge-intelligence-epistemic-truth-engine"
    assert record["implementation_task"] == "AION-211"
    assert record["formal_closeout_task"] == "AION-212"
    assert record["authorization_scope"] == SCOPE
    assert record["authorization_transaction_approved"] is True
    assert record["explicit_approval_record_approval"] is True
    assert record["implementation_authorization_approved"] is True
    assert record["implementation_go_status"] is True
    assert record["implementation_no_go_status"] is False
    assert record["authorization_active"] is True
    assert record["authorization_consumed"] is False
    assert record["authorization_expired"] is False
    assert record["authorization_reusable"] is False
    assert set(record["authorized_capabilities"]) == AUTHORIZED_KEYS
    assert all(record["authorized_capabilities"].values())
    assert set(record["prohibited_capabilities"]) == PROHIBITED_KEYS
    assert all(value is False for value in record["prohibited_capabilities"].values())
    assert record["resource_limits"] == RESOURCE_LIMITS
    assert record["epistemic_truth_engine_authorized"] is True
    assert record["epistemic_truth_engine_implemented"] is False
    assert record["runtime_effect"] is False


def assert_epistemic_authorization_rejects(mutator) -> None:
    record = copy.deepcopy(active_authorization_record())
    mutator(record)
    try:
        validate_epistemic_authorization(record)
    except AssertionError:
        return
    raise AssertionError("invalid epistemic authorization was accepted")


def changed_files() -> set[str]:
    base = None
    for ref in ("origin/main", "main"):
        exists = subprocess.run(
            ["git", "rev-parse", "--verify", "--quiet", ref],
            cwd=ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if exists.returncode == 0:
            merge_base = subprocess.run(
                ["git", "merge-base", "HEAD", ref],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            if merge_base.returncode == 0 and merge_base.stdout.strip():
                base = merge_base.stdout.strip()
                break
    if base is None:
        return set()
    diff = subprocess.run(
        ["git", "diff", "--name-only", base, "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return {line.strip() for line in diff.stdout.splitlines() if line.strip()}
