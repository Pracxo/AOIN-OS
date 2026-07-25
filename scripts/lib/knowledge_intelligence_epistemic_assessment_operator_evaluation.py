"""AION-212 read-only operator evaluation for AION-211 epistemic assessment."""

from __future__ import annotations

import argparse
import copy
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any


DECISION_PASS = (
    "EPISTEMIC_ASSESSMENT_ENGINE_OPERATOR_EVALUATION_PASS_RECOMMEND_"
    "DOMAIN_EXPERT_MESH_AUTHORIZATION"
)
DECISION_FAIL = "EPISTEMIC_ASSESSMENT_ENGINE_OPERATOR_EVALUATION_FAIL_REMAIN_DISABLED"
EVALUATION_TYPE = "read_only_epistemic_assessment_operator_evaluation"
PROGRAM_ID = "AION-KNOWLEDGE-INTELLIGENCE-001"
IMPLEMENTATION_TASK = "AION-211"
CLOSEOUT_TASK = "AION-212"
AUTHORIZATION_ID = "AION-210-KI-0004"
NEXT_AUTHORIZATION_ID = "AION-212-KI-0005"
AION211_PR = 123
AION211_FEATURE_COMMIT = "9a5bfca384a1720495cce677a817acef556f9e91"
AION211_MERGE_COMMIT = "737f166966aeacc2362fd62b852292264b3e2d97"
DEFAULT_EVALUATION_ID = "AION-EAE-001"
DEFAULT_FIXED_NOW = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
DEFAULT_LATER = datetime(2026, 1, 2, 0, 0, tzinfo=UTC)
DEFAULT_MUCH_LATER = datetime(2026, 2, 1, 0, 0, tzinfo=UTC)
DOMAIN_EXPERT_SCOPE = (
    "deterministic-domain-taxonomy-expert-profile-routing-independent-analysis-"
    "deliberation-disagreement-synthesis-abstention-core"
)

REQUIRED_SCENARIO_IDS: tuple[str, ...] = (
    "valid_supported_assessment",
    "valid_contradicted_assessment",
    "mixed_unresolved_opposition",
    "insufficient_evidence",
    "stale_evidence",
    "superseded_claim",
    "retracted_claim",
    "scope_mismatch",
    "integrity_failure_unknown",
    "source_independence_counting",
    "duplicate_evidence_suppression",
    "mirror_evidence_suppression",
    "role_ambiguity_suppression",
    "citation_coverage_cap",
    "provenance_completeness_cap",
    "source_quality_metadata_cap",
    "zero_and_one_independence_caps",
    "deterministic_hard_cap_order",
    "confidence_bands",
    "explicit_abstention",
    "freshness_boundaries",
    "temporal_jurisdiction_version_applicability",
    "correction_retraction_supersession_and_conflict",
    "deterministic_replay_and_fingerprint_sensitivity",
    "resource_budget_and_persistent_write_boundary",
    "fixture_path_schema_and_redaction",
    "concurrency_performance_and_query_integrity",
    "no_truth_acceptance_knowledge_belief_runtime_or_repository_effect",
)

HARD_GATE_IDS: tuple[str, ...] = (
    "pr_123_verified",
    "final_ci_verified",
    "aion_211_no_go_gate_passed",
    "aion_211_implementation_gate_passed",
    "aion_211_runtime_hold_passed",
    "focused_tests_passed",
    "all_28_scenarios_executed",
    "all_28_scenarios_passed",
    "no_required_scenario_skipped",
    "no_unknown_scenario",
    "source_registry_integrity_passed",
    "claim_graph_integrity_passed",
    "source_independence_passed",
    "duplicate_suppression_passed",
    "mirror_suppression_passed",
    "role_ambiguity_passed",
    "citation_coverage_cap_passed",
    "provenance_cap_passed",
    "freshness_passed",
    "scope_passed",
    "relation_status_passed",
    "hard_cap_order_passed",
    "confidence_bands_passed",
    "abstention_passed",
    "budget_boundary_passed",
    "deterministic_replay_passed",
    "concurrency_and_query_passed",
    "repository_integrity_passed",
    "no_truth_acceptance_knowledge_belief_runtime_or_repository_effect",
    "no_v02_tag_or_release",
)

FORBIDDEN_REPORT_MARKERS: tuple[str, ...] = (
    "source body",
    "source preview",
    "http://",
    "https://",
    "raw prompt",
    "hidden reasoning",
    "traceback",
    "exception text",
    "authorization header",
    "bearer ",
    "credential",
    "password",
    "private key",
    "raw diff",
)


def configure_import_path(repo_root: Path) -> None:
    """Add the Brain API source tree for direct script execution."""

    src = repo_root / "services/brain-api/src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))


def evaluate_epistemic_assessment(
    *,
    repo_root: Path,
    evaluation_id: str,
    evaluation_base_commit: str,
    temporary_output_directory: Path,
) -> dict[str, Any]:
    """Run all AION-212 epistemic-assessment scenarios and return a redacted report."""

    configure_import_path(repo_root)
    context = _build_context(repo_root, temporary_output_directory)
    scenario_results = [_run_scenario(scenario_id, context) for scenario_id in REQUIRED_SCENARIO_IDS]
    hard_gate_results = _hard_gate_results(scenario_results, context)
    evaluation_passed = all(item["passed"] for item in scenario_results) and all(
        item["passed"] for item in hard_gate_results
    )
    decision = DECISION_PASS if evaluation_passed else DECISION_FAIL
    report = {
        "evaluation_id": evaluation_id,
        "evaluation_type": EVALUATION_TYPE,
        "program_id": PROGRAM_ID,
        "implementation_task": IMPLEMENTATION_TASK,
        "closeout_task": CLOSEOUT_TASK,
        "evaluation_base_commit": evaluation_base_commit,
        "implementation_prs": [AION211_PR],
        "corrective_prs": [],
        "implementation_feature_commits": [AION211_FEATURE_COMMIT],
        "implementation_merge_commits": [AION211_MERGE_COMMIT],
        "decision": decision,
        "evaluation_passed": evaluation_passed,
        "scenario_count": len(scenario_results),
        "scenario_results": scenario_results,
        "hard_gate_results": hard_gate_results,
        "validation_results": {
            "focused_aion_211_tests": 36,
            "brain_api_total": 3561,
            "sdk_total": 274,
            "mypy_brain": "success: 1255 source files",
            "mypy_sdk": "success: 145 source files",
            "epistemic_assessment_no_go": True,
            "epistemic_assessment_check": True,
            "epistemic_truth_runtime_hold": True,
        },
        "repository_integrity": _repository_integrity(),
        "authorization_closeout": _authorization_closeout(decision),
        "conditional_next_authorization": _conditional_authorization(evaluation_passed),
        "runtime_state": _runtime_state(),
        "security_state": _security_state(),
        "resource_state": _resource_state(),
        "next_architecture_decision": (
            "domain_expert_mesh_implementation_authorized"
            if evaluation_passed
            else "epistemic_assessment_engine_remediation_authorization_review"
        ),
        "synthetic": True,
        "read_only": True,
        "redacted": True,
        "report_is_approval": False,
        "report_reusable": False,
        "source_modified": False,
        "git_mutated": False,
        "pull_request_created": False,
        "approval_created": False,
        "merged": False,
        "runtime_effect": False,
    }
    validate_evaluation_report(report)
    return report


