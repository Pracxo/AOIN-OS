"""Dry-run cognitive task runner."""

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.approvals.integration import ApprovalGateResult, evaluate_approval_gate
from aion_brain.contracts.autonomy import AutonomyDecisionRequest
from aion_brain.contracts.execution import ExecutionRequest
from aion_brain.contracts.planning import PlanGraph
from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.tasks import (
    CognitiveTask,
    LifecycleEventType,
    TaskLifecycleEvent,
    TaskRunRecord,
    TaskRunRequest,
)
from aion_brain.contracts.workflows import WorkflowRunMode, WorkflowRunRequest
from aion_brain.policy.base import PolicyAdapter
from aion_brain.tasks.repository import TaskRepository
from aion_brain.tasks.service import (
    TaskService,
    get_task_from_repository,
    transition_task_record,
)

_CONTROLLED_TASK_TYPES = {"brain.plan", "brain.evaluate", "brain.learn", "generic"}


class CognitiveTaskRunner:
    """Runs explicit cognitive task requests without background workers."""

    def __init__(
        self,
        *,
        task_service: TaskService,
        policy_adapter: PolicyAdapter,
        task_repository: TaskRepository | object,
        execution_orchestrator: object | None = None,
        brain_runtime: object | None = None,
        workflow_service: object | None = None,
        telemetry_service: object | None = None,
        approval_service: object | None = None,
        autonomy_governor: object | None = None,
    ) -> None:
        self._task_service = task_service
        self._policy_adapter = policy_adapter
        self._repository = task_repository
        self._execution_orchestrator = execution_orchestrator
        self._brain_runtime = brain_runtime
        self._workflow_service = workflow_service
        self._telemetry_service = telemetry_service
        self._approval_service = approval_service
        self._autonomy_governor = autonomy_governor

    def run_task(self, request: TaskRunRequest) -> TaskRunRecord:
        """Run a task explicitly in dry-run or controlled mode."""
        task = get_task_from_repository(self._repository, request.task_id)
        if task is None:
            raise ValueError("task_not_found")
        run_id = request.task_run_id or f"task-run-{task.task_id}-{uuid4().hex}"
        autonomy = self._autonomy_decision(task, request, run_id)
        if autonomy is not None and not bool(getattr(autonomy, "allow", False)):
            return self._finish_without_running(
                task,
                request,
                run_id,
                "blocked_by_policy",
                {
                    "reason": str(getattr(autonomy, "reason", "autonomy_denied")),
                    "autonomy_decision_id": getattr(autonomy, "autonomy_decision_id", None),
                },
                "task_run_blocked",
            )
        decision = self._policy_adapter.authorize(
            PolicyRequest(
                request_id=f"task.run-{run_id}",
                trace_id=request.trace_id or task.trace_id,
                actor_id=task.actor_id,
                workspace_id=task.workspace_id,
                action_type="task.run",
                resource_type="task",
                resource_id=task.task_id,
                risk_level=task.risk_level,
                approval_present=request.approval_present,
                requested_permissions=[],
                security_scope=task.owner_scope,
                context={"run_mode": request.run_mode, "task_type": task.task_type},
            )
        )
        if not decision.allow:
            return self._finish_without_running(
                task,
                request,
                run_id,
                "blocked_by_policy",
                {"reason": decision.reason},
                "task_run_blocked",
            )
        if task.risk_level in {"high", "critical"} and not request.approval_present:
            gate = self._approval_gate_for_task(task, request)
            if gate is not None and gate.final_decision == "block":
                return self._finish_without_running(
                    task,
                    request,
                    run_id,
                    "blocked_by_policy",
                    {"reason": gate.reason, "constraints": gate.constraints},
                    "task_run_blocked",
                )
            return self._finish_without_running(
                task,
                request,
                run_id,
                "waiting_for_approval",
                {
                    "reason": "approval_required",
                    "approval_request_id": (gate.approval_request_id if gate is not None else None),
                },
                "task_run_blocked",
            )

        running_task = self._mark_running(task)
        started_at = datetime.now(UTC)
        self._task_service.record_event(
            TaskLifecycleEvent(
                lifecycle_event_id=f"lifecycle-{run_id}-started",
                task_id=task.task_id,
                goal_id=task.goal_id,
                trace_id=request.trace_id or task.trace_id,
                event_type="task_run_started",
                from_status=task.status,
                to_status="running",
                reason=None,
                payload={"run_mode": request.run_mode},
                created_at=started_at,
            )
        )
        self._task_service.emit_task(running_task, "task_run_started", 0.6)
        if _workflow_requested(task, request):
            run = self._run_explicit_workflow(running_task, request, run_id, started_at)
        elif request.run_mode == "dry_run":
            run = TaskRunRecord(
                task_run_id=run_id,
                task_id=task.task_id,
                trace_id=request.trace_id or task.trace_id,
                execution_id=task.execution_id,
                status="completed",
                run_mode="dry_run",
                input={"task": task.model_dump(mode="json"), "metadata": request.metadata},
                output={
                    "dry_run": True,
                    "task_id": task.task_id,
                    "message": "Task validated but not executed.",
                },
                error={},
                started_at=started_at,
                completed_at=datetime.now(UTC),
                created_at=started_at,
            )
        else:
            run = self._run_controlled(running_task, request, run_id, started_at)
        saved_run = self._save_run(run)
        final_task = transition_task_record(
            running_task,
            "completed" if saved_run.status == "completed" else "failed",
        )
        self._save_task(final_task)
        self._task_service.record_event(_run_event(saved_run, final_task))
        self._task_service.emit_task(
            final_task,
            "task_run_completed" if saved_run.status == "completed" else "task_run_failed",
            1.0 if saved_run.status == "completed" else 0.9,
        )
        return saved_run

    def _run_explicit_workflow(
        self,
        task: CognitiveTask,
        request: TaskRunRequest,
        run_id: str,
        started_at: datetime,
    ) -> TaskRunRecord:
        workflow_id = _workflow_id(task, request)
        if workflow_id is None:
            return _run_record(
                task,
                request,
                run_id,
                "failed",
                {},
                {"reason": "workflow_id_required"},
                started_at,
            )
        run_workflow = getattr(self._workflow_service, "run_workflow", None)
        if not callable(run_workflow):
            return _run_record(
                task,
                request,
                run_id,
                "failed",
                {},
                {"reason": "workflow_service_unavailable"},
                started_at,
            )
        metadata = _merged_metadata(task, request)
        workflow_mode: WorkflowRunMode = (
            "controlled" if metadata.get("workflow_mode") == "controlled" else "dry_run"
        )
        try:
            workflow_run = run_workflow(
                WorkflowRunRequest(
                    workflow_id=workflow_id,
                    trace_id=request.trace_id or task.trace_id,
                    task_id=task.task_id,
                    goal_id=task.goal_id,
                    actor_id=task.actor_id,
                    workspace_id=task.workspace_id,
                    mode=workflow_mode,
                    input=task.input,
                    approval_present=request.approval_present,
                    metadata=metadata,
                )
            )
        except Exception as exc:
            return _run_record(
                task,
                request,
                run_id,
                "failed",
                {},
                {"reason": str(exc)},
                started_at,
            )
        task_run_status = _task_status_from_workflow_status(str(workflow_run.status))
        return _run_record(
            task,
            request,
            run_id,
            task_run_status,
            {
                "workflow_run_id": workflow_run.workflow_run_id,
                "workflow_id": workflow_run.workflow_id,
                "workflow_status": workflow_run.status,
                "dry_run": workflow_mode == "dry_run",
            },
            workflow_run.error if task_run_status != "completed" else {},
            started_at,
        )

    def _finish_without_running(
        self,
        task: CognitiveTask,
        request: TaskRunRequest,
        run_id: str,
        status: str,
        error: dict[str, Any],
        event_type: str,
    ) -> TaskRunRecord:
        now = datetime.now(UTC)
        run = TaskRunRecord(
            task_run_id=run_id,
            task_id=task.task_id,
            trace_id=request.trace_id or task.trace_id,
            execution_id=task.execution_id,
            status=status,  # type: ignore[arg-type]
            run_mode=request.run_mode,
            input={"task": task.model_dump(mode="json"), "metadata": request.metadata},
            output={},
            error=error,
            started_at=None,
            completed_at=now,
            created_at=now,
        )
        saved_run = self._save_run(run)
        self._task_service.record_event(
            TaskLifecycleEvent(
                lifecycle_event_id=f"lifecycle-{run_id}-{event_type}",
                task_id=task.task_id,
                goal_id=task.goal_id,
                trace_id=request.trace_id or task.trace_id,
                event_type=event_type,  # type: ignore[arg-type]
                from_status=task.status,
                to_status=status,
                reason=error.get("reason"),
                payload={"run_mode": request.run_mode},
                created_at=now,
            )
        )
        self._task_service.emit_task(task, event_type, 0.9)
        return saved_run

    def _mark_running(self, task: CognitiveTask) -> CognitiveTask:
        if task.status == "running":
            return task
        if task.status == "proposed":
            queued = transition_task_record(task, "queued")
            self._save_task(queued)
            task = queued
        running = transition_task_record(task, "running")
        return self._save_task(running)

    def _run_controlled(
        self,
        task: CognitiveTask,
        request: TaskRunRequest,
        run_id: str,
        started_at: datetime,
    ) -> TaskRunRecord:
        if task.task_type not in _CONTROLLED_TASK_TYPES:
            return _run_record(
                task,
                request,
                run_id,
                "failed",
                {},
                {"reason": "controlled_task_type_not_supported"},
                started_at,
            )
        plan_payload = task.input.get("plan")
        if task.plan_id and isinstance(plan_payload, dict) and self._execution_orchestrator:
            plan = PlanGraph(**plan_payload)
            execute = getattr(self._execution_orchestrator, "execute", None)
            if callable(execute):
                execution_id = task.execution_id or f"execution-{run_id}"
                execution = execute(
                    ExecutionRequest(
                        execution_id=execution_id,
                        trace_id=request.trace_id or task.trace_id,
                        plan=plan,
                        requested_by=task.actor_id,
                        workspace_id=task.workspace_id,
                        mode="controlled",
                        approval_present=request.approval_present,
                        metadata={**task.metadata, **request.metadata},
                    )
                )
                return _run_record(
                    task,
                    request,
                    run_id,
                    "completed",
                    {"execution_id": execution.execution_id, "execution_status": execution.status},
                    {},
                    started_at,
                )
        return _run_record(
            task,
            request,
            run_id,
            "completed",
            {
                "executed": True,
                "task_id": task.task_id,
                "message": "Generic controlled task completed without external side effects.",
            },
            {},
            started_at,
        )

    def _save_task(self, task: CognitiveTask) -> CognitiveTask:
        save_task = getattr(self._repository, "save_task", None)
        if callable(save_task):
            result = save_task(task)
            if isinstance(result, CognitiveTask):
                return result
        return task

    def _save_run(self, run: TaskRunRecord) -> TaskRunRecord:
        save_run = getattr(self._repository, "save_task_run", None)
        if callable(save_run):
            result = save_run(run)
            if isinstance(result, TaskRunRecord):
                return result
        return run

    def _approval_gate_for_task(
        self,
        task: CognitiveTask,
        request: TaskRunRequest,
    ) -> ApprovalGateResult | None:
        return evaluate_approval_gate(
            self._approval_service,
            trace_id=request.trace_id or task.trace_id,
            actor_id=task.actor_id,
            workspace_id=task.workspace_id,
            action_type="task.run",
            resource_type="task",
            resource_id=task.task_id,
            requested_risk_level=task.risk_level,
            security_scope=task.owner_scope,
            payload={"task_id": task.task_id, "task_type": task.task_type},
            context={
                "mode": request.run_mode,
                "approval_present": request.approval_present,
                "controlled_execution": request.run_mode == "controlled",
            },
            metadata={"task_run_id": request.task_run_id},
        )

    def _autonomy_decision(
        self,
        task: CognitiveTask,
        request: TaskRunRequest,
        run_id: str,
    ) -> object | None:
        decide = getattr(self._autonomy_governor, "decide", None)
        if not callable(decide):
            return None
        requested_mode = "dry_run" if request.run_mode == "dry_run" else "supervised_controlled"
        metadata = _merged_metadata(task, request)
        return cast(
            object,
            decide(
                AutonomyDecisionRequest(
                    trace_id=request.trace_id or task.trace_id,
                    actor_id=task.actor_id,
                    workspace_id=task.workspace_id,
                    requested_mode=cast(Any, requested_mode),
                    action_type="task.run",
                    resource_type="task",
                    resource_id=task.task_id,
                    risk_level=task.risk_level,
                    approval_present=request.approval_present,
                    delegation_id=_metadata_str(metadata, "delegation_id"),
                    context={
                        "run_mode": request.run_mode,
                        "task_run_id": run_id,
                        "security_scope": task.owner_scope,
                        "controlled_execution": request.run_mode == "controlled",
                    },
                    metadata=metadata,
                )
            ),
        )


