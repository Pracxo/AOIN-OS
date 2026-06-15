"""Resilience control-plane contracts owned by AION Brain."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.versioning import reject_secret_like_keys

DependencyType = Literal[
    "database",
    "cache",
    "event_bus",
    "policy_engine",
    "object_store",
    "model_gateway",
    "semantic_memory",
    "graph_memory",
    "workflow_engine",
    "module_runtime",
    "mcp",
    "sandbox",
    "observability",
    "optional_adapter",
]
DependencyStatus = Literal[
    "healthy",
    "degraded",
    "unhealthy",
    "unavailable",
    "disabled",
    "unknown",
]
DependencyCriticality = Literal["critical", "important", "optional"]
RetryPolicyStatus = Literal["active", "disabled"]
RetryPolicyTargetType = Literal[
    "command",
    "outbox",
    "workflow",
    "model_gateway",
    "memory_adapter",
    "graph_adapter",
    "mcp",
    "module_runtime",
    "backup",
    "release_package",
    "generic",
]
CircuitBreakerStatus = Literal["closed", "open", "half_open", "disabled"]
DegradedModeStatus = Literal["active", "resolved"]
DegradedModeSeverity = Literal["low", "medium", "high", "critical"]
FaultRuleStatus = Literal["active", "disabled"]
FaultType = Literal[
    "latency",
    "exception",
    "unavailable",
    "timeout",
    "policy_denied",
    "degraded_response",
    "noop",
]
FaultTargetType = Literal[
    "model_gateway",
    "semantic_memory",
    "graph_memory",
    "mcp",
    "module_runtime",
    "outbox",
    "workflow",
    "command",
    "kernel",
    "generic",
]
ResilienceRunMode = Literal["dry_run", "controlled"]
ResilienceRunStatus = Literal["passed", "warning", "failed"]
ResilienceOverallStatus = Literal["healthy", "degraded", "unhealthy"]


class DependencyHealth(BaseModel):
    """One dependency health observation."""

    model_config = ConfigDict(extra="forbid")

    dependency_health_id: str = Field(min_length=1)
    dependency_name: str = Field(min_length=1)
    dependency_type: DependencyType
    status: DependencyStatus
    criticality: DependencyCriticality
    latency_ms: int | None = Field(default=None, ge=0)
    details: dict[str, Any] = Field(default_factory=dict)
    checked_at: datetime | None = None

    @field_validator("details")
    @classmethod
    def details_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value


class RetryPolicy(BaseModel):
    """Bounded retry policy metadata."""

    model_config = ConfigDict(extra="forbid")

    retry_policy_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    status: RetryPolicyStatus
    target_type: RetryPolicyTargetType
    max_attempts: int = Field(ge=1, le=10)
    initial_delay_ms: int = Field(ge=0)
    max_delay_ms: int = Field(ge=0)
    backoff_multiplier: float = Field(ge=1)
    jitter_enabled: bool
    retryable_statuses: list[str] = Field(default_factory=list)
    non_retryable_statuses: list[str] = Field(default_factory=list)
    owner_scope: list[str] = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    disabled_at: datetime | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value

    @model_validator(mode="after")
    def delay_bounds_must_be_coherent(self) -> RetryPolicy:
        if self.max_delay_ms < self.initial_delay_ms:
            raise ValueError("max_delay_ms must be greater than or equal to initial_delay_ms")
        return self


class CircuitBreaker(BaseModel):
    """Generic circuit breaker state."""

    model_config = ConfigDict(extra="forbid")

    circuit_breaker_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    target_type: RetryPolicyTargetType
    target_id: str | None = None
    status: CircuitBreakerStatus
    failure_count: int = Field(ge=0)
    success_count: int = Field(ge=0)
    failure_threshold: int = Field(ge=1, le=100)
    recovery_timeout_seconds: int = Field(ge=1, le=86400)
    half_open_max_calls: int = Field(ge=1, le=100)
    last_failure_at: datetime | None = None
    opened_at: datetime | None = None
    half_opened_at: datetime | None = None
    closed_at: datetime | None = None
    owner_scope: list[str] = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value


class DegradedModeEvent(BaseModel):
    """A local degraded-mode record."""

    model_config = ConfigDict(extra="forbid")

    degraded_event_id: str = Field(min_length=1)
    trace_id: str | None = None
    component: str = Field(min_length=1)
    status: DegradedModeStatus
    severity: DegradedModeSeverity
    reason: str = Field(min_length=1)
    dependencies: list[str] = Field(default_factory=list)
    fallbacks_active: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    resolved_at: datetime | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value


class FaultInjectionRule(BaseModel):
    """Local deterministic fault-injection rule."""

    model_config = ConfigDict(extra="forbid")

    fault_rule_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    status: FaultRuleStatus
    target_type: FaultTargetType
    target_id: str | None = None
    fault_type: FaultType
    probability: float = Field(ge=0, le=1)
    duration_ms: int | None = Field(default=None, gt=0)
    error_code: str | None = None
    owner_scope: list[str] = Field(min_length=1)
    constraints: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    disabled_at: datetime | None = None

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value


class ResilienceTestRunRequest(BaseModel):
    """Request to run a local resilience report."""

    model_config = ConfigDict(extra="forbid")

    resilience_test_run_id: str | None = None
    trace_id: str | None = None
    owner_scope: list[str] = Field(min_length=1)
    mode: ResilienceRunMode = "dry_run"
    fault_rule_ids: list[str] = Field(default_factory=list)
    include_dependency_health: bool = True
    include_circuit_breakers: bool = True
    include_retry_policies: bool = True
    include_fault_injection: bool = True
    include_degraded_mode: bool = True
    created_by: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_secret_like_keys(value)
        return value


class ResilienceTestRun(BaseModel):
    """Persisted resilience test result."""

    model_config = ConfigDict(extra="forbid")

    resilience_test_run_id: str = Field(min_length=1)
    trace_id: str | None = None
    status: ResilienceRunStatus
    mode: ResilienceRunMode
    owner_scope: list[str] = Field(min_length=1)
    fault_rule_ids: list[str]
    checks: list[dict[str, Any]]
    failures: list[dict[str, Any]]
    warnings: list[dict[str, Any]]
    report: dict[str, Any]
    created_by: str | None = None
    created_at: datetime | None = None
    completed_at: datetime | None = None


class ResilienceStatus(BaseModel):
    """Combined resilience posture."""

    model_config = ConfigDict(extra="forbid")

    overall_status: ResilienceOverallStatus
    dependencies: list[DependencyHealth]
    active_degraded_events: list[DegradedModeEvent]
    open_circuit_breakers: list[CircuitBreaker]
    active_fault_rules: list[FaultInjectionRule]
    generated_at: datetime


class ResilienceDryRunRequest(BaseModel):
    """Small dry-run request shape used by API helpers."""

    dry_run: bool = True


class ResilienceStatusUpdateRequest(BaseModel):
    """Simple status update request."""

    actor_id: str | None = None
    reason: str = Field(min_length=1)

