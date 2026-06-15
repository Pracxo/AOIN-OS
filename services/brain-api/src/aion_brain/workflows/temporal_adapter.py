"""Optional Temporal workflow engine adapter boundary."""

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.workflows import (
    TemporalAdapterStatus,
    WorkflowCreateRequest,
    WorkflowDefinition,
    WorkflowEngineStatus,
    WorkflowRun,
    WorkflowRunRequest,
    WorkflowTransitionRequest,
)
from aion_brain.workflows.temporal_compat import TemporalCompat


class TemporalAdapter:
    """Temporal is optional. AION contracts must remain independent of Temporal internals."""

    def __init__(
        self,
        *,
        enabled: bool,
        endpoint_ref: str | None,
        namespace: str,
        task_queue: str,
        compat: TemporalCompat | None = None,
    ) -> None:
        self._enabled = enabled
        self._endpoint_ref = endpoint_ref
        self._namespace = namespace
        self._task_queue = task_queue
        self._compat = compat or TemporalCompat()

    def temporal_status(self) -> TemporalAdapterStatus:
        """Return optional Temporal adapter status without connecting."""
        available = self._compat.is_available()
        reason = (
            "temporal_disabled"
            if not self._enabled
            else None
            if available
            else self._compat.availability_reason()
        )
        return TemporalAdapterStatus(
            adapter_name="temporal",
            enabled=self._enabled,
            package_available=available,
            endpoint_ref=self._endpoint_ref,
            reason=reason,
            metadata={"namespace": self._namespace, "task_queue": self._task_queue},
        )

    def create_workflow(self, request: WorkflowCreateRequest) -> WorkflowDefinition:
        """Temporal workflow definition creation is owned by the local repository."""
        raise NotImplementedError("Temporal workflow definition persistence is local in v0.1.")

    def run_workflow(self, request: WorkflowRunRequest) -> WorkflowRun:
        """Return a structured unavailable run unless explicitly implemented later."""
        now = datetime.now(UTC)
        reason = "temporal_disabled" if not self._enabled else "temporal_unavailable"
        return WorkflowRun(
            workflow_run_id=request.workflow_run_id or f"workflow-run-{uuid4().hex}",
            workflow_id=request.workflow_id,
            trace_id=request.trace_id,
            task_id=request.task_id,
            goal_id=request.goal_id,
            execution_id=None,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            status="failed",
            trigger_type="manual",
            input=request.input,
            output={},
            error={"reason": reason},
            retry_count=0,
            step_runs=[],
            started_at=None,
            completed_at=now,
            next_retry_at=None,
            created_at=now,
            updated_at=now,
        )

    def pause_run(self, request: WorkflowTransitionRequest) -> WorkflowRun:
        """Temporal pause is not implemented in v0.1."""
        raise NotImplementedError("Temporal pause is not implemented in v0.1.")

    def resume_run(self, request: WorkflowTransitionRequest) -> WorkflowRun:
        """Temporal resume is not implemented in v0.1."""
        raise NotImplementedError("Temporal resume is not implemented in v0.1.")

    def cancel_run(self, request: WorkflowTransitionRequest) -> WorkflowRun:
        """Temporal cancellation is not implemented in v0.1."""
        raise NotImplementedError("Temporal cancel is not implemented in v0.1.")

    def retry_run(
        self,
        workflow_run_id: str,
        actor_id: str | None,
        reason: str | None,
    ) -> WorkflowRun:
        """Temporal retry is not implemented in v0.1."""
        raise NotImplementedError("Temporal retry is not implemented in v0.1.")

    def status(self) -> WorkflowEngineStatus:
        """Return an engine status for the optional Temporal adapter."""
        adapter_status = self.temporal_status()
        return WorkflowEngineStatus(
            engine_name="aion-workflow-engine",
            active_adapter="temporal",
            temporal_available=adapter_status.package_available,
            temporal_enabled=adapter_status.enabled,
            local_worker_enabled=False,
            pending_runs=0,
            running_runs=0,
            failed_runs=0,
            metadata={"reason": adapter_status.reason},
        )
