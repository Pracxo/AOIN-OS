"""Cognitive Cycle Orchestrator."""

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.contracts.approvals import ApprovalCreateRequest
from aion_brain.contracts.autonomy import AutonomyDecisionRequest
from aion_brain.contracts.cycles import (
    CognitiveCycleRun,
    CognitiveCycleRunRequest,
    CognitiveCycleStep,
    CognitiveCycleStepRun,
    CognitiveCycleTemplate,
    CycleStatus,
    SleepConsolidationRecord,
)
from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.risk import RiskAssessmentRequest
from aion_brain.contracts.telemetry import VisualTelemetryEvent
from aion_brain.cycles.repository import CognitiveCycleRepository, new_run_from_request
from aion_brain.cycles.state_machine import require_valid_cycle_step_transition
from aion_brain.cycles.templates import default_template_for_cycle
from aion_brain.policy.base import PolicyAdapter


class CognitiveCycleOrchestrator:
    """Coordinate manual, deterministic cognitive cycles."""

    def __init__(
        self,
        *,
        cycle_repository: CognitiveCycleRepository,
        autonomy_governor: object | None,
        risk_engine: object | None,
        approval_service: object | None,
        policy_adapter: PolicyAdapter,
        telemetry_service: object | None,
        sleep_consolidation_service: object | None,
        maintenance_service: object | None,
        settings: object,
    ) -> None:
        self._repository = cycle_repository
        self._autonomy_governor = autonomy_governor
        self._risk_engine = risk_engine
        self._approval_service = approval_service
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._sleep_consolidation_service = sleep_consolidation_service
        self._maintenance_service = maintenance_service
        self._settings = settings

    def create_template(self, template: CognitiveCycleTemplate) -> CognitiveCycleTemplate:
        """Create or update one cycle template."""
        self._authorize(
            "cycle.template.create",
            actor_id=template.created_by,
            workspace_id=None,
            scope=template.owner_scope,
            risk_level="low",
            context={"cycle_type": template.cycle_type},
        )
        saved = self._repository.save_template(template)
        self._emit(
            "cognitive_cycle_template_created",
            "cycle",
            saved.cycle_template_id,
            0.4,
            {"cycle_type": saved.cycle_type, "owner_scope": saved.owner_scope},
            None,
        )
        return saved

    def list_templates(
        self,
        cycle_type: str | None = None,
        status: str | None = None,
    ) -> list[CognitiveCycleTemplate]:
        """List cycle templates."""
        self._authorize(
            "cycle.template.read",
            actor_id=None,
            workspace_id=None,
            scope=["workspace:main"],
            risk_level="low",
            context={"cycle_type": cycle_type, "status": status},
        )
        return self._repository.list_templates(cycle_type=cycle_type, status=status)

    def disable_template(
        self,
        cycle_template_id: str,
        actor_id: str | None,
        reason: str,
    ) -> CognitiveCycleTemplate:
        """Disable one template."""
        template = self._repository.get_template(cycle_template_id)
        if template is None:
            raise ValueError("cycle_template_not_found")
        self._authorize(
            "cycle.template.disable",
            actor_id=actor_id,
            workspace_id=None,
            scope=template.owner_scope,
            risk_level="low",
            context={"reason": reason},
        )
        return self._repository.save_template(
            template.model_copy(
                update={
                    "status": "disabled",
                    "disabled_at": datetime.now(UTC),
                    "metadata": {**template.metadata, "disabled_reason": reason},
                }
            )
        )

    def run_cycle(self, request: CognitiveCycleRunRequest) -> CognitiveCycleRun:
        """Run one manual cognitive cycle."""
        now = datetime.now(UTC)
        run_id = request.cycle_run_id or f"cycle-run-{uuid4().hex}"
        run = new_run_from_request(request, run_id, now)
        if not bool(getattr(self._settings, "cognitive_cycles_enabled", True)):
            return self._save_run(
                run.model_copy(
                    update={
                        "status": "failed",
                        "error": {"reason": "cognitive_cycles_disabled"},
                        "completed_at": now,
                    }
                )
            )
        policy = self._policy_decision(
            "cycle.run",
            run,
            risk_level="low",
            context={"mode": request.mode, "cycle_type": request.cycle_type},
        )
        if not bool(getattr(policy, "allow", False)):
            return self._blocked_run(run, "policy_denied", getattr(policy, "reason", "denied"))

        autonomy = self._autonomy_decision(request)
        if autonomy is not None and not bool(getattr(autonomy, "allow", False)):
            return self._blocked_run(
                run.model_copy(
                    update={"autonomy_decision_id": getattr(autonomy, "autonomy_decision_id", None)}
                ),
                "autonomy_denied",
                str(getattr(autonomy, "reason", "autonomy_denied")),
            )

        risk = self._risk_assessment(request)
        risk_assessment_id = getattr(risk, "risk_assessment_id", None)
        if getattr(risk, "decision", "allow") == "block":
            return self._blocked_run(
                run.model_copy(update={"risk_assessment_id": risk_assessment_id}),
                "risk_blocked",
                "risk_engine_blocked",
            )
        if self._requires_approval(request, risk):
            approval_id = self._create_approval(request, run_id, risk_assessment_id)
            return self._save_run(
                run.model_copy(
                    update={
                        "status": "waiting_for_approval",
                        "risk_assessment_id": risk_assessment_id,
                        "approval_request_id": approval_id,
                        "updated_at": datetime.now(UTC),
                    }
                )
            )

        template = self._template_for_request(request)
        running = self._save_run(
            run.model_copy(
                update={
                    "cycle_template_id": template.cycle_template_id,
                    "status": "running",
                    "risk_assessment_id": risk_assessment_id,
                    "autonomy_decision_id": getattr(autonomy, "autonomy_decision_id", None),
                    "started_at": datetime.now(UTC),
                }
            )
        )
        self._emit(
            "cognitive_cycle_started",
            "cycle",
            running.cycle_run_id,
            0.5,
            {"cycle_type": running.cycle_type, "mode": running.mode},
            running.trace_id,
        )
        steps: list[CognitiveCycleStepRun] = []
        output: dict[str, Any] = {}
        required_failed = False
        for step in template.steps:
            if not step.enabled:
                continue
            step_run = self._run_step(step, running)
            steps.append(step_run)
            output[step.step_id] = {"status": step_run.status, **step_run.output}
            if step.required and step_run.status in {"failed", "blocked_by_policy"}:
                required_failed = True
                break

        sleep_record = None
        if not required_failed and running.cycle_type == "sleep_consolidation":
            sleep_record = self._run_sleep_consolidation(running)
            if sleep_record is not None:
                output["sleep_consolidation_id"] = sleep_record.consolidation_id

        final_status = "failed" if required_failed else "completed"
        final = self._save_run(
            running.model_copy(
                update={
                    "status": final_status,
                    "steps": steps,
                    "output": output,
                    "completed_at": datetime.now(UTC),
                }
            )
        )
        self._emit(
            "cognitive_cycle_failed" if final_status == "failed" else "cognitive_cycle_completed",
            "cycle",
            final.cycle_run_id,
            0.9 if final_status == "failed" else 1.0,
            {"cycle_type": final.cycle_type, "status": final.status},
            final.trace_id,
        )
        return final

    def get_run(self, cycle_run_id: str, scope: list[str]) -> CognitiveCycleRun | None:
        """Return one run visible to scope."""
        self._authorize(
            "cycle.read",
            actor_id=None,
            workspace_id=None,
            scope=scope,
            risk_level="low",
        )
        run = self._repository.get_run(cycle_run_id)
        if run is None or not _scope_matches(run.owner_scope, scope):
            return None
        return run

    def list_runs(
        self,
        scope: list[str],
        cycle_type: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[CognitiveCycleRun]:
        """List visible runs."""
        self._authorize(
            "cycle.read",
            actor_id=None,
            workspace_id=None,
            scope=scope,
            risk_level="low",
        )
        return self._repository.list_runs(
            scope=scope,
            cycle_type=cycle_type,
            status=status,
            limit=limit,
        )

    def status(self, cycle_type: str, scope: list[str]) -> CycleStatus:
        """Return status for one cycle type."""
        self._authorize(
            "cycle.status.read",
            actor_id=None,
            workspace_id=None,
            scope=scope,
            risk_level="low",
            context={"cycle_type": cycle_type},
        )
        runs = self._repository.list_runs(scope=scope, cycle_type=cycle_type, limit=500)
        return CycleStatus(
            cycle_type=cast(Any, cycle_type),
            latest_run=runs[0] if runs else None,
            active_run_count=sum(1 for run in runs if run.status == "running"),
            completed_run_count=sum(1 for run in runs if run.status == "completed"),
            failed_run_count=sum(1 for run in runs if run.status == "failed"),
            generated_at=datetime.now(UTC),
        )

    def get_sleep_record(
        self,
        cycle_run_id: str,
        scope: list[str],
    ) -> SleepConsolidationRecord | None:
        """Return sleep consolidation record for a run."""
        run = self.get_run(cycle_run_id, scope)
        if run is None:
            return None
        return self._repository.get_sleep_record(cycle_run_id)

    def _run_step(
        self,
        step: CognitiveCycleStep,
        run: CognitiveCycleRun,
    ) -> CognitiveCycleStepRun:
        now = datetime.now(UTC)
        step_run = CognitiveCycleStepRun(
            cycle_step_run_id=f"cycle-step-{uuid4().hex}",
            cycle_run_id=run.cycle_run_id,
            step_id=step.step_id,
            step_type=step.step_type,
            status="pending",
            input={**step.input_template, "cycle_input": run.input},
            output={},
            error={},
            created_at=now,
            updated_at=now,
        )
        require_valid_cycle_step_transition(step_run.status, "running")
        step_run = self._repository.save_step(
            step_run.model_copy(update={"status": "running", "started_at": now})
        )
        self._emit(
            "cognitive_cycle_step_started",
            "cycle_step",
            step_run.cycle_step_run_id,
            0.5,
            {"step_type": step.step_type, "cycle_run_id": run.cycle_run_id},
            run.trace_id,
        )
        policy = self._policy_decision(
            "cycle.step.run",
            run,
            risk_level=step.risk_level,
            context={"step_type": step.step_type, "step_id": step.step_id},
        )
        if not bool(getattr(policy, "allow", False)):
            return self._finish_step(
                step_run,
                "blocked_by_policy",
                {},
                {"reason": getattr(policy, "reason", "policy_denied")},
                run,
            )
        try:
            output = self._maintenance_output(step, run)
        except Exception as exc:
            return self._finish_step(step_run, "failed", {}, {"reason": str(exc)}, run)
        return self._finish_step(step_run, "completed", output, {}, run)

    def _finish_step(
        self,
        step_run: CognitiveCycleStepRun,
        status: str,
        output: dict[str, Any],
        error: dict[str, Any],
        run: CognitiveCycleRun,
    ) -> CognitiveCycleStepRun:
        require_valid_cycle_step_transition(step_run.status, status)
        saved = self._repository.save_step(
            step_run.model_copy(
                update={
                    "status": status,
                    "output": output,
                    "error": error,
                    "completed_at": datetime.now(UTC),
                }
            )
        )
        self._emit(
            "cognitive_cycle_step_completed",
            "cycle_step",
            saved.cycle_step_run_id,
            0.7,
            {"step_type": saved.step_type, "status": saved.status},
            run.trace_id,
        )
        return saved

    def _maintenance_output(
        self,
        step: CognitiveCycleStep,
        run: CognitiveCycleRun,
    ) -> dict[str, Any]:
        runner = getattr(self._maintenance_service, "run_step", None)
        if not callable(runner):
            if step.required:
                raise RuntimeError("maintenance_service_unavailable")
            return {"skipped": True, "reason": "maintenance_service_unavailable"}
        return cast(dict[str, Any], runner(step, run, run.mode == "dry_run"))

    def _run_sleep_consolidation(self, run: CognitiveCycleRun) -> Any | None:
        runner = getattr(self._sleep_consolidation_service, "run", None)
        if not callable(runner):
            return None
        return runner(run, run.mode == "dry_run")

    def _blocked_run(self, run: CognitiveCycleRun, reason: str, detail: str) -> CognitiveCycleRun:
        return self._save_run(
            run.model_copy(
                update={
                    "status": "blocked_by_policy",
                    "error": {"reason": reason, "detail": detail},
                    "completed_at": datetime.now(UTC),
                }
            )
        )

    def _save_run(self, run: CognitiveCycleRun) -> CognitiveCycleRun:
        return self._repository.save_run(run)

    def _template_for_request(self, request: CognitiveCycleRunRequest) -> CognitiveCycleTemplate:
        if request.cycle_template_id:
            template = self._repository.get_template(request.cycle_template_id)
            if template is None:
                raise ValueError("cycle_template_not_found")
            return template
        return default_template_for_cycle(request.cycle_type, request.owner_scope)

    def _requires_approval(self, request: CognitiveCycleRunRequest, risk: Any | None) -> bool:
        if request.approval_present:
            return False
        if request.mode == "controlled" and bool(
            getattr(self._settings, "cycle_controlled_mode_requires_approval", True)
        ):
            return True
        return getattr(risk, "decision", "allow") == "require_approval"

    def _create_approval(
        self,
        request: CognitiveCycleRunRequest,
        cycle_run_id: str,
        risk_assessment_id: str | None,
    ) -> str | None:
        create = getattr(self._approval_service, "create_request", None)
        if not callable(create):
            return None
        approval = create(
            ApprovalCreateRequest(
                trace_id=request.trace_id,
                actor_id=request.actor_id,
                workspace_id=request.workspace_id,
                requested_by=request.actor_id,
                action_type="cycle.run",
                resource_type="cognitive_cycle",
                resource_id=cycle_run_id,
                title="Cognitive cycle approval required",
                description=f"Approval required to run {request.cycle_type}.",
                risk_assessment_id=risk_assessment_id,
                approval_scope=request.owner_scope,
                payload={"cycle_type": request.cycle_type, "mode": request.mode},
            )
        )
        return getattr(approval, "approval_request_id", None)

    def _risk_assessment(self, request: CognitiveCycleRunRequest) -> Any | None:
        assess = getattr(self._risk_engine, "assess", None)
        if not callable(assess):
            return None
        return assess(
            RiskAssessmentRequest(
                trace_id=request.trace_id,
                actor_id=request.actor_id,
                workspace_id=request.workspace_id,
                action_type="cycle.run",
                resource_type="cognitive_cycle",
                resource_id=request.cycle_run_id,
                requested_risk_level="medium",
                payload=request.input,
                context={
                    "dry_run": request.mode == "dry_run",
                    "controlled_execution": request.mode == "controlled",
                    "approval_present": request.approval_present,
                    "security_scope": request.owner_scope,
                },
                metadata=request.metadata,
            )
        )

    def _autonomy_decision(self, request: CognitiveCycleRunRequest) -> Any | None:
        decide = getattr(self._autonomy_governor, "decide", None)
        if not callable(decide):
            return None
        return decide(
            AutonomyDecisionRequest(
                trace_id=request.trace_id,
                actor_id=request.actor_id,
                workspace_id=request.workspace_id,
                requested_mode="dry_run" if request.mode == "dry_run" else "supervised_controlled",
                action_type="cycle.run",
                resource_type="cognitive_cycle",
                resource_id=request.cycle_run_id,
                risk_level="medium",
                approval_present=request.approval_present,
                context={
                    "security_scope": request.owner_scope,
                    "controlled_execution": request.mode == "controlled",
                },
                metadata=request.metadata,
            )
        )

    def _policy_decision(
        self,
        action_type: str,
        run: CognitiveCycleRun,
        *,
        risk_level: str,
        context: dict[str, Any],
    ) -> Any:
        return self._policy_adapter.authorize(
            PolicyRequest(
                request_id=f"{action_type}-{uuid4().hex}",
                trace_id=run.trace_id,
                actor_id=run.actor_id,
                workspace_id=run.workspace_id,
                action_type=action_type,
                resource_type="cognitive_cycle",
                resource_id=run.cycle_run_id,
                risk_level=cast(Any, risk_level),
                approval_present=run.input.get("approval_present") is True,
                requested_permissions=[],
                security_scope=run.owner_scope,
                context=context,
            )
        )

    def _authorize(
        self,
        action_type: str,
        *,
        actor_id: str | None,
        workspace_id: str | None,
        scope: list[str],
        risk_level: str = "medium",
        context: dict[str, Any] | None = None,
    ) -> None:
        decision = self._policy_adapter.authorize(
            PolicyRequest(
                request_id=f"{action_type}-{uuid4().hex}",
                trace_id=None,
                actor_id=actor_id,
                workspace_id=workspace_id,
                action_type=action_type,
                resource_type="cognitive_cycle",
                resource_id=None,
                risk_level=cast(Any, risk_level),
                approval_present=True,
                requested_permissions=[],
                security_scope=scope,
                context=context or {},
            )
        )
        if not bool(getattr(decision, "allow", False)):
            raise PermissionError(getattr(decision, "reason", "policy_denied"))

    def _emit(
        self,
        event_type: str,
        node_type: str,
        node_id: str,
        intensity: float,
        payload: dict[str, Any],
        trace_id: str | None,
    ) -> None:
        if self._telemetry_service is None:
            return
        event = VisualTelemetryEvent(
            telemetry_id=f"telemetry-{node_id}-{event_type}",
            trace_id=trace_id or node_id,
            event_type=event_type,  # type: ignore[arg-type]
            node_type=node_type,  # type: ignore[arg-type]
            node_id=node_id,
            edge_from=None,
            edge_to=node_id,
            intensity=intensity,
            payload=payload,
            created_at=datetime.now(UTC),
        )
        try:
            emit = getattr(self._telemetry_service, "emit", None)
            if callable(emit):
                emit(event)
                return
            save = getattr(self._telemetry_service, "save_visual_telemetry", None)
            if callable(save):
                save(event.trace_id, [event])
        except Exception:
            return


def _scope_matches(owner_scope: list[str], scope: list[str]) -> bool:
    return bool(set(owner_scope).intersection(scope))
