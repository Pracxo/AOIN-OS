"""Deterministic evaluation and ephemeral storage for shadow-mode runs."""

from __future__ import annotations

import threading
from collections.abc import Iterable
from datetime import datetime, timedelta
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from aion_brain.contracts.self_improvement_shadow import (
    DEFAULT_RETENTION_SECONDS,
    FROZEN_MODEL_CONFIG,
    SHADOW_DIAGNOSTIC_SCHEMA_VERSION,
    SHADOW_METRIC_NAMES,
    SHADOW_REASON_CODES,
    ShadowMetricName,
    ShadowRedactedMetric,
    fingerprint_model,
    require_finite_number,
    require_safe_identifier,
    require_utc_datetime,
    utc_now,
)
from aion_brain.self_improvement.shadow_observation import ShadowObservationRecord


class ShadowMetricDrift(BaseModel):
    """Deterministic drift result for one shadow metric."""

    model_config = FROZEN_MODEL_CONFIG

    metric_name: ShadowMetricName
    baseline_value: float = Field(ge=0.0)
    current_value: float = Field(ge=0.0)
    target_value: float = Field(ge=0.0)
    absolute_delta: float = Field(ge=0.0)
    target_gap: float = Field(ge=0.0)
    higher_is_better: bool
    regressed: bool
    target_met: bool
    fingerprint: str = ""

    @field_validator(
        "baseline_value",
        "current_value",
        "target_value",
        "absolute_delta",
        "target_gap",
    )
    @classmethod
    def values_are_finite(cls, value: float) -> float:
        return require_finite_number(value)

    @model_validator(mode="after")
    def set_fingerprint(self) -> ShadowMetricDrift:
        if not self.fingerprint:
            object.__setattr__(self, "fingerprint", fingerprint_model(self))
        return self