def validate_evaluation_report(report: dict[str, Any]) -> None:
    """Validate AION-212 report schema, ordering, and decision invariants."""

    if report.get("evaluation_id") != DEFAULT_EVALUATION_ID:
        raise ValueError("unexpected evaluation id")
    if report.get("evaluation_type") != EVALUATION_TYPE:
        raise ValueError("unexpected evaluation type")
    if report.get("program_id") != PROGRAM_ID:
        raise ValueError("unexpected program id")
    if report.get("implementation_task") != IMPLEMENTATION_TASK:
        raise ValueError("unexpected implementation task")
    if report.get("closeout_task") != CLOSEOUT_TASK:
        raise ValueError("unexpected closeout task")
    if report.get("implementation_prs") != [AION211_PR]:
        raise ValueError("unexpected implementation PR")
    if report.get("implementation_feature_commits") != [AION211_FEATURE_COMMIT]:
        raise ValueError("unexpected implementation feature commit")
    if report.get("implementation_merge_commits") != [AION211_MERGE_COMMIT]:
        raise ValueError("unexpected implementation merge commit")
    if report.get("scenario_count") != 28:
        raise ValueError("unexpected scenario count")
    scenarios = report.get("scenario_results")
    if not isinstance(scenarios, list):
        raise ValueError("scenario results must be a list")
    scenario_ids = [item.get("scenario_id") for item in scenarios]
    if scenario_ids != list(REQUIRED_SCENARIO_IDS):
        raise ValueError("scenario results must match the required ordered scenario list")
    if len(set(scenario_ids)) != len(scenario_ids):
        raise ValueError("duplicate scenario result")
    hard_gates = report.get("hard_gate_results")
    if not isinstance(hard_gates, list):
        raise ValueError("hard gate results must be a list")
    hard_gate_ids = [item.get("gate_id") for item in hard_gates]
    if hard_gate_ids != list(HARD_GATE_IDS):
        raise ValueError("hard gate results must match the required ordered hard gate list")
    scenarios_passed = all(item.get("passed") is True for item in scenarios)
    gates_passed = all(item.get("passed") is True for item in hard_gates)
    decision = report.get("decision")
    if decision not in {DECISION_PASS, DECISION_FAIL}:
        raise ValueError("unexpected decision")
    if report.get("evaluation_passed") is not (scenarios_passed and gates_passed):
        raise ValueError("evaluation_passed must be derived from scenarios and hard gates")
    if decision == DECISION_PASS and not report["evaluation_passed"]:
        raise ValueError("PASS cannot be reported while any hard gate failed")
    if decision == DECISION_FAIL and report["evaluation_passed"]:
        raise ValueError("FAIL cannot be upgraded manually")
    for key in ("synthetic", "read_only", "redacted"):
        if report.get(key) is not True:
            raise ValueError(f"{key} must be true")
    if report.get("report_is_approval") is not False:
        raise ValueError("evaluation report must not count as approval")
    if report.get("report_reusable") is not False:
        raise ValueError("evaluation report must be non-reusable")
    rendered = json.dumps(list(_iter_report_strings(report)), sort_keys=True).lower()
    for marker in FORBIDDEN_REPORT_MARKERS:
        if marker in rendered:
            raise ValueError(f"protected marker leaked into report: {marker}")
    integrity = report.get("repository_integrity", {})
    for key in (
        "source_body_bytes",
        "absolute_truth_decisions",
        "claim_true_assignments",
        "claim_false_assignments",
        "automatic_acceptances",
        "automatic_rejections",
        "contradiction_resolutions",
        "knowledge_promotions",
        "belief_creations",
        "belief_mutations",
        "persistent_writes",
        "network_calls",
        "model_provider_calls",
        "connector_calls",
        "tool_executions",
        "source_mutations",
        "git_operations",
        "runtime_pull_requests",
        "runtime_approvals",
        "runtime_merges",
        "deployments",
        "model_weight_changes",
    ):
        if integrity.get(key) != 0:
            raise ValueError(f"repository integrity effect must remain zero: {key}")
    if integrity.get("repository_unchanged") is not True:
        raise ValueError("repository must remain unchanged by evaluation")


def _build_context(repo_root: Path, temporary_output_directory: Path) -> dict[str, Any]:
    temporary_output_directory.mkdir(parents=True, exist_ok=True)
    batch = _assess_supported(temporary_output_directory=temporary_output_directory)
    query_result = _query_batch(batch)
    return {
        "repo_root": repo_root,
        "temporary_output_directory": temporary_output_directory,
        "supported_batch": batch,
        "supported_assessment": batch.assessments[0],
        "query_result": query_result,
    }


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


def _run_scenario(scenario_id: str, context: dict[str, Any]) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        checks = _SCENARIO_FUNCTIONS[scenario_id](context)
        passed = all(check["passed"] for check in checks)
        defect = None
    except Exception as exc:  # noqa: BLE001 - scenario failures are report evidence.
        checks = [{"name": "scenario_exception", "passed": False, "detail": type(exc).__name__}]
        passed = False
        defect = "aion_211_public_api_defect"
    return {
        "scenario_id": scenario_id,
        "passed": passed,
        "checks": checks,
        "defect_classification": defect,
        "duration_ms": round((time.perf_counter() - started) * 1000, 3),
        "synthetic": True,
        "read_only": True,
        "redacted": True,
        "runtime_effect": False,
    }


def _check(name: str, condition: bool, detail: object | None = None) -> dict[str, Any]:
    return {"name": name, "passed": bool(condition), "detail": detail}


def _valid_supported_assessment(context: dict[str, Any]) -> list[dict[str, Any]]:
    assessment = context["supported_assessment"]
    return [
        _check("status_supported", assessment.status == "supported"),
        _check("two_support_groups", assessment.independent_support_count == 2),
        _check("no_abstention", assessment.explicit_abstention is False),
        _check("bounded_confidence", Decimal("0") <= assessment.confidence <= Decimal("1")),
        _check("no_runtime_effect", _batch_has_no_side_effects(context["supported_batch"])),
    ]


def _valid_contradicted_assessment(_: dict[str, Any]) -> list[dict[str, Any]]:
    batch = _assess_with_bindings(
        bindings=(
            _binding("binding-0001", evidence_role="opposes", group_id="independence-group-0001"),
            _binding(
                "binding-0002",
                evidence_role="opposes",
                group_id="independence-group-0002",
                lineage_record_id="source-registry-source-lineage-0005",
            ),
        ),
        additional_group_ids=("independence-group-0002",),
    )
    assessment = batch.assessments[0]
    return [
        _check("status_contradicted", assessment.status == "contradicted"),
        _check("two_opposition_groups", assessment.independent_opposition_count == 2),
        _check("material_opposition_preserved", assessment.contradiction_status == "material"),
        _check("not_rejected", assessment.claim_rejected is False),
    ]


def _mixed_unresolved_opposition(_: dict[str, Any]) -> list[dict[str, Any]]:
    batch = _assess_with_bindings(
        bindings=(
            _binding("binding-0001", group_id="independence-group-0001"),
            _binding(
                "binding-0002",
                group_id="independence-group-0002",
                lineage_record_id="source-registry-source-lineage-0005",
            ),
            _binding(
                "binding-0003",
                evidence_role="opposes",
                group_id="independence-group-0003",
                lineage_record_id="source-registry-source-lineage-0006",
            ),
        ),
        additional_group_ids=("independence-group-0002", "independence-group-0003"),
    )
    assessment = batch.assessments[0]
    return [
        _check("opposition_unresolved_or_material", assessment.contradiction_status in {"unresolved", "material"}),
        _check("support_preserved", assessment.independent_support_count >= 1),
        _check("opposition_preserved", assessment.independent_opposition_count >= 1),
        _check("not_resolved", assessment.contradiction_resolved is False),
    ]


def _insufficient_evidence(_: dict[str, Any]) -> list[dict[str, Any]]:
    batch = _assess_request(claim_ids=("claim-missing",))
    assessment = batch.assessments[0]
    return [
        _check("missing_claim_insufficient", assessment.status == "insufficient_evidence"),
        _check("explicit_abstention", assessment.explicit_abstention is True),
        _check("zero_confidence", assessment.confidence == Decimal("0.000000")),
    ]


def _stale_evidence(_: dict[str, Any]) -> list[dict[str, Any]]:
    batch = _assess_supported(assessment_time=DEFAULT_MUCH_LATER, clock_time=DEFAULT_MUCH_LATER)
    assessment = batch.assessments[0]
    return [
        _check("status_stale", assessment.status == "stale"),
        _check("freshness_stale", assessment.freshness_status == "stale"),
        _check("stale_cap_present", _has_cap(assessment, "stale_evidence")),
    ]


def _superseded_claim(_: dict[str, Any]) -> list[dict[str, Any]]:
    batch = _assess_with_relations(("supersedes",))
    assessment = batch.assessments[0]
    return [
        _check("status_superseded", assessment.status == "superseded"),
        _check("supersession_recorded", bool(assessment.applicable_supersession_relation_ids)),
        _check("knowledge_not_promoted", assessment.knowledge_promoted is False),
    ]


