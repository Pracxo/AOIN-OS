"""Workflow API tests."""

from datetime import UTC, datetime
from types import SimpleNamespace

from fastapi.testclient import TestClient

from aion_brain.api.workflows import (
    get_workflow_policy_adapter,
    get_workflow_scheduler,
    get_workflow_service,
    get_workflow_worker,
)
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.scopes import ActorContext
from aion_brain.contracts.workflows import (
    TemporalAdapterStatus,
    WorkflowCreateRequest,
    WorkflowDefinition,
    WorkflowEngineStatus,
    WorkflowRun,
    WorkflowRunRequest,
    WorkflowTransitionRequest,
)
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.main import app


class FakeWorkflowService:
    """Workflow service fake for API tests."""

    def __init__(self) -> None:
        self.workflow = make_workflow()
        self.run = make_run()

    def create_workflow(self, request: WorkflowCreateRequest) -> WorkflowDefinition:
        self.workflow = self.workflow.model_copy(
            update={
                "workflow_id": request.workflow_id or "workflow-created",
                "name": request.name,
                "description": request.description,
                "owner_scope": request.owner_scope,
                "created_by": request.created_by,
            }
        )
        return self.workflow

    def get_workflow(self, workflow_id: str, scope: list[str]) -> WorkflowDefinition | None:
        return self.workflow if workflow_id == self.workflow.workflow_id and scope else None

    def list_workflows(
        self,
        *,
        scope: list[str],
        status: str | None = None,
        limit: int = 50,
    ) -> list[WorkflowDefinition]:
        return [self.workflow][:limit] if scope and status in {None, self.workflow.status} else []

    def update_workflow_status(
        self,
        workflow_id: str,
        status: str,
        *,
        actor_id: str | None,
        reason: str | None,
    ) -> WorkflowDefinition:
        self.workflow = self.workflow.model_copy(update={"status": status})
        return self.workflow

    def run_workflow(self, request: WorkflowRunRequest) -> WorkflowRun:
        self.run = make_run(request.workflow_run_id or "workflow-run-1")
        return self.run

    def get_run(self, workflow_run_id: str, scope: list[str]) -> WorkflowRun | None:
        return self.run if workflow_run_id == self.run.workflow_run_id and scope else None

    def list_runs(
        self,
        workflow_id: str | None = None,
        status: str | None = None,
        scope: list[str] | None = None,
        limit: int = 50,
    ) -> list[WorkflowRun]:
        return [self.run][:limit] if scope and status in {None, self.run.status} else []

    def pause_run(self, request: WorkflowTransitionRequest) -> WorkflowRun:
        return self.run.model_copy(update={"status": "paused"})

    def resume_run(self, request: WorkflowTransitionRequest) -> WorkflowRun:
        return self.run.model_copy(update={"status": "running"})

    def cancel_run(self, request: WorkflowTransitionRequest) -> WorkflowRun:
        return self.run.model_copy(update={"status": "cancelled"})

    def retry_run(
        self,
        workflow_run_id: str,
        actor_id: str | None,
        reason: str | None,
    ) -> WorkflowRun:
        return self.run.model_copy(update={"status": "retry_scheduled"})

    def engine_status(self) -> WorkflowEngineStatus:
        return WorkflowEngineStatus(
            engine_name="aion-workflow-engine",
            active_adapter="local",
            temporal_available=False,
            temporal_enabled=False,
            local_worker_enabled=False,
            pending_runs=0,
            running_runs=0,
            failed_runs=0,
        )

    def temporal_status(self) -> TemporalAdapterStatus:
        return TemporalAdapterStatus(
            adapter_name="temporal",
            enabled=False,
            package_available=False,
            endpoint_ref=None,
            reason="temporal_disabled",
        )


class FakePolicyAdapter:
    """Policy fake."""

    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        return PolicyDecision(
            decision_id=f"decision-{request.action_type}",
            trace_id=request.trace_id or "",
            allow=True,
            approval_required=False,
            reason="allowed",
            constraints=[],
            audit_level="standard",
        )


