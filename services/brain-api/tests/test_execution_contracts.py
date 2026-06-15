"""Execution contract tests."""

import pytest
from pydantic import ValidationError

from aion_brain.contracts.execution import ExecutionRequest
from aion_brain.contracts.planning import PlanGraph, PlanStep


def test_execution_request_validates_mode() -> None:
    """Execution mode must use the v0.1 vocabulary."""
    with pytest.raises(ValidationError):
        ExecutionRequest(
            execution_id="execution-1",
            trace_id="trace-1",
            plan=make_plan(),
            requested_by=None,
            workspace_id=None,
            mode="external",
        )


def test_execution_request_rejects_empty_plan_steps() -> None:
    """Execution requests require at least one plan step."""
    plan = make_plan().model_copy(update={"steps": []})

    with pytest.raises(ValidationError):
        ExecutionRequest(
            execution_id="execution-1",
            trace_id="trace-1",
            plan=plan,
            requested_by=None,
            workspace_id=None,
        )


def make_plan() -> PlanGraph:
    """Create a generic plan graph."""
    return PlanGraph(
        plan_id="plan-1",
        intent_id="intent-1",
        goal="generic goal",
        steps=[
            PlanStep(
                step_id="retrieve_context",
                action_type="memory.retrieve",
                capability_required="memory.retrieve",
                risk_level="low",
                status="pending",
            )
        ],
        dependencies=[],
        risk_level="low",
        approval_required=False,
        status="draft",
    )