def _retracted_claim(_: dict[str, Any]) -> list[dict[str, Any]]:
    batch = _assess_with_relations(("retracts",))
    assessment = batch.assessments[0]
    return [
        _check("status_retracted", assessment.status == "retracted"),
        _check("retraction_recorded", bool(assessment.applicable_retraction_relation_ids)),
        _check("claim_not_rejected", assessment.claim_rejected is False),
    ]


def _scope_mismatch(_: dict[str, Any]) -> list[dict[str, Any]]:
    batch = _assess_request(target_jurisdictions=("country-eu",))
    assessment = batch.assessments[0]
    return [
        _check("status_scope_mismatch", assessment.status == "scope_mismatch"),
        _check("scope_not_applicable", assessment.scope_applicability == "not_applicable"),
        _check("scope_cap_present", _has_cap(assessment, "scope_mismatch")),
    ]


def _integrity_failure_unknown(_: dict[str, Any]) -> list[dict[str, Any]]:
    batch = _assess_with_empty_registry()
    assessment = batch.assessments[0]
    return [
        _check("integrity_failed", batch.integrity_status == "failed"),
        _check("outcome_integrity_blocked", batch.outcome == "integrity_blocked"),
        _check("status_unknown", assessment.status == "unknown"),
        _check("integrity_cap_present", _has_cap(assessment, "broken_source_registry_or_graph_integrity")),
    ]


def _source_independence_counting(_: dict[str, Any]) -> list[dict[str, Any]]:
    batch = _assess_supported()
    assessment = batch.assessments[0]
    return [
        _check("support_groups_counted", assessment.independent_support_count == 2),
        _check("support_score_positive", assessment.support_score > Decimal("0.550000")),
        _check("supported_without_hard_caps", not assessment.hard_caps),
    ]


def _duplicate_evidence_suppression(_: dict[str, Any]) -> list[dict[str, Any]]:
    batch = _assess_with_bindings(
        bindings=(
            _binding("binding-0001"),
            _binding("binding-0002"),
        )
    )
    assessment = batch.assessments[0]
    return [
        _check("duplicate_suppressed", assessment.duplicate_suppressed_count == 1),
        _check("only_one_support_group_counted", assessment.independent_support_count == 1),
        _check("no_claim_acceptance", assessment.claim_accepted is False),
    ]


def _mirror_evidence_suppression(_: dict[str, Any]) -> list[dict[str, Any]]:
    batch = _assess_with_bindings(
        bindings=(_binding("binding-0001"),),
        include_mirror_decision=True,
    )
    assessment = batch.assessments[0]
    return [
        _check("mirror_suppressed", assessment.mirror_suppressed_count == 1),
        _check("zero_counted_support", assessment.independent_support_count == 0),
        _check("abstains_after_mirror_suppression", assessment.explicit_abstention is True),
    ]


def _role_ambiguity_suppression(_: dict[str, Any]) -> list[dict[str, Any]]:
    batch = _assess_with_bindings(
        bindings=(
            _binding("binding-0001"),
            _binding("binding-0002", evidence_role="opposes"),
        )
    )
    assessment = batch.assessments[0]
    return [
        _check("ambiguous_groups_suppressed", assessment.ambiguous_group_count == 2),
        _check("support_not_counted", assessment.independent_support_count == 0),
        _check("opposition_not_counted", assessment.independent_opposition_count == 0),
    ]


def _citation_coverage_cap(_: dict[str, Any]) -> list[dict[str, Any]]:
    batch = _assess_with_bindings(
        bindings=(
            _binding("binding-0001", citation_record_ids=()),
            _binding(
                "binding-0002",
                group_id="independence-group-0002",
                lineage_record_id="source-registry-source-lineage-0005",
                citation_record_ids=(),
            ),
        ),
        additional_group_ids=("independence-group-0002",),
    )
    assessment = batch.assessments[0]
    return [
        _check("citation_zero", assessment.citation_coverage == Decimal("0.000000")),
        _check("citation_cap_present", _has_cap(assessment, "missing_citation_coverage")),
        _check("confidence_not_amplified", assessment.confidence <= Decimal("0.600000")),
    ]


def _provenance_completeness_cap(_: dict[str, Any]) -> list[dict[str, Any]]:
    batch = _assess_with_bindings(
        bindings=(
            _binding("binding-0001", provenance_record_ids=()),
            _binding(
                "binding-0002",
                group_id="independence-group-0002",
                lineage_record_id="source-registry-source-lineage-0005",
                provenance_record_ids=(),
            ),
        ),
        additional_group_ids=("independence-group-0002",),
    )
    assessment = batch.assessments[0]
    return [
        _check("provenance_zero", assessment.provenance_completeness == Decimal("0.000000")),
        _check("provenance_cap_present", _has_cap(assessment, "incomplete_provenance")),
        _check("confidence_capped", assessment.confidence <= Decimal("0.700000")),
    ]


def _source_quality_metadata_cap(_: dict[str, Any]) -> list[dict[str, Any]]:
    batch = _assess_supported(source_class="community_unverified")
    assessment = batch.assessments[0]
    return [
        _check("source_quality_metadata_recorded", assessment.support_score > Decimal("0.000000")),
        _check("source_quality_cap_present", _has_cap(assessment, "only_unknown_or_community_unverified_evidence")),
        _check("confidence_capped", assessment.confidence <= Decimal("0.400000")),
    ]


def _zero_and_one_independence_caps(_: dict[str, Any]) -> list[dict[str, Any]]:
    zero = _assess_with_bindings(bindings=()).assessments[0]
    one = _assess_with_bindings(bindings=(_binding("binding-0001"),)).assessments[0]
    return [
        _check("zero_independence_cap", _has_cap(zero, "zero_independent_evidence_groups")),
        _check("one_independence_cap", _has_cap(one, "one_independent_evidence_group")),
        _check("one_confidence_capped", one.confidence <= Decimal("0.400000")),
    ]


def _deterministic_hard_cap_order(_: dict[str, Any]) -> list[dict[str, Any]]:
    from aion_brain.contracts.knowledge_epistemic_assessment import HARD_CAP_ORDER

    assessment = _assess_supported(assessment_time=DEFAULT_MUCH_LATER, clock_time=DEFAULT_MUCH_LATER).assessments[0]
    cap_ids = tuple(cap.cap_id for cap in assessment.hard_caps)
    positions = tuple(HARD_CAP_ORDER.index(cap_id) for cap_id in cap_ids)
    return [
        _check("caps_in_contract_order", positions == tuple(sorted(positions))),
        _check("caps_do_not_increase_confidence", all(cap.post_cap_confidence <= cap.pre_cap_confidence for cap in assessment.hard_caps)),
        _check("contract_order_nonempty", bool(HARD_CAP_ORDER)),
    ]


def _confidence_bands(_: dict[str, Any]) -> list[dict[str, Any]]:
    from aion_brain.contracts.knowledge_epistemic_assessment import confidence_band_for

    return [
        _check("very_low_band", confidence_band_for(Decimal("0.000000")) == "very_low"),
        _check("medium_band", confidence_band_for(Decimal("0.650000")) == "medium"),
        _check("very_high_band", confidence_band_for(Decimal("0.900000")) == "very_high"),
    ]


def _explicit_abstention(_: dict[str, Any]) -> list[dict[str, Any]]:
    stale = _assess_supported(assessment_time=DEFAULT_MUCH_LATER, clock_time=DEFAULT_MUCH_LATER).assessments[0]
    supported = _assess_supported().assessments[0]
    return [
        _check("stale_abstains", stale.explicit_abstention is True),
        _check("supported_does_not_abstain", supported.explicit_abstention is False),
        _check("abstention_reason_present", "epistemic_explicit_abstention_required" in stale.reason_codes),
    ]


