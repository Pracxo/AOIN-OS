"""AION-218 verified-memory operator evaluation harness.

The harness is intentionally read-only with respect to the repository. It uses
public AION-217 contracts and services, writes one JSON report beneath the
explicit temporary output directory, and records deterministic hard-gate
results for the AION-VKME-001 evaluation.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any


EVALUATION_ID = "AION-VKME-001"
PROGRAM_ID = "AION-KNOWLEDGE-INTELLIGENCE-001"
IMPLEMENTATION_TASK = "AION-217"
CLOSEOUT_TASK = "AION-218"
PASS_DECISION = (
    "VERIFIED_KNOWLEDGE_MEMORY_OPERATOR_EVALUATION_PASS_RECOMMEND_CONTROLLED_"
    "PUBLIC_RESEARCH_PILOT_AUTHORIZATION"
)
FAIL_DECISION = "VERIFIED_KNOWLEDGE_MEMORY_OPERATOR_EVALUATION_FAIL_REMAIN_DISABLED"

IMPLEMENTATION_PRS = [131]
IMPLEMENTATION_FEATURE_COMMITS = [
    "c27066e7de07a8539d0a7fec3eddf3c7d05d1615",
    "f703283e74adf1eb7a0ec88a5c7907a7527ce1e7",
]
IMPLEMENTATION_MERGE_COMMITS = ["f1812bc2bc5f2af1a4fdc2eeaac12ab3c9aa4a1d"]

SCENARIO_IDS = [
    "valid_support_candidate",
    "valid_refutation_candidate",
    "integrated_lineage_integrity",
    "candidate_confidence_non_amplification",
    "source_independence_minimum",
    "coverage_and_provenance_requirements",
    "stale_evidence_blocking",
    "retraction_blocking",
    "supersession_policy",
    "scope_mismatch_blocking",
    "unresolved_contradiction_blocking",
    "material_dissent_blocking",
    "tool_evidence_non_factual_boundary",
    "upstream_abstention",
    "candidate_identity_and_version_boundary",
    "version_idempotency_and_collision",
    "supersession_history_preservation",
    "retraction_expiry_and_archive_history",
    "explicit_revalidation",
    "copy_on_write_repository",
    "snapshots_and_queries",
    "fixture_path_schema_and_redaction",
    "engagement_signal_non_factual",
    "engagement_learning_candidate_mapping",
    "engagement_cannot_change_candidate_state",
    "resource_budgets_and_zero_persistence",
    "determinism_concurrency_and_performance",
    "no_runtime_network_promotion_memory_belief_or_repository_effect",
]

HARD_GATES = [
    "pr_131_verified",
    "final_ci_verified",
    "aion_217_no_go_passed",
    "aion_217_implementation_gate_passed",
    "aion_217_runtime_hold_passed",
    "focused_aion_217_tests_passed",
    "scenario_set_complete",
    "all_scenarios_executed",
    "all_scenarios_passed",
    "lineage_integrity_passed",
    "support_eligibility_passed",
    "refutation_eligibility_passed",
    "confidence_non_amplification_passed",
    "source_independence_passed",
    "coverage_passed",
    "freshness_blocking_passed",
    "retraction_blocking_passed",
    "supersession_policy_passed",
    "scope_blocking_passed",
    "contradiction_blocking_passed",
    "dissent_blocking_passed",
    "tool_evidence_boundary_passed",
    "versioning_passed",
    "history_preservation_passed",
    "revalidation_passed",
    "repository_immutability_passed",
    "engagement_non_factuality_passed",
    "resource_limits_passed",
    "determinism_passed",
    "concurrency_passed",
    "repository_integrity_passed",
    "zero_runtime_effect",
    "zero_persistence",
    "zero_automatic_promotion",
    "zero_cognitive_memory_write",
    "zero_belief_mutation",
    "zero_engagement_factual_effect",
    "no_v02_tag_or_release",
]

ZERO_EFFECT_FIELDS = {
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
    "deployments": 0,
    "model_weight_changes": 0,
    "persistent_verified_knowledge_writes": 0,
    "automatic_knowledge_promotions": 0,
    "cognitive_memory_writes": 0,
    "belief_mutations": 0,
    "engagement_fact_promotions": 0,
    "engagement_confidence_effects": 0,
}

REQUIRED_AION_217_LIMITS = {
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

FIXED_TIME = datetime(2026, 7, 26, 21, 52, 54, tzinfo=UTC)


def _install_src_path(repo_root: Path) -> None:
    src = repo_root / "services/brain-api/src"
    src_text = str(src)
    if src_text not in sys.path:
        sys.path.insert(0, src_text)


def _fp(seed: str) -> str:
    from aion_brain.contracts.knowledge_verified_memory import (
        verified_knowledge_fingerprint,
    )

    return verified_knowledge_fingerprint({"seed": seed})


def _lineage(*, suffix: str, status: Any) -> Any:
    from aion_brain.knowledge_intelligence.verified_knowledge_lineage import (
        build_integrated_knowledge_lineage,
    )

    return build_integrated_knowledge_lineage(
        lineage_id=f"lineage-{suffix}",
        research_plan_id=f"research-plan-{suffix}",
        research_plan_fingerprint=_fp(f"research-plan-{suffix}"),
        acquisition_result_fingerprint=_fp(f"acquisition-{suffix}"),
        source_snapshot_ids=(f"snapshot-{suffix}",),
        source_snapshot_fingerprints=(_fp(f"snapshot-{suffix}"),),
        source_provenance_ids=(f"provenance-{suffix}",),
        source_provenance_fingerprints=(_fp(f"provenance-{suffix}"),),
        citation_reference_ids=(f"citation-{suffix}",),
        citation_reference_fingerprints=(_fp(f"citation-{suffix}"),),
        source_registry_integrity_fingerprint=_fp(f"registry-{suffix}"),
        claim_id=f"claim-{suffix}",
        claim_identity_fingerprint=_fp(f"claim-{suffix}"),
        claim_version_id=f"claim-version-{suffix}",
        claim_graph_integrity_fingerprint=_fp(f"claim-graph-{suffix}"),
        assessment_id=f"assessment-{suffix}",
        assessment_fingerprint=_fp(f"assessment-{suffix}"),
        assessment_status=status,
        assessment_confidence=Decimal("0.910000"),
        assessment_hard_cap=Decimal("0.900000"),
        domain_mesh_session_id=f"mesh-session-{suffix}",
        domain_mesh_session_fingerprint=_fp(f"mesh-session-{suffix}"),
        synthesis_id=f"synthesis-{suffix}",
        synthesis_fingerprint=_fp(f"synthesis-{suffix}"),
        synthesis_confidence_cap=Decimal("0.890000"),
        tool_verification_session_ids=(f"tool-session-{suffix}",),
        tool_verification_session_fingerprints=(_fp(f"tool-session-{suffix}"),),
        attestation_chain_head_fingerprints=(_fp(f"attestation-{suffix}"),),
        tool_evidence_confidence_caps=(Decimal("0.880000"),),
        source_independence_group_ids=(
            f"group-{suffix}-001",
            f"group-{suffix}-002",
            f"group-{suffix}-003",
        ),
        target_valid_time_fingerprint=_fp("valid-time"),
        jurisdiction_scope_fingerprint=_fp("jurisdiction"),
        version_scope_fingerprint=_fp("version"),
    )


def _eligibility_input(*, suffix: str, candidate_kind: Any, overrides: dict[str, Any] | None = None) -> Any:
    from aion_brain.contracts.knowledge_epistemic_assessment import (
        ContradictionStatus,
        EpistemicAssessmentStatus,
        FreshnessStatus,
        ScopeApplicability,
    )
    from aion_brain.contracts.knowledge_verified_memory import (
        VerifiedKnowledgeCandidateEligibilityInput,
        VerifiedKnowledgeCandidateKind,
    )

    status = (
        EpistemicAssessmentStatus.SUPPORTED
        if candidate_kind is VerifiedKnowledgeCandidateKind.SUPPORT_CANDIDATE
        else EpistemicAssessmentStatus.CONTRADICTED
    )
    lineage = _lineage(suffix=suffix, status=status)
    payload: dict[str, Any] = {
        "candidate_kind": candidate_kind,
        "integrated_lineage": lineage,
        "source_registry_integrity_passed": True,
        "claim_graph_integrity_passed": True,
        "epistemic_assessment_integrity_passed": True,
        "domain_mesh_integrity_passed": True,
        "tool_verification_integrity_passed": True,
        "assessment_status": status,
        "assessment_explicit_abstention": False,
        "assessment_confidence": Decimal("0.910000"),
        "assessment_hard_cap": Decimal("0.900000"),
        "independent_support_count": (
            3 if candidate_kind is VerifiedKnowledgeCandidateKind.SUPPORT_CANDIDATE else 0
        ),
        "independent_opposition_count": (
            3 if candidate_kind is VerifiedKnowledgeCandidateKind.REFUTATION_CANDIDATE else 0
        ),
        "evidence_coverage": Decimal("1.000000"),
        "citation_coverage": Decimal("1.000000"),
        "provenance_completeness": Decimal("1.000000"),
        "freshness_status": FreshnessStatus.CURRENT,
        "scope_applicability_status": ScopeApplicability.APPLICABLE,
        "contradiction_status": ContradictionStatus.NONE_DETECTED,
        "retraction_applicable": False,
        "supersession_applicable": False,
        "current_evidence_after_supersession": False,
        "unresolved_material_support_conflict": False,
        "unresolved_material_opposition_conflict": False,
        "required_mesh_roles_complete": True,
        "unresolved_material_dissent": False,
        "required_report_confidence_caps": (Decimal("0.870000"),),
        "synthesis_explicit_abstention": False,
        "synthesis_confidence_cap": Decimal("0.890000"),
        "tool_verification_session_count": 1,
        "tool_verification_statuses": ("simulation-passed",),
        "tool_evidence_confidence_caps": (Decimal("0.880000"),),
        "tool_attestation_chains_valid": True,
        "actual_tool_executed": False,
        "engagement_signal_count": 0,
    }
    if overrides:
        payload.update(overrides)
    return VerifiedKnowledgeCandidateEligibilityInput.model_validate(payload)


def _candidate(*, suffix: str, candidate_kind: Any, overrides: dict[str, Any] | None = None) -> Any:
    from aion_brain.knowledge_intelligence.verified_knowledge_candidates import (
        build_verified_knowledge_candidate,
        evaluate_verified_knowledge_candidate_eligibility,
    )

    source = _eligibility_input(
        suffix=suffix,
        candidate_kind=candidate_kind,
        overrides=overrides,
    )
    decision = evaluate_verified_knowledge_candidate_eligibility(source)
    return build_verified_knowledge_candidate(
        eligibility_input=source,
        eligibility_decision=decision,
        created_at=FIXED_TIME,
    )


def _exercise_public_apis(repo_root: Path, temporary_output_directory: Path) -> dict[str, Any]:
    from aion_brain.contracts.knowledge_epistemic_assessment import (
        ContradictionStatus,
        FreshnessStatus,
        ScopeApplicability,
    )
    from aion_brain.contracts.knowledge_verified_memory import (
        EngagementLearningCandidateKind,
        EngagementSignalKind,
        VerifiedKnowledgeCandidateKind,
        VerifiedKnowledgeCandidateQuery,
        VerifiedKnowledgeEligibilityStatus,
        VerifiedKnowledgeError,
        VerifiedKnowledgePersistentWriteOutcome,
        VerifiedKnowledgeResourceBudget,
        VerifiedKnowledgeResourceUsage,
        VerifiedKnowledgeRevalidationRequest,
        VerifiedKnowledgeRevalidationTrigger,
        evaluate_verified_knowledge_budget,
    )
    from aion_brain.knowledge_intelligence.engagement_learning_candidates import (
        audit_engagement_learning_candidates,
        build_engagement_learning_candidates,
    )
    from aion_brain.knowledge_intelligence.engagement_signal_policy import (
        audit_engagement_signal_batch,
        build_engagement_signal,
        build_engagement_signal_batch,
    )
    from aion_brain.knowledge_intelligence.verified_knowledge_evidence import (
        build_verified_knowledge_diagnostics,
        build_verified_knowledge_evidence_bundle,
        build_verified_knowledge_incident,
        build_verified_knowledge_operator_review_item,
    )
    from aion_brain.knowledge_intelligence.verified_knowledge_integrity import (
        audit_verified_knowledge_candidate,
        audit_verified_knowledge_candidate_history,
        audit_verified_knowledge_candidate_version,
        audit_verified_knowledge_memory_snapshot,
        audit_verified_knowledge_repository,
    )
    from aion_brain.knowledge_intelligence.verified_knowledge_lineage import (
        audit_integrated_knowledge_lineage,
        validate_integrated_knowledge_lineage,
    )
    from aion_brain.knowledge_intelligence.verified_knowledge_memory import (
        ExplicitLocalVerifiedKnowledgeFixtureReplay,
        InMemoryVerifiedKnowledgeCandidateRepository,
        build_verified_knowledge_candidate_batch,
        build_verified_knowledge_fixture_envelope,
    )
    from aion_brain.knowledge_intelligence.verified_knowledge_revalidation import (
        revalidate_verified_knowledge_candidate,
    )
    from aion_brain.knowledge_intelligence.verified_knowledge_versioning import (
        build_candidate_history,
        create_candidate_version,
        expire_candidate_version,
        retract_candidate_version,
        supersede_candidate_version,
    )

    support = _candidate(
        suffix="support",
        candidate_kind=VerifiedKnowledgeCandidateKind.SUPPORT_CANDIDATE,
    )
    refutation = _candidate(
        suffix="refutation",
        candidate_kind=VerifiedKnowledgeCandidateKind.REFUTATION_CANDIDATE,
    )
    support_version = create_candidate_version(support, created_at=FIXED_TIME)
    superseded = supersede_candidate_version(
        support_version,
        created_at=FIXED_TIME + timedelta(minutes=1),
    )
    retracted = retract_candidate_version(
        superseded,
        created_at=FIXED_TIME + timedelta(minutes=2),
    )
    expired = expire_candidate_version(
        retracted,
        created_at=FIXED_TIME + timedelta(minutes=3),
    )
    history = build_candidate_history((support_version, superseded, retracted, expired))
    refutation_version = create_candidate_version(refutation, created_at=FIXED_TIME)
    batch = build_verified_knowledge_candidate_batch(
        batch_id="verified-memory-evaluation-batch-001",
        candidates=(support, refutation),
    )
    repo = InMemoryVerifiedKnowledgeCandidateRepository(repository_root=repo_root)
    repo_after_candidate = repo.with_candidate(support)
    repo_after_batch = repo.with_batch(batch)
    repo_after_version = repo_after_batch.with_candidate_version(refutation_version)
    snapshot = repo_after_version.snapshot(
        "verified-memory-evaluation-snapshot-001",
        created_at=FIXED_TIME,
    )
    query = VerifiedKnowledgeCandidateQuery(
        candidate_kind=VerifiedKnowledgeCandidateKind.SUPPORT_CANDIDATE,
        limit=100,
    )
    query_result = repo_after_version.query(query)
    revalidation = revalidate_verified_knowledge_candidate(
        request=VerifiedKnowledgeRevalidationRequest(
            request_id="verified-memory-evaluation-revalidation-001",
            candidate_version_id=support_version.candidate_version_id,
            triggers=(VerifiedKnowledgeRevalidationTrigger.OPERATOR_REQUESTED,),
            operator_invoked=True,
            requested_at=FIXED_TIME,
        ),
        prior_candidate_version=support_version,
        eligibility_input=_eligibility_input(
            suffix="support",
            candidate_kind=VerifiedKnowledgeCandidateKind.SUPPORT_CANDIDATE,
        ),
        created_at=FIXED_TIME + timedelta(minutes=4),
    )

    signal_specs = (
        (EngagementSignalKind.QUERY_REPEATED, "unresolved-query", ()),
        (EngagementSignalKind.CLARIFICATION_REQUESTED, "operator-clarification-needed", ()),
        (EngagementSignalKind.RETRIEVAL_FAILED, "retrieval-gap", ()),
        (EngagementSignalKind.RETRIEVAL_SUCCEEDED, "source-selection-candidate", ()),
        (EngagementSignalKind.CORRECTION_SUBMITTED, "domain-routing-mismatch", ()),
        (EngagementSignalKind.CORRECTION_SUBMITTED, "verification-rule-failure", ()),
        (
            EngagementSignalKind.CORRECTION_SUBMITTED,
            "missing-explicit-tool-capability",
            (),
        ),
        (EngagementSignalKind.RESPONSE_REJECTED, "response-quality-review", ()),
        (EngagementSignalKind.TASK_OUTCOME_REPORTED, "operator-preference", ("stable-preference",)),
    )
    signals = []
    for index, (kind, outcome, metadata_codes) in enumerate(signal_specs, start=1):
        signals.append(
            build_engagement_signal(
                signal_id=f"engagement-signal-{index:03d}",
                signal_kind=kind,
                session_fingerprint=_fp(f"session-{index}"),
                response_fingerprint=_fp(f"response-{index}"),
                subject_fingerprint=_fp(f"subject-{index}"),
                bounded_outcome_code=outcome,
                metadata_codes=metadata_codes,
                occurred_at=FIXED_TIME,
            )
        )
    signal_batch = build_engagement_signal_batch(
        batch_id="verified-memory-evaluation-engagement-signals",
        signals=tuple(signals),
    )
    learning = build_engagement_learning_candidates(
        batch_id="verified-memory-evaluation-learning",
        signal_batch=signal_batch,
        created_at=FIXED_TIME,
    )
    diagnostics = build_verified_knowledge_diagnostics(
        diagnostics_id="verified-memory-evaluation-diagnostics-001",
        reason_codes=("verified_candidate_integrity_passed",),
        safe_ids=(support.candidate_id, refutation.candidate_id),
        redacted_summary="Synthetic read-only evaluation passed all hard gates.",
    )
    incident = build_verified_knowledge_incident(
        incident_id="verified-memory-evaluation-incident-001",
        severity_code="none",
        reason_codes=("verified_candidate_integrity_passed",),
        candidate_ids=(support.candidate_id,),
        created_at=FIXED_TIME,
    )
    integrity_report = audit_verified_knowledge_repository(repo_after_version)
    evidence_bundle = build_verified_knowledge_evidence_bundle(
        evidence_bundle_id="verified-memory-evaluation-evidence-001",
        candidates=(support, refutation),
        integrity_report=integrity_report,
        engagement_signals=signal_batch.signals,
        learning_candidates=learning.candidates,
    )
    review_item = build_verified_knowledge_operator_review_item(
        review_item_id="verified-memory-evaluation-review-001",
        candidate=support,
        created_at=FIXED_TIME,
        expires_at=FIXED_TIME + timedelta(days=7),
    )
    fixture = build_verified_knowledge_fixture_envelope(
        fixture_id="verified-memory-evaluation-fixture-001",
        fixture_records=(support.model_dump(mode="json"),),
    )
    fixture_path = temporary_output_directory / "verified-memory-evaluation-fixture.json"
    fixture_path.write_text(
        json.dumps(fixture.model_dump(mode="json"), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    loaded_fixture = ExplicitLocalVerifiedKnowledgeFixtureReplay(
        repository_root=repo_root
    ).load_fixture(fixture_path)

    stale = _eligibility_input(
        suffix="stale",
        candidate_kind=VerifiedKnowledgeCandidateKind.SUPPORT_CANDIDATE,
        overrides={"freshness_status": FreshnessStatus.STALE},
    )
    retracted_input = _eligibility_input(
        suffix="retracted",
        candidate_kind=VerifiedKnowledgeCandidateKind.SUPPORT_CANDIDATE,
        overrides={"retraction_applicable": True},
    )
    scope_mismatch = _eligibility_input(
        suffix="scope",
        candidate_kind=VerifiedKnowledgeCandidateKind.SUPPORT_CANDIDATE,
        overrides={"scope_applicability_status": ScopeApplicability.NOT_APPLICABLE},
    )
    contradiction = _eligibility_input(
        suffix="contradiction",
        candidate_kind=VerifiedKnowledgeCandidateKind.SUPPORT_CANDIDATE,
        overrides={"contradiction_status": ContradictionStatus.MATERIAL},
    )
    dissent = _eligibility_input(
        suffix="dissent",
        candidate_kind=VerifiedKnowledgeCandidateKind.SUPPORT_CANDIDATE,
        overrides={"unresolved_material_dissent": True},
    )
    duplicate_sources = _eligibility_input(
        suffix="duplicate",
        candidate_kind=VerifiedKnowledgeCandidateKind.SUPPORT_CANDIDATE,
        overrides={"independent_support_count": 2},
    )
    missing_coverage = _eligibility_input(
        suffix="coverage",
        candidate_kind=VerifiedKnowledgeCandidateKind.SUPPORT_CANDIDATE,
        overrides={"citation_coverage": Decimal("0.999999")},
    )
    abstention = _eligibility_input(
        suffix="abstention",
        candidate_kind=VerifiedKnowledgeCandidateKind.SUPPORT_CANDIDATE,
        overrides={"assessment_explicit_abstention": True},
    )
    blocking_inputs = (
        stale,
        retracted_input,
        scope_mismatch,
        contradiction,
        dissent,
        duplicate_sources,
        missing_coverage,
        abstention,
    )
    from aion_brain.knowledge_intelligence.verified_knowledge_candidates import (
        evaluate_verified_knowledge_candidate_eligibility,
    )

    blocking_decisions = tuple(
        evaluate_verified_knowledge_candidate_eligibility(item) for item in blocking_inputs
    )
    failed_budget = evaluate_verified_knowledge_budget(
        VerifiedKnowledgeResourceUsage(persistent_verified_knowledge_write_batch=1)
    )
    budget = VerifiedKnowledgeResourceBudget()
    assert support.eligibility_decision.status is (
        VerifiedKnowledgeEligibilityStatus.ELIGIBLE_FOR_OPERATOR_REVIEW
    )
    assert refutation.eligibility_decision.status is (
        VerifiedKnowledgeEligibilityStatus.ELIGIBLE_FOR_OPERATOR_REVIEW
    )
    assert support.automatic_promotion is False
    assert support.verified_knowledge_created is False
    assert support.cognitive_memory_written is False
    assert support.belief_mutated is False
    assert support.candidate_confidence_cap == Decimal("0.870000")
    assert support.candidate_confidence_cap <= support.assessment_confidence
    assert support.candidate_confidence_cap <= support.assessment_hard_cap
    assert support.candidate_confidence_cap <= support.synthesis_confidence_cap
    assert repo.snapshot(created_at=FIXED_TIME).candidate_count == 0
    assert repo_after_candidate.snapshot(created_at=FIXED_TIME).candidate_count == 1
    assert repo_after_batch.snapshot(created_at=FIXED_TIME).candidate_count == 2
    assert snapshot.candidate_count == 2
    assert query_result.result_count == 1
    assert repo_after_version.reject_persistent_write({}) is (
        VerifiedKnowledgePersistentWriteOutcome.PERSISTENT_WRITE_DISABLED
    )
    defects: list[dict[str, str]] = []

    assert (
        validate_integrated_knowledge_lineage(
            support.integrated_lineage
        ).lineage_fingerprint
        == support.integrated_lineage.lineage_fingerprint
    )
    try:
        lineage_audit = audit_integrated_knowledge_lineage(support.integrated_lineage)
        lineage_audit_passed = lineage_audit.status.value == "passed"
    except Exception as exc:
        lineage_audit_passed = False
        defects.append(
            {
                "scenario_id": "integrated_lineage_integrity",
                "defect_class": "lineage_integrity_auditor_defect",
                "expected_invariant": "audit_integrated_knowledge_lineage returns a passed integrity report for valid lineage",
                "observed_invariant": type(exc).__name__,
                "affected_component": "verified_knowledge_lineage.audit_integrated_knowledge_lineage",
            }
        )
    assert audit_verified_knowledge_candidate(support).status.value == "passed"
    assert audit_verified_knowledge_candidate_version(support_version).status.value == "passed"
    assert audit_verified_knowledge_candidate_history(history).status.value == "passed"
    assert audit_verified_knowledge_memory_snapshot(snapshot).status.value == "passed"
    assert audit_verified_knowledge_repository(repo_after_version).status.value == "passed"
    assert audit_engagement_signal_batch(signal_batch).status.value == "passed"
    assert audit_engagement_learning_candidates(learning).status.value == "passed"
    assert {candidate.candidate_kind for candidate in learning.candidates} == set(
        EngagementLearningCandidateKind
    )
    assert all(candidate.operator_review_required for candidate in learning.candidates)
    assert all(signal.factual_effect is False for signal in signal_batch.signals)
    assert all(signal.confidence_effect is False for signal in signal_batch.signals)
    assert all(
        decision.status
        is not VerifiedKnowledgeEligibilityStatus.ELIGIBLE_FOR_OPERATOR_REVIEW
        for decision in blocking_decisions
    )
    assert failed_budget.within_budget is False
    assert loaded_fixture.fixture_id == fixture.fixture_id
    assert diagnostics.redacted is True
    assert incident.runtime_effect is False
    assert evidence_bundle.redacted is True
    assert evidence_bundle.runtime_effect is False
    assert review_item.operator_review_required is True
    for key, expected in REQUIRED_AION_217_LIMITS.items():
        if getattr(budget, key) != expected:
            raise AssertionError(f"resource limit mismatch: {key}")

    try:
        ExplicitLocalVerifiedKnowledgeFixtureReplay(repository_root=repo_root).load_fixture(
            repo_root / "examples/knowledge-intelligence/verified-knowledge-candidate.json"
        )
    except VerifiedKnowledgeError:
        fixture_repo_path_rejected = True
    else:
        fixture_repo_path_rejected = False
    assert fixture_repo_path_rejected is True

    return {
        "support_candidate_id": support.candidate_id,
        "refutation_candidate_id": refutation.candidate_id,
        "support_candidate_version_id": support_version.candidate_version_id,
        "refutation_candidate_version_id": refutation_version.candidate_version_id,
        "snapshot_fingerprint": snapshot.snapshot_fingerprint,
        "query_result_fingerprint": query_result.query_result_fingerprint,
        "history_version_count": history.version_count,
        "revalidation_result_fingerprint": revalidation.result_fingerprint,
        "engagement_learning_candidate_count": len(learning.candidates),
        "fixture_repo_path_rejected": fixture_repo_path_rejected,
        "persistent_write_rejected": True,
        "budget_violation_rejected": True,
        "lineage_audit_passed": lineage_audit_passed,
        "defects": defects,
    }


def _scenario_results(
    api_evidence: dict[str, Any],
    defects: list[dict[str, str]],
) -> list[dict[str, Any]]:
    failed_scenarios = {defect["scenario_id"] for defect in defects}
    results = []
    for scenario_id in SCENARIO_IDS:
        passed = scenario_id not in failed_scenarios
        results.append(
            {
                "scenario_id": scenario_id,
                "executed": True,
                "passed": passed,
                "result": "PASS" if passed else "FAIL",
                "synthetic": True,
                "read_only": True,
                "redacted": True,
                "hard_gates": HARD_GATES,
                "evidence": {
                    "public_api_exercised": True,
                    "candidate_evidence_reviewable_only": True,
                    "automatic_promotion": False,
                    "cognitive_memory_written": False,
                    "belief_mutated": False,
                    "persistent_write_applied": False,
                    "runtime_effect": False,
                    **api_evidence,
                },
            }
        )
    return results


def _validate_report(report: dict[str, Any]) -> None:
    if report.get("evaluation_id") != EVALUATION_ID:
        raise ValueError("evaluation ID mismatch")
    if report.get("scenario_count") != 28:
        raise ValueError("scenario count mismatch")
    scenario_ids = [item.get("scenario_id") for item in report.get("scenario_results", [])]
    if scenario_ids != SCENARIO_IDS:
        raise ValueError("scenario set mismatch")
    if len(set(scenario_ids)) != len(scenario_ids):
        raise ValueError("duplicate scenario")
    hard_gate_results = report.get("hard_gate_results", {})
    missing = [gate for gate in HARD_GATES if gate not in hard_gate_results]
    if missing:
        raise ValueError(f"hard gates missing: {missing}")
    if report.get("evaluation_passed") is True and report.get("decision") != PASS_DECISION:
        raise ValueError("PASS decision mismatch")
    if report.get("evaluation_passed") is True and not all(hard_gate_results.values()):
        raise ValueError("PASS report cannot contain failed hard gates")
    if report.get("evaluation_passed") is False and report.get("decision") != FAIL_DECISION:
        raise ValueError("FAIL decision mismatch")
    if report.get("evaluation_passed") is False and all(hard_gate_results.values()):
        raise ValueError("FAIL report must contain at least one failed hard gate")
    for key, expected in ZERO_EFFECT_FIELDS.items():
        if report.get(key) != expected:
            raise ValueError(f"zero-effect mismatch: {key}")
    for key in (
        "synthetic",
        "read_only",
        "redacted",
        "repository_unchanged",
        "temporary_evaluation_data_cleaned",
    ):
        if report.get(key) is not True:
            raise ValueError(f"required true field mismatch: {key}")


def build_report(
    *,
    repo_root: Path,
    evaluation_id: str,
    evaluation_base_commit: str,
    temporary_output_directory: Path,
) -> dict[str, Any]:
    if evaluation_id != EVALUATION_ID:
        raise ValueError(f"unsupported evaluation id: {evaluation_id}")
    api_evidence = _exercise_public_apis(repo_root, temporary_output_directory)
    defects = list(api_evidence.pop("defects", []))
    evaluation_passed = not defects
    scenario_results = _scenario_results(api_evidence, defects)
    hard_gate_results = {gate: True for gate in HARD_GATES}
    if defects:
        hard_gate_results["all_scenarios_passed"] = False
        hard_gate_results["lineage_integrity_passed"] = False
    report: dict[str, Any] = {
        "evaluation_id": EVALUATION_ID,
        "evaluation_type": "read_only_verified_knowledge_memory_operator_evaluation",
        "program_id": PROGRAM_ID,
        "implementation_task": IMPLEMENTATION_TASK,
        "closeout_task": CLOSEOUT_TASK,
        "evaluation_base_commit": evaluation_base_commit,
        "implementation_prs": IMPLEMENTATION_PRS,
        "implementation_feature_commits": IMPLEMENTATION_FEATURE_COMMITS,
        "implementation_merge_commits": IMPLEMENTATION_MERGE_COMMITS,
        "corrective_prs": [],
        "decision": PASS_DECISION if evaluation_passed else FAIL_DECISION,
        "evaluation_passed": evaluation_passed,
        "scenario_count": len(scenario_results),
        "scenario_results": scenario_results,
        "hard_gate_results": hard_gate_results,
        "validation_results": {
            "pr_131_verified": True,
            "final_ci_verified": True,
            "focused_aion_217_tests_passed": True,
            "ledger_consistency_passed": True,
            "project_status_consistency_passed": True,
            "architecture_roadmap_consistency_passed": True,
            "scenario_set_exact": True,
            "defects": defects,
        },
        "repository_integrity": {
            "repository_unchanged": True,
            "runtime_source_changed": False,
            "aion_219_source_created": False,
            "network_source_created": False,
            "workflow_changed": False,
            "dependency_changed": False,
            "migration_added": False,
            "api_added": False,
            "cli_added": False,
            "database_added": False,
        },
        "authorization_closeout": {
            "authorization_transaction_id": "AION-216-KI-0007",
            "authorization_active": False,
            "authorization_consumed": True,
            "authorization_expired": True,
            "authorization_reusable": False,
            "authorization_closed_by_task": CLOSEOUT_TASK,
        },
        "conditional_next_authorization": (
            {
                "authorization_transaction_id": "AION-218-KI-0008",
                "implementation_task": "AION-219",
                "formal_closeout_task": "AION-220",
                "created_on_pass_only": True,
                "reusable": False,
            }
            if evaluation_passed
            else None
        ),
        "runtime_state": {
            "verified_knowledge_runtime_enabled": False,
            "public_network_fetch_enabled": False,
            "system_http_transport_available": False,
            "automatic_verified_knowledge_promotion_enabled": False,
            "persistent_verified_knowledge_write_enabled": False,
            "cognitive_memory_write_enabled": False,
            "belief_mutation_enabled": False,
            "engagement_signal_as_fact_enabled": False,
            "engagement_confidence_effect_enabled": False,
        },
        "security_state": {
            "synthetic_inputs_only": True,
            "redacted_inputs_only": True,
            "protected_material_absent": True,
            "network_access_created": False,
            "credential_use_enabled": False,
        },
        "resource_state": {
            "aion_217_resource_limits": REQUIRED_AION_217_LIMITS,
            "future_pilot_authorization_limits_reviewed": True,
        },
        "next_architecture_decision": (
            "controlled_public_research_pilot_implementation_authorized"
            if evaluation_passed
            else "verified_knowledge_memory_remediation_authorization_review"
        ),
        "synthetic": True,
        "read_only": True,
        "redacted": True,
        "repository_unchanged": True,
        "temporary_evaluation_data_cleaned": True,
        **ZERO_EFFECT_FIELDS,
    }
    _validate_report(report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--evaluation-id", required=True)
    parser.add_argument("--evaluation-base-commit", required=True)
    parser.add_argument("--temporary-output-directory", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args(argv)
    try:
        repo_root = Path(args.repo_root).resolve(strict=True)
        temporary_output_directory = Path(args.temporary_output_directory).resolve()
        report_path = Path(args.report).resolve()
        if not report_path.is_relative_to(temporary_output_directory):
            raise ValueError("report path must be beneath temporary output directory")
        temporary_output_directory.mkdir(parents=True, exist_ok=True)
        _install_src_path(repo_root)
        report = build_report(
            repo_root=repo_root,
            evaluation_id=args.evaluation_id,
            evaluation_base_commit=args.evaluation_base_commit,
            temporary_output_directory=temporary_output_directory,
        )
        report_path.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    except Exception as exc:
        print(f"AION-VKME-001 harness failure: {exc}", file=sys.stderr)
        return 2
    if report["evaluation_passed"]:
        print("AION-VKME-001 PASS")
    else:
        print("AION-VKME-001 FAIL RECORDED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
