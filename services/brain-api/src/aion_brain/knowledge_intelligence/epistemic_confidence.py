"""Transparent scorecard and hard-cap application."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal

from aion_brain.contracts.knowledge_epistemic_assessment import (
    ConfidenceBand,
    ContradictionStatus,
    EpistemicAssessmentStatus,
    EpistemicHardCapApplication,
    EpistemicScorecard,
    EpistemicScorecardPolicy,
    FreshnessStatus,
    RoleEvidenceScore,
    ScopeApplicability,
    confidence_band_for,
    default_scorecard_policy,
    epistemic_scorecard_fingerprint,
    hard_cap_fingerprint,
    quantize_score,
)


@dataclass(frozen=True)
class ScorecardInputs:
    """Deterministic scorecard inputs for one claim."""

    claim_id: str
    support_score: RoleEvidenceScore
    opposition_score: RoleEvidenceScore
    source_registry_integrity_passed: bool
    claim_graph_integrity_passed: bool
    freshness_status: FreshnessStatus
    scope_applicability: ScopeApplicability
    contradiction_status: ContradictionStatus
    correction_relation_count: int
    retraction_relation_count: int
    supersession_relation_count: int
    duplicate_suppressed_count: int
    mirror_suppressed_count: int
    ambiguous_group_count: int
    only_low_quality_evidence: bool
    missing_citation_coverage: bool
    incomplete_provenance: bool


def build_epistemic_scorecard(
    inputs: ScorecardInputs,
    *,
    policy: EpistemicScorecardPolicy | None = None,
) -> EpistemicScorecard:
    """Build a transparent scorecard with deterministic hard caps."""

    active_policy = policy or default_scorecard_policy()
    base_status = classify_status(inputs, active_policy)
    base_confidence = base_confidence_score(inputs, base_status)
    hard_caps, capped_status, capped_confidence = apply_hard_caps(
        inputs,
        status=base_status,
        confidence=base_confidence,
    )
    reasons = _reason_codes(inputs, capped_status, hard_caps)
    explicit_abstention = (
        capped_confidence < active_policy.abstention_confidence_threshold
        or capped_status
        in {
            EpistemicAssessmentStatus.INSUFFICIENT_EVIDENCE,
            EpistemicAssessmentStatus.SCOPE_MISMATCH,
            EpistemicAssessmentStatus.UNKNOWN,
        }
        or bool(hard_caps)
    )
    if explicit_abstention:
        reasons.append("epistemic_explicit_abstention_required")
    else:
        reasons.append("epistemic_explicit_abstention_not_required")
    payload = {
        "schema_version": "aion-knowledge-epistemic-scorecard/v1",
        "claim_id": inputs.claim_id,
        "policy_fingerprint": active_policy.policy_fingerprint,
        "scorecard_version": "aion-epistemic-scorecard/v1",
        "support_score": inputs.support_score,
        "opposition_score": inputs.opposition_score,
        "status": capped_status,
        "contradiction_status": inputs.contradiction_status,
        "freshness_status": inputs.freshness_status,
        "scope_applicability": inputs.scope_applicability,
        "confidence": capped_confidence,
        "confidence_band": confidence_band_for(capped_confidence),
        "explicit_abstention": explicit_abstention,
        "hard_caps": hard_caps,
        "reason_codes": tuple(dict.fromkeys(reasons)),
        "absolute_truth_claimed": False,
        "claim_accepted": False,
        "claim_rejected": False,
        "knowledge_promoted": False,
        "belief_mutated": False,
        "persistent_write_applied": False,
        "runtime_effect": False,
    }
    return EpistemicScorecard.model_validate(
        {**payload, "scorecard_fingerprint": epistemic_scorecard_fingerprint(payload)}
    )


def classify_status(
    inputs: ScorecardInputs,
    policy: EpistemicScorecardPolicy | None = None,
) -> EpistemicAssessmentStatus:
    """Classify evidence posture without assigning a truth value."""

    active_policy = policy or default_scorecard_policy()
    support = inputs.support_score.raw_role_score
    opposition = inputs.opposition_score.raw_role_score
    if not inputs.source_registry_integrity_passed or not inputs.claim_graph_integrity_passed:
        return EpistemicAssessmentStatus.UNKNOWN
    if inputs.retraction_relation_count:
        return EpistemicAssessmentStatus.RETRACTED
    if inputs.supersession_relation_count and inputs.support_score.independent_group_count < 2:
        return EpistemicAssessmentStatus.SUPERSEDED
    if inputs.scope_applicability == ScopeApplicability.NOT_APPLICABLE:
        return EpistemicAssessmentStatus.SCOPE_MISMATCH
    if inputs.scope_applicability == ScopeApplicability.INSUFFICIENT_SCOPE:
        return EpistemicAssessmentStatus.UNKNOWN
    if (
        inputs.support_score.independent_group_count == 0
        and inputs.opposition_score.independent_group_count == 0
    ):
        return EpistemicAssessmentStatus.INSUFFICIENT_EVIDENCE
    if inputs.freshness_status == FreshnessStatus.STALE and support >= opposition:
        return EpistemicAssessmentStatus.STALE
    if (
        opposition >= active_policy.contradicted_raw_score_threshold
        and (opposition - support) >= active_policy.dominance_margin
    ):
        return EpistemicAssessmentStatus.CONTRADICTED
    if (
        support >= active_policy.supported_raw_score_threshold
        and (support - opposition) >= active_policy.dominance_margin
    ):
        return EpistemicAssessmentStatus.SUPPORTED
    if (
        support >= active_policy.mixed_raw_score_threshold
        and opposition >= active_policy.mixed_raw_score_threshold
    ):
        return EpistemicAssessmentStatus.MIXED
    return EpistemicAssessmentStatus.INSUFFICIENT_EVIDENCE


def base_confidence_score(
    inputs: ScorecardInputs,
    status: EpistemicAssessmentStatus,
) -> Decimal:
    """Compute the uncapped confidence score."""

    if status == EpistemicAssessmentStatus.CONTRADICTED:
        return quantize_score(inputs.opposition_score.raw_role_score)
    if status == EpistemicAssessmentStatus.MIXED:
        return quantize_score(
            (inputs.support_score.raw_role_score + inputs.opposition_score.raw_role_score)
            / Decimal("2")
        )
    if status in {
        EpistemicAssessmentStatus.SUPPORTED,
        EpistemicAssessmentStatus.STALE,
        EpistemicAssessmentStatus.SUPERSEDED,
    }:
        return quantize_score(inputs.support_score.raw_role_score)
    return quantize_score("0.000000")


def apply_hard_caps(
    inputs: ScorecardInputs,
    *,
    status: EpistemicAssessmentStatus,
    confidence: Decimal,
) -> tuple[tuple[EpistemicHardCapApplication, ...], EpistemicAssessmentStatus, Decimal]:
    """Apply deterministic hard caps in the contract order."""

    current_status = status
    current_confidence = quantize_score(confidence)
    caps: list[EpistemicHardCapApplication] = []
    for cap_id, reason_code, limit, forced_status, applies in _cap_rules(inputs):
        if not applies:
            continue
        next_confidence = quantize_score(min(current_confidence, limit))
        if forced_status is not None:
            current_status = forced_status
        payload = {
            "cap_id": cap_id,
            "reason_code": reason_code,
            "pre_cap_confidence": current_confidence,
            "post_cap_confidence": next_confidence,
            "forced_status": forced_status,
            "applied": True,
        }
        caps.append(
            EpistemicHardCapApplication.model_validate(
                {**payload, "cap_fingerprint": hard_cap_fingerprint(payload)}
            )
        )
        current_confidence = next_confidence
    return tuple(caps), current_status, current_confidence


def confidence_band(confidence: Decimal) -> ConfidenceBand:
    """Expose the versioned confidence-band mapping."""

    return confidence_band_for(confidence)


def _cap_rules(
    inputs: ScorecardInputs,
) -> Iterable[tuple[str, str, Decimal, EpistemicAssessmentStatus | None, bool]]:
    yield (
        "broken_source_registry_or_graph_integrity",
        "epistemic_hard_cap_integrity",
        Decimal("0.000000"),
        EpistemicAssessmentStatus.UNKNOWN,
        not inputs.source_registry_integrity_passed or not inputs.claim_graph_integrity_passed,
    )
    yield (
        "applicable_retraction",
        "epistemic_hard_cap_retraction",
        Decimal("0.000000"),
        EpistemicAssessmentStatus.RETRACTED,
        inputs.retraction_relation_count > 0,
    )
    yield (
        "applicable_supersession_without_current_support",
        "epistemic_hard_cap_supersession",
        Decimal("0.200000"),
        EpistemicAssessmentStatus.SUPERSEDED,
        inputs.supersession_relation_count > 0 and inputs.support_score.independent_group_count < 2,
    )
    yield (
        "scope_mismatch",
        "epistemic_hard_cap_scope_mismatch",
        Decimal("0.000000"),
        EpistemicAssessmentStatus.SCOPE_MISMATCH,
        inputs.scope_applicability == ScopeApplicability.NOT_APPLICABLE,
    )
    yield (
        "insufficient_explicit_scope",
        "epistemic_hard_cap_insufficient_scope",
        Decimal("0.000000"),
        EpistemicAssessmentStatus.UNKNOWN,
        inputs.scope_applicability == ScopeApplicability.INSUFFICIENT_SCOPE,
    )
    yield (
        "unresolved_material_opposition",
        "epistemic_hard_cap_material_opposition",
        Decimal("0.600000"),
        None,
        inputs.contradiction_status
        in {ContradictionStatus.MATERIAL, ContradictionStatus.UNRESOLVED},
    )
    total_independent = (
        inputs.support_score.independent_group_count
        + inputs.opposition_score.independent_group_count
    )
    yield (
        "zero_independent_evidence_groups",
        "epistemic_hard_cap_zero_independence",
        Decimal("0.000000"),
        EpistemicAssessmentStatus.INSUFFICIENT_EVIDENCE,
        total_independent == 0,
    )
    yield (
        "one_independent_evidence_group",
        "epistemic_hard_cap_one_independence",
        Decimal("0.400000"),
        None,
        total_independent == 1,
    )
    yield (
        "only_unknown_or_community_unverified_evidence",
        "epistemic_hard_cap_unverified_source_class",
        Decimal("0.400000"),
        None,
        inputs.only_low_quality_evidence and total_independent > 0,
    )
    yield (
        "missing_citation_coverage",
        "epistemic_hard_cap_missing_citation",
        Decimal("0.600000"),
        None,
        inputs.missing_citation_coverage,
    )
    yield (
        "incomplete_provenance",
        "epistemic_hard_cap_incomplete_provenance",
        Decimal("0.700000"),
        None,
        inputs.incomplete_provenance,
    )
    yield (
        "stale_evidence",
        "epistemic_hard_cap_stale_evidence",
        Decimal("0.500000"),
        EpistemicAssessmentStatus.STALE,
        inputs.freshness_status == FreshnessStatus.STALE,
    )


def _reason_codes(
    inputs: ScorecardInputs,
    status: EpistemicAssessmentStatus,
    hard_caps: tuple[EpistemicHardCapApplication, ...],
) -> list[str]:
    codes: list[str] = [
        "epistemic_source_registry_integrity_valid"
        if inputs.source_registry_integrity_passed
        else "epistemic_source_registry_integrity_failed",
        "epistemic_claim_graph_integrity_valid"
        if inputs.claim_graph_integrity_passed
        else "epistemic_claim_graph_integrity_failed",
        _status_reason(status),
    ]
    codes.extend(cap.reason_code for cap in hard_caps)
    return codes


def _status_reason(status: EpistemicAssessmentStatus) -> str:
    return f"epistemic_status_{status.value}"


__all__ = [
    "ScorecardInputs",
    "apply_hard_caps",
    "base_confidence_score",
    "build_epistemic_scorecard",
    "classify_status",
    "confidence_band",
]