def _run_record(
    task: CognitiveTask,
    request: TaskRunRequest,
    run_id: str,
    status: str,
    output: dict[str, Any],
    error: dict[str, Any],
    started_at: datetime,
) -> TaskRunRecord:
    return TaskRunRecord(
        task_run_id=run_id,
        task_id=task.task_id,
        trace_id=request.trace_id or task.trace_id,
        execution_id=task.execution_id,
        status=status,  # type: ignore[arg-type]
        run_mode=request.run_mode,
        input={"task": task.model_dump(mode="json"), "metadata": request.metadata},
        output=output,
        error=error,
        started_at=started_at,
        completed_at=datetime.now(UTC),
        created_at=started_at,
    )


def _merged_metadata(task: CognitiveTask, request: TaskRunRequest) -> dict[str, Any]:
    return {**task.metadata, **request.metadata}


def _workflow_requested(task: CognitiveTask, request: TaskRunRequest) -> bool:
    return bool(_merged_metadata(task, request).get("run_workflow"))


def _workflow_id(task: CognitiveTask, request: TaskRunRequest) -> str | None:
    value = _merged_metadata(task, request).get("workflow_id")
    return value if isinstance(value, str) and value.strip() else None


def _metadata_str(metadata: dict[str, Any], key: str) -> str | None:
    value = metadata.get(key)
    return value if isinstance(value, str) and value else None


def _task_status_from_workflow_status(status: str) -> str:
    if status == "blocked_by_policy":
        return "blocked_by_policy"
    if status == "waiting_for_approval":
        return "waiting_for_approval"
    if status in {"failed", "cancelled"}:
        return "failed"
    return "completed"


def _run_event(run: TaskRunRecord, task: CognitiveTask) -> TaskLifecycleEvent:
    event_type = "task_run_completed" if run.status == "completed" else "task_run_failed"
    return TaskLifecycleEvent(
        lifecycle_event_id=f"lifecycle-{run.task_run_id}-{event_type}",
        task_id=task.task_id,
        goal_id=task.goal_id,
        trace_id=run.trace_id,
        event_type=cast(LifecycleEventType, event_type),
        from_status="running",
        to_status=run.status,
        reason=run.error.get("reason") if run.error else None,
        payload={"run_mode": run.run_mode, "output": run.output},
        created_at=datetime.now(UTC),
    )
