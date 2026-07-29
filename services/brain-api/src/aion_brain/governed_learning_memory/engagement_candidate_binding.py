"""Candidate and signal-lineage binding for AION-226 shadow application."""

from __future__ import annotations

from datetime import datetime

from aion_brain.contracts.governed_engagement_learning import (
    EngagementCandidateBinding,
    EngagementCandidateDisposition,
    EngagementCandidateLifecycleEvidence,
    build_record,
    target_spec_for_candidate_kind,
    utc_now,
)
from aion_brain.contracts.knowledge_verified_memory import (
    EngagementLearningCandidate,
    EngagementLearningLifecycleStatus,
    EngagementSignalBatch,
)
from aion_brain.knowledge_intelligence.engagement_learning_candidates import (
    audit_engagement_learning_candidates,
    build_engagement_learning_candidate_batch,
)
from aion_brain.knowledge_intelligence.engagement_signal_policy import (
    audit_engagement_signal_batch,
    validate_engagement_signal,
)

_ALLOWED_LIFECYCLE = {
    EngagementLearningLifecycleStatus.PROPOSED,
    EngagementLearningLifecycleStatus.OPERATOR_REVIEW_PENDING,
}


def build_lifecycle_evidence(
    *,
    lifecycle_evidence_id: str,
    candidate: EngagementLearningCandidate,
    observed_at: datetime | None = None,
    valid_until: datetime,
    lifecycle_status: EngagementLearningLifecycleStatus | None = None,
    retraction_record_fingerprint: str | None = None,
) -> EngagementCandidateLifecycleEvidence:
    """Project externally supplied lifecycle evidence without persistence."""

    payload = {
        "lifecycle_evidence_id": lifecycle_evidence_id,
        "learning_candidate_id": candidate.learning_candidate_id,
        "candidate_fingerprint": candidate.candidate_fingerprint,
        "candidate_version": candidate.candidate_version,
        "lifecycle_status": lifecycle_status or candidate.lifecycle_status,
        "supersedes_candidate_id": candidate.supersedes_candidate_id,
        "retraction_record_fingerprint": retraction_record_fingerprint,
        "observed_at": observed_at or utc_now(),
        "valid_until": valid_until,
        "externally_supplied": True,
        "read_only": True,
        "redacted": True,
    }
    return build_record(
        EngagementCandidateLifecycleEvidence,
        payload,
        "lifecycle_fingerprint",
    )


