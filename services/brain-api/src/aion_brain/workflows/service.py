"""Workflow orchestration service and adapter selector."""

from aion_brain.contracts.workflows import (
    TemporalAdapterStatus,
    WorkflowCreateRequest,
    WorkflowDefinition,
    WorkflowEngineStatus,
    WorkflowRun,
    WorkflowRunRequest,
    WorkflowTransitionRequest,
)
from aion_brain.workflows.local_engine import LocalWorkflowEngine
from aion_brain.workflows.temporal_adapter import TemporalAdapter


class WorkflowService:
    """Facade for durable workflow definitions and active engine selection."""

    def __init__(
        self,
        *,
        local_engine: LocalWorkflowEngine,
        temporal_adapter: TemporalAdapter,
        workflow_engine_adapter: str,
        temporal_enabled: bool,
    ) -> None:
        self._local_engine = local_engine
        self._temporal_adapter = temporal_adapter
        self._workflow_engine_adapter = workflow_engine_adapter
        self._temporal_enabled = temporal_enabled

    def create_workflow(self, request: WorkflowCreateRequest) -> WorkflowDefinition:
        """Create a workflow definition in the canonical local repository."""
        return self._local_engine.create_workflow(request)

    def get_workflow(self, workflow_id: str, scope: list[str]) -> WorkflowDefinition | None:
        """Return one workflow definition."""
        return self._local_engine.get_workflow(workflow_id, scope)

    def list_workflows(
        self,
        *,
        scope: list[str],
        status: str | None = None,
        limit: int = 50,
    ) -> list[WorkflowDefinition]:
        """List workflow definitions."""
        return self._local_engine.list_workflows(scope=scope, status=status, limit=limit)

    def update_workflow_status(
        self,
        workflow_id: str,
        status: str,
        *,
        actor_id: str | None,
        reason: str | None,
    ) -> WorkflowDefinition:
        """Activate or disable a workflow definition."""
        return self._local_engine.update_workflow_status(
            workflow_id,
            status,
            actor_id=actor_id,
            reason=reason,
        )

    def run_workflow(self, request: WorkflowRunRequest) -> WorkflowRun:
        """Run a workflow through the selected adapter."""
        if self._workflow_engine_adapter == "temporal" and self._temporal_enabled:
            return self._temporal_adapter.run_workflow(request)
        return self._local_engine.run_workflow(request)

    def get_run(self, workflow_run_id: str, scope: list[str]) -> WorkflowRun | None:
        """Return one workflow run."""
        return self._local_engine.get_run(workflow_run_id, scope)

    def list_runs(
        self,
        workflow_id: str | None = None,
        status: str | None = None,
        scope: list[str] | None = None,
        limit: int = 50,
    ) -> list[WorkflowRun]:
        """List workflow runs."""
        return self._local_engine.list_runs(
            workflow_id=workflow_id,
            status=status,
            scope=scope,
            limit=limit,
        )

    def pause_run(self, request: WorkflowTransitionRequest) -> WorkflowRun:
        """Pause a workflow run."""
        return self._local_engine.pause_run(request)

    def resume_run(self, request: WorkflowTransitionRequest) -> WorkflowRun:
        """Resume a workflow run."""
        return self._local_engine.resume_run(request)

    def cancel_run(self, request: WorkflowTransitionRequest) -> WorkflowRun:
        """Cancel a workflow run."""
        return self._local_engine.cancel_run(request)

    def retry_run(
        self,
        workflow_run_id: str,
        actor_id: str | None,
        reason: str | None,
    ) -> WorkflowRun:
        """Schedule a workflow retry."""
        return self._local_engine.retry_run(workflow_run_id, actor_id, reason)

    def engine_status(self) -> WorkflowEngineStatus:
        """Return selected workflow engine status."""
        if self._workflow_engine_adapter == "temporal" and self._temporal_enabled:
            return self._temporal_adapter.status()
        return self._local_engine.status()

    def temporal_status(self) -> TemporalAdapterStatus:
        """Return optional Temporal adapter status."""
        return self._temporal_adapter.temporal_status()