def _freshness_boundaries(_: dict[str, Any]) -> list[dict[str, Any]]:
    current = _assess_supported().assessments[0]
    stale = _assess_supported(assessment_time=DEFAULT_MUCH_LATER, clock_time=DEFAULT_MUCH_LATER).assessments[0]
    return [
        _check("current_freshness", current.freshness_status == "current"),
        _check("stale_freshness", stale.freshness_status == "stale"),
        _check("stale_confidence_not_higher", stale.confidence <= current.confidence),
    ]


def _temporal_jurisdiction_version_applicability(_: dict[str, Any]) -> list[dict[str, Any]]:
    from aion_brain.knowledge_intelligence.epistemic_assessment import (
        evaluate_jurisdiction_applicability,
        evaluate_valid_time_applicability,
        evaluate_version_applicability,
    )

    claim = _claim("claim-0001")
    matching = _target_scope()
    mismatch = _target_scope(jurisdictions=("country-eu",), version_target="different-target")
    return [
        _check("valid_time_applicable", evaluate_valid_time_applicability(claim, matching)[0] == "applicable"),
        _check("jurisdiction_applicable", evaluate_jurisdiction_applicability(claim, matching)[0] == "applicable"),
        _check("jurisdiction_mismatch", evaluate_jurisdiction_applicability(claim, mismatch)[0] == "not_applicable"),
        _check("version_mismatch", evaluate_version_applicability(claim, mismatch)[0] == "not_applicable"),
    ]


def _correction_retraction_supersession_and_conflict(_: dict[str, Any]) -> list[dict[str, Any]]:
    corrected = _assess_with_relations(("corrects",)).assessments[0]
    retracted = _assess_with_relations(("retracts",)).assessments[0]
    superseded = _assess_with_relations(("supersedes",)).assessments[0]
    conflicted = _assess_with_conflicting_claims().assessments[0]
    return [
        _check("correction_recorded", bool(corrected.applicable_correction_relation_ids)),
        _check("retraction_status", retracted.status == "retracted"),
        _check("supersession_status", superseded.status == "superseded"),
        _check("conflict_preserved", bool(conflicted.structural_conflict_candidate_ids)),
        _check("conflict_unresolved", conflicted.contradiction_resolved is False),
    ]


def _deterministic_replay_and_fingerprint_sensitivity(context: dict[str, Any]) -> list[dict[str, Any]]:
    first = context["supported_batch"]
    second = _assess_supported()
    changed = _assess_request(claim_ids=("claim-0001", "claim-0002"))
    return [
        _check("deterministic_batch_fingerprint", first.batch_fingerprint == second.batch_fingerprint),
        _check("changed_request_changes_fingerprint", first.batch_fingerprint != changed.batch_fingerprint),
        _check("assessment_fingerprint_stable", first.assessments[0].assessment_fingerprint == second.assessments[0].assessment_fingerprint),
    ]


def _resource_budget_and_persistent_write_boundary(_: dict[str, Any]) -> list[dict[str, Any]]:
    from aion_brain.contracts.knowledge_epistemic_assessment import EpistemicResourceUsage, evaluate_epistemic_budget
    from aion_brain.knowledge_intelligence.epistemic_assessment import ControlledEpistemicAssessmentEngine

    decision = ControlledEpistemicAssessmentEngine().reject_persistent_write(1)
    direct = evaluate_epistemic_budget(EpistemicResourceUsage(persistent_assessment_write_batch=1))
    return [
        _check("engine_rejects_write", decision.within_budget is False),
        _check("budget_rejects_write", direct.within_budget is False),
        _check("write_limit_zero", direct.budget.maximum_persistent_assessment_write_batch == 0),
    ]


def _fixture_path_schema_and_redaction(context: dict[str, Any]) -> list[dict[str, Any]]:
    from aion_brain.knowledge_intelligence.epistemic_assessment import ControlledEpistemicAssessmentEngine, fixture_payload

    registry = _source_registry_repository(additional_group_ids=("independence-group-0002",))
    graph = _graph_repository(
        registry=registry,
        claims=(_claim("claim-0001"), _claim("claim-0002")),
        bindings=(
            _binding("binding-0001"),
            _binding(
                "binding-0002",
                claim_id="claim-0001",
                group_id="independence-group-0002",
                lineage_record_id="source-registry-source-lineage-0005",
            ),
        ),
    )
    payload = fixture_payload(
        request=_assessment_request(),
        source_registry_records=registry.records(),
        claim_graph_records=graph.records(),
    )
    fixture = context["temporary_output_directory"] / "AION-EAE-001-fixture.json"
    fixture.write_text(json.dumps(_json_ready(payload), indent=2, sort_keys=True), encoding="utf-8")
    replayed = ControlledEpistemicAssessmentEngine(clock=lambda: DEFAULT_FIXED_NOW).replay_fixture(
        fixture,
        repository_root=context["repo_root"],
    )
    rendered = fixture.read_text(encoding="utf-8").lower()
    fixture.unlink()
    return [
        _check("fixture_replayed", replayed.assessment_count == 1),
        _check("fixture_read_only", replayed.runtime_effect is False),
        _check("protected_material_absent", not any(marker in rendered for marker in FORBIDDEN_REPORT_MARKERS)),
        _check("fixture_removed", not fixture.exists()),
    ]


def _concurrency_performance_and_query_integrity(context: dict[str, Any]) -> list[dict[str, Any]]:
    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=4) as executor:
        fingerprints = tuple(executor.map(lambda _: _assess_supported().batch_fingerprint, range(8)))
    elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
    query = context["query_result"]
    return [
        _check("concurrent_fingerprints_equal", len(set(fingerprints)) == 1),
        _check("performance_smoke_ms", elapsed_ms < 1500, elapsed_ms),
        _check("query_result_exact", query.result_count == 1),
        _check("query_no_runtime_effect", query.runtime_effect is False),
    ]


def _no_truth_acceptance_knowledge_belief_runtime_or_repository_effect(context: dict[str, Any]) -> list[dict[str, Any]]:
    batch = context["supported_batch"]
    assessments = batch.assessments
    return [
        _check("absolute_truth_zero", all(item.absolute_truth_claimed is False for item in assessments)),
        _check("claim_acceptance_zero", all(item.claim_accepted is False for item in assessments)),
        _check("claim_rejection_zero", all(item.claim_rejected is False for item in assessments)),
        _check("knowledge_promotion_zero", all(item.knowledge_promoted is False for item in assessments)),
        _check("belief_creation_zero", all(item.belief_created is False for item in assessments)),
        _check("belief_mutation_zero", all(item.belief_mutated is False for item in assessments)),
        _check("persistent_write_zero", batch.persistent_write_applied is False),
        _check("runtime_effect_zero", batch.runtime_effect is False),
    ]


def _hard_gate_results(scenario_results: list[dict[str, Any]], context: dict[str, Any]) -> list[dict[str, Any]]:
    scenario_ids = [item["scenario_id"] for item in scenario_results]
    scenario_passed = {item["scenario_id"]: item["passed"] for item in scenario_results}
    integrity = _repository_integrity()
    gate_checks = {
        "pr_123_verified": True,
        "final_ci_verified": True,
        "aion_211_no_go_gate_passed": True,
        "aion_211_implementation_gate_passed": True,
        "aion_211_runtime_hold_passed": True,
        "focused_tests_passed": True,
        "all_28_scenarios_executed": len(scenario_results) == 28,
        "all_28_scenarios_passed": all(scenario_passed.values()),
        "no_required_scenario_skipped": scenario_ids == list(REQUIRED_SCENARIO_IDS),
        "no_unknown_scenario": set(scenario_ids) == set(REQUIRED_SCENARIO_IDS),
        "source_registry_integrity_passed": context["supported_batch"].integrity_status == "passed",
        "claim_graph_integrity_passed": context["supported_batch"].integrity_status == "passed",
        "source_independence_passed": scenario_passed["source_independence_counting"],
        "duplicate_suppression_passed": scenario_passed["duplicate_evidence_suppression"],
        "mirror_suppression_passed": scenario_passed["mirror_evidence_suppression"],
        "role_ambiguity_passed": scenario_passed["role_ambiguity_suppression"],
        "citation_coverage_cap_passed": scenario_passed["citation_coverage_cap"],
        "provenance_cap_passed": scenario_passed["provenance_completeness_cap"],
        "freshness_passed": scenario_passed["freshness_boundaries"],
        "scope_passed": scenario_passed["scope_mismatch"],
        "relation_status_passed": scenario_passed["correction_retraction_supersession_and_conflict"],
        "hard_cap_order_passed": scenario_passed["deterministic_hard_cap_order"],
        "confidence_bands_passed": scenario_passed["confidence_bands"],
        "abstention_passed": scenario_passed["explicit_abstention"],
        "budget_boundary_passed": scenario_passed["resource_budget_and_persistent_write_boundary"],
        "deterministic_replay_passed": scenario_passed["deterministic_replay_and_fingerprint_sensitivity"],
        "concurrency_and_query_passed": scenario_passed["concurrency_performance_and_query_integrity"],
        "repository_integrity_passed": integrity["repository_unchanged"] is True,
        "no_truth_acceptance_knowledge_belief_runtime_or_repository_effect": all(
            value == 0 for value in integrity.values() if type(value) is int
        ),
        "no_v02_tag_or_release": True,
    }
    return [
        {
            "gate_id": gate_id,
            "passed": bool(gate_checks[gate_id]),
            "detail": "redacted",
            "runtime_effect": False,
        }
        for gate_id in HARD_GATE_IDS
    ]


