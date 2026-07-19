"""Canary and rollback contracts for AION-174 self-improvement."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.model_outputs import reject_hidden_or_secret_text
from aion_brain.contracts.self_improvement import utc_now
from aion_brain.self_improvement.benchmark_contracts import BenchmarkMetric, BenchmarkMetricName

CANARY_AUTHORIZATION_TRANSACTION_ID = "AION-173-SI-0005"
CANARY_IMPLEMENTATION_TASK = "AION-174"
CANARY_AUTHORIZATION_SCOPE = "approval-bound-canary-rollback-and-adaptive-policy"
CANARY_RUNTIME_ENABLED = False
PRODUCTION_EXPOSURE_ENABLED = False

CanaryState = Literal[
    "planned",
    "approved",
    "running",
    "passed",
    "failed",
    "rolled_back",
    "promoted",
]
OutcomeValue = Literal[
    "improvement_success",
    "improvement_failed",
    "improvement_rolled_back",
    "improvement_inconclusive",
]
RollbackTrigger = Literal[
    "policy_violation",
    "security_regression",
    "task_success_degradation",
    "user_correction_increase",
    "latency_budget_breach",
    "error_rate_increase",
    "benchmark_drift",
    "unexpected_runtime_effect",
]

ROLLBACK_TRIGGERS: tuple[RollbackTrigger, ...] = (
    "policy_violation",
    "security_regression",
    "task_success_degradation",
    "user_correction_increase",
    "latency_budget_breach",
    "error_rate_increase",
    "benchmark_drift",
    "unexpected_runtime_effect",
)

_SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def safe_text(value: str, context: str) -> str:
    """Strip and reject hidden or secret markers in governance text."""

    cleaned = value.strip()
    reject_hidden_or_secret_text(cleaned, context)
    return cleaned


def require_sha1(value: str) -> str:
    """Require an exact lowercase Git SHA-1 value."""

    if not _SHA1_RE.fullmatch(value):
        raise ValueError("git SHA must be a 40-character lowercase SHA-1 value")
    return value


def require_sha256(value: str) -> str:
    """Require an exact lowercase SHA-256 value."""

    if not _SHA256_RE.fullmatch(value):
        raise ValueError("fingerprint must be a 64-character lowercase SHA-256 value")
    return value


class CanaryExposureBudget(BaseModel):
    """Bounded exposure budget; production exposure remains disabled by default."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    budget_id: str = Field(min_length=1)
    max_exposure_percentage: float = Field(ge=0.0, le=100.0)
    max_subjects: int = Field(ge=0)
    max_duration_minutes: int = Field(gt=0)
    production_exposure_enabled: bool = PRODUCTION_EXPOSURE_ENABLED
    unrestricted_traffic_exposure_enabled: bool = False

    @field_validator("budget_id")
    @classmethod
    def budget_id_must_be_safe(cls, value: str) -> str:
        return safe_text(value, "canary exposure budget id")

    @model_validator(mode="after")
    def exposure_must_be_bounded_and_disabled(self) -> CanaryExposureBudget:
        if self.production_exposure_enabled:
            raise ValueError("production exposure must be disabled by default")
        if self.unrestricted_traffic_exposure_enabled:
            raise ValueError("unrestricted traffic exposure is prohibited")
        if self.max_exposure_percentage == 100.0:
            raise ValueError("canary exposure cannot be unrestricted")
        return self


