"""Execution API tests."""

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from aion_brain.api.execution import get_execution_orchestrator, get_execution_repository
from aion_brain.contracts.execution import (
    ApprovalCheckpoint,
    ExecutionRequest,
    ExecutionRun,
    ExecutionStepRun,
)
from aion_brain.main import app


class FakeOrchestrator:
    """Execution orchestrator fake."""

    def execute(self, request: ExecutionRequest) -> ExecutionRun:
        return make_run(request.execution_id)


class FakeRepository:
    """Execution repository fake."""

    def get_execution(self, execution_id: str) -> ExecutionRun | None:
        if execution_id == "missing":
            return None
        return make_run(execution_id)

    def list_steps(self, execution_id: str) -> list[ExecutionStepRun]:
        return [make_step(execution_id)]

    def list_approvals(self, execution_id: str) -> list[ApprovalCheckpoint]:
        return [make_approval(execution_id)]

    def cancel_execution(self, execution_id: str, *, reason: str) -> ExecutionRun | None:
        return make_run(execution_id).model_copy(
            update={"status": "cancelled", "error": {"reason": reason}}
        )

    def resolve_approval(
        self,
        approval_id: str,
        *,
        approved: bool,
        approved_by: str,
        reason: str,
    ) -> ApprovalCheckpoint | None:
        return make_approval("execution-1").model_copy(
            update={
                "approval_id": approval_id,
                "status": "approved" if approved else "denied",
                "approved_by": approved_by,
                "approval_payload": {"resolution_reason": reason},
                "resolved_at": datetime.now(UTC),
            }
        )


def test_execute_api_returns_execution_run() -> None:
    """POST /brain/execute returns ExecutionRun."""
    app.dependency_overrides[get_execution_orchestrator] = lambda: FakeOrchestrator()
    try:
        response = TestClient(app).post("/brain/execute", json=request_payload())
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["execution_id"] == "execution-1"


def test_execution_lookup_apis_work() -> None:
    """Execution lookup endpoints return persisted child records."""
    app.dependency_overrides[get_execution_repository] = lambda: FakeRepository()
    try:
        client = TestClient(app)
        run = client.get("/brain/executions/execution-1")
        steps = client.get("/brain/executions/execution-1/steps")
        approvals = client.get("/brain/executions/execution-1/approvals")
    finally:
        app.dependency_overrides.clear()

    assert run.status_code == 200
    assert steps.status_code == 200
    assert approvals.status_code == 200
    assert steps.json()[0]["step_run_id"] == "step-run-1"
    assert approvals.json()[0]["approval_id"] == "approval-1"


def test_cancel_and_approval_resolution_apis_work() -> None:
    """Cancel and approval resolution endpoints update state."""
    app.dependency_overrides[get_execution_repository] = lambda: FakeRepository()
    try:
        client = TestClient(app)
        cancel = client.post("/brain/executions/execution-1/cancel", json={"reason": "stop"})
        approval = client.post(
            "/brain/approvals/approval-1/resolve",
            json={"approved": True, "approved_by": "actor-2", "reason": "ok"},
        )
    finally:
        app.dependency_overrides.clear()

    assert cancel.status_code == 200
    assert cancel.json()["status"] == "cancelled"
    assert approval.status_code == 200
    assert approval.json()["status"] == "approved"


def request_payload() -> dict[str, object]:
    """Create an execution request payload."""
    return {
        "execution_id": "execution-1",
        "trace_id": "trace-1",
        "plan": {
            "plan_id": "plan-1",
            "intent_id": "intent-1",
            "goal": "generic goal",
            "steps": [
                {
                    "step_id": "retrieve_context",
                    "action_type": "memory.retrieve",
                    "capability_required": "memory.retrieve",
                    "risk_level": "low",
                    "status": "pending",
                }
            ],
            "dependencies": [],
            "risk_level": "low",
            "approval_required": False,
            "status": "draft",
            "metadata": {},
        },
        "requested_by": "actor-1",
        "workspace_id": "workspace-1",
        "mode": "dry_run",
        "approval_present": False,
        "max_steps": 50,
        "metadata": {},
    }


def make_run(execution_id: str) -> ExecutionRun:
    """Create an execution run."""
    now = datetime.now(UTC)
    return ExecutionRun(
        execution_id=execution_id,
        trace_id="trace-1",
        plan_id="plan-1",
        intent_id="intent-1",
        context_id="context-1",
        status="completed",
        requested_by="actor-1",
        workspace_id="workspace-1",
        steps=[make_step(execution_id)],
        approvals=[],
        capability_invocations=[],
        input={},
        output={},
        error={},
        started_at=now,
        completed_at=now,
        created_at=now,
        updated_at=now,
    )


def make_step(execution_id: str) -> ExecutionStepRun:
    """Create an execution step."""
    now = datetime.now(UTC)
    return ExecutionStepRun(
        step_run_id="step-run-1",
        execution_id=execution_id,
        plan_id="plan-1",
        step_id="retrieve_context",
        action_type="memory.retrieve",
        capability_required="memory.retrieve",
        risk_level="low",
        status="completed",
        attempt=1,
        input={},
        output={},
        error={},
        policy_decision_id="decision-1",
        started_at=now,
        completed_at=now,
        created_at=now,
    )


def make_approval(execution_id: str) -> ApprovalCheckpoint:
    """Create an approval checkpoint."""
    now = datetime.now(UTC)
    return ApprovalCheckpoint(
        approval_id="approval-1",
        execution_id=execution_id,
        step_run_id="step-run-1",
        trace_id="trace-1",
        reason="approval_required",
        risk_level="high",
        status="pending",
        requested_by="actor-1",
        approved_by=None,
        approval_payload={},
        created_at=now,
        resolved_at=None,
    )