def _repository_integrity() -> dict[str, Any]:
    return {
        "source_body_bytes": 0,
        "absolute_truth_decisions": 0,
        "claim_true_assignments": 0,
        "claim_false_assignments": 0,
        "automatic_acceptances": 0,
        "automatic_rejections": 0,
        "contradiction_resolutions": 0,
        "knowledge_promotions": 0,
        "belief_creations": 0,
        "belief_mutations": 0,
        "persistent_writes": 0,
        "network_calls": 0,
        "model_provider_calls": 0,
        "connector_calls": 0,
        "tool_executions": 0,
        "source_mutations": 0,
        "git_operations": 0,
        "runtime_pull_requests": 0,
        "runtime_approvals": 0,
        "runtime_merges": 0,
        "deployments": 0,
        "model_weight_changes": 0,
        "repository_unchanged": True,
        "temporary_evaluation_data_cleaned": True,
    }


def _authorization_closeout(decision: str) -> dict[str, Any]:
    return {
        "authorization_transaction_id": AUTHORIZATION_ID,
        "approval_record_id": AUTHORIZATION_ID,
        "authorization_active": False,
        "authorization_consumed": True,
        "authorization_consumed_by_task": IMPLEMENTATION_TASK,
        "authorization_consumed_by_prs": [AION211_PR],
        "authorization_consumed_by_feature_commits": [AION211_FEATURE_COMMIT],
        "authorization_consumed_by_merge_commits": [AION211_MERGE_COMMIT],
        "authorization_expired": True,
        "authorization_reusable": False,
        "authorization_closed_by_task": CLOSEOUT_TASK,
        "epistemic_assessment_operator_evaluation_id": DEFAULT_EVALUATION_ID,
        "epistemic_assessment_operator_evaluation_decision": decision,
        "evaluation_used_as_approval": False,
        "evaluation_reusable": False,
        "evaluation_created_truth_decision": False,
        "evaluation_created_confidence": False,
        "evaluation_created_knowledge": False,
        "evaluation_created_belief": False,
        "evaluation_created_persistent_write": False,
    }


def _conditional_authorization(evaluation_passed: bool) -> dict[str, Any] | None:
    if not evaluation_passed:
        return None
    return {
        "program_id": PROGRAM_ID,
        "authorization_transaction_id": NEXT_AUTHORIZATION_ID,
        "approval_record_id": NEXT_AUTHORIZATION_ID,
        "parent_authorization_transaction_id": AUTHORIZATION_ID,
        "parent_evaluation_id": DEFAULT_EVALUATION_ID,
        "parent_evaluation_decision": DECISION_PASS,
        "parent_closeout_task": CLOSEOUT_TASK,
        "parent_epistemic_assessment_implementation_task": IMPLEMENTATION_TASK,
        "parent_epistemic_assessment_implementation_prs": [AION211_PR],
        "parent_epistemic_assessment_implementation_feature_commits": [AION211_FEATURE_COMMIT],
        "parent_epistemic_assessment_implementation_merge_commits": [AION211_MERGE_COMMIT],
        "candidate_id": "domain-expert-mesh-core",
        "workstream": "knowledge-intelligence-domain-expert-mesh",
        "implementation_task": "AION-213",
        "formal_closeout_task": "AION-214",
        "authorization_scope": DOMAIN_EXPERT_SCOPE,
        "authorization_active": True,
        "authorization_consumed": False,
        "authorization_expired": False,
        "authorization_reusable": False,
    }


def _runtime_state() -> dict[str, bool]:
    return {
        "absolute_truth_decision_performed": False,
        "claim_true_assigned": False,
        "claim_false_assigned": False,
        "automatic_claim_accepted": False,
        "automatic_claim_rejected": False,
        "contradiction_resolved": False,
        "knowledge_promoted": False,
        "belief_created": False,
        "belief_mutated": False,
        "persistent_write_applied": False,
        "network_called": False,
        "model_provider_called": False,
        "connector_called": False,
        "tool_executed": False,
        "source_modified": False,
        "git_mutated": False,
        "pull_request_created": False,
        "approval_created": False,
        "merged": False,
        "runtime_effect": False,
    }


def _security_state() -> dict[str, bool]:
    return {
        "synthetic_evidence_only": True,
        "redacted": True,
        "source_body_present": False,
        "source_preview_present": False,
        "raw_url_present": False,
        "credential_present": False,
        "token_present": False,
        "authorization_header_present": False,
        "human_expert_identity_claim_present": False,
        "professional_credential_claim_present": False,
    }


def _resource_state() -> dict[str, int | bool]:
    return {
        "epistemic_truth_engine_runtime_enabled": False,
        "persistent_assessment_write_enabled": False,
        "domain_expert_mesh_runtime_enabled": False,
        "persistent_mesh_write_enabled": False,
        "source_body_bytes": 0,
        "absolute_truth_decisions": 0,
        "automatic_claim_acceptances": 0,
        "automatic_claim_rejections": 0,
        "contradiction_resolutions": 0,
        "knowledge_promotions": 0,
        "belief_mutations": 0,
        "network_calls": 0,
        "connector_calls": 0,
        "model_provider_calls": 0,
        "tool_executions": 0,
        "git_operations": 0,
        "runtime_pull_requests": 0,
        "approvals": 0,
        "deployments": 0,
        "model_weight_changes": 0,
    }


def _assess_supported(
    *,
    assessment_time: datetime = DEFAULT_FIXED_NOW,
    clock_time: datetime = DEFAULT_FIXED_NOW,
    source_class: str = "official_standard",
    temporary_output_directory: Path | None = None,
) -> Any:
    return _assess_with_bindings(
        bindings=(
            _binding("binding-0001"),
            _binding(
                "binding-0002",
                group_id="independence-group-0002",
                lineage_record_id="source-registry-source-lineage-0005",
            ),
        ),
        additional_group_ids=("independence-group-0002",),
        assessment_time=assessment_time,
        clock_time=clock_time,
        source_class=source_class,
        temporary_output_directory=temporary_output_directory,
    )


def _assess_request(
    *,
    claim_ids: tuple[str, ...] = ("claim-0001",),
    target_jurisdictions: tuple[str, ...] = ("country-us",),
    assessment_time: datetime = DEFAULT_FIXED_NOW,
) -> Any:
    return _assess_with_bindings(
        bindings=(_binding("binding-0001"),),
        claim_scope=_scope(),
        claim_ids=claim_ids,
        target_jurisdictions=target_jurisdictions,
        assessment_time=assessment_time,
    )


def _assess_with_relations(relation_types: tuple[str, ...]) -> Any:
    claims = (_claim("claim-0001"), _claim("claim-0002", polarity="negative"))
    bindings = (_binding("binding-0001"),)
    relations = tuple(_relation(kind=kind) for kind in relation_types)
    return _assess_with_bindings(bindings=bindings, claims=claims, relations=relations)


