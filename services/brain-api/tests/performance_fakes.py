"""Shared fakes for performance tests."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from aion_brain.config import Settings
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.performance.baseline import CapacityBaselineService
from aion_brain.performance.budgets import ResourceBudgetService
from aion_brain.performance.regression import PerformanceRegressionComparator
from aion_brain.performance.repository import PerformanceRepository
from aion_brain.performance.runner import BenchmarkRunner
from aion_brain.performance.summary import PerformanceSummaryService

SCOPE = ["workspace:main"]


class AllowPolicy:
    """Always-allow policy fake."""

    def __init__(self) -> None:
        self.requests: list[PolicyRequest] = []

    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        self.requests.append(request)
        return PolicyDecision(
            decision_id=f"decision-{request.request_id}",
            trace_id=request.trace_id or "",
            allow=True,
            approval_required=False,
            reason="allowed",
            constraints=[],
            audit_level="standard",
        )


class DenyPolicy:
    """Always-deny policy fake."""

    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        return PolicyDecision(
            decision_id=f"decision-{request.request_id}",
            trace_id=request.trace_id or "",
            allow=False,
            approval_required=False,
            reason="denied",
            constraints=[],
            audit_level="high",
        )


class FakeTelemetry:
    """Collect emitted events."""

    def __init__(self) -> None:
        self.events: list[object] = []

    def emit(self, event: object) -> None:
        self.events.append(event)


def repository() -> PerformanceRepository:
    """Return an in-memory performance repository."""
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    return PerformanceRepository(engine=engine)


def settings(*, controlled: bool = False) -> Settings:
    """Return local test settings."""
    return Settings(  # type: ignore[call-arg]
        _env_file=None,
        DATABASE_URL="sqlite+pysqlite:///:memory:",
        AION_BENCHMARK_CONTROLLED_MODE_ENABLED=controlled,
    )


def services(
    *,
    policy: object | None = None,
    controlled: bool = False,
) -> tuple[
    PerformanceRepository,
    BenchmarkRunner,
    CapacityBaselineService,
    ResourceBudgetService,
    PerformanceRegressionComparator,
    PerformanceSummaryService,
    FakeTelemetry,
]:
    """Return wired local performance services."""
    repo = repository()
    telemetry = FakeTelemetry()
    comparator = PerformanceRegressionComparator(repo, telemetry_service=telemetry)
    runner = BenchmarkRunner(
        repo,
        policy or AllowPolicy(),  # type: ignore[arg-type]
        telemetry_service=telemetry,
        regression_comparator=comparator,
        settings=settings(controlled=controlled),
    )
    baseline = CapacityBaselineService(repo, telemetry_service=telemetry, settings=settings())
    budgets = ResourceBudgetService(repo, telemetry_service=telemetry)
    summary = PerformanceSummaryService(repo)
    return repo, runner, baseline, budgets, comparator, summary, telemetry