def test_workflow_api_create_list_get_run_and_transitions() -> None:
    """Workflow API exposes definition and run controls."""
    service = FakeWorkflowService()
    with workflow_overrides(service):
        client = TestClient(app)
        created = client.post("/brain/workflows", json=create_payload())
        listed = client.get("/brain/workflows", params={"scope": "workspace:main"})
        fetched = client.get("/brain/workflows/workflow-1", params={"scope": "workspace:main"})
        run = client.post("/brain/workflows/run", json={"workflow_id": "workflow-1"})
        runs = client.get("/brain/workflows/runs", params={"scope": "workspace:main"})
        paused = client.post(
            "/brain/workflows/runs/workflow-run-1/pause",
            json={"workflow_run_id": "workflow-run-1", "to_status": "paused"},
        )
        resumed = client.post(
            "/brain/workflows/runs/workflow-run-1/resume",
            json={"workflow_run_id": "workflow-run-1", "to_status": "running"},
        )

    assert created.status_code == 200
    assert listed.status_code == 200
    assert fetched.status_code == 200
    assert run.status_code == 200
    assert runs.status_code == 200
    assert paused.json()["status"] == "paused"
    assert resumed.json()["status"] == "running"


def test_workflow_api_worker_scheduler_and_status_endpoints() -> None:
    """Workflow operational endpoints remain explicit one-shot controls."""
    with workflow_overrides(FakeWorkflowService()):
        client = TestClient(app)
        scheduler = client.post("/brain/workflows/scheduler/tick", json={"dry_run": True})
        worker = client.post("/brain/workflows/worker/start-once", json={"max_runs": 1})
        engine = client.get("/brain/workflows/engine/status")
        temporal = client.get("/brain/workflows/temporal/status")

    assert scheduler.status_code == 200
    assert worker.status_code == 200
    assert engine.json()["active_adapter"] == "local"
    assert temporal.json()["reason"] == "temporal_disabled"


def workflow_overrides(service: FakeWorkflowService) -> object:
    """Install workflow API dependency overrides for one context."""

    class OverrideContext:
        def __enter__(self) -> None:
            app.dependency_overrides[get_workflow_service] = lambda: service
            app.dependency_overrides[get_workflow_policy_adapter] = lambda: FakePolicyAdapter()
            app.dependency_overrides[get_actor_context] = lambda: ActorContext(
                actor_id="actor-1",
                workspace_id="workspace-1",
                permissions=["workflow.read"],
                security_scope=["workspace:main"],
                dev_mode=True,
            )
            app.dependency_overrides[get_workflow_scheduler] = lambda: SimpleNamespace(
                tick=lambda: {"status": "completed", "triggered": 0}
            )
            app.dependency_overrides[get_workflow_worker] = lambda: SimpleNamespace(
                start_once=lambda max_runs=None: {"status": "completed", "ran": max_runs or 0}
            )

        def __exit__(self, *args: object) -> None:
            app.dependency_overrides.clear()

    return OverrideContext()


def create_payload() -> dict[str, object]:
    """Create a workflow API payload."""
    return {
        "workflow_id": "workflow-1",
        "name": "Generic workflow",
        "description": "Generic workflow description",
        "owner_scope": ["workspace:main"],
        "trigger_type": "manual",
        "steps": [
            {
                "step_id": "noop",
                "action_type": "noop",
                "description": "No-op step",
                "risk_level": "low",
            }
        ],
        "risk_level": "low",
        "activate": True,
    }


def make_workflow() -> WorkflowDefinition:
    """Create a workflow definition."""
    now = datetime.now(UTC)
    return WorkflowDefinition(
        workflow_id="workflow-1",
        name="Generic workflow",
        description="Generic workflow description",
        status="active",
        owner_scope=["workspace:main"],
        trigger_type="manual",
        trigger_config={},
        steps=[
            {
                "step_id": "noop",
                "action_type": "noop",
                "description": "No-op step",
                "risk_level": "low",
            }
        ],
        risk_level="low",
        created_at=now,
        updated_at=now,
    )


def make_run(workflow_run_id: str = "workflow-run-1") -> WorkflowRun:
    """Create a workflow run."""
    now = datetime.now(UTC)
    return WorkflowRun(
        workflow_run_id=workflow_run_id,
        workflow_id="workflow-1",
        trace_id="trace-1",
        status="completed",
        trigger_type="manual",
        input={},
        output={},
        error={},
        retry_count=0,
        step_runs=[],
        started_at=now,
        completed_at=now,
        created_at=now,
        updated_at=now,
    )