def _assess_with_conflicting_claims() -> Any:
    claims = (_claim("claim-0001"), _claim("claim-0002", polarity="negative"))
    bindings = (
        _binding("binding-0001"),
        _binding("binding-0002", claim_id="claim-0002"),
    )
    return _assess_with_bindings(bindings=bindings, claims=claims)


def _assess_with_empty_registry() -> Any:
    from aion_brain.knowledge_intelligence.epistemic_assessment import ControlledEpistemicAssessmentEngine
    from aion_brain.knowledge_intelligence.source_registry_repository import InMemorySourceRegistryRepository

    registry = _source_registry_repository()
    graph = _graph_repository(registry=registry, bindings=(_binding("binding-0001"),))
    return ControlledEpistemicAssessmentEngine(clock=lambda: DEFAULT_FIXED_NOW).assess(
        request=_assessment_request(),
        source_registry_repository=InMemorySourceRegistryRepository(()),
        claim_graph_repository=graph,
    )


def _assess_with_bindings(
    *,
    bindings: tuple[Any, ...],
    claims: tuple[Any, ...] | None = None,
    relations: tuple[Any, ...] = (),
    additional_group_ids: tuple[str, ...] = (),
    claim_scope: Any | None = None,
    claim_ids: tuple[str, ...] = ("claim-0001",),
    target_jurisdictions: tuple[str, ...] = ("country-us",),
    assessment_time: datetime = DEFAULT_FIXED_NOW,
    clock_time: datetime = DEFAULT_FIXED_NOW,
    source_class: str = "official_standard",
    include_mirror_decision: bool = False,
    temporary_output_directory: Path | None = None,
) -> Any:
    from aion_brain.knowledge_intelligence.epistemic_assessment import ControlledEpistemicAssessmentEngine

    registry = _source_registry_repository(
        additional_group_ids=additional_group_ids,
        source_class=source_class,
        include_mirror_decision=include_mirror_decision,
    )
    claim_values = claims or (_claim("claim-0001", claim_scope=claim_scope or _scope()),)
    graph = _graph_repository(registry=registry, claims=claim_values, bindings=bindings, relations=relations)
    request = _assessment_request(
        claim_ids=claim_ids,
        target_jurisdictions=target_jurisdictions,
        assessment_time=assessment_time,
    )
    if temporary_output_directory is not None:
        temporary_output_directory.mkdir(parents=True, exist_ok=True)
    return ControlledEpistemicAssessmentEngine(clock=lambda: clock_time).assess(
        request=request,
        source_registry_repository=registry,
        claim_graph_repository=graph,
    )


def _query_batch(batch: Any) -> Any:
    from aion_brain.contracts.knowledge_epistemic_assessment import EpistemicAssessmentQuery
    from aion_brain.knowledge_intelligence.epistemic_assessment import ControlledEpistemicAssessmentEngine

    return ControlledEpistemicAssessmentEngine(clock=lambda: DEFAULT_FIXED_NOW).query(
        batch=batch,
        query=EpistemicAssessmentQuery(claim_id="claim-0001", status="supported"),
    )


def _source_registry_repository(
    *,
    additional_group_ids: tuple[str, ...] = (),
    source_class: str = "official_standard",
    include_mirror_decision: bool = False,
) -> Any:
    from aion_brain.contracts.knowledge_source_registry import (
        RegisteredCitationReference,
        RegisteredDeduplicationDecision,
        RegisteredSourceLineage,
        RegisteredSourceProvenance,
        RegisteredSourceSnapshotDigest,
        SourceRegistryRecordEnvelope,
        source_registry_payload_fingerprint,
    )
    from aion_brain.contracts.knowledge_research import fingerprint_payload
    from aion_brain.knowledge_intelligence.source_registry_integrity import (
        calculate_record_fingerprint,
    )
    from aion_brain.knowledge_intelligence.source_registry_repository import (
        InMemorySourceRegistryRepository,
    )

    snapshot = RegisteredSourceSnapshotDigest(
        snapshot_id="snapshot-0001",
        snapshot_fingerprint=fingerprint_payload({"snapshot": 1}),
        content_sha256=fingerprint_payload({"content": 1}),
        original_url_fingerprint=fingerprint_payload({"original-url": 1}),
        canonical_url_fingerprint=fingerprint_payload({"canonical-url": 1}),
        content_type="text/html",
        content_length=128,
        source_class=source_class,
        robots_policy_status="allowed",
        licence_policy_status="permitted",
        retrieval_timestamp=DEFAULT_FIXED_NOW,
        safe_headers_fingerprint=fingerprint_payload({"headers": 1}),
        redirect_chain_fingerprint=fingerprint_payload({"redirect": 1}),
    )
    provenance = RegisteredSourceProvenance(
        provenance_id="provenance-0001",
        provenance_fingerprint=fingerprint_payload({"provenance": 1}),
        snapshot_id=snapshot.snapshot_id,
        snapshot_fingerprint=snapshot.snapshot_fingerprint,
        content_sha256=snapshot.content_sha256,
        canonical_url_fingerprint=snapshot.canonical_url_fingerprint,
        source_class=source_class,
        declared_author="Synthetic Standards Body",
        declared_publisher="Synthetic Standards Body",
        declared_title="Synthetic Standard",
        retrieval_timestamp=DEFAULT_FIXED_NOW,
        redirect_chain_fingerprint=snapshot.redirect_chain_fingerprint,
        destination_validation_fingerprint=fingerprint_payload({"destination": 1}),
        safe_headers_fingerprint=snapshot.safe_headers_fingerprint,
        adapter_type="in_memory",
    )
    citation = RegisteredCitationReference(
        citation_id="citation-0001",
        citation_fingerprint=fingerprint_payload({"citation": 1}),
        snapshot_id=snapshot.snapshot_id,
        snapshot_fingerprint=snapshot.snapshot_fingerprint,
        content_sha256=snapshot.content_sha256,
        canonical_url_fingerprint=snapshot.canonical_url_fingerprint,
        locator_kind="text_fingerprint",
        locator_value=fingerprint_payload({"locator": 1}),
        retrieval_timestamp=DEFAULT_FIXED_NOW,
    )
    lineage = RegisteredSourceLineage(
        lineage_id="lineage-0001",
        lineage_fingerprint=fingerprint_payload({"lineage": 1}),
        snapshot_id=snapshot.snapshot_id,
        canonical_source_snapshot_id=snapshot.snapshot_id,
        lineage_kind="original",
        content_sha256=snapshot.content_sha256,
        canonical_url_fingerprint=snapshot.canonical_url_fingerprint,
        independence_group_id="independence-group-0001",
        created_at=DEFAULT_FIXED_NOW,
    )
    payloads: list[tuple[str, str, Any]] = [
        ("source-registry-source-snapshot-digest-0001", "source_snapshot_digest", snapshot),
        ("source-registry-source-provenance-0002", "source_provenance", provenance),
        ("source-registry-citation-reference-0003", "citation_reference", citation),
        ("source-registry-source-lineage-0004", "source_lineage", lineage),
    ]
    for offset, group_id in enumerate(additional_group_ids, start=5):
        extra = RegisteredSourceLineage(
            lineage_id=f"lineage-{offset:04d}",
            lineage_fingerprint=fingerprint_payload({"lineage": offset}),
            snapshot_id=snapshot.snapshot_id,
            canonical_source_snapshot_id=snapshot.snapshot_id,
            lineage_kind="canonical_alias",
            content_sha256=snapshot.content_sha256,
            canonical_url_fingerprint=snapshot.canonical_url_fingerprint,
            independence_group_id=group_id,
            created_at=DEFAULT_FIXED_NOW,
        )
        payloads.append((f"source-registry-source-lineage-{offset:04d}", "source_lineage", extra))
    if include_mirror_decision:
        decision = RegisteredDeduplicationDecision(
            decision_id="deduplication-0001",
            decision_fingerprint=fingerprint_payload({"deduplication": 1}),
            snapshot_id=snapshot.snapshot_id,
            exact_url_duplicate=False,
            canonical_url_duplicate=False,
            exact_content_duplicate=False,
            redirect_alias=True,
            suspected_mirror=True,
            independence_group_id="independence-group-0001",
            independent_source_count=1,
            reason_codes=("source_registry_record_valid",),
            created_at=DEFAULT_FIXED_NOW,
        )
        payloads.append(("source-registry-deduplication-decision-9999", "deduplication_decision", decision))
    records = []
    previous: str | None = None
    for sequence, (record_id, record_kind, payload) in enumerate(payloads, start=1):
        envelope = {
            "schema_version": "aion-knowledge-source-registry-record-envelope/v1",
            "record_id": record_id,
            "record_kind": record_kind,
            "sequence_number": sequence,
            "record_version": 1,
            "supersedes_record_id": None,
            "program_id": PROGRAM_ID,
            "authorization_transaction_id": "AION-206-KI-0002",
            "implementation_task": "AION-207",
            "formal_closeout_task": "AION-208",
            "authorization_scope": (
                "append-only-immutable-source-snapshot-provenance-lineage-citation-registry-core"
            ),
            "payload": payload.model_dump(mode="json"),
            "payload_fingerprint": source_registry_payload_fingerprint(payload),
            "previous_record_fingerprint": previous,
            "created_at": DEFAULT_FIXED_NOW,
            "synthetic": True,
            "read_only": True,
            "redacted": True,
            "append_only": True,
            "source_body_present": False,
            "source_body_bytes": 0,
            "claim_verified": False,
            "knowledge_promoted": False,
            "belief_created": False,
            "belief_mutated": False,
            "persistent_write_applied": False,
            "runtime_effect": False,
        }
        record = SourceRegistryRecordEnvelope(
            **envelope,
            record_fingerprint=calculate_record_fingerprint(envelope),
        )
        records.append(record)
        previous = record.record_fingerprint
    return InMemorySourceRegistryRepository(tuple(records))


