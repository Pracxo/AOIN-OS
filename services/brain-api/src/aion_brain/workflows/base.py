"""Workflow engine adapter boundary."""

from typing import Protocol

from aion_brain.contracts.workflows import (
    WorkflowCreateRequest,
    WorkflowDefinition,
    WorkflowEngineStatus,
    WorkflowRun,
    WorkflowRunRequest,
    WorkflowTransitionRequest,
)


class WorkflowEngineAdapter(Protocol):
    """AION-owned boundary for durable workflow engines."""

    def create_workflow(self, request: WorkflowCreateRequest) -> WorkflowDefinition:
        """Create a workflow definition."""
        ...

    def run_workflow(self, request: WorkflowRunRequest) -> WorkflowRun:
        """Run a workflow through the engine."""
        ...

    def pause_run(self, request: WorkflowTransitionRequest) -> WorkflowRun:
        """Pause a workflow run."""
        ...

    def resume_run(self, request: WorkflowTransitionRequest) -> WorkflowRun:
        """Resume a workflow run."""
        ...

    def cancel_run(self, request: WorkflowTransitionRequest) -> WorkflowRun:
        """Cancel a workflow run."""
        ...

    def retry_run(
        self,
        workflow_run_id: str,
        actor_id: str | None,
        reason: str | None,
    ) -> WorkflowRun:
        """Schedule a retry for a workflow run."""
        ...

    def status(self) -> WorkflowEngineStatus:
        """Return public engine status."""
        ...
