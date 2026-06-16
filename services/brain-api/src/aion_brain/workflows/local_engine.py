"""Local database-backed durable workflow engine."""

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.approvals.integration import ApprovalGateResult, evaluate_approval_gate
from aion_brain.contracts.autonomy import AutonomyDecisionRequest
from aion_brain.contracts.effects import ObservedEffectCreateRequest
from aion_brain.contracts.execution import ExecutionRequest
from aion_brain.contracts.modules import CapabilityInvocationRequest
from aion_brain.contracts.outcomes import OutcomeCreateRequest
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.tasks import TaskRunRequest
from aion_brain.contracts.telemetry import VisualTelemetryEvent
from aion_brain.contracts.workflows import (
    WorkflowCreateRequest,
    WorkflowDefinition,
    WorkflowEngineStatus,
    WorkflowRun,
    WorkflowRunRequest,
    WorkflowRunStatus,
    WorkflowStep,
    WorkflowStepRun,
    WorkflowStepRunStatus,
    WorkflowTransitionRequest,
)
from aion_brain.policy.base import PolicyAdapter
from aion_brain.workflows.repository import WorkflowRepository
from aion_brain.workflows.state_machine import (
    calculate_next_retry_at,
    require_valid_workflow_run_transition,
    require_valid_workflow_step_transition,
)

_CONTROLLED_INTERNAL_ACTIONS = {
    "noop",
    "wait",
    "brain.retrieve",
    "brain.evaluate",
    "brain.learn",
    "generic",
}