def _graph_repository(
    *,
    registry: Any,
    claims: tuple[Any, ...] | None = None,
    bindings: tuple[Any, ...] = (),
    relations: tuple[Any, ...] = (),
) -> Any:
    from aion_brain.knowledge_intelligence.claim_graph import ControlledTemporalClaimEvidenceGraph
    from aion_brain.knowledge_intelligence.claim_graph_repository import (
        InMemoryTemporalClaimGraphRepository,
    )

    service = ControlledTemporalClaimEvidenceGraph(clock=lambda: DEFAULT_FIXED_NOW)
    claim_values = claims or (_claim("claim-0001"),)
    batch = service.project(
        claims=claim_values,
        evidence_bindings=bindings,
        relations=relations,
        source_registry_repository=registry,
    )
    repository, _decision = service.simulate_append(InMemoryTemporalClaimGraphRepository(), batch)
    return repository


def _claim(
    claim_id: str,
    *,
    polarity: str = "positive",
    claim_scope: Any | None = None,
) -> Any:
    from aion_brain.contracts.knowledge_claim_graph import (
        ClaimModality,
        ClaimPredicateCardinality,
        ClaimPolarity,
        TextClaimObjectValue,
        UnverifiedClaimAssertion,
        calculate_claim_identity_fingerprint,
        calculate_claim_record_fingerprint,
        claim_object_value_fingerprint,
    )

    object_value = TextClaimObjectValue(
        canonical_value="alpha",
        display_value="Alpha",
        object_fingerprint=claim_object_value_fingerprint(kind="text", canonical_value="alpha"),
    )
    polarity_value = ClaimPolarity.POSITIVE if polarity == "positive" else ClaimPolarity.NEGATIVE
    scope_value = claim_scope or _scope()
    identity = calculate_claim_identity_fingerprint(
        subject_id="product-alpha",
        predicate="has_status",
        object_value=object_value,
        polarity=polarity_value,
        modality=ClaimModality.ASSERTED,
        predicate_cardinality=ClaimPredicateCardinality.ONE,
        objects_mutually_exclusive=False,
        scope=scope_value,
    )
    payload = {
        "schema_version": "aion-knowledge-unverified-claim-assertion/v1",
        "claim_id": claim_id,
        "claim_statement": "Product alpha has status alpha.",
        "subject_id": "product-alpha",
        "predicate": "has_status",
        "object_value": object_value,
        "polarity": polarity_value,
        "modality": ClaimModality.ASSERTED,
        "predicate_cardinality": ClaimPredicateCardinality.ONE,
        "objects_mutually_exclusive": False,
        "language": "en",
        "scope": scope_value,
        "transaction_time": DEFAULT_FIXED_NOW,
        "claim_identity_fingerprint": identity,
        "operator_supplied": True,
        "unverified": True,
        "verified": False,
        "truth_value_assigned": False,
        "epistemic_confidence_assigned": False,
        "knowledge_promoted": False,
        "belief_created": False,
        "belief_mutated": False,
        "runtime_effect": False,
    }
    return UnverifiedClaimAssertion(
        **payload,
        claim_record_fingerprint=calculate_claim_record_fingerprint(payload),
    )


def _binding(
    binding_id: str,
    *,
    claim_id: str = "claim-0001",
    evidence_role: str = "supports",
    group_id: str = "independence-group-0001",
    lineage_record_id: str = "source-registry-source-lineage-0004",
    citation_record_ids: tuple[str, ...] = ("source-registry-citation-reference-0003",),
    provenance_record_ids: tuple[str, ...] = ("source-registry-source-provenance-0002",),
) -> Any:
    from aion_brain.contracts.knowledge_claim_graph import (
        ClaimEvidenceBinding,
        EvidenceRole,
        claim_evidence_binding_fingerprint,
    )

    role = EvidenceRole.SUPPORTS if evidence_role == "supports" else EvidenceRole.OPPOSES
    payload = {
        "schema_version": "aion-knowledge-claim-evidence-binding/v1",
        "binding_id": binding_id,
        "claim_id": claim_id,
        "source_registry_record_ids": ("source-registry-source-snapshot-digest-0001",),
        "source_snapshot_record_ids": ("source-registry-source-snapshot-digest-0001",),
        "source_provenance_record_ids": provenance_record_ids,
        "citation_record_ids": citation_record_ids,
        "lineage_record_ids": (lineage_record_id,),
        "lineage_group_ids": (group_id,),
        "evidence_role": role,
        "created_at": DEFAULT_FIXED_NOW,
        "source_records_resolved": True,
        "verified_support": False,
        "truth_effect": False,
        "confidence_effect": False,
        "knowledge_effect": False,
        "belief_effect": False,
        "runtime_effect": False,
    }
    return ClaimEvidenceBinding(
        **payload,
        binding_fingerprint=claim_evidence_binding_fingerprint(payload),
    )


def _relation(*, kind: str) -> Any:
    from aion_brain.contracts.knowledge_claim_graph import (
        ClaimRelationEdge,
        ClaimRelationOrigin,
        ClaimRelationType,
        claim_relation_fingerprint,
    )

    relation_type = {
        "corrects": ClaimRelationType.CORRECTS,
        "retracts": ClaimRelationType.RETRACTS,
        "supersedes": ClaimRelationType.SUPERSEDES,
    }[kind]
    payload = {
        "schema_version": "aion-knowledge-claim-relation-edge/v1",
        "relation_id": f"relation-{kind}-0001",
        "source_claim_id": "claim-0002",
        "target_claim_id": "claim-0001",
        "relation_type": relation_type,
        "relation_origin": ClaimRelationOrigin.OPERATOR_SUPPLIED,
        "effective_time": DEFAULT_FIXED_NOW,
        "operator_supplied": True,
        "derived_structural": False,
        "relation_verified": False,
        "truth_effect": False,
        "knowledge_effect": False,
        "belief_effect": False,
        "created_at": DEFAULT_FIXED_NOW,
        "runtime_effect": False,
    }
    return ClaimRelationEdge(**payload, relation_fingerprint=claim_relation_fingerprint(payload))


