"""Deterministic non-factual engagement-learning candidates."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime

from aion_brain.contracts.knowledge_verified_memory import (
    ENGAGEMENT_LEARNING_BATCH_SCHEMA_VERSION,
    ENGAGEMENT_LEARNING_CANDIDATE_SCHEMA_VERSION,
    VERIFIED_KNOWLEDGE_INTEGRITY_SCHEMA_VERSION,
    EngagementLearningCandidate,
    EngagementLearningCandidateBatch,
    EngagementLearningCandidateKind,
    EngagementLearningLifecycleStatus,
    EngagementSignalBatch,
    EngagementSignalKind,
    EngagementSignalMetadata,
    VerifiedKnowledgeIntegrityFinding,
    VerifiedKnowledgeIntegrityReport,
    VerifiedKnowledgeIntegrityStatus,
    utc_now,
    verified_knowledge_fingerprint,
)
from aion_brain.knowledge_intelligence.engagement_signal_policy import (
    validate_engagement_signal,
)


def _learning_kind(signal: EngagementSignalMetadata) -> EngagementLearningCandidateKind:
    fields = " ".join((signal.bounded_outcome_code, *signal.metadata_codes))
    if "preference" in fields:
        return EngagementLearningCandidateKind.PREFERENCE_CANDIDATE
    if "domain-routing" in fields:
        return EngagementLearningCandidateKind.DOMAIN_ROUTING
    if "verification-rule" in fields:
        return EngagementLearningCandidateKind.VERIFICATION_RULE
    if "tool-manifest" in fields or "missing-explicit-tool-capability" in fields:
        return EngagementLearningCandidateKind.TOOL_MANIFEST_GAP
    if signal.signal_kind is EngagementSignalKind.QUERY_REPEATED:
        return EngagementLearningCandidateKind.RESEARCH_GAP
    if signal.signal_kind in {
        EngagementSignalKind.CLARIFICATION_REQUESTED,
        EngagementSignalKind.FOLLOW_UP_REQUESTED,
    }:
        return EngagementLearningCandidateKind.CLARIFICATION_NEED
    if signal.signal_kind is EngagementSignalKind.RETRIEVAL_FAILED:
        return EngagementLearningCandidateKind.RETRIEVAL_STRATEGY
    if signal.signal_kind is EngagementSignalKind.RETRIEVAL_SUCCEEDED:
        return EngagementLearningCandidateKind.SOURCE_SELECTION
    return EngagementLearningCandidateKind.RESPONSE_QUALITY


def _target_codes(kind: EngagementLearningCandidateKind) -> tuple[str, str]:
    mapping = {
        EngagementLearningCandidateKind.RESEARCH_GAP: (
            "research-acquisition",
            "research-gap-review",
        ),
        EngagementLearningCandidateKind.CLARIFICATION_NEED: (
            "operator-dialogue",
            "clarification-review",
        ),
        EngagementLearningCandidateKind.RETRIEVAL_STRATEGY: (
            "retrieval-planning",
            "retrieval-strategy-review",
        ),
        EngagementLearningCandidateKind.SOURCE_SELECTION: (
            "source-registry",
            "source-selection-review",
        ),
        EngagementLearningCandidateKind.DOMAIN_ROUTING: (
            "domain-expert-mesh",
            "domain-routing-review",
        ),
        EngagementLearningCandidateKind.VERIFICATION_RULE: (
            "tool-verification",
            "verification-rule-review",
        ),
        EngagementLearningCandidateKind.TOOL_MANIFEST_GAP: (
            "tool-manifest-registry",
            "tool-manifest-gap-review",
        ),
        EngagementLearningCandidateKind.RESPONSE_QUALITY: (
            "operator-response",
            "response-quality-review",
        ),
        EngagementLearningCandidateKind.PREFERENCE_CANDIDATE: (
            "preference-review",
            "operator-preference-review",
        ),
    }
    return mapping[kind]


def _build_learning_candidate(
    *,
    kind: EngagementLearningCandidateKind,
    signals: tuple[EngagementSignalMetadata, ...],
    candidate_version: int = 1,
    supersedes_candidate_id: str | None = None,
    created_at: datetime | None = None,
    expires_at: datetime | None = None,
) -> EngagementLearningCandidate:
    signal_ids = tuple(signal.signal_id for signal in signals)
    signal_fingerprints = tuple(signal.signal_fingerprint for signal in signals)
    target_component_code, target_policy_code = _target_codes(kind)
    digest = verified_knowledge_fingerprint(
        {
            "candidate_kind": kind.value,
            "signal_fingerprints": signal_fingerprints,
            "target_component_code": target_component_code,
            "target_policy_code": target_policy_code,
        }
    )
    payload = {
        "schema_version": ENGAGEMENT_LEARNING_CANDIDATE_SCHEMA_VERSION,
        "learning_candidate_id": f"engagement-learning-{digest[:48]}-v{candidate_version:03d}",
        "candidate_kind": kind,
        "signal_ids": signal_ids,
        "signal_fingerprints": signal_fingerprints,
        "target_component_code": target_component_code,
        "target_policy_code": target_policy_code,
        "reason_codes": (
            "engagement_learning_candidate_proposed",
            "engagement_learning_candidate_operator_review_required",
            "engagement_learning_candidate_automatic_application_blocked",
            "engagement_learning_candidate_model_training_blocked",
        ),
        "lifecycle_status": EngagementLearningLifecycleStatus.PROPOSED,
        "candidate_version": candidate_version,
        "supersedes_candidate_id": supersedes_candidate_id,
        "created_at": created_at or utc_now(),
        "expires_at": expires_at,
        "operator_review_required": True,
        "automatic_application": False,
        "factual_effect": False,
        "confidence_effect": False,
        "knowledge_effect": False,
        "cognitive_memory_effect": False,
        "belief_effect": False,
        "model_weight_effect": False,
        "runtime_effect": False,
    }
    return EngagementLearningCandidate.model_validate(
        {**payload, "candidate_fingerprint": verified_knowledge_fingerprint(payload)}
    )


def build_engagement_learning_candidates(
    *,
    batch_id: str,
    signal_batch: EngagementSignalBatch,
    created_at: datetime | None = None,
) -> EngagementLearningCandidateBatch:
    """Map bounded engagement metadata to operator-review learning candidates."""

    grouped: dict[EngagementLearningCandidateKind, list[EngagementSignalMetadata]] = {}
    for signal in signal_batch.signals:
        checked = validate_engagement_signal(signal)
        grouped.setdefault(_learning_kind(checked), []).append(checked)
    candidates = tuple(
        sorted(
            (
                _build_learning_candidate(
                    kind=kind,
                    signals=tuple(sorted(signals, key=lambda item: item.signal_id)),
                    created_at=created_at,
                )
                for kind, signals in grouped.items()
            ),
            key=lambda candidate: candidate.learning_candidate_id,
        )
    )
    payload = {
        "schema_version": ENGAGEMENT_LEARNING_BATCH_SCHEMA_VERSION,
        "batch_id": batch_id,
        "candidates": candidates,
        "candidate_count": len(candidates),
        "automatic_application": False,
        "model_weight_effect": False,
        "runtime_effect": False,
    }
    return EngagementLearningCandidateBatch.model_validate(
        {**payload, "batch_fingerprint": verified_knowledge_fingerprint(payload)}
    )


def version_engagement_learning_candidate(
    candidate: EngagementLearningCandidate,
    *,
    created_at: datetime | None = None,
    expires_at: datetime | None = None,
) -> EngagementLearningCandidate:
    """Create an immutable follow-up learning-candidate version."""

    return _build_learning_candidate(
        kind=candidate.candidate_kind,
        signals=tuple(
            EngagementSignalMetadata.model_construct(
                signal_id=signal_id,
                signal_fingerprint=fingerprint,
            )
            for signal_id, fingerprint in zip(
                candidate.signal_ids, candidate.signal_fingerprints, strict=True
            )
        ),
        candidate_version=candidate.candidate_version + 1,
        supersedes_candidate_id=candidate.learning_candidate_id,
        created_at=created_at,
        expires_at=expires_at,
    )


def audit_engagement_learning_candidates(
    batch: EngagementLearningCandidateBatch,
) -> VerifiedKnowledgeIntegrityReport:
    """Audit engagement-learning candidates for non-application controls."""

    status = VerifiedKnowledgeIntegrityStatus.PASSED
    reason = "verified_memory_integrity_passed"
    for candidate in batch.candidates:
        if any(
            (
                candidate.automatic_application,
                candidate.factual_effect,
                candidate.confidence_effect,
                candidate.knowledge_effect,
                candidate.cognitive_memory_effect,
                candidate.belief_effect,
                candidate.model_weight_effect,
                candidate.runtime_effect,
            )
        ):
            status = VerifiedKnowledgeIntegrityStatus.FAILED
            reason = "verified_memory_integrity_failed"
            break
    finding = VerifiedKnowledgeIntegrityFinding.model_validate(
        {
            "finding_id": f"finding-{batch.batch_id}",
            "status": status,
            "reason_codes": (reason, "engagement_learning_candidate_proposed"),
            "safe_ids": (batch.batch_id,),
            "fingerprints": tuple(
                sorted(candidate.candidate_fingerprint for candidate in batch.candidates)
            ),
            "bounded_count": batch.candidate_count,
            "redacted_summary": "engagement learning candidate audit",
            "runtime_effect": False,
        }
    )
    payload = {
        "schema_version": VERIFIED_KNOWLEDGE_INTEGRITY_SCHEMA_VERSION,
        "report_id": f"integrity-{batch.batch_id}",
        "status": status,
        "findings": (finding,),
        "finding_count": 1,
        "read_only": True,
        "redacted": True,
        "persistent_write_applied": False,
        "runtime_effect": False,
    }
    return VerifiedKnowledgeIntegrityReport.model_validate(
        {**payload, "report_fingerprint": verified_knowledge_fingerprint(payload)}
    )


def build_engagement_learning_candidate_batch(
    *,
    batch_id: str,
    candidates: Iterable[EngagementLearningCandidate],
) -> EngagementLearningCandidateBatch:
    """Build a deterministic engagement-learning candidate batch."""

    ordered = tuple(sorted(candidates, key=lambda candidate: candidate.learning_candidate_id))
    payload = {
        "schema_version": ENGAGEMENT_LEARNING_BATCH_SCHEMA_VERSION,
        "batch_id": batch_id,
        "candidates": ordered,
        "candidate_count": len(ordered),
        "automatic_application": False,
        "model_weight_effect": False,
        "runtime_effect": False,
    }
    return EngagementLearningCandidateBatch.model_validate(
        {**payload, "batch_fingerprint": verified_knowledge_fingerprint(payload)}
    )


__all__ = [
    "audit_engagement_learning_candidates",
    "build_engagement_learning_candidate_batch",
    "build_engagement_learning_candidates",
    "version_engagement_learning_candidate",
]