class LocalWorkflowEngine:
    """Side-effect-free-by-default durable workflow runner."""

    def __init__(
        self,
        *,
        repository: WorkflowRepository,
        policy_adapter: PolicyAdapter,
        telemetry_service: object | None = None,
        execution_orchestrator: object | None = None,
        task_runner: object | None = None,
        capability_runtime_gateway: object | None = None,
        temporal_available: bool = False,
        temporal_enabled: bool = False,
        local_worker_enabled: bool = False,
        approval_service: object | None = None,
        autonomy_governor: object | None = None,
        observed_effect_collector: object | None = None,
        outcome_service: object | None = None,
        settings: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._execution_orchestrator = execution_orchestrator
        self._task_runner = task_runner
        self._capability_runtime_gateway = capability_runtime_gateway
        self._temporal_available = temporal_available
        self._temporal_enabled = temporal_enabled
        self._local_worker_enabled = local_worker_enabled
        self._approval_service = approval_service
        self._autonomy_governor = autonomy_governor
        self._observed_effect_collector = observed_effect_collector
        self._outcome_service = outcome_service
        self._settings = settings

    def create_workflow(self, request: WorkflowCreateRequest) -> WorkflowDefinition:
        """Create a workflow definition after policy authorization."""
        decision = self._authorize(
            action_type="workflow.create",
            resource_type="workflow",
            resource_id=request.workflow_id,
            risk_level=request.risk_level,
            trace_id=None,
            actor_id=request.created_by,
            workspace_id=None,
            scope=request.owner_scope,
            approval_present=True,
            context=request.model_dump(mode="json"),
        )
        if not decision.allow:
            raise ValueError(f"policy_denied:{decision.reason}")
        now = datetime.now(UTC)
        workflow = WorkflowDefinition(
            workflow_id=request.workflow_id or f"workflow-{uuid4().hex}",
            name=request.name,
            description=request.description,
            status="active" if request.activate else "draft",
            owner_scope=request.owner_scope,
            trigger_type=request.trigger_type,
            trigger_config=request.trigger_config,
            steps=request.steps,
            retry_policy=request.retry_policy,
            timeout_seconds=request.timeout_seconds,
            risk_level=request.risk_level,
            metadata=request.metadata,
            created_by=request.created_by,
            created_at=now,
            updated_at=now,
            disabled_at=None,
        )
        saved = self._repository.save_workflow(workflow)
        self._record_event(saved.workflow_id, None, None, "workflow_created", None, saved.status)
        self._emit("workflow_created", "workflow", saved.workflow_id, 0.5, {"status": saved.status})
        return saved

    def get_workflow(self, workflow_id: str, scope: list[str]) -> WorkflowDefinition | None:
        """Return one workflow definition if scope permits."""
        self._authorize_read(workflow_id, scope)
        workflow = self._repository.get_workflow(workflow_id)
        if workflow is None or not _within_scope(workflow.owner_scope, scope):
            return None
        return workflow

    def list_workflows(
        self,
        *,
        scope: list[str],
        status: str | None = None,
        limit: int = 50,
    ) -> list[WorkflowDefinition]:
        """List workflow definitions after policy authorization."""
        self._authorize_read(None, scope)
        return self._repository.list_workflows(scope=scope, status=status, limit=limit)

    def update_workflow_status(
        self,
        workflow_id: str,
        status: str,
        *,
        actor_id: str | None,
        reason: str | None,
    ) -> WorkflowDefinition:
        """Activate, disable, or archive a workflow definition."""
        workflow = self._repository.get_workflow(workflow_id)
        if workflow is None:
            raise ValueError("workflow_not_found")
        action = "workflow.activate" if status == "active" else "workflow.disable"
        decision = self._authorize(
            action_type=action,
            resource_type="workflow",
            resource_id=workflow_id,
            risk_level="medium",
            trace_id=None,
            actor_id=actor_id,
            workspace_id=None,
            scope=workflow.owner_scope,
            approval_present=True,
            context={"status": status, "reason": reason},
        )
        if not decision.allow:
            raise ValueError(f"policy_denied:{decision.reason}")
        now = datetime.now(UTC)
        updated = workflow.model_copy(
            update={
                "status": status,
                "updated_at": now,
                "disabled_at": now if status == "disabled" else workflow.disabled_at,
            }
        )
        saved = self._repository.save_workflow(updated)
        event_type = "workflow_activated" if status == "active" else "workflow_disabled"
        self._record_event(
            workflow_id,
            None,
            None,
            event_type,
            workflow.status,
            saved.status,
            reason,
        )
        self._emit(event_type, "workflow", workflow_id, 0.6, {"status": saved.status})
        return saved

    def run_workflow(self, request: WorkflowRunRequest) -> WorkflowRun:
        """Run a workflow through local deterministic execution."""
        workflow = self._repository.get_workflow(request.workflow_id)
        if workflow is None:
            raise ValueError("workflow_not_found")
        now = datetime.now(UTC)
        run = _new_run(request, workflow, now)
        autonomy = self._autonomy_decision(workflow, request)
        if autonomy is not None and not bool(getattr(autonomy, "allow", False)):
            blocked = run.model_copy(
                update={
                    "status": "blocked_by_policy",
                    "error": {
                        "reason": str(getattr(autonomy, "reason", "autonomy_denied")),
                        "autonomy_decision_id": getattr(autonomy, "autonomy_decision_id", None),
                    },
                    "completed_at": now,
                    "updated_at": now,
                }
            )
            saved = self._repository.save_run(blocked)
            self._record_event(
                workflow.workflow_id,
                saved.workflow_run_id,
                None,
                "workflow_run_failed",
                "pending",
                saved.status,
                str(saved.error.get("reason")),
            )
            return saved
        decision = self._authorize(
            action_type="workflow.run",
            resource_type="workflow",
            resource_id=workflow.workflow_id,
            risk_level=workflow.risk_level,
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            scope=workflow.owner_scope,
            approval_present=request.approval_present,
            context={"mode": request.mode, "workflow_id": workflow.workflow_id},
        )
        if not decision.allow:
            blocked = run.model_copy(
                update={
                    "status": "blocked_by_policy",
                    "error": {"reason": decision.reason, "constraints": decision.constraints},
                    "completed_at": now,
                    "updated_at": now,
                }
            )
            saved = self._repository.save_run(blocked)
            self._record_event(
                workflow.workflow_id,
                saved.workflow_run_id,
                None,
                "workflow_run_failed",
                "pending",
                saved.status,
                decision.reason,
            )
            return saved
        if _workflow_requires_approval(workflow.risk_level, request.mode, request.approval_present):
            gate = self._approval_gate_for_workflow(workflow, request)
            if gate is not None and gate.final_decision == "block":
                waiting_error: dict[str, Any] = {
                    "reason": gate.reason,
                    "constraints": gate.constraints,
                }
                waiting_status = "blocked_by_policy"
            else:
                waiting_error = {
                    "reason": "approval_required",
                    "approval_request_id": (gate.approval_request_id if gate is not None else None),
                }
                waiting_status = "waiting_for_approval"
            waiting = run.model_copy(
                update={
                    "status": waiting_status,
                    "error": waiting_error,
                    "updated_at": now,
                }
            )
            saved = self._repository.save_run(waiting)
            self._record_event(
                workflow.workflow_id,
                saved.workflow_run_id,
                None,
                "workflow_run_started",
                "pending",
                saved.status,
            )
            return saved

        require_valid_workflow_run_transition(run.status, "running")
        running = run.model_copy(update={"status": "running", "started_at": now, "updated_at": now})
        running = self._repository.save_run(running)
        self._record_event(
            workflow.workflow_id,
            running.workflow_run_id,
            None,
            "workflow_run_started",
            "pending",
            "running",
        )
        self._emit(
            "workflow_run_started",
            "workflow_run",
            running.workflow_run_id,
            0.6,
            {"workflow_id": workflow.workflow_id},
        )
        current_run = running
        for step in workflow.steps:
            step_run = self._run_step(workflow, current_run, step, request)
            current_run.step_runs.append(step_run)
            if step_run.status in {"blocked_by_policy", "waiting_for_approval"}:
                status = cast(WorkflowRunStatus, step_run.status)
                current_run = current_run.model_copy(
                    update={
                        "status": status,
                        "error": step_run.error,
                        "updated_at": datetime.now(UTC),
                    }
                )
                return self._repository.save_run(current_run)
            if step_run.status == "failed":
                return self._finish_failed_or_retry(workflow, current_run, step, step_run)

        completed = current_run.model_copy(
            update={
                "status": "completed",
                "output": {"completed_steps": len(workflow.steps)},
                "completed_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
            }
        )
        self._record_event(
            workflow.workflow_id,
            completed.workflow_run_id,
            None,
            "workflow_run_completed",
            "running",
            "completed",
        )
        self._emit(
            "workflow_run_completed",
            "workflow_run",
            completed.workflow_run_id,
            1.0,
            {"workflow_id": workflow.workflow_id},
        )
        saved_completed = self._repository.save_run(completed)
        self._record_workflow_outcome(saved_completed, workflow.owner_scope)
        return saved_completed

    def _record_workflow_outcome(
        self,
        run: WorkflowRun,
        owner_scope: list[str],
    ) -> None:
        if not bool(getattr(self._settings, "outcome_auto_collect_from_workflows", True)):
            return
        create_observed = getattr(self._observed_effect_collector, "create_observed_effect", None)
        create_outcome = getattr(self._outcome_service, "create_outcome_once_for_source", None)
        if not callable(create_observed) or not callable(create_outcome):
            return
        try:
            observed = create_observed(
                ObservedEffectCreateRequest(
                    trace_id=run.trace_id,
                    source_type="workflow",
                    source_id=run.workflow_run_id,
                    effect_type="workflow_completed",
                    predicate="status",
                    observed_value={"status": run.status},
                    observation_source_type="workflow",
                    observation_source_id=run.workflow_run_id,
                    confidence=0.9 if run.status == "completed" else 0.6,
                    owner_scope=owner_scope,
                    metadata={"auto_collected": True, "completion_is_not_verification": True},
                    observed_at=run.completed_at,
                )
            )
            create_outcome(
                OutcomeCreateRequest(
                    trace_id=run.trace_id,
                    actor_id=run.actor_id,
                    workspace_id=run.workspace_id,
                    source_type="workflow",
                    source_id=run.workflow_run_id,
                    outcome_type="workflow",
                    title="Workflow outcome recorded",
                    summary="Workflow completion was recorded as an observed effect.",
                    owner_scope=owner_scope,
                    observed_effects=[observed.observed_effect_id],
                    confidence=observed.confidence,
                    score=0.5,
                    metadata={"auto_collected": True, "completion_is_not_verification": True},
                    observed_at=run.completed_at,
                    created_by=run.actor_id,
                )
            )
        except Exception:
            return

    def run_existing(self, workflow_run_id: str) -> WorkflowRun:
        """Run a persisted pending or retry-scheduled workflow run."""
        run = self._repository.get_run(workflow_run_id)
        if run is None:
            raise ValueError("workflow_run_not_found")
        mode = str(run.input.get("_mode", "dry_run"))
        return self.run_workflow(
            WorkflowRunRequest(
                workflow_run_id=run.workflow_run_id,
                workflow_id=run.workflow_id,
                trace_id=run.trace_id,
                task_id=run.task_id,
                goal_id=run.goal_id,
                actor_id=run.actor_id,
                workspace_id=run.workspace_id,
                mode=cast(Any, mode),
                input={key: value for key, value in run.input.items() if not key.startswith("_")},
                approval_present=bool(run.input.get("_approval_present", False)),
                metadata=_dict(run.input.get("_metadata")),
            )
        )

    def get_run(self, workflow_run_id: str, scope: list[str]) -> WorkflowRun | None:
        """Return one workflow run if scope permits."""
        run = self._repository.get_run(workflow_run_id)
        if run is None:
            return None
        workflow = self._repository.get_workflow(run.workflow_id)
        if workflow is None or not _within_scope(workflow.owner_scope, scope):
            return None
        self._authorize_read(workflow.workflow_id, scope)
        return run

    def list_runs(
        self,
        workflow_id: str | None = None,
        status: str | None = None,
        scope: list[str] | None = None,
        limit: int = 50,
    ) -> list[WorkflowRun]:
        """List workflow runs."""
        if scope is not None:
            self._authorize_read(workflow_id, scope)
        return self._repository.list_runs(
            workflow_id=workflow_id,
            status=status,
            scope=scope,
            limit=limit,
        )

    def pause_run(self, request: WorkflowTransitionRequest) -> WorkflowRun:
        """Pause a running workflow."""
        return self._transition_run(request, "workflow.pause")

    def resume_run(self, request: WorkflowTransitionRequest) -> WorkflowRun:
        """Resume a paused workflow."""
        return self._transition_run(request, "workflow.resume")

    def cancel_run(self, request: WorkflowTransitionRequest) -> WorkflowRun:
        """Cancel a workflow."""
        return self._transition_run(request, "workflow.cancel")

    def retry_run(
        self,
        workflow_run_id: str,
        actor_id: str | None,
        reason: str | None,
    ) -> WorkflowRun:
        """Schedule a retry for a failed workflow."""
        run = self._require_run(workflow_run_id)
        workflow = self._require_workflow(run.workflow_id)
        decision = self._authorize(
            action_type="workflow.retry",
            resource_type="workflow_run",
            resource_id=workflow_run_id,
            risk_level=workflow.risk_level,
            trace_id=run.trace_id,
            actor_id=actor_id,
            workspace_id=run.workspace_id,
            scope=workflow.owner_scope,
            approval_present=True,
            context={"reason": reason},
        )
        if not decision.allow:
            raise ValueError(f"policy_denied:{decision.reason}")
        require_valid_workflow_run_transition(run.status, "retry_scheduled")
        now = datetime.now(UTC)
        next_retry_at = calculate_next_retry_at(run.retry_count + 1, workflow.retry_policy, now)
        updated = run.model_copy(
            update={
                "status": "retry_scheduled",
                "retry_count": run.retry_count + 1,
                "next_retry_at": next_retry_at,
                "updated_at": now,
                "error": {"reason": reason or "retry_requested"},
            }
        )
        self._record_event(
            workflow.workflow_id,
            run.workflow_run_id,
            None,
            "workflow_retry_scheduled",
            run.status,
            "retry_scheduled",
            reason,
        )
        self._emit("workflow_retry_scheduled", "workflow_run", run.workflow_run_id, 0.7, {})
        return self._repository.save_run(updated)

    def status(self) -> WorkflowEngineStatus:
        """Return local workflow engine status."""
        return WorkflowEngineStatus(
            engine_name="aion-workflow-engine",
            active_adapter="local",
            temporal_available=self._temporal_available,
            temporal_enabled=self._temporal_enabled,
            local_worker_enabled=self._local_worker_enabled,
            pending_runs=self._repository.count_runs("pending"),
            running_runs=self._repository.count_runs("running"),
            failed_runs=self._repository.count_runs("failed"),
            metadata={"side_effect_free_default": True},
        )

    def _run_step(
        self,
        workflow: WorkflowDefinition,
        run: WorkflowRun,
        step: WorkflowStep,
        request: WorkflowRunRequest,
    ) -> WorkflowStepRun:
        now = datetime.now(UTC)
        step_run = WorkflowStepRun(
            workflow_step_run_id=f"workflow-step-run-{uuid4().hex}",
            workflow_run_id=run.workflow_run_id,
            step_id=step.step_id,
            action_type=step.action_type,
            status="pending",
            attempt=run.retry_count + 1,
            input={"template": step.input_template, "workflow_input": request.input},
            output={},
            error={},
            started_at=None,
            completed_at=None,
            created_at=now,
            updated_at=now,
        )
        self._repository.save_step_run(step_run)
        require_valid_workflow_step_transition("pending", "running")
        step_run = step_run.model_copy(
            update={"status": "running", "started_at": now, "updated_at": now}
        )
        self._repository.save_step_run(step_run)
        self._record_event(
            workflow.workflow_id,
            run.workflow_run_id,
            step_run.workflow_step_run_id,
            "workflow_step_started",
            "pending",
            "running",
        )
        self._emit(
            "workflow_step_started",
            "workflow_step",
            step_run.workflow_step_run_id,
            0.5,
            {"step_id": step.step_id},
        )

        policy_action = (
            step.action_type if step.action_type.startswith("workflow.") else "workflow.run"
        )
        decision = self._authorize(
            action_type=policy_action,
            resource_type="workflow_step",
            resource_id=step.step_id,
            risk_level=step.risk_level,
            trace_id=run.trace_id,
            actor_id=run.actor_id,
            workspace_id=run.workspace_id,
            scope=workflow.owner_scope,
            approval_present=request.approval_present,
            context={
                "mode": request.mode,
                "workflow_id": workflow.workflow_id,
                "step_id": step.step_id,
                "step_action_type": step.action_type,
            },
        )
        if not decision.allow:
            return self._finish_step(
                workflow,
                run,
                step_run,
                "blocked_by_policy",
                {},
                {"reason": decision.reason, "constraints": decision.constraints},
            )
        if _workflow_requires_approval(step.risk_level, request.mode, request.approval_present):
            gate = self._approval_gate_for_step(workflow, run, step, request)
            if gate is not None and gate.final_decision == "block":
                return self._finish_step(
                    workflow,
                    run,
                    step_run,
                    "blocked_by_policy",
                    {},
                    {"reason": gate.reason, "constraints": gate.constraints},
                )
            return self._finish_step(
                workflow,
                run,
                step_run,
                "waiting_for_approval",
                {},
                {
                    "reason": "approval_required",
                    "approval_request_id": (gate.approval_request_id if gate is not None else None),
                },
                completed=False,
            )
        if request.mode == "dry_run":
            return self._finish_step(
                workflow,
                run,
                step_run,
                "completed",
                {"dry_run": True, "step_id": step.step_id},
                {},
            )
        output, error = self._execute_controlled_step(step, request, run)
        if error:
            return self._finish_step(workflow, run, step_run, "failed", {}, error)
        return self._finish_step(workflow, run, step_run, "completed", output, {})

    def _autonomy_decision(
        self,
        workflow: WorkflowDefinition,
        request: WorkflowRunRequest,
    ) -> object | None:
        decide = getattr(self._autonomy_governor, "decide", None)
        if not callable(decide):
            return None
        requested_mode = "dry_run" if request.mode == "dry_run" else "supervised_controlled"
        return cast(
            object,
            decide(
                AutonomyDecisionRequest(
                    trace_id=request.trace_id,
                    actor_id=request.actor_id,
                    workspace_id=request.workspace_id,
                    requested_mode=cast(Any, requested_mode),
                    action_type="workflow.run",
                    resource_type="workflow",
                    resource_id=workflow.workflow_id,
                    risk_level=workflow.risk_level,
                    approval_present=request.approval_present,
                    delegation_id=_metadata_str(request.metadata, "delegation_id"),
                    context={
                        "mode": request.mode,
                        "security_scope": workflow.owner_scope,
                        "background_workflow": bool(request.metadata.get("scheduled"))
                        or bool(request.metadata.get("worker")),
                    },
                    metadata=request.metadata,
                )
            ),
        )

    def _execute_controlled_step(
        self,
        step: WorkflowStep,
        request: WorkflowRunRequest,
        run: WorkflowRun,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        if step.action_type in _CONTROLLED_INTERNAL_ACTIONS:
            return (
                {
                    "executed": True,
                    "action_type": step.action_type,
                    "message": "Generic workflow step completed locally.",
                },
                {},
            )
        if step.action_type == "task.run":
            if not request.approval_present:
                return (
                    {
                        "dry_run": True,
                        "task_id": request.task_id,
                        "message": "Task run validated by workflow without controlled execution.",
                    },
                    {},
                )
            run_task = getattr(self._task_runner, "run_task", None)
            if callable(run_task) and request.task_id:
                task_run = run_task(
                    TaskRunRequest(
                        task_id=request.task_id,
                        trace_id=request.trace_id,
                        run_mode="dry_run",
                        approval_present=request.approval_present,
                        metadata={"workflow_run_id": run.workflow_run_id},
                    )
                )
                return {"task_run_id": task_run.task_run_id, "status": task_run.status}, {}
            return {}, {"reason": "task_runner_unavailable"}
        if step.action_type == "brain.execute":
            if not request.approval_present:
                return {"dry_run": True, "message": "Execution validated without execution."}, {}
            execute = getattr(self._execution_orchestrator, "execute", None)
            plan = step.input_template.get("plan")
            if callable(execute) and isinstance(plan, dict):
                execution = execute(
                    ExecutionRequest(
                        execution_id=f"execution-{run.workflow_run_id}-{step.step_id}",
                        trace_id=request.trace_id,
                        plan=cast(Any, plan),
                        requested_by=request.actor_id,
                        workspace_id=request.workspace_id,
                        mode="dry_run",
                        approval_present=request.approval_present,
                        metadata={"workflow_run_id": run.workflow_run_id},
                    )
                )
                return {"execution_id": execution.execution_id, "status": execution.status}, {}
            return {}, {"reason": "execution_orchestrator_unavailable"}
        if step.action_type == "capability.invoke":
            invoke = getattr(self._capability_runtime_gateway, "invoke", None)
            capability_id = step.capability_required
            if callable(invoke) and capability_id:
                result = invoke(
                    CapabilityInvocationRequest(
                        invocation_id=f"workflow-invocation-{uuid4().hex}",
                        trace_id=request.trace_id,
                        execution_id=run.execution_id,
                        step_run_id=None,
                        capability_id=capability_id,
                        actor_id=request.actor_id,
                        workspace_id=request.workspace_id,
                        mode="dry_run",
                        payload=step.input_template,
                        approval_present=request.approval_present,
                        metadata={"workflow_run_id": run.workflow_run_id},
                    )
                )
                return {"capability_status": getattr(result, "status", "unknown")}, {}
            return {}, {"reason": "capability_runtime_gateway_unavailable"}
        return {}, {"reason": "controlled_workflow_action_not_supported"}

    def _finish_step(
        self,
        workflow: WorkflowDefinition,
        run: WorkflowRun,
        step_run: WorkflowStepRun,
        status: str,
        output: dict[str, Any],
        error: dict[str, Any],
        *,
        completed: bool = True,
    ) -> WorkflowStepRun:
        require_valid_workflow_step_transition(step_run.status, status)
        now = datetime.now(UTC)
        updated = step_run.model_copy(
            update={
                "status": cast(WorkflowStepRunStatus, status),
                "output": output,
                "error": error,
                "completed_at": now if completed else None,
                "updated_at": now,
            }
        )
        saved = self._repository.save_step_run(updated)
        event_type = {
            "completed": "workflow_step_completed",
            "failed": "workflow_step_failed",
            "blocked_by_policy": "workflow_step_failed",
            "waiting_for_approval": "workflow_step_failed",
        }.get(saved.status, "workflow_step_completed")
        intensity = 0.8 if saved.status == "completed" else 0.9
        self._record_event(
            workflow.workflow_id,
            run.workflow_run_id,
            saved.workflow_step_run_id,
            event_type,
            "running",
            saved.status,
            error.get("reason"),
        )
        self._emit(
            event_type,
            "workflow_step",
            saved.workflow_step_run_id,
            intensity,
            {"status": saved.status},
        )
        return saved

    def _finish_failed_or_retry(
        self,
        workflow: WorkflowDefinition,
        run: WorkflowRun,
        step: WorkflowStep,
        step_run: WorkflowStepRun,
    ) -> WorkflowRun:
        now = datetime.now(UTC)
        should_retry = step.retryable and run.retry_count + 1 < workflow.retry_policy.max_attempts
        if should_retry:
            next_retry_at = calculate_next_retry_at(run.retry_count + 1, workflow.retry_policy, now)
            updated = run.model_copy(
                update={
                    "status": "retry_scheduled",
                    "retry_count": run.retry_count + 1,
                    "error": step_run.error,
                    "next_retry_at": next_retry_at,
                    "updated_at": now,
                }
            )
            self._record_event(
                workflow.workflow_id,
                run.workflow_run_id,
                step_run.workflow_step_run_id,
                "workflow_retry_scheduled",
                "running",
                "retry_scheduled",
                step_run.error.get("reason"),
            )
            self._emit("workflow_retry_scheduled", "workflow_run", run.workflow_run_id, 0.7, {})
            return self._repository.save_run(updated)
        failed = run.model_copy(
            update={
                "status": "failed",
                "error": step_run.error,
                "completed_at": now,
                "updated_at": now,
            }
        )
        self._record_event(
            workflow.workflow_id,
            run.workflow_run_id,
            step_run.workflow_step_run_id,
            "workflow_run_failed",
            "running",
            "failed",
            step_run.error.get("reason"),
        )
        self._emit(
            "workflow_run_failed",
            "workflow_run",
            run.workflow_run_id,
            0.9,
            {"error": step_run.error},
        )
        return self._repository.save_run(failed)

    def _transition_run(
        self,
        request: WorkflowTransitionRequest,
        action_type: str,
    ) -> WorkflowRun:
        run = self._require_run(request.workflow_run_id)
        workflow = self._require_workflow(run.workflow_id)
        decision = self._authorize(
            action_type=action_type,
            resource_type="workflow_run",
            resource_id=run.workflow_run_id,
            risk_level=workflow.risk_level,
            trace_id=run.trace_id,
            actor_id=request.actor_id,
            workspace_id=run.workspace_id,
            scope=workflow.owner_scope,
            approval_present=True,
            context=request.model_dump(mode="json"),
        )
        if not decision.allow:
            raise ValueError(f"policy_denied:{decision.reason}")
        require_valid_workflow_run_transition(run.status, request.to_status)
        now = datetime.now(UTC)
        updates: dict[str, Any] = {
            "status": request.to_status,
            "updated_at": now,
            "error": {"reason": request.reason} if request.reason else run.error,
        }
        if request.to_status in {"completed", "failed", "cancelled"}:
            updates["completed_at"] = now
        updated = run.model_copy(update=updates)
        event_type = f"workflow_run_{request.to_status}"
        if request.to_status == "paused":
            event_type = "workflow_run_paused"
        if request.to_status == "running" and run.status == "paused":
            event_type = "workflow_run_resumed"
        if request.to_status == "cancelled":
            event_type = "workflow_run_cancelled"
        self._record_event(
            workflow.workflow_id,
            run.workflow_run_id,
            None,
            event_type,
            run.status,
            request.to_status,
            request.reason,
        )
        self._emit(
            event_type,
            "workflow_run",
            run.workflow_run_id,
            0.8,
            {"status": request.to_status},
        )
        return self._repository.save_run(updated)

    def _authorize_read(self, workflow_id: str | None, scope: list[str]) -> None:
        decision = self._authorize(
            action_type="workflow.read",
            resource_type="workflow",
            resource_id=workflow_id,
            risk_level="low",
            trace_id=None,
            actor_id=None,
            workspace_id=None,
            scope=scope,
            approval_present=False,
            context={},
        )
        if not decision.allow:
            raise ValueError(f"policy_denied:{decision.reason}")

    def _authorize(
        self,
        *,
        action_type: str,
        resource_type: str,
        resource_id: str | None,
        risk_level: str,
        trace_id: str | None,
        actor_id: str | None,
        workspace_id: str | None,
        scope: list[str],
        approval_present: bool,
        context: dict[str, Any],
    ) -> PolicyDecision:
        return self._policy_adapter.authorize(
            PolicyRequest(
                request_id=f"{action_type}-{resource_id or uuid4().hex}",
                trace_id=trace_id,
                actor_id=actor_id,
                workspace_id=workspace_id,
                action_type=action_type,
                resource_type=resource_type,
                resource_id=resource_id,
                risk_level=risk_level,
                approval_present=approval_present,
                requested_permissions=[],
                security_scope=scope,
                context=context,
            )
        )

    def _approval_gate_for_workflow(
        self,
        workflow: WorkflowDefinition,
        request: WorkflowRunRequest,
    ) -> ApprovalGateResult | None:
        return evaluate_approval_gate(
            self._approval_service,
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            action_type="workflow.run",
            resource_type="workflow",
            resource_id=workflow.workflow_id,
            requested_risk_level=workflow.risk_level,
            security_scope=workflow.owner_scope,
            payload={"workflow_id": workflow.workflow_id},
            context={
                "mode": request.mode,
                "approval_present": request.approval_present,
                "controlled_execution": request.mode == "controlled",
            },
            metadata={"workflow_run_id": request.workflow_run_id},
        )

    def _approval_gate_for_step(
        self,
        workflow: WorkflowDefinition,
        run: WorkflowRun,
        step: WorkflowStep,
        request: WorkflowRunRequest,
    ) -> ApprovalGateResult | None:
        return evaluate_approval_gate(
            self._approval_service,
            trace_id=run.trace_id,
            actor_id=run.actor_id,
            workspace_id=run.workspace_id,
            action_type=step.action_type,
            resource_type="workflow_step",
            resource_id=step.step_id,
            requested_risk_level=step.risk_level,
            security_scope=workflow.owner_scope,
            payload={"step_id": step.step_id, "capability_required": step.capability_required},
            context={
                "mode": request.mode,
                "approval_present": request.approval_present,
                "controlled_execution": request.mode == "controlled",
                "invokes_capability": step.action_type == "capability.invoke",
            },
            metadata={"workflow_run_id": run.workflow_run_id},
        )

    def _require_run(self, workflow_run_id: str) -> WorkflowRun:
        run = self._repository.get_run(workflow_run_id)
        if run is None:
            raise ValueError("workflow_run_not_found")
        return run

    def _require_workflow(self, workflow_id: str) -> WorkflowDefinition:
        workflow = self._repository.get_workflow(workflow_id)
        if workflow is None:
            raise ValueError("workflow_not_found")
        return workflow

    def _record_event(
        self,
        workflow_id: str | None,
        workflow_run_id: str | None,
        step_run_id: str | None,
        event_type: str,
        from_status: str | None,
        to_status: str | None,
        reason: str | None = None,
    ) -> None:
        self._repository.save_event(
            workflow_event_id=f"workflow-event-{uuid4().hex}",
            workflow_id=workflow_id,
            workflow_run_id=workflow_run_id,
            step_run_id=step_run_id,
            event_type=event_type,
            from_status=from_status,
            to_status=to_status,
            reason=reason,
            payload={},
        )

    def _emit(
        self,
        event_type: str,
        node_type: str,
        node_id: str,
        intensity: float,
        payload: dict[str, Any],
    ) -> None:
        if self._telemetry_service is None:
            return
        event = VisualTelemetryEvent(
            telemetry_id=f"telemetry-{node_id}-{event_type}",
            trace_id=node_id,
            event_type=cast(Any, event_type),
            node_type=cast(Any, node_type),
            node_id=node_id,
            edge_from=None,
            edge_to=node_id,
            intensity=intensity,
            payload=payload,
            created_at=datetime.now(UTC),
        )
        emit = getattr(self._telemetry_service, "emit", None)
        save = getattr(self._telemetry_service, "save_visual_telemetry", None)
        if callable(emit):
            emit(event)
        elif callable(save):
            save(event.trace_id, [event])


def _new_run(
    request: WorkflowRunRequest,
    workflow: WorkflowDefinition,
    now: datetime,
) -> WorkflowRun:
    run_input = {
        **request.input,
        "_mode": request.mode,
        "_approval_present": request.approval_present,
        "_metadata": request.metadata,
    }
    return WorkflowRun(
        workflow_run_id=request.workflow_run_id or f"workflow-run-{uuid4().hex}",
        workflow_id=workflow.workflow_id,
        trace_id=request.trace_id,
        task_id=request.task_id,
        goal_id=request.goal_id,
        execution_id=None,
        actor_id=request.actor_id,
        workspace_id=request.workspace_id,
        status="pending",
        trigger_type=workflow.trigger_type,
        input=run_input,
        output={},
        error={},
        retry_count=0,
        step_runs=[],
        started_at=None,
        completed_at=None,
        next_retry_at=None,
        created_at=now,
        updated_at=now,
    )


def _within_scope(owner_scope: list[str], requested_scope: list[str]) -> bool:
    return any(scope in owner_scope for scope in requested_scope)


def _workflow_requires_approval(
    risk_level: str,
    mode: str,
    approval_present: bool,
) -> bool:
    if approval_present:
        return False
    return risk_level in {"high", "critical"}


def _dict(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _metadata_str(metadata: dict[str, Any], key: str) -> str | None:
    value = metadata.get(key)
    return value if isinstance(value, str) and value else None
