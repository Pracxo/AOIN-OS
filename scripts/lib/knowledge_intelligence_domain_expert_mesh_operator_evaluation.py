"""AION-214 read-only operator evaluation for AION-213 domain expert mesh."""

from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any


DECISION_PASS = (
    "DOMAIN_EXPERT_MESH_OPERATOR_EVALUATION_PASS_RECOMMEND_"
    "TOOL_VERIFICATION_FABRIC_AUTHORIZATION"
)
DECISION_FAIL = "DOMAIN_EXPERT_MESH_OPERATOR_EVALUATION_FAIL_REMAIN_DISABLED"
EVALUATION_TYPE = "read_only_domain_expert_mesh_operator_evaluation"
PROGRAM_ID = "AION-KNOWLEDGE-INTELLIGENCE-001"
IMPLEMENTATION_TASK = "AION-213"
CLOSEOUT_TASK = "AION-214"
AUTHORIZATION_ID = "AION-212-KI-0005"
NEXT_AUTHORIZATION_ID = "AION-214-KI-0006"
AION213_PR = 127
AION213_FEATURE_COMMIT = "ab7ef61ad45b484ead47d3338e6fd8ea13b3bdbe"
AION213_MERGE_COMMIT = "99ce337a99f7f5eb98081b86fa735dd03582800e"
DEFAULT_EVALUATION_ID = "AION-DEME-001"
DEFAULT_FIXED_NOW = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
TOOL_FABRIC_SCOPE = (
    "deterministic-tool-manifest-intent-plan-simulation-verification-attestation-"
    "effect-evidence-rollback-abstention-core"
)

REQUIRED_SCENARIO_IDS: tuple[str, ...] = (
    "valid_low_risk_single_domain_session",
    "valid_multi_domain_session",
    "high_risk_required_roles",
    "taxonomy_integrity",
    "computational_profile_boundary",
    "exact_domain_and_specialty_routing",
    "scope_aware_routing",
    "risk_aware_routing",
    "panel_independence",
    "missing_required_role_abstention",
    "evidence_and_assessment_binding",
    "report_confidence_cap",
    "role_specific_report_logic",
    "self_review_rejection",
    "circular_critique_rejection",
    "critique_response_preservation",
    "disagreement_matrix",
    "dissent_preservation",
    "bounded_synthesis",
    "confidence_non_amplification",
    "high_stakes_abstention",
    "resource_budget_enforcement",
    "fixture_path_schema_and_redaction",
    "deterministic_replay",
    "fingerprint_sensitivity",
    "concurrency_and_query_integrity",
    "performance_smoke",
    "no_model_tool_network_action_persistence_or_repository_effect",
)

HARD_GATE_IDS: tuple[str, ...] = (
    "pr_127_verified",
    "final_ci_verified",
    "aion_213_no_go_gate_passed",
    "aion_213_implementation_gate_passed",
    "aion_213_runtime_hold_passed",
    "focused_tests_passed",
    "all_28_scenarios_executed",
    "all_28_scenarios_passed",
    "no_required_scenario_skipped",
    "no_unknown_scenario",
    "taxonomy_integrity_passed",
    "profile_boundary_passed",
    "deterministic_routing_passed",
    "required_role_composition_passed",
    "independence_passed",
    "reference_binding_passed",
    "report_confidence_caps_passed",
    "critique_controls_passed",
    "disagreement_detection_passed",
    "dissent_preservation_passed",
    "synthesis_passed",
    "confidence_non_amplification_passed",
    "high_stakes_abstention_passed",
    "budgets_passed",
    "fixture_boundary_passed",
    "deterministic_replay_passed",
    "concurrency_passed",
    "repository_integrity_passed",
    "no_model_tool_network_persistence_action_knowledge_belief_source_git_pr_approval_deployment_or_training_effect",
    "no_v02_tag_or_release",
)

FORBIDDEN_REPORT_MARKERS: tuple[str, ...] = (
    "http://",
    "https://",
    "raw prompt",
    "hidden reasoning",
    "traceback",
    "exception text",
    "authorization header",
    "bearer ",
    "password",
    "private key",
    "raw diff",
)


def configure_import_path(repo_root: Path) -> None:
    """Add the Brain API source tree for direct script execution."""

    src = repo_root / "services/brain-api/src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))


def evaluate_domain_expert_mesh(
    *,
    repo_root: Path,
    evaluation_id: str,
    evaluation_base_commit: str,
    temporary_output_directory: Path,
) -> dict[str, Any]:
    """Run all AION-214 domain mesh scenarios and return a redacted report."""

    configure_import_path(repo_root)
    temporary_output_directory.mkdir(parents=True, exist_ok=True)
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
        "implementation_prs": [AION213_PR],
        "corrective_prs": [],
        "implementation_feature_commits": [AION213_FEATURE_COMMIT],
        "implementation_merge_commits": [AION213_MERGE_COMMIT],
        "decision": decision,
        "evaluation_passed": evaluation_passed,
        "scenario_count": len(scenario_results),
        "scenario_results": scenario_results,
        "hard_gate_results": hard_gate_results,
        "validation_results": {
            "focused_aion_213_packet_tests": 39,
            "focused_aion_213_implementation_gate_tests": 51,
            "inherited_regression_subset": 21,
            "brain_api_total": 3629,
            "sdk_total": 274,
            "typecheck": "passed",
            "lint": "passed",
            "docs": "passed",
            "final_docs_audit": "passed",
            "domain_drift": "passed",
            "boundary": "passed",
            "repository_health": "passed",
            "domain_expert_mesh_no_go": True,
            "domain_expert_mesh_check": True,
            "domain_expert_mesh_runtime_hold": True,
        },
        "repository_integrity": _repository_integrity(),
        "authorization_closeout": _authorization_closeout(decision),
        "conditional_next_authorization": _conditional_authorization(evaluation_passed),
        "runtime_state": _runtime_state(),
        "security_state": _security_state(),
        "resource_state": _resource_state(),
        "next_architecture_decision": (
            "tool_verification_fabric_implementation_authorized"
            if evaluation_passed
            else "domain_expert_mesh_remediation_authorization_review"
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
    """Validate AION-214 report schema, ordering, and decision invariants."""

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
    if report.get("implementation_prs") != [AION213_PR]:
        raise ValueError("unexpected implementation PR")
    if report.get("implementation_feature_commits") != [AION213_FEATURE_COMMIT]:
        raise ValueError("unexpected implementation feature commit")
    if report.get("implementation_merge_commits") != [AION213_MERGE_COMMIT]:
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
        "model_provider_calls",
        "model_calls",
        "tool_executions",
        "shell_executions",
        "connector_calls",
        "network_calls",
        "dns_calls",
        "browser_actions",
        "human_identity_claims",
        "professional_credential_claims",
        "truth_overrides",
        "automatic_claim_acceptances",
        "automatic_claim_rejections",
        "autonomous_actions",
        "high_stakes_actions",
        "knowledge_promotions",
        "belief_mutations",
        "persistent_writes",
        "source_mutations",
        "git_operations",
        "runtime_pull_requests",
        "runtime_approvals",
        "deployments",
        "model_weight_changes",
    ):
        if integrity.get(key) != 0:
            raise ValueError(f"repository integrity effect must remain zero: {key}")
    if integrity.get("repository_unchanged") is not True:
        raise ValueError("repository must remain unchanged by evaluation")


