"""Durable workflow contract tests."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from aion_brain.contracts.schedules import ScheduleCreateRequest
from aion_brain.contracts.workflows import (
    WorkflowCreateRequest,
    WorkflowHeartbeat,
    WorkflowRetryPolicy,
    WorkflowStep,
)


def test_workflow_definition_requires_steps() -> None:
    """Workflow definitions must contain at least one generic step."""
    with pytest.raises(ValidationError):
        WorkflowCreateRequest(
            name="Empty",
            description="Empty workflow",
            owner_scope=["workspace:main"],
            steps=[],
        )


def test_workflow_step_rejects_unknown_action() -> None:
    """Workflow step action types are constrained to generic Brain actions."""
    with pytest.raises(ValidationError):
        WorkflowStep(
            step_id="step-1",
            action_type="domain.specific",
            description="Invalid action",
            risk_level="low",
        )


def test_retry_policy_validates_backoff_bounds() -> None:
    """Retry policy cannot shrink max backoff below the base delay."""
    with pytest.raises(ValidationError):
        WorkflowRetryPolicy(backoff_seconds=60, max_backoff_seconds=10)


def test_heartbeat_contract_accepts_worker_status() -> None:
    """Heartbeat records are AION-owned contracts."""
    heartbeat = WorkflowHeartbeat(
        heartbeat_id="heartbeat-1",
        workflow_run_id="run-1",
        worker_id="worker-1",
        status="running",
        payload={"tick": 1},
        created_at=datetime.now(UTC),
    )

    assert heartbeat.worker_id == "worker-1"
    assert heartbeat.payload["tick"] == 1


def test_schedule_owner_type_allows_workflow() -> None:
    """Schedules can explicitly target workflow owners."""
    request = ScheduleCreateRequest(
        owner_type="workflow",
        owner_id="workflow-1",
        schedule_type="once",
        schedule_expression="2026-06-12T10:00:00Z",
    )

    assert request.owner_type == "workflow"
