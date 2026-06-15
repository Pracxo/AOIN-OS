"""Shared resilience fakes and factories."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from aion_brain.config import Settings
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.resilience import (
    CircuitBreaker,
    DependencyHealth,
    FaultInjectionRule,
    ResilienceTestRun,
    RetryPolicy,
)
from aion_brain.resilience.repository import ResilienceRepository

SCOPE = ["workspace:main"]


class AllowPolicy:
    """Policy fake that allows and records requests."""

    def __init__(self) -> None:
        self.requests: list[PolicyRequest] = []

    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        self.requests.append(request)
        return PolicyDecision(
            decision_id=f"decision-{len(self.requests)}",
            trace_id=request.trace_id or "",
            allow=True,
            approval_required=False,
            reason="allowed",
            constraints=[],
            audit_level="standard",
        )


class DenyPolicy(AllowPolicy):
    """Policy fake that denies matching actions."""

    def __init__(self, action_type: str) -> None:
        super().__init__()
        self.action_type = action_type

    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        self.requests.append(request)
        allow = request.action_type != self.action_type
        return PolicyDecision(
            decision_id=f"decision-{len(self.requests)}",
            trace_id=request.trace_id or "",
            allow=allow,
            approval_required=False,
            reason="allowed" if allow else "denied",
            constraints=[] if allow else ["blocked"],
            audit_level="standard" if allow else "high",
        )


class FakeTelemetry:
    """Collect telemetry events."""

    def __init__(self) -> None:
        self.events: list[object] = []

    def emit(self, event: object) -> None:
        self.events.append(event)


def repository() -> ResilienceRepository:
    """Return an in-memory resilience repository."""
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    return ResilienceRepository(engine=engine)


def settings(**overrides: Any) -> Settings:
    """Return local-only test settings."""
    values: dict[str, Any] = {
        "_env_file": None,
        "DATABASE_URL": "sqlite+pysqlite:///:memory:",
        "AION_FAULT_INJECTION_ENABLED": False,
    }
    values.update(overrides)
    return Settings(**values)


def retry_policy(name: str = "command-standard", target_type: str = "command") -> RetryPolicy:
    """Return a valid retry policy."""
    return RetryPolicy(
        retry_policy_id=f"retry-{name}",
        name=name,
        description="Bounded local retry policy.",
        status="active",
        target_type=target_type,  # type: ignore[arg-type]
        max_attempts=3,
        initial_delay_ms=100,
        max_delay_ms=1000,
        backoff_multiplier=2.0,
        jitter_enabled=False,
        retryable_statuses=["failed"],
        non_retryable_statuses=["blocked_by_policy"],
        owner_scope=SCOPE,
        metadata={},
    )


def circuit_breaker(name: str = "command") -> CircuitBreaker:
    """Return a valid circuit breaker."""
    return CircuitBreaker(
        circuit_breaker_id=f"breaker-{name}",
        name=name,
        target_type="command",
        target_id=None,
        status="closed",
        failure_count=0,
        success_count=0,
        failure_threshold=2,
        recovery_timeout_seconds=1,
        half_open_max_calls=1,
        owner_scope=SCOPE,
        metadata={},
    )


def fault_rule(
    fault_rule_id: str = "fault-command",
    *,
    probability: float = 1.0,
) -> FaultInjectionRule:
    """Return a valid fault rule."""
    return FaultInjectionRule(
        fault_rule_id=fault_rule_id,
        name=fault_rule_id,
        description="Local deterministic fault rule.",
        status="active",
        target_type="command",
        target_id=None,
        fault_type="exception",
        probability=probability,
        duration_ms=None,
        error_code="test_fault",
        owner_scope=SCOPE,
        constraints=["local_only"],
        metadata={"seed": "always"},
    )


def dependency_health(
    name: str,
    status: str = "healthy",
    criticality: str = "critical",
) -> DependencyHealth:
    """Return a dependency health record."""
    return DependencyHealth(
        dependency_health_id=f"dependency-{name}",
        dependency_name=name,
        dependency_type="database",
        status=status,  # type: ignore[arg-type]
        criticality=criticality,  # type: ignore[arg-type]
        latency_ms=1,
        details={},
        checked_at=datetime.now(UTC),
    )


def test_run(status: str = "passed") -> ResilienceTestRun:
    """Return a resilience test run."""
    return ResilienceTestRun(
        resilience_test_run_id="resilience-run-1",
        trace_id="trace-1",
        status=status,  # type: ignore[arg-type]
        mode="dry_run",
        owner_scope=SCOPE,
        fault_rule_ids=[],
        checks=[],
        failures=[{"name": "critical"}] if status == "failed" else [],
        warnings=[{"name": "warning"}] if status == "warning" else [],
        report={},
        created_by="tester",
        created_at=datetime.now(UTC),
        completed_at=datetime.now(UTC),
    )