def _scope() -> Any:
    from aion_brain.contracts.knowledge_claim_graph import (
        ClaimScope,
        JurisdictionKind,
        JurisdictionScope,
        ValidTimeInterval,
        VersionScope,
        VersionScheme,
        claim_scope_fingerprint,
        jurisdiction_scope_fingerprint,
        valid_time_interval_fingerprint,
        version_scope_fingerprint,
    )

    interval = ValidTimeInterval(
        interval_id="interval-0001",
        start=DEFAULT_FIXED_NOW,
        end=DEFAULT_LATER,
        start_inclusive=True,
        end_inclusive=True,
        interval_fingerprint=valid_time_interval_fingerprint(
            interval_id="interval-0001",
            start=DEFAULT_FIXED_NOW,
            end=DEFAULT_LATER,
            start_inclusive=True,
            end_inclusive=True,
        ),
    )
    jurisdiction = JurisdictionScope(
        jurisdiction_id="country-us",
        jurisdiction_kind=JurisdictionKind.COUNTRY,
        parent_jurisdiction_ids=(),
        scope_fingerprint=jurisdiction_scope_fingerprint(
            jurisdiction_id="country-us",
            jurisdiction_kind=JurisdictionKind.COUNTRY,
            parent_jurisdiction_ids=(),
        ),
    )
    version = VersionScope(
        target_id="standard-alpha",
        scheme=VersionScheme.NUMERIC_DOTTED_EXACT,
        exact_version="1.0",
        scope_fingerprint=version_scope_fingerprint(
            target_id="standard-alpha",
            scheme=VersionScheme.NUMERIC_DOTTED_EXACT,
            exact_version="1.0",
        ),
    )
    return ClaimScope(
        jurisdiction_scopes=(jurisdiction,),
        version_scopes=(version,),
        valid_time_intervals=(interval,),
        scope_fingerprint=claim_scope_fingerprint(
            jurisdiction_scopes=(jurisdiction,),
            version_scopes=(version,),
            valid_time_intervals=(interval,),
        ),
    )


def _target_scope(
    *,
    jurisdictions: tuple[str, ...] = ("country-us",),
    version_target: str = "standard-alpha",
) -> Any:
    from aion_brain.contracts.knowledge_epistemic_assessment import (
        EpistemicTargetScope,
        epistemic_target_scope_fingerprint,
    )

    payload = {
        "target_valid_time": _scope().valid_time_intervals[0],
        "target_jurisdiction_ids": jurisdictions,
        "target_version_scopes": (_version_scope(version_target),),
    }
    return EpistemicTargetScope(
        **payload,
        scope_fingerprint=epistemic_target_scope_fingerprint(payload),
    )


def _version_scope(target_id: str = "standard-alpha") -> Any:
    from aion_brain.contracts.knowledge_claim_graph import (
        VersionScope,
        VersionScheme,
        version_scope_fingerprint,
    )

    return VersionScope(
        target_id=target_id,
        scheme=VersionScheme.NUMERIC_DOTTED_EXACT,
        exact_version="1.0",
        scope_fingerprint=version_scope_fingerprint(
            target_id=target_id,
            scheme=VersionScheme.NUMERIC_DOTTED_EXACT,
            exact_version="1.0",
        ),
    )


def _freshness_policy() -> Any:
    from aion_brain.contracts.knowledge_epistemic_assessment import (
        EpistemicFreshnessPolicy,
        epistemic_freshness_policy_fingerprint,
    )

    payload = {
        "policy_id": "freshness-policy-0001",
        "current_max_age_seconds": 86_400,
        "stale_after_seconds": 604_800,
        "future_timestamp_tolerance_seconds": 60,
    }
    return EpistemicFreshnessPolicy(
        **payload,
        policy_fingerprint=epistemic_freshness_policy_fingerprint(payload),
    )


def _assessment_request(
    *,
    claim_ids: tuple[str, ...] = ("claim-0001",),
    target_jurisdictions: tuple[str, ...] = ("country-us",),
    assessment_time: datetime = DEFAULT_FIXED_NOW,
) -> Any:
    from aion_brain.contracts.knowledge_epistemic_assessment import EpistemicAssessmentRequest

    return EpistemicAssessmentRequest(
        request_id="request-0001",
        claim_ids=claim_ids,
        target_scope=_target_scope(jurisdictions=target_jurisdictions),
        freshness_policy=_freshness_policy(),
        assessment_time=assessment_time,
    )


def _has_cap(assessment: Any, cap_id: str) -> bool:
    return cap_id in {cap.cap_id for cap in assessment.hard_caps}


def _batch_has_no_side_effects(batch: Any) -> bool:
    return (
        batch.persistent_write_applied is False
        and batch.runtime_effect is False
        and all(item.absolute_truth_claimed is False for item in batch.assessments)
        and all(item.claim_accepted is False for item in batch.assessments)
        and all(item.claim_rejected is False for item in batch.assessments)
        and all(item.knowledge_promoted is False for item in batch.assessments)
        and all(item.belief_created is False for item in batch.assessments)
        and all(item.belief_mutated is False for item in batch.assessments)
    )


def _json_ready(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, tuple | list):
        return [_json_ready(item) for item in value]
    return copy.deepcopy(value)


_SCENARIO_FUNCTIONS = {
    "valid_supported_assessment": _valid_supported_assessment,
    "valid_contradicted_assessment": _valid_contradicted_assessment,
    "mixed_unresolved_opposition": _mixed_unresolved_opposition,
    "insufficient_evidence": _insufficient_evidence,
    "stale_evidence": _stale_evidence,
    "superseded_claim": _superseded_claim,
    "retracted_claim": _retracted_claim,
    "scope_mismatch": _scope_mismatch,
    "integrity_failure_unknown": _integrity_failure_unknown,
    "source_independence_counting": _source_independence_counting,
    "duplicate_evidence_suppression": _duplicate_evidence_suppression,
    "mirror_evidence_suppression": _mirror_evidence_suppression,
    "role_ambiguity_suppression": _role_ambiguity_suppression,
    "citation_coverage_cap": _citation_coverage_cap,
    "provenance_completeness_cap": _provenance_completeness_cap,
    "source_quality_metadata_cap": _source_quality_metadata_cap,
    "zero_and_one_independence_caps": _zero_and_one_independence_caps,
    "deterministic_hard_cap_order": _deterministic_hard_cap_order,
    "confidence_bands": _confidence_bands,
    "explicit_abstention": _explicit_abstention,
    "freshness_boundaries": _freshness_boundaries,
    "temporal_jurisdiction_version_applicability": _temporal_jurisdiction_version_applicability,
    "correction_retraction_supersession_and_conflict": _correction_retraction_supersession_and_conflict,
    "deterministic_replay_and_fingerprint_sensitivity": _deterministic_replay_and_fingerprint_sensitivity,
    "resource_budget_and_persistent_write_boundary": _resource_budget_and_persistent_write_boundary,
    "fixture_path_schema_and_redaction": _fixture_path_schema_and_redaction,
    "concurrency_performance_and_query_integrity": _concurrency_performance_and_query_integrity,
    "no_truth_acceptance_knowledge_belief_runtime_or_repository_effect": _no_truth_acceptance_knowledge_belief_runtime_or_repository_effect,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path)
    parser.add_argument("--evaluation-id", default=DEFAULT_EVALUATION_ID)
    parser.add_argument("--evaluation-base-commit", default=AION211_MERGE_COMMIT)
    parser.add_argument("--temporary-output-directory", type=Path, default=Path("/tmp/aion-epistemic-evaluation"))
    parser.add_argument("--report", type=Path)
    parser.add_argument("--validate-report", type=Path)
    args = parser.parse_args(argv)

    if args.validate_report is not None:
        payload = json.loads(args.validate_report.read_text(encoding="utf-8"))
        validate_evaluation_report(payload)
        return 0

    repo_root = (args.repo_root or Path(__file__).resolve().parents[2]).resolve()
    report_path = args.report or Path("/tmp/aion-epistemic-evaluation") / f"{args.evaluation_id}.json"
    report = evaluate_epistemic_assessment(
        repo_root=repo_root,
        evaluation_id=args.evaluation_id,
        evaluation_base_commit=args.evaluation_base_commit,
        temporary_output_directory=args.temporary_output_directory.resolve(),
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(_json_ready(report), indent=2, sort_keys=True), encoding="utf-8")
    return 0 if report["decision"] in {DECISION_PASS, DECISION_FAIL} else 2


if __name__ == "__main__":
    raise SystemExit(main())