class CanaryMetricThreshold(BaseModel):
    """Metric threshold that maps a regression to an approved rollback trigger."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    metric_name: BenchmarkMetricName
    threshold: float = Field(ge=0.0)
    higher_is_better: bool
    rollback_trigger: RollbackTrigger


class CanaryApprovalBinding(BaseModel):
    """Exact approval binding required before a canary simulation can start."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    authorization_transaction_id: str = CANARY_AUTHORIZATION_TRANSACTION_ID
    approval_status: Literal["pending", "approved", "rejected", "invalidated"]
    plan_id: str = Field(min_length=1)
    approved_merge_commit: str
    approved_deployment_artifact: str
    approved_exposure_budget_id: str = Field(min_length=1)
    approved_monitoring_duration_minutes: int = Field(gt=0)
    approved_rollback_commit: str
    approved_metric_threshold_fingerprint: str
    current_merge_commit: str
    current_deployment_artifact: str
    current_exposure_budget_id: str = Field(min_length=1)
    current_monitoring_duration_minutes: int = Field(gt=0)
    current_rollback_commit: str
    current_metric_threshold_fingerprint: str
    approver_actor_ids: tuple[str, ...] = Field(min_length=1)
    production_canary_enabled: bool = False
    autonomous_production_activation_enabled: bool = False
    created_at: datetime = Field(default_factory=utc_now)

    @field_validator("plan_id", "approved_exposure_budget_id", "current_exposure_budget_id")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        return safe_text(value, "canary approval binding text")

    @field_validator(
        "approved_merge_commit",
        "approved_rollback_commit",
        "current_merge_commit",
        "current_rollback_commit",
    )
    @classmethod
    def git_sha_must_be_exact(cls, value: str) -> str:
        return require_sha1(value)

    @field_validator(
        "approved_deployment_artifact",
        "approved_metric_threshold_fingerprint",
        "current_deployment_artifact",
        "current_metric_threshold_fingerprint",
    )
    @classmethod
    def fingerprint_must_be_exact(cls, value: str) -> str:
        return require_sha256(value)

    @field_validator("approver_actor_ids")
    @classmethod
    def approver_ids_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for actor_id in value:
            safe_text(actor_id, "canary approver actor id")
        return value

    @model_validator(mode="after")
    def approval_must_bind_exact_evidence(self) -> CanaryApprovalBinding:
        if self.authorization_transaction_id != CANARY_AUTHORIZATION_TRANSACTION_ID:
            raise ValueError("canary approval must use the AION-173 authorization")
        if self.production_canary_enabled:
            raise ValueError("production canary is disabled by default")
        if self.autonomous_production_activation_enabled:
            raise ValueError("autonomous production activation is prohibited")
        if self.approval_status == "approved" and not self.is_valid:
            raise ValueError("approved canary binding must match current evidence exactly")
        return self

    @property
    def is_valid(self) -> bool:
        """Return whether the approval exactly matches the current canary plan."""

        return self.approval_status == "approved" and (
            self.approved_merge_commit == self.current_merge_commit
            and self.approved_deployment_artifact == self.current_deployment_artifact
            and self.approved_exposure_budget_id == self.current_exposure_budget_id
            and self.approved_monitoring_duration_minutes
            == self.current_monitoring_duration_minutes
            and self.approved_rollback_commit == self.current_rollback_commit
            and self.approved_metric_threshold_fingerprint
            == self.current_metric_threshold_fingerprint
        )


class CanaryPlan(BaseModel):
    """Approved-shape canary plan; runtime activation is disabled by default."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    authorization_transaction_id: str = CANARY_AUTHORIZATION_TRANSACTION_ID
    plan_id: str = Field(min_length=1)
    proposal_id: str = Field(min_length=1)
    merge_commit_sha: str
    deployment_artifact_fingerprint: str
    exposure_budget: CanaryExposureBudget
    monitoring_duration_minutes: int = Field(gt=0)
    rollback_commit_sha: str
    metric_thresholds: tuple[CanaryMetricThreshold, ...] = Field(min_length=1)
    metric_threshold_fingerprint: str
    state: CanaryState = "planned"
    canary_runtime_enabled: bool = CANARY_RUNTIME_ENABLED
    production_exposure_enabled: bool = PRODUCTION_EXPOSURE_ENABLED
    created_at: datetime = Field(default_factory=utc_now)

    @field_validator("plan_id", "proposal_id")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        return safe_text(value, "canary plan text")

    @field_validator("merge_commit_sha", "rollback_commit_sha")
    @classmethod
    def sha_must_be_exact(cls, value: str) -> str:
        return require_sha1(value)

    @field_validator("deployment_artifact_fingerprint", "metric_threshold_fingerprint")
    @classmethod
    def fingerprint_must_be_exact(cls, value: str) -> str:
        return require_sha256(value)

    @model_validator(mode="after")
    def plan_must_be_bound_and_disabled(self) -> CanaryPlan:
        if self.authorization_transaction_id != CANARY_AUTHORIZATION_TRANSACTION_ID:
            raise ValueError("canary plan must use the AION-173 authorization")
        if self.canary_runtime_enabled:
            raise ValueError("canary runtime must be disabled by default")
        if self.production_exposure_enabled:
            raise ValueError("production exposure must be disabled by default")
        if self.monitoring_duration_minutes != self.exposure_budget.max_duration_minutes:
            raise ValueError("monitoring duration must match the approved exposure budget")
        return self

    def approval_binding(self, *, approver_actor_ids: tuple[str, ...]) -> CanaryApprovalBinding:
        """Create a synthetic exact approval binding for tests and evidence."""

        return CanaryApprovalBinding(
            approval_status="approved",
            plan_id=self.plan_id,
            approved_merge_commit=self.merge_commit_sha,
            approved_deployment_artifact=self.deployment_artifact_fingerprint,
            approved_exposure_budget_id=self.exposure_budget.budget_id,
            approved_monitoring_duration_minutes=self.monitoring_duration_minutes,
            approved_rollback_commit=self.rollback_commit_sha,
            approved_metric_threshold_fingerprint=self.metric_threshold_fingerprint,
            current_merge_commit=self.merge_commit_sha,
            current_deployment_artifact=self.deployment_artifact_fingerprint,
            current_exposure_budget_id=self.exposure_budget.budget_id,
            current_monitoring_duration_minutes=self.monitoring_duration_minutes,
            current_rollback_commit=self.rollback_commit_sha,
            current_metric_threshold_fingerprint=self.metric_threshold_fingerprint,
            approver_actor_ids=approver_actor_ids,
        )


class CanaryObservation(BaseModel):
    """One canary metric observation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    observation_id: str = Field(min_length=1)
    plan_id: str = Field(min_length=1)
    metrics: tuple[BenchmarkMetric, ...] = Field(min_length=1)
    policy_violation_count: int = Field(default=0, ge=0)
    security_regression_count: int = Field(default=0, ge=0)
    unexpected_runtime_effect: bool = False
    observed_at: datetime = Field(default_factory=utc_now)

    @field_validator("observation_id", "plan_id")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        return safe_text(value, "canary observation text")


