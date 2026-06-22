"""Local executor tests."""

from datetime import UTC, datetime

from aion_brain.contracts.execution import ExecutionStepRun
from aion_brain.execution.local_executor import LocalExecutor


def test_local_executor_completes_safe_internal_step() -> None:
    """Safe generic internal steps complete deterministically."""
    result = LocalExecutor().execute_step(make_step("retrieve_context", "low"))

    assert result.status == "completed"
    assert result.output["executed"] is True
    assert result.output["message"] == "Generic AION internal step completed."


def test_local_executor_skips_unknown_low_risk_step() -> None:
    """Unknown low-risk actions are skipped without failing the run."""
    result = LocalExecutor().execute_step(make_step("unknown_generic", "low"))

    assert result.status == "skipped"
    assert result.output["reason"] == "No executor exists for this generic action_type in v0.1."


def make_step(step_id: str, risk_level: str) -> ExecutionStepRun:
    """Create a running execution step."""
    return ExecutionStepRun(
        step_run_id=f"step-{step_id}",
        execution_id="execution-1",
        plan_id="plan-1",
        step_id=step_id,
        action_type=step_id,
        capability_required=None,
        risk_level=risk_level,
        status="running",
        attempt=1,
        input={},
        output={},
        error={},
        policy_decision_id=None,
        started_at=datetime.now(UTC),
        completed_at=None,
        created_at=datetime.now(UTC),
    )
