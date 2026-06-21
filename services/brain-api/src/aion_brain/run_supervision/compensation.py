"""Compensation planning service."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.action_proposals import ActionProposalCreateRequest
from aion_brain.contracts.compensation import (
    CompensationPlan,
    CompensationPlanCreateRequest,
    CompensationPlanType,
    CompensationStep,
)
from aion_brain.contracts.run_supervision import RunSupervisionRecord
from aion_brain.contracts.scopes import ActorContext
from aion_brain.dialogue._shared import authorize, emit_telemetry


class CompensationPlanner:
    """Create metadata-only compensation plans."""

    def __init__(
        self,
        repository: object,
        policy_adapter: object | None,
        *,
        action_proposal_service: object | None = None,
        telemetry_service: object | None = None,
        audit_sink: object | None = None,
        provenance_service: object | None = None,
        settings: object | None = None,
        actor_context: ActorContext | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._action_proposal_service = action_proposal_service
        self._telemetry_service = telemetry_service
        self._audit_sink = audit_sink
        self._provenance_service = provenance_service
        self._settings = settings
        self._actor_context = actor_context or ActorContext()

    def with_actor_context(self, actor_context: ActorContext) -> CompensationPlanner:
        return CompensationPlanner(
            self._repository,
            self._policy_adapter,
            action_proposal_service=self._action_proposal_service,
            telemetry_service=self._telemetry_service,
            audit_sink=self._audit_sink,
            provenance_service=self._provenance_service,
            settings=self._settings,
            actor_context=actor_context,
        )

    def create_plan(self, request: CompensationPlanCreateRequest) -> CompensationPlan:
        if self._settings is not None and not bool(
            getattr(self._settings, "run_compensation_planning_enabled", True)
        ):
            raise RuntimeError("run_compensation_planning_disabled")
        authorize(
            self._policy_adapter,
            action_type="run_supervision.compensation.create",
            resource_type="compensation_plan",
            resource_id=request.compensation_plan_id,
            scope=request.owner_scope,
            trace_id=request.trace_id or self._actor_context.trace_id,
            actor_id=request.created_by or self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level=request.risk_level,
        )
        now = datetime.now(UTC)
        plan_id = request.compensation_plan_id or f"compensation-plan-{uuid4().hex}"
        plan = CompensationPlan(
            compensation_plan_id=plan_id,
            trace_id=request.trace_id or self._actor_context.trace_id,
            run_supervision_id=request.run_supervision_id,
            source_type=request.source_type,
            source_id=request.source_id,
            status="proposed",
            plan_type=request.plan_type,
            title=request.title,
            description=request.description,
            owner_scope=request.owner_scope,
            trigger_reason=request.trigger_reason,
            target_refs=request.target_refs,
            steps=_default_steps(plan_id, request.plan_type, request.risk_level),
            risk_level=request.risk_level,
            executable=False,
            execution_allowed=False,
            metadata={**request.metadata, "compensation_plans_do_not_execute": True},
            created_by=request.created_by or self._actor_context.actor_id,
            created_at=now,
        )
        stored = _save_plan(self._repository, plan)
        _record(
            self._audit_sink,
            {"event_type": "compensation_plan_created", "id": stored.compensation_plan_id},
        )
        _link(
            self._provenance_service,
            stored.source_id,
            stored.compensation_plan_id,
            "compensates_with_plan",
        )
        emit_telemetry(
            self._telemetry_service,
            event_type="compensation_plan_created",
            node_type="compensation_plan",
            node_id=stored.compensation_plan_id,
            intensity=0.7,
            trace_id=stored.trace_id,
            payload={"plan_type": stored.plan_type, "status": stored.status},
        )
        return stored

    def propose_for_run(
        self, run_supervision_id: str, trigger_reason: str, created_by: str | None = None
    ) -> CompensationPlan:
        run = _require_run(self._repository, run_supervision_id)
        plan_type = _plan_type_for_run(run)
        request = CompensationPlanCreateRequest(
            trace_id=run.trace_id,
            run_supervision_id=run.run_supervision_id,
            source_type="run_supervision",
            source_id=run.run_supervision_id,
            plan_type=plan_type,
            title=f"Compensation plan for {run.title}",
            description="Metadata-only compensation plan for a supervised run.",
            owner_scope=run.owner_scope,
            trigger_reason=trigger_reason,
            target_refs=[run.target_run_id] if run.target_run_id else [],
            risk_level="medium" if run.current_status != "failed" else "high",
            metadata={
                "target_system": run.target_system,
                "current_status": run.current_status,
                "auto_execution": False,
            },
            created_by=created_by or self._actor_context.actor_id,
        )
        plan = self.create_plan(request)
        plan = plan.model_copy(update={"steps": _steps_for_run(plan, run)})
        return _save_plan(self._repository, plan)

    def get_plan(self, compensation_plan_id: str, scope: list[str]) -> CompensationPlan | None:
        authorize(
            self._policy_adapter,
            action_type="run_supervision.compensation.read",
            resource_type="compensation_plan",
            resource_id=compensation_plan_id,
            scope=scope,
            risk_level="low",
        )
        get = getattr(self._repository, "get_compensation_plan", None)
        plan = get(compensation_plan_id) if callable(get) else None
        if not isinstance(plan, CompensationPlan):
            return None
        return plan if _scope_matches(plan.owner_scope, scope) else None

    def list_plans(
        self,
        scope: list[str],
        status: str | None = None,
        run_supervision_id: str | None = None,
        limit: int = 100,
    ) -> list[CompensationPlan]:
        authorize(
            self._policy_adapter,
            action_type="run_supervision.compensation.read",
            resource_type="compensation_plan",
            resource_id=run_supervision_id,
            scope=scope,
            risk_level="low",
        )
        list_plans = getattr(self._repository, "list_compensation_plans", None)
        if not callable(list_plans):
            return []
        result = list_plans(
            scope=scope,
            status=status,
            run_supervision_id=run_supervision_id,
            limit=limit,
        )
        return [item for item in result if isinstance(item, CompensationPlan)]

    def approve_plan(
        self,
        compensation_plan_id: str,
        actor_id: str | None,
        approval_present: bool,
        reason: str,
    ) -> CompensationPlan:
        plan = _require_plan(self._repository, compensation_plan_id)
        authorize(
            self._policy_adapter,
            action_type="run_supervision.compensation.update",
            resource_type="compensation_plan",
            resource_id=compensation_plan_id,
            scope=plan.owner_scope,
            actor_id=actor_id or self._actor_context.actor_id,
            risk_level=plan.risk_level,
            approval_present=approval_present,
            context={"reason": reason},
        )
        update = {
            "status": "approved",
            "approved_at": datetime.now(UTC),
            "metadata": {
                **plan.metadata,
                "approval_reason": reason,
                "steps_executed": False,
            },
        }
        approved = _save_plan(self._repository, plan.model_copy(update=update))
        emit_telemetry(
            self._telemetry_service,
            event_type="compensation_plan_approved",
            node_type="compensation_plan",
            node_id=approved.compensation_plan_id,
            intensity=0.8,
            trace_id=approved.trace_id,
            payload={"steps_executed": False},
        )
        return approved

    def convert_steps_to_action_proposals(
        self,
        compensation_plan_id: str,
        actor_id: str | None,
        approval_present: bool,
        reason: str,
    ) -> CompensationPlan:
        plan = _require_plan(self._repository, compensation_plan_id)
        authorize(
            self._policy_adapter,
            action_type="run_supervision.compensation.convert",
            resource_type="compensation_plan",
            resource_id=compensation_plan_id,
            scope=plan.owner_scope,
            actor_id=actor_id or self._actor_context.actor_id,
            risk_level=plan.risk_level,
            approval_present=approval_present,
            context={"reason": reason},
        )
        if plan.risk_level in {"high", "critical"} and not approval_present:
            raise PermissionError("approval_required")
        converted_steps: list[CompensationStep] = []
        action_refs: list[str] = []
        for step in plan.steps:
            if step.proposed_action_type is None:
                converted_steps.append(step)
                continue
            action_id = self._create_action_proposal(plan, step, actor_id, reason)
            action_refs.append(action_id)
            converted_steps.append(
                step.model_copy(update={"status": "converted", "action_proposal_id": action_id})
            )
        converted = plan.model_copy(
            update={
                "status": "converted_to_action_proposals",
                "steps": converted_steps,
                "metadata": {
                    **plan.metadata,
                    "conversion_reason": reason,
                    "action_proposal_refs": action_refs,
                    "direct_execution": False,
                },
            }
        )
        stored = _save_plan(self._repository, converted)
        emit_telemetry(
            self._telemetry_service,
            event_type="compensation_steps_converted",
            node_type="compensation_plan",
            node_id=stored.compensation_plan_id,
            intensity=0.8,
            trace_id=stored.trace_id,
            payload={"action_proposal_count": len(action_refs), "direct_execution": False},
        )
        return stored

    def _create_action_proposal(
        self,
        plan: CompensationPlan,
        step: CompensationStep,
        actor_id: str | None,
        reason: str,
    ) -> str:
        create = getattr(self._action_proposal_service, "create_proposal", None)
        if not callable(create):
            return f"action-proposal-placeholder-{step.compensation_step_id}"
        proposal = create(
            ActionProposalCreateRequest(
                source_type="generic",
                source_id=step.compensation_step_id,
                proposal_type="generic",
                title=step.title,
                description=step.description,
                action_type=step.proposed_action_type or "generic",
                target_type=step.proposed_target_system or "noop",
                target_id=None,
                owner_scope=plan.owner_scope,
                proposed_payload={
                    **step.proposed_payload,
                    "reason": reason,
                    "compensation_plan_id": plan.compensation_plan_id,
                },
                required_permissions=[],
                required_approvals=["approval"] if step.requires_approval else [],
                risk_level=step.risk_level,
                metadata={"created_from_compensation_plan": True, "direct_execution": False},
                created_by=actor_id or self._actor_context.actor_id,
            )
        )
        return str(getattr(proposal, "action_proposal_id", step.compensation_step_id))


def _default_steps(plan_id: str, plan_type: str, risk_level: str) -> list[CompensationStep]:
    if plan_type == "manual_review":
        return [
            _step(
                plan_id,
                1,
                "inspect",
                "Manual review",
                "Inspect the supervised run before choosing follow-up action.",
                risk_level,
            )
        ]
    return [
        _step(plan_id, 1, "inspect", "Inspect run state", "Inspect target run state.", risk_level),
        _step(
            plan_id,
            2,
            "verify_outcome",
            "Verify outcome",
            "Check whether a separate outcome record already exists.",
            risk_level,
        ),
    ]


def _steps_for_run(plan: CompensationPlan, run: RunSupervisionRecord) -> list[CompensationStep]:
    if run.target_system == "command_bus" and run.current_status == "failed":
        return [
            _step(
                plan.compensation_plan_id,
                1,
                "inspect",
                "Inspect failed command",
                "Inspect the command result and error metadata.",
                "medium",
            ),
            _step(
                plan.compensation_plan_id,
                2,
                "verify_outcome",
                "Verify command outcome",
                "Verify whether the command produced a valid outcome record.",
                "medium",
            ),
            _step(
                plan.compensation_plan_id,
                3,
                "create_action_proposal",
                "Optional retry proposal",
                "Create a separate action proposal for any retry decision.",
                "high",
                proposed_action_type="generic.retry",
                proposed_target_system="command_bus",
                proposed_payload={"target_run_id": run.target_run_id},
                requires_approval=True,
            ),
        ]
    if run.stalled or run.status == "stalled":
        return [
            _step(
                plan.compensation_plan_id,
                1,
                "inspect",
                "Request current status",
                "Create a status request before any other follow-up.",
                "medium",
            ),
            _step(
                plan.compensation_plan_id,
                2,
                "notify_operator",
                "Notify operator",
                "Surface the stalled supervised run for operator review.",
                "medium",
            ),
        ]
    return _default_steps(plan.compensation_plan_id, "manual_review", "medium")


def _step(
    plan_id: str,
    order: int,
    step_type: str,
    title: str,
    description: str,
    risk_level: str,
    *,
    proposed_action_type: str | None = None,
    proposed_target_system: str | None = None,
    proposed_payload: dict[str, object] | None = None,
    requires_approval: bool = False,
) -> CompensationStep:
    return CompensationStep(
        compensation_step_id=f"compensation-step-{uuid4().hex}",
        compensation_plan_id=plan_id,
        step_order=order,
        step_type=step_type,  # type: ignore[arg-type]
        status="proposed",
        title=title,
        description=description,
        proposed_action_type=proposed_action_type,
        proposed_target_system=proposed_target_system,
        proposed_payload=dict(proposed_payload or {}),
        expected_effects=[],
        risk_level=risk_level,  # type: ignore[arg-type]
        requires_approval=requires_approval,
        metadata={"does_not_execute": True},
        created_at=datetime.now(UTC),
    )


def _plan_type_for_run(run: RunSupervisionRecord) -> CompensationPlanType:
    if run.current_status == "failed":
        return "retry"
    if run.stalled or run.status in {"stalled", "timed_out"}:
        return "manual_review"
    return "manual_review"


def _require_run(repository: object, run_supervision_id: str) -> RunSupervisionRecord:
    get = getattr(repository, "get_run", None)
    run = get(run_supervision_id) if callable(get) else None
    if not isinstance(run, RunSupervisionRecord):
        raise ValueError("run_supervision_not_found")
    return run


def _require_plan(repository: object, compensation_plan_id: str) -> CompensationPlan:
    get = getattr(repository, "get_compensation_plan", None)
    plan = get(compensation_plan_id) if callable(get) else None
    if not isinstance(plan, CompensationPlan):
        raise ValueError("compensation_plan_not_found")
    return plan


def _save_plan(repository: object, plan: CompensationPlan) -> CompensationPlan:
    save = getattr(repository, "save_compensation_plan", None)
    stored = save(plan) if callable(save) else plan
    return stored if isinstance(stored, CompensationPlan) else plan


def _scope_matches(owner_scope: list[str], scope: list[str]) -> bool:
    return bool(set(owner_scope).intersection(scope))


def _record(audit_sink: object | None, payload: dict[str, object]) -> None:
    record = getattr(audit_sink, "record_event", None)
    if callable(record):
        try:
            record(payload)
        except Exception:
            return


def _link(
    provenance_service: object | None, source_id: str, target_id: str, relation_type: str
) -> None:
    link = getattr(provenance_service, "record_link", None)
    if callable(link):
        try:
            link(source_id, target_id, relation_type)
        except Exception:
            return


__all__ = ["CompensationPlanner"]