class CanaryDecision(BaseModel):
    """State decision for a canary plan."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    plan_id: str
    from_state: CanaryState
    to_state: CanaryState
    allowed: bool
    reason_codes: tuple[str, ...] = Field(default_factory=tuple)
    created_at: datetime = Field(default_factory=utc_now)


class RollbackDecision(BaseModel):
    """Rollback decision for an approved canary plan."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    plan_id: str
    rollback_required: bool
    rollback_allowed: bool
    rollback_commit_sha: str
    triggers: tuple[RollbackTrigger, ...] = Field(default_factory=tuple)
    reason_codes: tuple[str, ...] = Field(default_factory=tuple)
    created_at: datetime = Field(default_factory=utc_now)

    @field_validator("rollback_commit_sha")
    @classmethod
    def sha_must_be_exact(cls, value: str) -> str:
        return require_sha1(value)


class ImprovementOutcome(BaseModel):
    """Final outcome recorded for a self-improvement candidate."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    outcome_id: str = Field(min_length=1)
    proposal_id: str = Field(min_length=1)
    outcome_value: OutcomeValue
    canary_state: CanaryState
    promoted: bool
    rolled_back: bool
    review_window_days: int = Field(ge=0)
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)
    created_at: datetime = Field(default_factory=utc_now)

    @field_validator("outcome_id", "proposal_id")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        return safe_text(value, "improvement outcome text")

    @model_validator(mode="after")
    def outcome_must_match_state(self) -> ImprovementOutcome:
        if self.outcome_value == "improvement_success" and not self.promoted:
            raise ValueError("successful improvements must be promoted")
        if self.outcome_value == "improvement_rolled_back" and not self.rolled_back:
            raise ValueError("rolled-back outcomes must mark rolled_back=true")
        return self


__all__ = [
    "CANARY_AUTHORIZATION_SCOPE",
    "CANARY_AUTHORIZATION_TRANSACTION_ID",
    "CANARY_IMPLEMENTATION_TASK",
    "CANARY_RUNTIME_ENABLED",
    "PRODUCTION_EXPOSURE_ENABLED",
    "ROLLBACK_TRIGGERS",
    "CanaryApprovalBinding",
    "CanaryDecision",
    "CanaryExposureBudget",
    "CanaryMetricThreshold",
    "CanaryObservation",
    "CanaryPlan",
    "CanaryState",
    "ImprovementOutcome",
    "OutcomeValue",
    "RollbackDecision",
    "RollbackTrigger",
    "require_sha1",
    "require_sha256",
    "safe_text",
]