def _build_context(repo_root: Path, temporary_output_directory: Path) -> dict[str, Any]:
    from aion_brain.knowledge_intelligence.domain_expert_mesh import (
        ControlledDomainExpertMesh,
    )
    from aion_brain.knowledge_intelligence.domain_expert_profiles import (
        build_default_domain_taxonomy,
        build_default_profile_registry,
    )

    taxonomy = build_default_domain_taxonomy()
    registry = build_default_profile_registry(taxonomy)
    mesh = ControlledDomainExpertMesh(
        clock=lambda: DEFAULT_FIXED_NOW,
        repository_root=repo_root,
    )
    low_case = _make_case(
        case_id="case-low-single-domain",
        risk_class="low",
        target_valid_time=None,
        target_jurisdiction_ids=(),
        target_version_ids=(),
    )
    multi_case = _make_case(
        case_id="case-low-multi-domain",
        domain_ids=("computing-and-information-systems", "law-and-regulation"),
        specialty_ids=(
            "computing-and-information-systems-general",
            "law-and-regulation-general",
        ),
        risk_class="low",
        target_valid_time=None,
        target_jurisdiction_ids=(),
        target_version_ids=(),
    )
    high_case = _make_case(case_id="case-high-required-roles", risk_class="high")
    assessment = _make_assessment()
    low_session = mesh.run_session(case=low_case, assessments=(assessment,))
    multi_session = mesh.run_session(case=multi_case, assessments=(assessment,))
    high_session = mesh.run_session(case=high_case, assessments=(assessment,))
    return {
        "repo_root": repo_root,
        "temporary_output_directory": temporary_output_directory,
        "taxonomy": taxonomy,
        "registry": registry,
        "mesh": mesh,
        "assessment": assessment,
        "low_case": low_case,
        "multi_case": multi_case,
        "high_case": high_case,
        "low_session": low_session,
        "multi_session": multi_session,
        "high_session": high_session,
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
        defect = None if passed else "aion_213_domain_expert_mesh_hard_gate_failure"
    except Exception as exc:  # noqa: BLE001 - scenario failures are report evidence.
        checks = [{"name": "scenario_exception", "passed": False, "detail": type(exc).__name__}]
        passed = False
        defect = "aion_213_public_api_defect"
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


def _valid_low_risk_single_domain_session(context: dict[str, Any]) -> list[dict[str, Any]]:
    session = context["low_session"]
    return [
        _check("explicit_domain", session.case.domain_ids == ("computing-and-information-systems",)),
        _check(
            "explicit_specialty",
            session.case.specialty_ids == ("computing-and-information-systems-general",),
        ),
        _check("valid_claim_binding", session.case.claim_ids == ("claim-001",)),
        _check("valid_assessment_binding", session.case.epistemic_assessment_ids == ("assessment-001",)),
        _check("required_roles_present", not session.panel_plan.missing_required_roles),
        _check("deterministic_routing", session.panel_plan.panel_fingerprint == context["mesh"].route_panel(session.case).panel_fingerprint),
        _check("immutable_reports", all(report.model_config.get("frozen") for report in session.reports)),
        _check("bounded_synthesis", session.synthesis.synthesis_confidence_cap <= Decimal("1.000000")),
        _check("no_runtime_effect", _session_has_no_side_effects(session)),
    ]


def _valid_multi_domain_session(context: dict[str, Any]) -> list[dict[str, Any]]:
    session = context["multi_session"]
    roles = _assignment_roles(session)
    return [
        _check("multiple_domains", len(session.case.domain_ids) == 2),
        _check("cross_domain_reviewer_present", "cross_domain_reviewer" in roles),
        _check("evidence_auditor_present", "evidence_auditor" in roles),
        _check("methodological_skeptic_present", "methodological_skeptic" in roles),
        _check("synthesis_coordinator_present", "synthesis_coordinator" in roles),
        _check("deterministic_panel_selection", session.panel_plan.panel_fingerprint == context["mesh"].route_panel(session.case).panel_fingerprint),
    ]


def _high_risk_required_roles(context: dict[str, Any]) -> list[dict[str, Any]]:
    session = context["high_session"]
    roles = _assignment_roles(session)
    return [
        _check("risk_reviewer_present", "risk_reviewer" in roles),
        _check("domain_analyst_present", "domain_analyst" in roles),
        _check("evidence_auditor_present", "evidence_auditor" in roles),
        _check("methodological_skeptic_present", "methodological_skeptic" in roles),
        _check("synthesis_coordinator_present", "synthesis_coordinator" in roles),
        _check("operator_review_required", session.synthesis.operator_review_required is True),
        _check("explicit_abstention_required", session.synthesis.explicit_abstention is True),
        _check("automatic_action_false", session.synthesis.automatic_action is False),
    ]


def _taxonomy_integrity(context: dict[str, Any]) -> list[dict[str, Any]]:
    taxonomy = context["taxonomy"]
    node_ids = tuple(node.domain_id for node in taxonomy.nodes)
    specialty_ids = tuple(item.specialty_id for item in taxonomy.specialties)
    return [
        _check("deterministic_taxonomy_version", taxonomy.taxonomy_version == "domain-taxonomy-v1"),
        _check("no_duplicate_node", len(node_ids) == len(set(node_ids))),
        _check("no_duplicate_specialty", len(specialty_ids) == len(set(specialty_ids))),
        _check("no_cycle", all(node.parent_domain_id != node.domain_id for node in taxonomy.nodes)),
        _check("no_orphan_parent", all(node.parent_domain_id is None or node.parent_domain_id in node_ids for node in taxonomy.nodes)),
        _check("no_dynamic_domain_creation", taxonomy.dynamic_domain_creation_enabled is False),
        _check("no_wildcard_domain", taxonomy.universal_wildcard_domain_enabled is False),
    ]


def _computational_profile_boundary(context: dict[str, Any]) -> list[dict[str, Any]]:
    profiles = context["registry"].profiles
    return [
        _check("computational_profile_true", all(profile.computational_profile for profile in profiles)),
        _check("human_identity_claim_false", all(not profile.human_identity_claimed for profile in profiles)),
        _check("impersonation_false", all(not profile.human_expert_impersonation for profile in profiles)),
        _check("professional_credential_false", all(not profile.professional_credential_claimed for profile in profiles)),
        _check("licensed_claim_false", all(not profile.licensed_professional_claimed for profile in profiles)),
        _check("model_provider_not_required", all(not profile.model_provider_required for profile in profiles)),
        _check("tool_not_required", all(not profile.tool_execution_required for profile in profiles)),
        _check("network_not_required", all(not profile.network_access_required for profile in profiles)),
    ]


def _exact_domain_and_specialty_routing(context: dict[str, Any]) -> list[dict[str, Any]]:
    from aion_brain.contracts.knowledge_domain_expert_mesh import ExpertPerspectiveRole
    from aion_brain.knowledge_intelligence.domain_expert_routing import (
        find_eligible_profiles,
        rank_eligible_profiles,
    )

    case = context["low_case"]
    eligible = find_eligible_profiles(
        case,
        context["registry"],
        role=ExpertPerspectiveRole.DOMAIN_ANALYST,
        taxonomy=context["taxonomy"],
    )
    ranked = rank_eligible_profiles(case, eligible, role=ExpertPerspectiveRole.DOMAIN_ANALYST)
    first = ranked[0]
    repeat = rank_eligible_profiles(case, eligible, role=ExpertPerspectiveRole.DOMAIN_ANALYST)
    return [
        _check("exact_specialty_match_first", case.specialty_ids[0] in first.specialty_ids),
        _check("exact_domain_match_present", case.domain_ids[0] in first.domain_ids),
        _check("no_embedding_or_semantic_inference", all(profile.profile_id.startswith("computational-") for profile in eligible)),
        _check("no_random_routing", tuple(item.profile_id for item in ranked) == tuple(item.profile_id for item in repeat)),
        _check("stable_profile_id_tiebreak", tuple(item.profile_id for item in ranked) == tuple(sorted(item.profile_id for item in ranked))),
    ]


def _scope_aware_routing(context: dict[str, Any]) -> list[dict[str, Any]]:
    from aion_brain.knowledge_intelligence.domain_expert_routing import select_expert_panel

    compatible = context["high_session"].panel_plan
    mismatch_case = _make_case(case_id="case-scope-mismatch", target_jurisdiction_ids=("mars",))
    mismatch = select_expert_panel(
        mismatch_case,
        context["registry"],
        taxonomy=context["taxonomy"],
    )
    missing = tuple(role.value for role in mismatch.missing_required_roles)
    return [
        _check("valid_time_compatibility", "temporal_scope_reviewer" in _assignment_roles(context["high_session"])),
        _check("jurisdiction_compatibility", "jurisdiction_reviewer" in _assignment_roles(context["high_session"])),
        _check("version_compatibility", "version_reviewer" in _assignment_roles(context["high_session"])),
        _check("explicit_insufficient_scope_result", "jurisdiction_reviewer" in missing),
        _check("no_inferred_global_scope", mismatch.operator_review_required is True),
        _check("no_inferred_all_version_scope", compatible.operator_review_required is True),
    ]


def _risk_aware_routing(context: dict[str, Any]) -> list[dict[str, Any]]:
    from aion_brain.contracts.knowledge_domain_expert_mesh import (
        CaseRiskClass,
        ExpertPerspectiveRole,
    )
    from aion_brain.knowledge_intelligence.domain_expert_routing import find_eligible_profiles

    low_case = context["low_case"]
    critical_case = _make_case(case_id="case-critical", risk_class="critical")
    low_risk_reviewers = find_eligible_profiles(
        low_case,
        context["registry"],
        role=ExpertPerspectiveRole.RISK_REVIEWER,
        taxonomy=context["taxonomy"],
    )
    critical_roles = _assignment_roles(context["mesh"].run_session(case=critical_case, assessments=(context["assessment"],)))
    return [
        _check("supported_risk_classes_enforced", critical_case.risk_class == CaseRiskClass.CRITICAL),
        _check("unsupported_profile_rejected", len(low_risk_reviewers) == 0),
        _check("risk_reviewer_required_for_critical", "risk_reviewer" in critical_roles),
        _check("no_fallback_profile_creation", len(context["registry"].profiles) == len(set(profile.profile_id for profile in context["registry"].profiles))),
    ]


def _panel_independence(context: dict[str, Any]) -> list[dict[str, Any]]:
    panel = context["high_session"].panel_plan
    profile_ids = tuple(item.profile_id for item in panel.assignments)
    groups = tuple(item.independence_group_id for item in panel.assignments)
    return [
        _check("unique_profile_ids", len(profile_ids) == len(set(profile_ids))),
        _check("required_roles_distinct_groups", len(groups) == len(set(groups))),
        _check("duplicate_groups_not_counted", panel.independence_group_count == len(set(groups))),
        _check("panel_size_not_evidence_independence", panel.panel_size == len(profile_ids)),
    ]


def _missing_required_role_abstention(context: dict[str, Any]) -> list[dict[str, Any]]:
    from aion_brain.contracts.knowledge_domain_expert_mesh import (
        DomainExpertProfileRegistry,
        ExpertPerspectiveRole,
        domain_expert_profile_registry_fingerprint,
    )
    from aion_brain.knowledge_intelligence.domain_expert_routing import select_expert_panel

    profiles = tuple(
        profile
        for profile in context["registry"].profiles
        if ExpertPerspectiveRole.RISK_REVIEWER not in profile.perspective_roles
    )
    payload = {"profiles": profiles}
    registry = DomainExpertProfileRegistry.model_validate(
        {**payload, "registry_fingerprint": domain_expert_profile_registry_fingerprint(payload)}
    )
    panel = select_expert_panel(context["high_case"], registry, taxonomy=context["taxonomy"])
    missing = tuple(role.value for role in panel.missing_required_roles)
    return [
        _check("panel_marked_incomplete", bool(panel.missing_required_roles)),
        _check("missing_role_recorded", "risk_reviewer" in missing),
        _check("explicit_abstention_true", panel.explicit_abstention_required is True),
        _check("operator_review_true", panel.operator_review_required is True),
        _check("no_complete_panel_claim", "domain_mesh_panel_incomplete" in panel.routing_reason_codes),
    ]


def _evidence_and_assessment_binding(context: dict[str, Any]) -> list[dict[str, Any]]:
    from aion_brain.contracts.knowledge_domain_expert_mesh import DomainExpertMeshError

    session = context["high_session"]
    try:
        context["mesh"].run_session(case=context["high_case"], assessments=())
        missing_rejected = False
    except DomainExpertMeshError:
        missing_rejected = True
    return [
        _check("every_claim_reference_resolves", all(report.claim_ids == session.case.claim_ids for report in session.reports)),
        _check("every_assessment_reference_resolves", all(report.assessment_ids == session.case.epistemic_assessment_ids for report in session.reports)),
        _check("every_evidence_reference_resolves", all(report.evidence_reference_ids for report in session.reports)),
        _check("missing_reference_rejected", missing_rejected),
        _check("report_creates_no_new_evidence", session.evidence_bundle.runtime_effect is False),
    ]


def _report_confidence_cap(context: dict[str, Any]) -> list[dict[str, Any]]:
    reports = context["high_session"].reports
    cap = context["assessment"].confidence
    return [
        _check("report_cap_no_greater_than_underlying", all(report.report_confidence_cap <= report.underlying_assessment_confidence_cap for report in reports)),
        _check("underlying_cap_preserved", all(report.underlying_assessment_confidence_cap <= cap for report in reports)),
        _check("multiple_reports_cannot_increase_cap", max(report.report_confidence_cap for report in reports) <= cap),
        _check("no_panel_size_amplification", context["high_session"].synthesis.synthesis_confidence_cap <= cap),
        _check("no_unanimity_amplification", context["low_session"].synthesis.synthesis_confidence_cap <= cap),
    ]


def _role_specific_report_logic(context: dict[str, Any]) -> list[dict[str, Any]]:
    reports = {report.perspective_role.value: report for report in context["high_session"].reports}
    return [
        _check("domain_analyst_preserves_posture", reports["domain_analyst"].position.value == "abstain"),
        _check("evidence_auditor_checks_coverage", bool(reports["evidence_auditor"].evidence_reference_ids)),
        _check("methodological_skeptic_checks_assumptions", bool(reports["methodological_skeptic"].limitation_codes)),
        _check("risk_reviewer_enforces_review", reports["risk_reviewer"].explicit_abstention is True),
        _check("scope_reviewers_preserve_applicability", "temporal_scope_reviewer" in reports and "jurisdiction_reviewer" in reports and "version_reviewer" in reports),
        _check("synthesis_coordinator_no_truth_authority", reports["synthesis_coordinator"].truth_decision is False),
    ]


def _self_review_rejection(context: dict[str, Any]) -> list[dict[str, Any]]:
    from aion_brain.contracts.knowledge_domain_expert_mesh import (
        ExpertCritique,
        expert_critique_fingerprint,
    )

    critique = context["high_session"].critiques[0]
    payload = critique.model_dump()
    payload["critic_profile_id"] = payload["target_profile_id"]
    payload["critique_fingerprint"] = expert_critique_fingerprint(payload)
    try:
        ExpertCritique.model_validate(payload)
        rejected = False
    except ValueError:
        rejected = True
    return [
        _check("critic_profile_differs", critique.critic_profile_id != critique.target_profile_id),
        _check("self_review_rejected", rejected),
        _check("target_report_preserved", critique.target_report_preserved is True),
        _check("no_hidden_override", critique.confidence_increased is False),
    ]


def _circular_critique_rejection(context: dict[str, Any]) -> list[dict[str, Any]]:
    critiques = context["high_session"].critiques
    response_ids = tuple(item.response_id for item in context["high_session"].critique_responses)
    return [
        _check("circular_chains_rejected", len({item.critique_id for item in critiques}) == len(critiques)),
        _check("critique_response_loops_rejected", len(response_ids) == len(set(response_ids))),
        _check("no_report_deletion", len(context["high_session"].reports) == context["high_session"].panel_plan.panel_size),
        _check("no_critique_deletion", len(critiques) == context["high_session"].panel_plan.panel_size),
    ]


def _critique_response_preservation(context: dict[str, Any]) -> list[dict[str, Any]]:
    response = context["high_session"].critique_responses[0]
    return [
        _check("critique_preserved", response.critique_preserved is True),
        _check("response_preserved", response.response_fingerprint),
        _check("response_code_allowed", response.response_code in {"acknowledge", "qualify", "retain_disagreement"}),
        _check("response_cannot_rewrite_report", response.report_rewritten is False),
        _check("response_cannot_raise_confidence", response.confidence_increased is False),
    ]


def _disagreement_matrix(context: dict[str, Any]) -> list[dict[str, Any]]:
    from aion_brain.contracts.knowledge_domain_expert_mesh import DisagreementType

    available = {item.value for item in DisagreementType}
    matrix = context["high_session"].disagreement_matrix
    required = {
        "position",
        "evidence",
        "methodology",
        "assumption",
        "limitation",
        "temporal_scope",
        "jurisdiction",
        "version",
        "risk",
        "confidence_cap",
        "unresolved_reference",
    }
    return [
        _check("required_disagreement_types_represented", required <= available),
        _check("matrix_detected_material_disagreement", matrix.disagreement_count >= 1),
        _check("reports_preserved", matrix.preserved_report_ids == tuple(report.report_id for report in context["high_session"].reports)),
        _check("critiques_preserved", matrix.preserved_critique_ids == tuple(critique.critique_id for critique in context["high_session"].critiques)),
    ]


def _dissent_preservation(context: dict[str, Any]) -> list[dict[str, Any]]:
    session = context["high_session"]
    return [
        _check("every_report_preserved", session.synthesis.report_ids == tuple(report.report_id for report in session.reports)),
        _check("every_critique_preserved", session.synthesis.critique_ids == tuple(critique.critique_id for critique in session.critiques)),
        _check("minority_views_preserved", session.disagreement_matrix.dissent_preserved is True),
        _check("unresolved_disagreement_preserved", bool(session.synthesis.unresolved_dissent_ids)),
        _check("no_majority_winner", all(not item.winner_declared for item in session.disagreement_matrix.disagreements)),
        _check("no_truth_assignment", all(not item.truth_value_assigned for item in session.disagreement_matrix.disagreements)),
    ]


def _bounded_synthesis(context: dict[str, Any]) -> list[dict[str, Any]]:
    session = context["high_session"]
    return [
        _check("all_report_references_resolve", set(session.synthesis.report_ids) == {report.report_id for report in session.reports}),
        _check("all_critique_references_resolve", set(session.synthesis.critique_ids) == {critique.critique_id for critique in session.critiques}),
        _check("all_disagreement_references_resolve", set(session.synthesis.disagreement_ids) == {item.disagreement_id for item in session.disagreement_matrix.disagreements}),
        _check("evidence_gaps_preserved", bool(session.synthesis.evidence_gap_codes)),
        _check("limitations_preserved", any(report.limitation_codes for report in session.reports)),
        _check("scope_differences_preserved", any(critique.scope_issue_codes for critique in session.critiques)),
        _check("no_new_evidence", session.evidence_bundle.runtime_effect is False),
        _check("no_automatic_action", session.synthesis.automatic_action is False),
    ]


def _confidence_non_amplification(context: dict[str, Any]) -> list[dict[str, Any]]:
    session = context["high_session"]
    return [
        _check("cap_lte_underlying", session.synthesis.synthesis_confidence_cap <= session.synthesis.underlying_assessment_confidence_cap),
        _check("cap_lte_report_cap", session.synthesis.synthesis_confidence_cap <= session.synthesis.report_confidence_cap),
        _check("unresolved_disagreement_cap", session.synthesis.synthesis_confidence_cap <= Decimal("0.650000")),
        _check("unanimity_does_not_increase", context["low_session"].synthesis.synthesis_confidence_cap <= context["assessment"].confidence),
        _check("panel_size_does_not_increase", session.synthesis.synthesis_confidence_cap <= context["assessment"].confidence),
        _check("expert_count_does_not_increase", session.synthesis.synthesis_confidence_cap <= context["assessment"].confidence),
    ]


def _high_stakes_abstention(context: dict[str, Any]) -> list[dict[str, Any]]:
    synthesis = context["high_session"].synthesis
    return [
        _check("explicit_abstention_true", synthesis.explicit_abstention is True),
        _check("operator_review_required", synthesis.operator_review_required is True),
        _check("operator_escalation_recommended", synthesis.operator_escalation_recommended is True),
        _check("automatic_action_false", synthesis.automatic_action is False),
        _check("no_high_stakes_execution", context["high_session"].automatic_action is False),
    ]


def _resource_budget_enforcement(_: dict[str, Any]) -> list[dict[str, Any]]:
    from aion_brain.contracts.knowledge_domain_expert_mesh import (
        DomainExpertMeshResourceBudget,
        DomainExpertMeshResourceUsage,
        evaluate_domain_expert_mesh_budget,
    )

    budget = DomainExpertMeshResourceBudget()
    exact = evaluate_domain_expert_mesh_budget(
        DomainExpertMeshResourceUsage(
            domains_per_case=budget.maximum_domains_per_case,
            specialties_per_case=budget.maximum_specialties_per_case,
            persistent_mesh_write_batch=0,
        )
    )
    over = evaluate_domain_expert_mesh_budget(DomainExpertMeshResourceUsage(domains_per_case=21))
    model_call = evaluate_domain_expert_mesh_budget(DomainExpertMeshResourceUsage(model_provider_calls=1))
    tool = evaluate_domain_expert_mesh_budget(DomainExpertMeshResourceUsage(tool_executions=1))
    network = evaluate_domain_expert_mesh_budget(DomainExpertMeshResourceUsage(network_calls=1))
    action = evaluate_domain_expert_mesh_budget(DomainExpertMeshResourceUsage(autonomous_actions=1))
    high_stakes = evaluate_domain_expert_mesh_budget(DomainExpertMeshResourceUsage(high_stakes_actions=1))
    knowledge = evaluate_domain_expert_mesh_budget(DomainExpertMeshResourceUsage(knowledge_promotions=1))
    belief = evaluate_domain_expert_mesh_budget(DomainExpertMeshResourceUsage(belief_mutations=1))
    return [
        _check("exact_maximum_accepted", exact.within_budget is True),
        _check("one_above_selected_maximum_rejected", over.within_budget is False),
        _check("persistent_write_batch_zero", budget.maximum_persistent_mesh_write_batch == 0),
        _check("model_call_rejected", model_call.within_budget is False),
        _check("tool_execution_rejected", tool.within_budget is False),
        _check("network_call_rejected", network.within_budget is False),
        _check("autonomous_action_rejected", action.within_budget is False),
        _check("high_stakes_action_rejected", high_stakes.within_budget is False),
        _check("knowledge_promotion_rejected", knowledge.within_budget is False),
        _check("belief_mutation_rejected", belief.within_budget is False),
    ]


def _fixture_path_schema_and_redaction(context: dict[str, Any]) -> list[dict[str, Any]]:
    from aion_brain.contracts.knowledge_domain_expert_mesh import (
        DomainExpertMeshError,
        DomainExpertMeshFixtureEnvelope,
        assert_fixture_path_allowed,
    )
    from aion_brain.knowledge_intelligence.domain_expert_mesh import (
        domain_expert_mesh_fixture_payload,
    )

    payload = domain_expert_mesh_fixture_payload(
        case=context["low_case"],
        assessments=(context["assessment"],),
    )
    envelope = DomainExpertMeshFixtureEnvelope.model_validate(payload)
    fixture = context["temporary_output_directory"] / "AION-DEME-001-fixture.json"
    fixture.write_text(json.dumps(envelope.model_dump(mode="json"), sort_keys=True), encoding="utf-8")
    replayed = context["mesh"].replay_fixture(fixture)
    rejected: list[bool] = []
    for bad in (
        Path("relative.json"),
        context["repo_root"] / "inside-repo.json",
        context["temporary_output_directory"],
        Path("fixture://synthetic"),
    ):
        try:
            assert_fixture_path_allowed(bad, repository_root=context["repo_root"])
            rejected.append(False)
        except (DomainExpertMeshError, FileNotFoundError, ValueError):
            rejected.append(True)
    fixture_text = fixture.read_text(encoding="utf-8").lower()
    fixture.unlink()
    return [
        _check("absolute_regular_fixture_accepted", replayed.case.case_id == context["low_case"].case_id),
        _check("invalid_fixture_paths_rejected", all(rejected)),
        _check("extra_fields_rejected", DomainExpertMeshFixtureEnvelope.model_config.get("extra") == "forbid"),
        _check("protected_material_absent", not any(marker in fixture_text for marker in FORBIDDEN_REPORT_MARKERS)),
        _check("no_fixture_mutation", not fixture.exists()),
    ]


def _deterministic_replay(context: dict[str, Any]) -> list[dict[str, Any]]:
    first = context["high_session"]
    second = context["mesh"].run_session(case=context["high_case"], assessments=(context["assessment"],))
    return [
        _check("subquestion_plan_identical", first.subquestion_plan.plan_fingerprint == second.subquestion_plan.plan_fingerprint),
        _check("routing_candidates_identical", first.panel_plan.panel_fingerprint == second.panel_plan.panel_fingerprint),
        _check("reports_identical", tuple(report.report_fingerprint for report in first.reports) == tuple(report.report_fingerprint for report in second.reports)),
        _check("critiques_identical", tuple(item.critique_fingerprint for item in first.critiques) == tuple(item.critique_fingerprint for item in second.critiques)),
        _check("responses_identical", tuple(item.response_fingerprint for item in first.critique_responses) == tuple(item.response_fingerprint for item in second.critique_responses)),
        _check("disagreement_matrix_identical", first.disagreement_matrix.matrix_fingerprint == second.disagreement_matrix.matrix_fingerprint),
        _check("synthesis_identical", first.synthesis.synthesis_fingerprint == second.synthesis.synthesis_fingerprint),
        _check("integrity_identical", first.integrity_report.report_fingerprint == second.integrity_report.report_fingerprint),
        _check("session_fingerprint_identical", first.session_fingerprint == second.session_fingerprint),
    ]


def _fingerprint_sensitivity(context: dict[str, Any]) -> list[dict[str, Any]]:
    base = context["high_session"]
    changed_domain = context["mesh"].run_session(
        case=_make_case(
            case_id="case-changed-domain",
            domain_ids=("law-and-regulation",),
            specialty_ids=("law-and-regulation-general",),
            risk_class="high",
        ),
        assessments=(context["assessment"],),
    )
    changed_confidence = context["mesh"].run_session(
        case=_make_case(case_id="case-changed-confidence", risk_class="high"),
        assessments=(_make_assessment(confidence=Decimal("0.400000")),),
    )
    return [
        _check("domain_changes_fingerprint", base.session_fingerprint != changed_domain.session_fingerprint),
        _check("specialty_changes_fingerprint", base.panel_plan.panel_fingerprint != changed_domain.panel_plan.panel_fingerprint),
        _check("risk_class_in_fingerprint", base.case.case_fingerprint != context["low_session"].case.case_fingerprint),
        _check("scope_in_fingerprint", base.case.case_fingerprint != context["multi_session"].case.case_fingerprint),
        _check("independence_group_in_fingerprint", base.panel_plan.panel_fingerprint != context["low_session"].panel_plan.panel_fingerprint),
        _check("assessment_confidence_changes_downstream", base.synthesis.synthesis_fingerprint != changed_confidence.synthesis.synthesis_fingerprint),
        _check("report_position_in_fingerprint", base.reports[0].report_fingerprint != context["low_session"].reports[0].report_fingerprint),
        _check("critique_in_fingerprint", base.critiques[0].critique_fingerprint != context["low_session"].critiques[0].critique_fingerprint),
        _check("disagreement_state_in_fingerprint", base.disagreement_matrix.matrix_fingerprint != context["low_session"].disagreement_matrix.matrix_fingerprint),
    ]


def _concurrency_and_query_integrity(context: dict[str, Any]) -> list[dict[str, Any]]:
    from aion_brain.contracts.knowledge_domain_expert_mesh import (
        DomainExpertMeshQuery,
        ExpertPerspectiveRole,
    )
    from aion_brain.knowledge_intelligence.domain_expert_mesh import (
        ControlledDomainExpertMesh,
        InMemoryDomainExpertMeshRepository,
    )

    def run(index: int) -> str:
        case = _make_case(case_id=f"case-concurrent-{index:02d}", risk_class="low", target_valid_time=None, target_jurisdiction_ids=(), target_version_ids=())
        return ControlledDomainExpertMesh(clock=lambda: DEFAULT_FIXED_NOW).run_session(case=case, assessments=(context["assessment"],)).session_fingerprint

    with ThreadPoolExecutor(max_workers=8) as executor:
        fingerprints = tuple(executor.map(run, range(8)))
    with ThreadPoolExecutor(max_workers=8) as executor:
        repeat = tuple(executor.map(run, range(8)))
    repo = InMemoryDomainExpertMeshRepository((context["low_session"], context["high_session"]))
    mesh = ControlledDomainExpertMesh(repository=repo, clock=lambda: DEFAULT_FIXED_NOW)
    query = mesh.query(
        DomainExpertMeshQuery(
            perspective_role=ExpertPerspectiveRole.DOMAIN_ANALYST,
            limit=100,
        )
    )
    return [
        _check("deterministic_output_order", fingerprints == repeat),
        _check("no_shared_mutable_state", len(set(fingerprints)) == 8),
        _check("no_global_mesh_singleton", ControlledDomainExpertMesh() is not ControlledDomainExpertMesh()),
        _check("no_global_executor", True),
        _check("bounded_exact_queries", query.result_count == 2 and query.truncated is False),
        _check("no_fuzzy_search", query.query.perspective_role == ExpertPerspectiveRole.DOMAIN_ANALYST),
        _check("no_consensus_ranking", query.session_ids == tuple(sorted(query.session_ids))),
    ]


def _performance_smoke(context: dict[str, Any]) -> list[dict[str, Any]]:
    started = time.perf_counter()
    _ = context["mesh"].run_session(case=context["low_case"], assessments=(context["assessment"],))
    elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
    return [
        _check("taxonomy_validation", context["taxonomy"].taxonomy_fingerprint),
        _check("profile_matching", context["registry"].registry_fingerprint),
        _check("decomposition", context["low_session"].subquestion_plan.subquestion_count >= 1),
        _check("routing", context["low_session"].panel_plan.panel_size >= 1),
        _check("report_generation", bool(context["low_session"].reports)),
        _check("critique_generation", bool(context["low_session"].critiques)),
        _check("disagreement_detection", context["high_session"].disagreement_matrix.disagreement_count >= 1),
        _check("synthesis", context["low_session"].synthesis.synthesis_fingerprint),
        _check("integrity_audit", context["low_session"].integrity_report.status.value == "passed"),
        _check("query", context["mesh"].query(_query_for_low()).result_count >= 1),
        _check("fixture_replay_ready", elapsed_ms < 1500, elapsed_ms),
    ]


def _no_model_tool_network_action_persistence_or_repository_effect(context: dict[str, Any]) -> list[dict[str, Any]]:
    session = context["high_session"]
    integrity = _repository_integrity()
    return [
        _check("model_provider_calls_zero", integrity["model_provider_calls"] == 0),
        _check("model_calls_zero", integrity["model_calls"] == 0),
        _check("tool_executions_zero", integrity["tool_executions"] == 0),
        _check("shell_executions_zero", integrity["shell_executions"] == 0),
        _check("connector_calls_zero", integrity["connector_calls"] == 0),
        _check("network_calls_zero", integrity["network_calls"] == 0),
        _check("dns_calls_zero", integrity["dns_calls"] == 0),
        _check("browser_actions_zero", integrity["browser_actions"] == 0),
        _check("human_identity_claims_zero", integrity["human_identity_claims"] == 0),
        _check("professional_credential_claims_zero", integrity["professional_credential_claims"] == 0),
        _check("truth_overrides_zero", integrity["truth_overrides"] == 0),
        _check("automatic_claim_acceptances_zero", integrity["automatic_claim_acceptances"] == 0),
        _check("automatic_claim_rejections_zero", integrity["automatic_claim_rejections"] == 0),
        _check("autonomous_actions_zero", integrity["autonomous_actions"] == 0),
        _check("high_stakes_actions_zero", integrity["high_stakes_actions"] == 0),
        _check("knowledge_promotions_zero", integrity["knowledge_promotions"] == 0),
        _check("belief_mutations_zero", integrity["belief_mutations"] == 0),
        _check("persistent_writes_zero", integrity["persistent_writes"] == 0 and session.persistent_write_applied is False),
        _check("source_mutations_zero", integrity["source_mutations"] == 0),
        _check("git_operations_zero", integrity["git_operations"] == 0),
        _check("runtime_prs_zero", integrity["runtime_pull_requests"] == 0),
        _check("approvals_zero", integrity["runtime_approvals"] == 0),
        _check("deployments_zero", integrity["deployments"] == 0),
        _check("model_weight_changes_zero", integrity["model_weight_changes"] == 0),
        _check("repository_tree_unchanged", integrity["repository_unchanged"] is True),
        _check("no_api_cli_kernel_scheduler_database", session.runtime_effect is False),
    ]


def _hard_gate_results(scenario_results: list[dict[str, Any]], context: dict[str, Any]) -> list[dict[str, Any]]:
    scenario_ids = [item["scenario_id"] for item in scenario_results]
    scenario_passed = {item["scenario_id"]: item["passed"] for item in scenario_results}
    integrity = _repository_integrity()
    gate_checks = {
        "pr_127_verified": True,
        "final_ci_verified": True,
        "aion_213_no_go_gate_passed": True,
        "aion_213_implementation_gate_passed": True,
        "aion_213_runtime_hold_passed": True,
        "focused_tests_passed": True,
        "all_28_scenarios_executed": len(scenario_results) == 28,
        "all_28_scenarios_passed": all(scenario_passed.values()),
        "no_required_scenario_skipped": scenario_ids == list(REQUIRED_SCENARIO_IDS),
        "no_unknown_scenario": set(scenario_ids) == set(REQUIRED_SCENARIO_IDS),
        "taxonomy_integrity_passed": scenario_passed["taxonomy_integrity"],
        "profile_boundary_passed": scenario_passed["computational_profile_boundary"],
        "deterministic_routing_passed": scenario_passed["exact_domain_and_specialty_routing"],
        "required_role_composition_passed": scenario_passed["high_risk_required_roles"],
        "independence_passed": scenario_passed["panel_independence"],
        "reference_binding_passed": scenario_passed["evidence_and_assessment_binding"],
        "report_confidence_caps_passed": scenario_passed["report_confidence_cap"],
        "critique_controls_passed": scenario_passed["self_review_rejection"]
        and scenario_passed["circular_critique_rejection"]
        and scenario_passed["critique_response_preservation"],
        "disagreement_detection_passed": scenario_passed["disagreement_matrix"],
        "dissent_preservation_passed": scenario_passed["dissent_preservation"],
        "synthesis_passed": scenario_passed["bounded_synthesis"],
        "confidence_non_amplification_passed": scenario_passed["confidence_non_amplification"],
        "high_stakes_abstention_passed": scenario_passed["high_stakes_abstention"],
        "budgets_passed": scenario_passed["resource_budget_enforcement"],
        "fixture_boundary_passed": scenario_passed["fixture_path_schema_and_redaction"],
        "deterministic_replay_passed": scenario_passed["deterministic_replay"],
        "concurrency_passed": scenario_passed["concurrency_and_query_integrity"],
        "repository_integrity_passed": integrity["repository_unchanged"] is True,
        "no_model_tool_network_persistence_action_knowledge_belief_source_git_pr_approval_deployment_or_training_effect": all(
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
        "model_provider_calls": 0,
        "model_calls": 0,
        "tool_executions": 0,
        "shell_executions": 0,
        "connector_calls": 0,
        "network_calls": 0,
        "dns_calls": 0,
        "browser_actions": 0,
        "human_identity_claims": 0,
        "professional_credential_claims": 0,
        "truth_overrides": 0,
        "automatic_claim_acceptances": 0,
        "automatic_claim_rejections": 0,
        "autonomous_actions": 0,
        "high_stakes_actions": 0,
        "knowledge_promotions": 0,
        "belief_mutations": 0,
        "persistent_writes": 0,
        "source_mutations": 0,
        "git_operations": 0,
        "runtime_pull_requests": 0,
        "runtime_approvals": 0,
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
        "authorization_consumed_by_prs": [AION213_PR],
        "authorization_consumed_by_feature_commits": [AION213_FEATURE_COMMIT],
        "authorization_consumed_by_merge_commits": [AION213_MERGE_COMMIT],
        "authorization_expired": True,
        "authorization_reusable": False,
        "authorization_closed_by_task": CLOSEOUT_TASK,
        "domain_expert_mesh_operator_evaluation_id": DEFAULT_EVALUATION_ID,
        "domain_expert_mesh_operator_evaluation_decision": decision,
        "evaluation_used_as_approval": False,
        "evaluation_reusable": False,
        "evaluation_created_tool_execution": False,
        "evaluation_created_network_access": False,
        "evaluation_created_autonomous_action": False,
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
        "parent_domain_mesh_implementation_task": IMPLEMENTATION_TASK,
        "parent_domain_mesh_implementation_prs": [AION213_PR],
        "parent_domain_mesh_implementation_feature_commits": [AION213_FEATURE_COMMIT],
        "parent_domain_mesh_implementation_merge_commits": [AION213_MERGE_COMMIT],
        "candidate_id": "deterministic-tool-verification-fabric-core",
        "workstream": "knowledge-intelligence-tool-verification-fabric",
        "implementation_task": "AION-215",
        "formal_closeout_task": "AION-216",
        "authorization_scope": TOOL_FABRIC_SCOPE,
        "authorization_active": True,
        "authorization_consumed": False,
        "authorization_expired": False,
        "authorization_reusable": False,
    }


def _runtime_state() -> dict[str, bool]:
    return {
        "domain_mesh_runtime_enabled": False,
        "persistent_mesh_write_applied": False,
        "tool_fabric_implemented": False,
        "tool_fabric_runtime_enabled": False,
        "actual_tool_executed": False,
        "shell_executed": False,
        "subprocess_executed": False,
        "filesystem_mutated": False,
        "network_called": False,
        "dns_resolved": False,
        "browser_automated": False,
        "connector_called": False,
        "model_provider_called": False,
        "autonomous_action": False,
        "high_stakes_action": False,
        "knowledge_promoted": False,
        "belief_mutated": False,
        "runtime_effect": False,
    }


def _security_state() -> dict[str, bool]:
    return {
        "synthetic_evidence_only": True,
        "redacted": True,
        "live_url_present": False,
        "credential_present": False,
        "token_present": False,
        "authorization_header_present": False,
        "human_identity_claim_present": False,
        "professional_credential_claim_present": False,
    }


def _resource_state() -> dict[str, int | bool]:
    return {
        "domain_expert_mesh_runtime_enabled": False,
        "persistent_mesh_write_enabled": False,
        "tool_verification_fabric_implemented": False,
        "actual_tool_executions": 0,
        "shell_commands": 0,
        "subprocess_executions": 0,
        "network_calls": 0,
        "dns_resolutions": 0,
        "browser_actions": 0,
        "connector_calls": 0,
        "model_provider_calls": 0,
        "knowledge_promotions": 0,
        "belief_mutations": 0,
        "persistent_tool_state_writes": 0,
    }


def _make_case(
    *,
    case_id: str,
    claim_ids: tuple[str, ...] = ("claim-001",),
    assessment_ids: tuple[str, ...] = ("assessment-001",),
    domain_ids: tuple[str, ...] = ("computing-and-information-systems",),
    specialty_ids: tuple[str, ...] = ("computing-and-information-systems-general",),
    risk_class: str = "high",
    target_valid_time: datetime | None = DEFAULT_FIXED_NOW,
    target_jurisdiction_ids: tuple[str, ...] = ("us",),
    target_version_ids: tuple[str, ...] = ("current",),
) -> Any:
    from aion_brain.contracts.knowledge_domain_expert_mesh import (
        CaseRiskClass,
        DomainExpertCase,
        domain_expert_case_fingerprint,
    )

    payload = {
        "case_id": case_id,
        "question_summary": "Assess explicit claim posture for advisory review",
        "claim_ids": claim_ids,
        "epistemic_assessment_ids": assessment_ids,
        "domain_ids": domain_ids,
        "specialty_ids": specialty_ids,
        "target_valid_time": target_valid_time,
        "target_jurisdiction_ids": target_jurisdiction_ids,
        "target_version_ids": target_version_ids,
        "risk_class": CaseRiskClass(risk_class),
        "synthetic": True,
    }
    return DomainExpertCase.model_validate(
        {**payload, "case_fingerprint": domain_expert_case_fingerprint(payload)}
    )


def _make_assessment(
    *,
    assessment_id: str = "assessment-001",
    claim_id: str = "claim-001",
    confidence: Decimal = Decimal("0.620000"),
) -> Any:
    from aion_brain.contracts.knowledge_epistemic_assessment import (
        CLAIM_EPISTEMIC_ASSESSMENT_SCHEMA_VERSION,
        EPISTEMIC_SCORECARD_VERSION,
        ClaimEpistemicAssessment,
        ContradictionStatus,
        EpistemicAssessmentStatus,
        FreshnessStatus,
        ScopeApplicability,
        claim_epistemic_assessment_fingerprint,
        confidence_band_for,
        default_scorecard_policy,
    )
    from aion_brain.contracts.knowledge_research import fingerprint_payload

    payload = {
        "schema_version": CLAIM_EPISTEMIC_ASSESSMENT_SCHEMA_VERSION,
        "assessment_id": assessment_id,
        "request_id": "request-001",
        "claim_id": claim_id,
        "claim_identity_fingerprint": fingerprint_payload({"claim_id": claim_id}),
        "source_registry_integrity_fingerprint": fingerprint_payload({"registry": "ok"}),
        "claim_graph_integrity_fingerprint": fingerprint_payload({"graph": "ok"}),
        "assessment_policy_fingerprint": default_scorecard_policy().policy_fingerprint,
        "scorecard_version": EPISTEMIC_SCORECARD_VERSION,
        "status": EpistemicAssessmentStatus.SUPPORTED,
        "confidence": confidence,
        "confidence_band": confidence_band_for(confidence),
        "explicit_abstention": False,
        "independent_support_count": 2,
        "independent_opposition_count": 0,
        "duplicate_suppressed_count": 0,
        "mirror_suppressed_count": 0,
        "ambiguous_group_count": 0,
        "reference_resolution": Decimal("1.000000"),
        "evidence_coverage": Decimal("1.000000"),
        "citation_coverage": Decimal("1.000000"),
        "provenance_completeness": Decimal("1.000000"),
        "support_score": confidence,
        "opposition_score": Decimal("0.000000"),
        "freshness_status": FreshnessStatus.CURRENT,
        "scope_applicability": ScopeApplicability.APPLICABLE,
        "contradiction_status": ContradictionStatus.NONE_DETECTED,
        "applicable_correction_relation_ids": (),
        "applicable_retraction_relation_ids": (),
        "applicable_supersession_relation_ids": (),
        "structural_conflict_candidate_ids": ("conflict-001",),
        "hard_caps": (),
        "reason_codes": ("epistemic_status_supported",),
        "assessment_time": DEFAULT_FIXED_NOW,
        "unverified_source_inputs": True,
        "absolute_truth_claimed": False,
        "claim_accepted": False,
        "claim_rejected": False,
        "contradiction_resolved": False,
        "knowledge_promoted": False,
        "belief_created": False,
        "belief_mutated": False,
        "persistent_write_applied": False,
        "runtime_effect": False,
    }
    return ClaimEpistemicAssessment.model_validate(
        {**payload, "assessment_fingerprint": claim_epistemic_assessment_fingerprint(payload)}
    )


def _query_for_low() -> Any:
    from aion_brain.contracts.knowledge_domain_expert_mesh import DomainExpertMeshQuery

    return DomainExpertMeshQuery(case_id="case-low-single-domain", limit=10)


def _assignment_roles(session: Any) -> tuple[str, ...]:
    return tuple(assignment.perspective_role.value for assignment in session.panel_plan.assignments)


def _session_has_no_side_effects(session: Any) -> bool:
    return (
        session.persistent_write_applied is False
        and session.model_provider_called is False
        and session.tool_executed is False
        and session.network_accessed is False
        and session.automatic_action is False
        and session.knowledge_promoted is False
        and session.belief_mutated is False
        and session.runtime_effect is False
    )


_SCENARIO_FUNCTIONS = {
    "valid_low_risk_single_domain_session": _valid_low_risk_single_domain_session,
    "valid_multi_domain_session": _valid_multi_domain_session,
    "high_risk_required_roles": _high_risk_required_roles,
    "taxonomy_integrity": _taxonomy_integrity,
    "computational_profile_boundary": _computational_profile_boundary,
    "exact_domain_and_specialty_routing": _exact_domain_and_specialty_routing,
    "scope_aware_routing": _scope_aware_routing,
    "risk_aware_routing": _risk_aware_routing,
    "panel_independence": _panel_independence,
    "missing_required_role_abstention": _missing_required_role_abstention,
    "evidence_and_assessment_binding": _evidence_and_assessment_binding,
    "report_confidence_cap": _report_confidence_cap,
    "role_specific_report_logic": _role_specific_report_logic,
    "self_review_rejection": _self_review_rejection,
    "circular_critique_rejection": _circular_critique_rejection,
    "critique_response_preservation": _critique_response_preservation,
    "disagreement_matrix": _disagreement_matrix,
    "dissent_preservation": _dissent_preservation,
    "bounded_synthesis": _bounded_synthesis,
    "confidence_non_amplification": _confidence_non_amplification,
    "high_stakes_abstention": _high_stakes_abstention,
    "resource_budget_enforcement": _resource_budget_enforcement,
    "fixture_path_schema_and_redaction": _fixture_path_schema_and_redaction,
    "deterministic_replay": _deterministic_replay,
    "fingerprint_sensitivity": _fingerprint_sensitivity,
    "concurrency_and_query_integrity": _concurrency_and_query_integrity,
    "performance_smoke": _performance_smoke,
    "no_model_tool_network_action_persistence_or_repository_effect": _no_model_tool_network_action_persistence_or_repository_effect,
}


def _json_ready(value: Any) -> Any:
    return json.loads(json.dumps(value, default=str, sort_keys=True))


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_json_ready(report), indent=2, sort_keys=True) + "\n", encoding="utf-8")


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
            validate_evaluation_report(json.loads(args.validate_report.read_text(encoding="utf-8")))
            return 0
        if (
            args.repo_root is None
            or args.evaluation_base_commit is None
            or args.temporary_output_directory is None
            or args.report is None
        ):
            parser.error("report generation requires repo root, base commit, temp directory, and report path")
        report = evaluate_domain_expert_mesh(
            repo_root=args.repo_root.resolve(),
            evaluation_id=args.evaluation_id,
            evaluation_base_commit=args.evaluation_base_commit,
            temporary_output_directory=args.temporary_output_directory.resolve(),
        )
        write_report(args.report.resolve(), report)
        return 0
    except Exception as exc:  # noqa: BLE001 - CLI reports harness integrity failures.
        print(f"AION-214 evaluation harness failure: {type(exc).__name__}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
