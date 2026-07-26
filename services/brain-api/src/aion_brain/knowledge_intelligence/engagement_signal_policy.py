"""Bounded non-factual engagement signal policy."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime

from aion_brain.contracts.knowledge_verified_memory import (
    ENGAGEMENT_SIGNAL_BATCH_SCHEMA_VERSION,
    ENGAGEMENT_SIGNAL_SCHEMA_VERSION,
    VERIFIED_KNOWLEDGE_INTEGRITY_SCHEMA_VERSION,
    EngagementSignalBatch,
    EngagementSignalKind,
    EngagementSignalMetadata,
    VerifiedKnowledgeIntegrityFinding,
    VerifiedKnowledgeIntegrityReport,
    VerifiedKnowledgeIntegrityStatus,
    reject_verified_knowledge_payload,
    utc_now,
    verified_knowledge_fingerprint,
)

_PROHIBITED_METADATA_MARKERS = (
    "raw_user_message",
    "prompt_transcript",
    "personal_data",
    "credential",
    "token",
    "source_body",
    "click_url",
    "ip_address",
    "device_fingerprint",
)


def validate_engagement_signal(signal: EngagementSignalMetadata) -> EngagementSignalMetadata:
    """Validate a signal while preserving zero factual and confidence effects."""

    for value in (signal.bounded_outcome_code, *signal.metadata_codes):
        lowered = value.lower()
        if any(marker in lowered for marker in _PROHIBITED_METADATA_MARKERS):
            raise ValueError("engagement signal contains protected metadata")
    if any(
        (
            signal.factual_effect,
            signal.confidence_effect,
            signal.source_independence_effect,
            signal.citation_coverage_effect,
            signal.provenance_effect,
            signal.contradiction_resolution_effect,
            signal.freshness_effect,
            signal.knowledge_effect,
            signal.cognitive_memory_effect,
            signal.belief_effect,
            signal.model_weight_effect,
            signal.runtime_effect,
        )
    ):
        raise ValueError("engagement signal must remain non-factual")
    return EngagementSignalMetadata.model_validate(signal.model_dump(mode="python"))


def build_engagement_signal(
    *,
    signal_id: str,
    signal_kind: EngagementSignalKind,
    session_fingerprint: str,
    response_fingerprint: str,
    subject_fingerprint: str,
    bounded_outcome_code: str,
    metadata_codes: Iterable[str] = (),
    occurred_at: datetime | None = None,
) -> EngagementSignalMetadata:
    """Build one bounded engagement signal with no factual effect."""

    metadata = tuple(sorted(metadata_codes))
    reject_verified_knowledge_payload(
        {"bounded_outcome_code": bounded_outcome_code, "metadata_codes": metadata},
        "engagement signal metadata",
    )
    payload = {
        "schema_version": ENGAGEMENT_SIGNAL_SCHEMA_VERSION,
        "signal_id": signal_id,
        "signal_kind": signal_kind,
        "session_fingerprint": session_fingerprint,
        "response_fingerprint": response_fingerprint,
        "subject_fingerprint": subject_fingerprint,
        "bounded_outcome_code": bounded_outcome_code,
        "metadata_codes": metadata,
        "occurred_at": occurred_at or utc_now(),
        "factual_effect": False,
        "confidence_effect": False,
        "source_independence_effect": False,
        "citation_coverage_effect": False,
        "provenance_effect": False,
        "contradiction_resolution_effect": False,
        "freshness_effect": False,
        "knowledge_effect": False,
        "cognitive_memory_effect": False,
        "belief_effect": False,
        "model_weight_effect": False,
        "runtime_effect": False,
    }
    signal = EngagementSignalMetadata.model_validate(
        {**payload, "signal_fingerprint": verified_knowledge_fingerprint(payload)}
    )
    return validate_engagement_signal(signal)


def build_engagement_signal_batch(
    *,
    batch_id: str,
    signals: Iterable[EngagementSignalMetadata],
) -> EngagementSignalBatch:
    """Build a deterministic bounded batch of engagement signals."""

    ordered = tuple(
        sorted(
            (validate_engagement_signal(signal) for signal in signals),
            key=lambda item: item.signal_id,
        )
    )
    payload = {
        "schema_version": ENGAGEMENT_SIGNAL_BATCH_SCHEMA_VERSION,
        "batch_id": batch_id,
        "signals": ordered,
        "signal_count": len(ordered),
        "factual_effect": False,
        "confidence_effect": False,
        "runtime_effect": False,
    }
    return EngagementSignalBatch.model_validate(
        {**payload, "batch_fingerprint": verified_knowledge_fingerprint(payload)}
    )


def audit_engagement_signal_batch(batch: EngagementSignalBatch) -> VerifiedKnowledgeIntegrityReport:
    """Audit engagement-signal non-factual controls."""

    try:
        for signal in batch.signals:
            validate_engagement_signal(signal)
        status = VerifiedKnowledgeIntegrityStatus.PASSED
        reason = "engagement_signal_valid"
    except ValueError:
        status = VerifiedKnowledgeIntegrityStatus.FAILED
        reason = "engagement_signal_invalid"
    finding = VerifiedKnowledgeIntegrityFinding.model_validate(
        {
            "finding_id": f"finding-{batch.batch_id}",
            "status": status,
            "reason_codes": (reason, "engagement_signal_non_factual"),
            "safe_ids": (batch.batch_id,),
            "fingerprints": tuple(sorted(signal.signal_fingerprint for signal in batch.signals)),
            "bounded_count": batch.signal_count,
            "redacted_summary": "engagement signal batch audit",
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


__all__ = [
    "audit_engagement_signal_batch",
    "build_engagement_signal",
    "build_engagement_signal_batch",
    "validate_engagement_signal",
]
