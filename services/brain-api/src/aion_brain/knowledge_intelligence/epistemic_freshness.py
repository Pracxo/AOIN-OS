"""Deterministic freshness evaluation for epistemic assessment."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from aion_brain.contracts.knowledge_epistemic_assessment import (
    EpistemicFreshnessPolicy,
    FreshnessStatus,
    quantize_score,
)
from aion_brain.contracts.knowledge_source_registry import (
    RegisteredCitationReference,
    RegisteredDeduplicationDecision,
    RegisteredSourceLineage,
    RegisteredSourceProvenance,
    RegisteredSourceSnapshotDigest,
    SourceRegistryPayload,
)


@dataclass(frozen=True)
class FreshnessEvaluation:
    """Freshness status and bounded score."""

    status: FreshnessStatus
    factor: Decimal
    reason_code: str
    evidence_timestamp: datetime | None


def source_registry_payload_timestamp(payload: SourceRegistryPayload) -> datetime | None:
    """Select a deterministic source metadata timestamp without consulting a clock."""

    if isinstance(payload, RegisteredSourceSnapshotDigest):
        return (
            payload.modification_timestamp
            or payload.publication_timestamp
            or payload.retrieval_timestamp
        )
    if isinstance(payload, RegisteredSourceProvenance):
        return (
            payload.declared_modification_timestamp
            or payload.declared_publication_timestamp
            or payload.retrieval_timestamp
        )
    if isinstance(payload, RegisteredCitationReference):
        return payload.retrieval_timestamp
    if isinstance(payload, (RegisteredSourceLineage, RegisteredDeduplicationDecision)):
        return payload.created_at
    return None


def evaluate_payload_freshness(
    payload: SourceRegistryPayload | None,
    *,
    policy: EpistemicFreshnessPolicy,
    assessment_time: datetime,
) -> FreshnessEvaluation:
    """Evaluate one payload freshness from explicit timestamps only."""

    timestamp = source_registry_payload_timestamp(payload) if payload is not None else None
    if timestamp is None:
        return FreshnessEvaluation(
            status=FreshnessStatus.UNKNOWN,
            factor=quantize_score("0.000000"),
            reason_code="epistemic_freshness_unknown",
            evidence_timestamp=None,
        )
    age_seconds = (assessment_time - timestamp).total_seconds()
    if age_seconds < -policy.future_timestamp_tolerance_seconds:
        return FreshnessEvaluation(
            status=FreshnessStatus.UNKNOWN,
            factor=quantize_score("0.000000"),
            reason_code="epistemic_freshness_unknown",
            evidence_timestamp=timestamp,
        )
    if age_seconds <= policy.current_max_age_seconds:
        return FreshnessEvaluation(
            status=FreshnessStatus.CURRENT,
            factor=quantize_score("1.000000"),
            reason_code="epistemic_freshness_current",
            evidence_timestamp=timestamp,
        )
    if age_seconds <= policy.stale_after_seconds:
        return FreshnessEvaluation(
            status=FreshnessStatus.AGEING,
            factor=quantize_score("0.650000"),
            reason_code="epistemic_freshness_ageing",
            evidence_timestamp=timestamp,
        )
    return FreshnessEvaluation(
        status=FreshnessStatus.STALE,
        factor=quantize_score("0.250000"),
        reason_code="epistemic_freshness_stale",
        evidence_timestamp=timestamp,
    )


def aggregate_freshness_status(statuses: tuple[FreshnessStatus, ...]) -> FreshnessStatus:
    """Aggregate counted evidence freshness conservatively."""

    if not statuses:
        return FreshnessStatus.UNKNOWN
    if FreshnessStatus.RETRACTED in statuses:
        return FreshnessStatus.RETRACTED
    if FreshnessStatus.SUPERSEDED in statuses:
        return FreshnessStatus.SUPERSEDED
    if all(status == FreshnessStatus.STALE for status in statuses):
        return FreshnessStatus.STALE
    if FreshnessStatus.STALE in statuses or FreshnessStatus.AGEING in statuses:
        return FreshnessStatus.AGEING
    if all(status == FreshnessStatus.CURRENT for status in statuses):
        return FreshnessStatus.CURRENT
    return FreshnessStatus.UNKNOWN


__all__ = [
    "FreshnessEvaluation",
    "aggregate_freshness_status",
    "evaluate_payload_freshness",
    "source_registry_payload_timestamp",
]
