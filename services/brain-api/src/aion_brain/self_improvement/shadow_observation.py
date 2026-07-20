"""Read-only reference resolution and shadow observations."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from typing import Protocol

from pydantic import BaseModel, Field, field_validator, model_validator

from aion_brain.contracts.self_improvement_shadow import (
    FROZEN_MODEL_CONFIG,
    SHADOW_OBSERVATION_SCHEMA_VERSION,
    ShadowPatternType,
    ShadowRedactedMetric,
    ShadowReference,
    fingerprint_model,
    require_fingerprint,
    require_safe_identifier,
    require_utc_datetime,
    validate_shadow_text,
)
from aion_brain.self_improvement.shadow_redaction import validate_shadow_safe_value


class ShadowReferenceResolutionError(RuntimeError):
    """Fail-closed reference resolution error with a fixed reason code."""


class ShadowReferenceSnapshot(BaseModel):
    """Resolved redacted snapshot supplied by an injected read-only adapter."""

    model_config = FROZEN_MODEL_CONFIG

    reference: ShadowReference
    summary: str = Field(min_length=1, max_length=512)
    metrics: tuple[ShadowRedactedMetric, ...] = Field(min_length=1, max_length=1000)
    evidence_reference_fingerprints: tuple[str, ...] = Field(min_length=1, max_length=1000)
    source_record_version: str = Field(min_length=1, max_length=128)
    resolved_at: datetime
    redacted: bool = True
    read_only: bool = True
    runtime_effect: bool = False
    fingerprint: str = ""

    @field_validator("summary")
    @classmethod
    def summary_is_safe(cls, value: str) -> str:
        return validate_shadow_text(value, max_length=512)

    @field_validator("evidence_reference_fingerprints")
    @classmethod
    def evidence_fingerprints_are_sha256(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if len(value) != len(set(value)):
            raise ValueError("duplicate shadow evidence fingerprint")
        return tuple(require_fingerprint(item) for item in value)

    @field_validator("source_record_version")
    @classmethod
    def source_record_version_is_safe(cls, value: str) -> str:
        return require_safe_identifier(value, "source_record_version")

    @field_validator("resolved_at")
    @classmethod
    def resolved_at_is_utc(cls, value: datetime) -> datetime:
        return require_utc_datetime(value)

    @model_validator(mode="after")
    def snapshot_is_safe(self) -> ShadowReferenceSnapshot:
        if not self.redacted or not self.read_only or self.runtime_effect:
            raise ValueError("shadow snapshots must be redacted, read-only, and inert")
        validate_shadow_safe_value(
            {
                "summary": self.summary,
                "source_record_version": self.source_record_version,
                "evidence_reference_fingerprints": self.evidence_reference_fingerprints,
            }
        )
        if not self.fingerprint:
            object.__setattr__(self, "fingerprint", fingerprint_model(self))
        return self


class ShadowReferenceAdapter(Protocol):
    """Explicit read-only adapter used by an operator-invoked shadow run."""

    def resolve(self, reference: ShadowReference) -> ShadowReferenceSnapshot:
        """Resolve an exact reference to a redacted snapshot."""


class DisabledShadowReferenceAdapter:
    """Fail-closed default adapter."""

    def resolve(self, reference: ShadowReference) -> ShadowReferenceSnapshot:  # noqa: ARG002
        raise ShadowReferenceResolutionError("shadow_reference_adapter_disabled")


class InMemoryShadowReferenceAdapter:
    """Immutable in-memory adapter for tests and explicit offline operator runs."""

    def __init__(self, snapshots: Iterable[ShadowReferenceSnapshot]) -> None:
        mapping: dict[tuple[str, str], ShadowReferenceSnapshot] = {}
        for snapshot in tuple(snapshots):
            key = (snapshot.reference.reference_kind, snapshot.reference.reference_id)
            if key in mapping:
                raise ValueError("duplicate shadow reference snapshot")
            mapping[key] = snapshot
        self._snapshots = mapping.copy()

    def resolve(self, reference: ShadowReference) -> ShadowReferenceSnapshot:
        key = (reference.reference_kind, reference.reference_id)
        snapshot = self._snapshots.get(key)
        if snapshot is None:
            raise ShadowReferenceResolutionError("shadow_reference_unavailable")
        if snapshot.reference.reference_fingerprint != reference.reference_fingerprint:
            raise ShadowReferenceResolutionError("shadow_reference_fingerprint_mismatch")
        if snapshot.reference != reference:
            raise ShadowReferenceResolutionError("shadow_reference_unavailable")
        return snapshot


class ShadowObservationRecord(BaseModel):
    """One deterministic read-only observation derived from a resolved snapshot."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: str = SHADOW_OBSERVATION_SCHEMA_VERSION
    observation_id: str = Field(min_length=1, max_length=128)
    source_reference: ShadowReference
    problem_category: ShadowPatternType
    problem_summary: str = Field(min_length=1, max_length=512)
    metrics: tuple[ShadowRedactedMetric, ...] = Field(min_length=1, max_length=1000)
    weakest_metric: str = Field(min_length=1, max_length=128)
    weakest_metric_value: float = Field(ge=0.0)
    target_metric_value: float = Field(ge=0.0)
    repeated_count: int = Field(ge=1, le=1000)
    evidence_reference_fingerprints: tuple[str, ...] = Field(min_length=1, max_length=1000)
    review_state: str = "shadow_observed"
    created_at: object
    shadow_mode: bool = True
    shadow_only: bool = True
    operator_review_required: bool = True
    implementation_authorization_created: bool = False
    approval_created: bool = False
    source_modified: bool = False
    git_mutated: bool = False
    pull_request_created: bool = False
    merged: bool = False
    runtime_effect: bool = False
    active_learning_promoted: bool = False
    fingerprint: str = ""

    @field_validator("observation_id")
    @classmethod
    def observation_id_is_safe(cls, value: str) -> str:
        return require_safe_identifier(value, "observation_id")

    @field_validator("problem_summary")
    @classmethod
    def problem_summary_is_safe(cls, value: str) -> str:
        return validate_shadow_text(value, max_length=512)

    @field_validator("weakest_metric")
    @classmethod
    def weakest_metric_is_safe(cls, value: str) -> str:
        return require_safe_identifier(value, "weakest_metric")

    @field_validator("evidence_reference_fingerprints")
    @classmethod
    def evidence_fingerprints_are_sha256(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if len(value) != len(set(value)):
            raise ValueError("duplicate shadow evidence fingerprint")
        return tuple(require_fingerprint(item) for item in value)

    @field_validator("created_at")
    @classmethod
    def created_at_is_utc(cls, value: datetime) -> datetime:
        return require_utc_datetime(value)

    @model_validator(mode="after")
    def observation_is_inert(self) -> ShadowObservationRecord:
        if self.review_state != "shadow_observed":
            raise ValueError("shadow observation state must be shadow_observed")
        if not all((self.shadow_mode, self.shadow_only, self.operator_review_required)):
            raise ValueError("shadow observation must require operator review")
        if any(
            (
                self.implementation_authorization_created,
                self.approval_created,
                self.source_modified,
                self.git_mutated,
                self.pull_request_created,
                self.merged,
                self.runtime_effect,
                self.active_learning_promoted,
            )
        ):
            raise ValueError("shadow observation cannot create side effects")
        if not self.fingerprint:
            object.__setattr__(self, "fingerprint", fingerprint_model(self))
        return self


def observation_from_shadow_snapshot(
    snapshot: ShadowReferenceSnapshot,
    *,
    observation_id: str,
    created_at: datetime,
) -> ShadowObservationRecord:
    """Create a deterministic observation from an already-resolved snapshot."""

    weakest = _weakest_metric(snapshot.metrics)
    category = _problem_category(weakest.metric_name)
    return ShadowObservationRecord(
        observation_id=observation_id,
        source_reference=snapshot.reference,
        problem_category=category,
        problem_summary=snapshot.summary,
        metrics=snapshot.metrics,
        weakest_metric=weakest.metric_name,
        weakest_metric_value=weakest.current_value,
        target_metric_value=weakest.target_value,
        repeated_count=snapshot.reference.repeated_count,
        evidence_reference_fingerprints=snapshot.evidence_reference_fingerprints,
        created_at=created_at,
    )


def _weakest_metric(metrics: tuple[ShadowRedactedMetric, ...]) -> ShadowRedactedMetric:
    def gap(metric: ShadowRedactedMetric) -> tuple[float, str]:
        if metric.higher_is_better:
            return (max(0.0, metric.target_value - metric.current_value), metric.metric_name)
        return (max(0.0, metric.current_value - metric.target_value), metric.metric_name)

    return max(sorted(metrics, key=lambda item: item.metric_name), key=gap)


def _problem_category(metric_name: str) -> ShadowPatternType:
    lowered = metric_name.lower()
    if "retrieval" in lowered or "memory" in lowered:
        return "retrieval_failure"
    if "plan" in lowered or "planning" in lowered:
        return "planning_failure"
    if "evidence" in lowered or "grounding" in lowered:
        return "evidence_grounding_failure"
    if "policy_violation" in lowered or "blocked_policy" in lowered or "policy" in lowered:
        return "policy_block"
    if "regression" in lowered:
        return "regression_drift"
    if "replay" in lowered:
        return "replay_drift"
    return "generic_failure"


__all__ = [
    "DisabledShadowReferenceAdapter",
    "InMemoryShadowReferenceAdapter",
    "ShadowObservationRecord",
    "ShadowReferenceAdapter",
    "ShadowReferenceResolutionError",
    "ShadowReferenceSnapshot",
    "observation_from_shadow_snapshot",
]
