"""Execution autonomy integration tests."""

from aion_brain.execution.orchestrator import ExecutionOrchestrator
from tests.autonomy_fakes import FakeAutonomyGovernor
from tests.test_execution_orchestrator import (
    FakeCapabilityInvoker,
    FakePolicyAdapter,
    FakeRepository,
    FakeTelemetry,
    make_request,
)


def test_execution_orchestrator_blocks_when_autonomy_denies() -> None:
    """Execution does not evaluate plan steps after autonomy denial."""
    repository = FakeRepository()
    orchestrator = ExecutionOrchestrator(
        policy_adapter=FakePolicyAdapter(),
        capability_invoker=FakeCapabilityInvoker(),
        execution_repository=repository,
        telemetry_service=FakeTelemetry(),
        autonomy_governor=FakeAutonomyGovernor(allow=False),
    )

    run = orchestrator.execute(make_request())

    assert run.status == "blocked_by_policy"
    assert run.error["reason"] == "autonomy_denied"
    assert run.steps == []
    assert repository.executions[-1].status == "blocked_by_policy"
