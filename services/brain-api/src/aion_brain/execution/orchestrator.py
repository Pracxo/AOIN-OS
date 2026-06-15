"""Policy-gated execution orchestrator."""

from datetime import UTC, datetime
from typing import Any, cast

from aion_brain.approvals.integration import ApprovalGateResult, evaluate_approval_gate
from aion_brain.contracts.autonomy import AutonomyDecisionRequest
from aion_brain.contracts.execution import (
    ApprovalCheckpoint,
    CapabilityInvocationRecord,
    ExecutionRequest,
    ExecutionRun,
    ExecutionStepRun,
)
from aion_brain.contracts.planning import PlanStep
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.telemetry import VisualTelemetryEvent, VisualTelemetryEventType
from aion_brain.execution.capability_invoker import CapabilityInvoker
from aion_brain.execution.local_executor import LocalExecutor
from aion_brain.execution.state_machine import (
    require_valid_execution_transition,
    require_valid_step_transition,
)
from aion_brain.policy.base import PolicyAdapter


class ExecutionOrchestrator:
    """Executes plans through a deterministic, auditable state machine."""

    def __init__(
        self,
        *,
        policy_adapter: PolicyAdapter,
        capability_invoker: CapabilityInvoker,
        execution_repository: object | None = None,
        telemetry_service: object | None = None,
        audit_ledger: object | None = None,
        local_executor: LocalExecutor | None = None,
        approval_service: object | None = None,
        autonomy_governor: object | None = None,
    ) -> None:
        self._policy_adapter = policy_adapter
        self._capability_invoker = capability_invoker
        self._execution_repository = execution_repository
        self._telemetry_service = telemetry_service
        self._audit_ledger = audit_ledger
        self._local_executor = local_executor or LocalExecutor()
        self._approval_service = approval_service
        self._autonomy_governor = autonomy_governor

    def execute(self, request: ExecutionRequest) -> ExecutionRun:
        """Execute a plan through policy-gated dry-run or controlled mode."""
        now = datetime.now(UTC)
        run = ExecutionRun(
            execution_id=request.execution_id,
            trace_id=request.trace_id,
            plan_id=request.plan.plan_id,
            intent_id=request.plan.intent_id,
            context_id=_metadata_str(request, "context_id"),
            status="pending",
            requested_by=request.requested_by,
            workspace_id=request.workspace_id,
            steps=[],
            approvals=[],
            capability_invocations=[],
            input=request.model_dump(mode="json"),
            output={},
            error={},
            started_at=None,
            completed_at=None,
            created_at=now,
            updated_at=now,
        )
        require_valid_execution_transition("pending", "running")
        run = run.model_copy(update={"status": "running", "started_at": now, "updated_at": now})
        self._save_execution(run)
        self._emit_execution_event(run, "execution_started", 0.4)

        autonomy = self._autonomy_decision(request)
        if autonomy is not None and not bool(getattr(autonomy, "allow", False)):
            run = self._block_run(run, reason=str(getattr(autonomy, "reason", "autonomy_denied")))
            run = run.model_copy(
                update={
                    "error": {
                        **run.error,
                        "autonomy_decision_id": getattr(autonomy, "autonomy_decision_id", None),
                    }
                }
            )
            self._emit_execution_event(run, "execution_blocked", 0.9)
            return self._save_execution(run)

        plan_decision = self._authorize_plan(request)
        if plan_decision.approval_required and not request.approval_present:
            gate = self._approval_gate_for_plan(request)
            if gate is not None and gate.final_decision == "block":
                run = self._block_run(run, reason=gate.reason)
                self._emit_execution_event(run, "execution_blocked", 0.9)
                return self._save_execution(run)
            approval_id = (
                gate.approval_request_id
                if gate is not None and gate.approval_request_id is not None
                else f"approval-{request.execution_id}-plan"
            )
            approval = ApprovalCheckpoint(
                approval_id=approval_id,
                execution_id=request.execution_id,
                step_run_id=None,
                trace_id=request.trace_id,
                reason=plan_decision.reason,
                risk_level=request.plan.risk_level,
                status="pending",
                requested_by=request.requested_by,
                approved_by=None,
                approval_payload={
                    "plan_id": request.plan.plan_id,
                    "policy_decision_id": plan_decision.decision_id,
                    "approval_request_id": approval_id,
                },
                created_at=datetime.now(UTC),
                resolved_at=None,
            )
            run.approvals.append(approval)
            run = run.model_copy(
                update={
                    "status": "waiting_for_approval",
                    "updated_at": datetime.now(UTC),
                }
            )
            self._save_approval(approval)
            self._emit_approval_event(run, approval, "approval_checkpoint_created")
            return self._save_execution(run)
        if not plan_decision.allow:
            run = self._block_run(run, reason=plan_decision.reason)
            self._emit_execution_event(run, "execution_blocked", 0.9)
            return self._save_execution(run)

        if len(request.plan.steps) > request.max_steps:
            run = run.model_copy(
                update={
                    "status": "failed",
                    "error": {"reason": "max_steps_exceeded"},
                    "completed_at": datetime.now(UTC),
                    "updated_at": datetime.now(UTC),
                }
            )
            return self._save_execution(run)

        for plan_step in request.plan.steps:
            step = self._new_step(request, plan_step)
            run.steps.append(step)
            self._save_step(step)
            require_valid_step_transition("pending", "running")
            step = step.model_copy(update={"status": "running", "started_at": datetime.now(UTC)})
            self._replace_step(run, step)
            self._save_step(step)
            self._emit_step_event(run, step, "execution_step_started", 0.5)

            decision = self._authorize_step(request, plan_step)
            step = step.model_copy(update={"policy_decision_id": decision.decision_id})
            if not decision.allow:
                step = _finish_step(step, "blocked_by_policy", error={"reason": decision.reason})
                run = self._finish_blocked(run, step)
                self._emit_step_event(run, step, "policy_blocked", 0.95)
                self._emit_execution_event(run, "execution_blocked", 0.9)
                return self._persist_run_and_step(run, step)

            if self._requires_approval(request, plan_step, decision):
                gate = self._approval_gate_for_step(request, plan_step)
                if gate is not None and gate.final_decision == "block":
                    step = _finish_step(step, "blocked_by_policy", error={"reason": gate.reason})
                    run = self._finish_blocked(run, step)
                    self._emit_step_event(run, step, "policy_blocked", 0.95)
                    self._emit_execution_event(run, "execution_blocked", 0.9)
                    return self._persist_run_and_step(run, step)
                approval = self._new_approval(request, step, decision, gate)
                step = _finish_step(
                    step,
                    "waiting_for_approval",
                    output={"approval_id": approval.approval_id},
                    completed=False,
                )
                run = run.model_copy(
                    update={
                        "status": "waiting_for_approval",
                        "updated_at": datetime.now(UTC),
                    }
                )
                self._replace_step(run, step)
                run.approvals.append(approval)
                self._save_approval(approval)
                self._save_step(step)
                self._emit_approval_event(run, approval, "approval_checkpoint_created")
                return self._save_execution(run)

            step, invocation = self._execute_step(request, step)
            self._replace_step(run, step)
            if invocation is not None:
                run.capability_invocations.append(invocation)
            self._save_step(step)
            self._emit_step_event(run, step, "execution_step_completed", 0.8)
            if step.status == "failed":
                run = run.model_copy(
                    update={
                        "status": "failed",
                        "error": step.error,
                        "completed_at": datetime.now(UTC),
                        "updated_at": datetime.now(UTC),
                    }
                )
                return self._save_execution(run)

        require_valid_execution_transition("running", "completed")
        run = run.model_copy(
            update={
                "status": "completed",
                "output": {"completed_steps": len(run.steps)},
                "completed_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
            }
        )
        self._emit_execution_event(run, "execution_completed", 1.0)
        return self._save_execution(run)

    def _execute_step(
        self,
        request: ExecutionRequest,
        step: ExecutionStepRun,
    ) -> tuple[ExecutionStepRun, CapabilityInvocationRecord | None]:
        if request.mode == "dry_run":
            return (
                _finish_step(
                    step,
                    "completed",
                    output={
                        "dry_run": True,
                        "message": "Step validated but not executed.",
                    },
                ),
                None,
            )
        if step.action_type == "capability.invoke" and step.capability_required:
            invocation = self._capability_invoker.invoke(
                step.capability_required,
                {
                    "execution_id": request.execution_id,
                    "trace_id": request.trace_id,
                    "step_run_id": step.step_run_id,
                    "step_id": step.step_id,
                    "actor_id": request.requested_by,
                    "workspace_id": request.workspace_id,
                    "mode": request.mode,
                    "approval_present": request.approval_present,
                    "risk_level": step.risk_level,
                    "security_scope": request.metadata.get("security_scope", ["workspace:main"]),
                },
                request.execution_id,
                step.step_run_id,
                request.trace_id,
            )
            return (
                _finish_step(
                    step,
                    "completed",
                    output={
                        "capability_invocation_id": invocation.invocation_id,
                        "capability_status": invocation.status,
                    },
                ),
                invocation,
            )
        return self._local_executor.execute_step(step), None

    def _authorize_plan(self, request: ExecutionRequest) -> PolicyDecision:
        return self._policy_adapter.authorize(
            PolicyRequest(
                request_id=f"plan.execute-{request.execution_id}",
                trace_id=request.trace_id,
                actor_id=request.requested_by,
                workspace_id=request.workspace_id,
                action_type="plan.execute",
                resource_type="plan",
                resource_id=request.plan.plan_id,
                risk_level=request.plan.risk_level,
                approval_present=request.approval_present,
                requested_permissions=[],
                security_scope=_security_scope(request),
                context={"mode": request.mode, "plan_id": request.plan.plan_id},
            )
        )

    def _autonomy_decision(self, request: ExecutionRequest) -> object | None:
        decide = getattr(self._autonomy_governor, "decide", None)
        if not callable(decide):
            return None
        requested_mode = (
            str(request.metadata.get("autonomy_mode"))
            if isinstance(request.metadata.get("autonomy_mode"), str)
            else "dry_run"
            if request.mode == "dry_run"
            else "supervised_controlled"
        )
        return cast(
            object,
            decide(
                AutonomyDecisionRequest(
                    trace_id=request.trace_id,
                    actor_id=request.requested_by,
                    workspace_id=request.workspace_id,
                    requested_mode=cast(Any, requested_mode),
                    action_type="plan.execute",
                    resource_type="plan",
                    resource_id=request.plan.plan_id,
                    risk_level=cast(Any, request.plan.risk_level),
                    approval_present=request.approval_present,
                    delegation_id=_metadata_str(request, "delegation_id"),
                    context={
                        "mode": request.mode,
                        "security_scope": _security_scope(request),
                        "controlled_execution": request.mode == "controlled",
                    },
                    metadata=request.metadata,
                )
            ),
        )

    def _authorize_step(self, request: ExecutionRequest, step: PlanStep) -> PolicyDecision:
        return self._policy_adapter.authorize(
            PolicyRequest(
                request_id=f"execution.step-{request.execution_id}-{step.step_id}",
                trace_id=request.trace_id,
                actor_id=request.requested_by,
                workspace_id=request.workspace_id,
                action_type="execution.step",
                resource_type="plan_step",
                resource_id=step.step_id,
                risk_level=step.risk_level,
                approval_present=request.approval_present,
                requested_permissions=[],
                security_scope=_security_scope(request),
                context={
                    "mode": request.mode,
                    "step_id": step.step_id,
                    "action_type": step.action_type,
                    "capability_required": step.capability_required,
                },
            )
        )

    def _requires_approval(
        self,
        request: ExecutionRequest,
        step: PlanStep,
        decision: PolicyDecision,
    ) -> bool:
        if request.approval_present:
            return False
        return decision.approval_required or step.risk_level in {"high", "critical"}

    def _new_step(self, request: ExecutionRequest, step: PlanStep) -> ExecutionStepRun:
        now = datetime.now(UTC)
        return ExecutionStepRun(
            step_run_id=f"step-run-{request.execution_id}-{step.step_id}",
            execution_id=request.execution_id,
            plan_id=request.plan.plan_id,
            step_id=step.step_id,
            action_type=step.action_type,
            capability_required=step.capability_required,
            risk_level=step.risk_level,
            status="pending",
            attempt=1,
            input={"step": step.model_dump(mode="json"), "mode": request.mode},
            output={},
            error={},
            policy_decision_id=None,
            started_at=None,
            completed_at=None,
            created_at=now,
        )

    def _new_approval(
        self,
        request: ExecutionRequest,
        step: ExecutionStepRun,
        decision: PolicyDecision,
        gate: ApprovalGateResult | None = None,
    ) -> ApprovalCheckpoint:
        approval_id = (
            gate.approval_request_id
            if gate is not None and gate.approval_request_id is not None
            else f"approval-{request.execution_id}-{step.step_id}"
        )
        return ApprovalCheckpoint(
            approval_id=approval_id,
            execution_id=request.execution_id,
            step_run_id=step.step_run_id,
            trace_id=request.trace_id,
            reason=decision.reason,
            risk_level=step.risk_level,
            status="pending",
            requested_by=request.requested_by,
            approved_by=None,
            approval_payload={
                "step_id": step.step_id,
                "action_type": step.action_type,
                "policy_decision_id": decision.decision_id,
                "approval_request_id": approval_id,
                "control_plane_reason": gate.reason if gate is not None else None,
            },
            created_at=datetime.now(UTC),
            resolved_at=None,
        )

    def _finish_blocked(self, run: ExecutionRun, step: ExecutionStepRun) -> ExecutionRun:
        require_valid_execution_transition("running", "blocked_by_policy")
        self._replace_step(run, step)
        return run.model_copy(
            update={
                "status": "blocked_by_policy",
                "error": step.error,
                "completed_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
            }
        )

    def _approval_gate_for_plan(self, request: ExecutionRequest) -> ApprovalGateResult | None:
        return evaluate_approval_gate(
            self._approval_service,
            trace_id=request.trace_id,
            actor_id=request.requested_by,
            workspace_id=request.workspace_id,
            action_type="plan.execute",
            resource_type="plan",
            resource_id=request.plan.plan_id,
            requested_risk_level=request.plan.risk_level,
            security_scope=_security_scope(request),
            payload={"plan_id": request.plan.plan_id},
            context={
                "mode": request.mode,
                "approval_present": request.approval_present,
                "controlled_execution": request.mode == "controlled",
            },
            metadata={"plan_id": request.plan.plan_id},
        )

    def _approval_gate_for_step(
        self,
        request: ExecutionRequest,
        step: PlanStep,
    ) -> ApprovalGateResult | None:
        return evaluate_approval_gate(
            self._approval_service,
            trace_id=request.trace_id,
            actor_id=request.requested_by,
            workspace_id=request.workspace_id,
            action_type=step.action_type,
            resource_type="plan_step",
            resource_id=step.step_id,
            requested_risk_level=step.risk_level,
            security_scope=_security_scope(request),
            payload={"step_id": step.step_id, "capability_required": step.capability_required},
            context={
                "mode": request.mode,
                "approval_present": request.approval_present,
                "controlled_execution": request.mode == "controlled",
                "invokes_capability": step.action_type == "capability.invoke",
            },
            metadata={"execution_id": request.execution_id},
        )

    def _block_run(self, run: ExecutionRun, *, reason: str) -> ExecutionRun:
        require_valid_execution_transition("running", "blocked_by_policy")
        return run.model_copy(
            update={
                "status": "blocked_by_policy",
                "error": {"reason": reason},
                "completed_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
            }
        )

    def _persist_run_and_step(
        self,
        run: ExecutionRun,
        step: ExecutionStepRun,
    ) -> ExecutionRun:
        self._replace_step(run, step)
        self._save_step(step)
        return self._save_execution(run)

    def _replace_step(self, run: ExecutionRun, step: ExecutionStepRun) -> None:
        for index, existing in enumerate(run.steps):
            if existing.step_run_id == step.step_run_id:
                run.steps[index] = step
                return
        run.steps.append(step)

    def _save_execution(self, run: ExecutionRun) -> ExecutionRun:
        save = getattr(self._execution_repository, "save_execution", None)
        if callable(save):
            try:
                save(run)
            except Exception:
                pass
        return run

    def _save_step(self, step: ExecutionStepRun) -> None:
        save = getattr(self._execution_repository, "save_step", None)
        if callable(save):
            try:
                save(step)
            except Exception:
                pass

    def _save_approval(self, approval: ApprovalCheckpoint) -> None:
        save = getattr(self._execution_repository, "save_approval", None)
        if callable(save):
            try:
                save(approval)
            except Exception:
                pass

    def _emit_execution_event(
        self,
        run: ExecutionRun,
        event_type: str,
        intensity: float,
    ) -> None:
        self._emit(
            VisualTelemetryEvent(
                telemetry_id=f"telemetry-{run.execution_id}-{event_type}",
                trace_id=run.trace_id or run.execution_id,
                event_type=cast(VisualTelemetryEventType, event_type),
                node_type="execution",
                node_id=run.execution_id,
                edge_from=run.plan_id,
                edge_to=run.execution_id,
                intensity=intensity,
                payload={"status": run.status},
                created_at=datetime.now(UTC),
            )
        )

    def _emit_step_event(
        self,
        run: ExecutionRun,
        step: ExecutionStepRun,
        event_type: str,
        intensity: float,
    ) -> None:
        self._emit(
            VisualTelemetryEvent(
                telemetry_id=f"telemetry-{step.step_run_id}-{event_type}",
                trace_id=run.trace_id or run.execution_id,
                event_type=cast(VisualTelemetryEventType, event_type),
                node_type="step" if event_type.startswith("execution") else "policy",
                node_id=step.step_run_id,
                edge_from=run.execution_id,
                edge_to=step.step_run_id,
                intensity=intensity,
                payload={"status": step.status, "action_type": step.action_type},
                created_at=datetime.now(UTC),
            )
        )

    def _emit_approval_event(
        self,
        run: ExecutionRun,
        approval: ApprovalCheckpoint,
        event_type: str,
    ) -> None:
        self._emit(
            VisualTelemetryEvent(
                telemetry_id=f"telemetry-{approval.approval_id}-{event_type}",
                trace_id=run.trace_id or run.execution_id,
                event_type=cast(VisualTelemetryEventType, event_type),
                node_type="approval",
                node_id=approval.approval_id,
                edge_from=approval.step_run_id,
                edge_to=approval.approval_id,
                intensity=0.7,
                payload={"status": approval.status, "reason": approval.reason},
                created_at=datetime.now(UTC),
            )
        )

    def _emit(self, event: VisualTelemetryEvent) -> None:
        if self._telemetry_service is None:
            return
        try:
            save = getattr(self._telemetry_service, "save_visual_telemetry", None)
            if callable(save):
                save(event.trace_id, [event])
                return
            emit = getattr(self._telemetry_service, "emit", None)
            if callable(emit):
                emit(event)
        except Exception:
            return


def _finish_step(
    step: ExecutionStepRun,
    status: str,
    *,
    output: dict[str, Any] | None = None,
    error: dict[str, Any] | None = None,
    completed: bool = True,
) -> ExecutionStepRun:
    require_valid_step_transition("running", status)
    return step.model_copy(
        update={
            "status": status,
            "output": output or step.output,
            "error": error or step.error,
            "completed_at": datetime.now(UTC) if completed else None,
        }
    )


def _security_scope(request: ExecutionRequest) -> list[str]:
    value = request.metadata.get("security_scope")
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return value
    return ["workspace:main"]


def _metadata_str(request: ExecutionRequest, key: str) -> str | None:
    value = request.metadata.get(key)
    if value is None:
        return None
    return str(value)