class ShadowEvaluationSummary(BaseModel):
    """Immutable deterministic evaluation summary for shadow observations."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: str = SHADOW_DIAGNOSTIC_SCHEMA_VERSION
    evaluation_id: str = Field(min_length=1, max_length=128)
    observation_ids: tuple[str, ...] = Field(default_factory=tuple)
    metric_drifts: tuple[ShadowMetricDrift, ...] = Field(default_factory=tuple)
    weakest_metric: str | None = Field(default=None, max_length=128)
    regression_count: int = Field(ge=0)
    target_miss_count: int = Field(ge=0)
    policy_violation_count: int = Field(ge=0)
    benchmark_cost_units: int = Field(ge=0, le=50)
    review_state: str = "shadow_evaluated"
    created_at: datetime
    implementation_authorization_created: bool = False
    approval_created: bool = False
    source_modified: bool = False
    git_mutated: bool = False
    pull_request_created: bool = False
    merged: bool = False
    runtime_effect: bool = False
    active_learning_promoted: bool = False
    fingerprint: str = ""

    @field_validator("evaluation_id")
    @classmethod
    def evaluation_id_is_safe(cls, value: str) -> str:
        return require_safe_identifier(value, "evaluation_id")

    @field_validator("observation_ids")
    @classmethod
    def observation_ids_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(require_safe_identifier(item, "observation_id") for item in value)

    @field_validator("weakest_metric")
    @classmethod
    def weakest_metric_is_safe(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return require_safe_identifier(value, "weakest_metric")

    @field_validator("created_at")
    @classmethod
    def created_at_is_utc(cls, value: datetime) -> datetime:
        return require_utc_datetime(value)

    @model_validator(mode="after")
    def summary_is_inert(self) -> ShadowEvaluationSummary:
        if self.review_state != "shadow_evaluated":
            raise ValueError("shadow evaluation state must be shadow_evaluated")
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
            raise ValueError("shadow evaluation cannot create side effects")
        if not self.fingerprint:
            object.__setattr__(self, "fingerprint", fingerprint_model(self))
        return self


class EphemeralShadowStore:
    """Per-instance in-memory store with explicit purge only."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._bundles: dict[str, Any] = {}

    def put(self, bundle: Any) -> None:
        run_id = getattr(bundle, "run_id", None)
        if not isinstance(run_id, str) or not run_id:
            raise ValueError("shadow bundle requires run_id")
        with self._lock:
            if run_id in self._bundles:
                raise ValueError("duplicate shadow run id")
            self._bundles[run_id] = bundle

    def get(self, run_id: str) -> Any | None:
        safe_run_id = require_safe_identifier(run_id, "run_id")
        with self._lock:
            return self._bundles.get(safe_run_id)

    def list_run_ids(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(sorted(self._bundles))

    def purge_expired(self, now: datetime) -> tuple[str, ...]:
        checked_now = require_utc_datetime(now)
        expired: list[str] = []
        with self._lock:
            for run_id, bundle in tuple(self._bundles.items()):
                expires_at = getattr(bundle, "expires_at", None)
                if isinstance(expires_at, datetime) and expires_at <= checked_now:
                    expired.append(run_id)
            for run_id in expired:
                del self._bundles[run_id]
        return tuple(expired)


def evaluate_shadow_metrics(
    observations: Iterable[ShadowObservationRecord],
) -> tuple[ShadowMetricDrift, ...]:
    """Evaluate redacted metrics in stable order without external calls."""

    metric_map: dict[ShadowMetricName, list[ShadowRedactedMetric]] = {}
    for observation in observations:
        for metric in observation.metrics:
            metric_map.setdefault(metric.metric_name, []).append(metric)

    drifts: list[ShadowMetricDrift] = []
    for name in SHADOW_METRIC_NAMES:
        metrics = metric_map.get(name)
        if not metrics:
            continue
        baseline = sum(item.baseline_value for item in metrics) / len(metrics)
        current = sum(item.current_value for item in metrics) / len(metrics)
        target = sum(item.target_value for item in metrics) / len(metrics)
        higher = metrics[0].higher_is_better
        regressed = current < baseline if higher else current > baseline
        target_met = current >= target if higher else current <= target
        target_gap = max(0.0, target - current) if higher else max(0.0, current - target)
        drifts.append(
            ShadowMetricDrift(
                metric_name=name,
                baseline_value=baseline,
                current_value=current,
                target_value=target,
                absolute_delta=abs(current - baseline),
                target_gap=target_gap,
                higher_is_better=higher,
                regressed=regressed,
                target_met=target_met,
            )
        )
    return tuple(drifts)


def build_shadow_evaluation_summary(
    *,
    evaluation_id: str,
    observations: Iterable[ShadowObservationRecord],
    benchmark_cost_units: int,
    created_at: datetime | None = None,
) -> ShadowEvaluationSummary:
    """Build one immutable evaluation summary from observations."""

    observation_tuple = tuple(observations)
    drifts = evaluate_shadow_metrics(observation_tuple)
    weakest = max(drifts, key=lambda item: (item.target_gap, item.metric_name)) if drifts else None
    return ShadowEvaluationSummary(
        evaluation_id=evaluation_id,
        observation_ids=tuple(item.observation_id for item in observation_tuple),
        metric_drifts=drifts,
        weakest_metric=weakest.metric_name if weakest else None,
        regression_count=sum(1 for item in drifts if item.regressed),
        target_miss_count=sum(1 for item in drifts if not item.target_met),
        policy_violation_count=int(
            sum(
                item.current_value
                for item in drifts
                if item.metric_name == "policy_violation_count"
            )
        ),
        benchmark_cost_units=benchmark_cost_units,
        created_at=created_at or utc_now(),
    )


def default_shadow_expires_at(
    created_at: datetime,
    retention_seconds: int = DEFAULT_RETENTION_SECONDS,
) -> datetime:
    """Return an explicit retention expiry timestamp."""

    return require_utc_datetime(created_at) + timedelta(seconds=retention_seconds)


__all__ = [
    "EphemeralShadowStore",
    "SHADOW_REASON_CODES",
    "ShadowEvaluationSummary",
    "ShadowMetricDrift",
    "build_shadow_evaluation_summary",
    "default_shadow_expires_at",
    "evaluate_shadow_metrics",
]