def bind_engagement_candidate(
    *,
    binding_id: str,
    candidate: EngagementLearningCandidate,
    signal_batch: EngagementSignalBatch,
    lifecycle_evidence: EngagementCandidateLifecycleEvidence,
) -> EngagementCandidateBinding:
    """Bind a candidate to exact signal lineage and closed target mapping."""

    for signal in signal_batch.signals:
        validate_engagement_signal(signal)
    if audit_engagement_signal_batch(signal_batch).status.value != "passed":
        raise ValueError("engagement signal lineage invalid")
    candidate_batch = build_engagement_learning_candidate_batch(
        batch_id=f"binding-batch-{binding_id}",
        candidates=(candidate,),
    )
    if audit_engagement_learning_candidates(candidate_batch).status.value != "passed":
        raise ValueError("engagement candidate audit failed")

    signal_by_id = {signal.signal_id: signal for signal in signal_batch.signals}
    signal_ids = candidate.signal_ids
    signal_fingerprints = tuple(
        signal_by_id[signal_id].signal_fingerprint for signal_id in signal_ids
    )
    if signal_fingerprints != candidate.signal_fingerprints:
        raise ValueError("candidate signal fingerprint mismatch")
    spec = target_spec_for_candidate_kind(candidate.candidate_kind)
    if (
        candidate.target_component_code != spec.target_component_code
        or candidate.target_policy_code != spec.target_policy_code
    ):
        raise ValueError("candidate target mapping mismatch")

    now = lifecycle_evidence.observed_at
    disposition = EngagementCandidateDisposition.ELIGIBLE_FOR_SHADOW
    reasons = [
        "engagement_candidate_binding_valid",
        "engagement_signal_lineage_valid",
        "engagement_candidate_non_factual_passed",
        "engagement_candidate_zero_confidence_effect_passed",
        "engagement_candidate_zero_knowledge_effect_passed",
        "engagement_candidate_zero_source_independence_effect_passed",
        "engagement_candidate_zero_belief_effect_passed",
        "engagement_candidate_version_valid",
    ]
    def add_reason(reason: str) -> None:
        if reason not in reasons:
            reasons.append(reason)

    if candidate.lifecycle_status not in _ALLOWED_LIFECYCLE:
        disposition = EngagementCandidateDisposition.INELIGIBLE
        add_reason("engagement_candidate_rejected")
    if candidate.expires_at is not None and candidate.expires_at <= now:
        disposition = EngagementCandidateDisposition.EXPIRED
        add_reason("engagement_candidate_expired")
    if candidate.lifecycle_status is EngagementLearningLifecycleStatus.SUPERSEDED:
        disposition = EngagementCandidateDisposition.SUPERSEDED
        add_reason("engagement_candidate_superseded")
    if candidate.lifecycle_status is EngagementLearningLifecycleStatus.OPERATOR_REVIEW_REJECTED:
        disposition = EngagementCandidateDisposition.REJECTED
        add_reason("engagement_candidate_rejected")
    if lifecycle_evidence.retraction_record_fingerprint is not None:
        disposition = EngagementCandidateDisposition.RETRACTED
        add_reason("engagement_candidate_retracted")

    payload = {
        "binding_id": binding_id,
        "candidate": candidate,
        "signal_batch": signal_batch,
        "learning_candidate_id": candidate.learning_candidate_id,
        "candidate_fingerprint": candidate.candidate_fingerprint,
        "candidate_kind": candidate.candidate_kind,
        "candidate_version": candidate.candidate_version,
        "lifecycle_status": candidate.lifecycle_status,
        "signal_ids": signal_ids,
        "signal_fingerprints": signal_fingerprints,
        "subject_fingerprints": tuple(
            sorted(signal_by_id[signal_id].subject_fingerprint for signal_id in signal_ids)
        ),
        "target_component_code": spec.target_component_code,
        "target_policy_code": spec.target_policy_code,
        "canonical_operation": spec.canonical_operation,
        "lifecycle_evidence": lifecycle_evidence,
        "candidate_disposition": disposition,
        "reason_codes": tuple(reasons),
        "non_factual_invariant_passed": disposition
        is EngagementCandidateDisposition.ELIGIBLE_FOR_SHADOW,
        "zero_confidence_effect_passed": not candidate.confidence_effect,
        "zero_knowledge_effect_passed": not candidate.knowledge_effect,
        "zero_source_independence_effect_passed": True,
        "zero_belief_effect_passed": not candidate.belief_effect,
        "read_only": True,
        "redacted": True,
        "runtime_effect": False,
    }
    return build_record(EngagementCandidateBinding, payload, "binding_fingerprint")


def bind_engagement_candidates(
    *,
    signal_batch: EngagementSignalBatch,
    candidates: tuple[EngagementLearningCandidate, ...],
    observed_at: datetime | None = None,
    valid_until: datetime,
) -> tuple[EngagementCandidateBinding, ...]:
    """Bind candidates deterministically in candidate-id order."""

    return tuple(
        bind_engagement_candidate(
            binding_id=f"binding-{candidate.learning_candidate_id}",
            candidate=candidate,
            signal_batch=signal_batch,
            lifecycle_evidence=build_lifecycle_evidence(
                lifecycle_evidence_id=f"lifecycle-{candidate.learning_candidate_id}",
                candidate=candidate,
                observed_at=observed_at,
                valid_until=valid_until,
            ),
        )
        for candidate in sorted(candidates, key=lambda item: item.learning_candidate_id)
    )


__all__ = [
    "bind_engagement_candidate",
    "bind_engagement_candidates",
    "build_lifecycle_evidence",
]
