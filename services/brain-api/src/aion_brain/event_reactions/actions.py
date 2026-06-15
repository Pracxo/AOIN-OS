"""Safe action runner boundary for event reactions."""

from datetime import UTC, datetime
from typing import Any, Literal, cast
from uuid import uuid4

from pydantic import BaseModel

from aion_brain.contracts.attention import AttentionSignalCreateRequest, InterruptCreateRequest
from aion_brain.contracts.cycles import CognitiveCycleRunRequest, CycleMode, CycleType
from aion_brain.contracts.event_reactions import (
    EventReactionAction,
    EventReactionActionStatus,
    EventSubscription,
)
from aion_brain.contracts.events import AIONEvent
from aion_brain.contracts.modules import CapabilityInvocationRequest, InvocationMode
from aion_brain.contracts.outbox import OutboxPublishRequest
from aion_brain.contracts.tasks import TaskCreateRequest
from aion_brain.contracts.workflows import WorkflowRunMode, WorkflowRunRequest

ActionRunResultStatus = Literal[
    "completed",
    "skipped",
    "blocked_by_policy",
    "blocked_by_autonomy",
    "waiting_for_approval",
    "failed",
]


class EventReactionActionRunner:
    """Translate approved event reaction actions into existing Brain service calls."""

    def __init__(
        self,
        *,
        attention_controller: object | None = None,
        interrupt_router: object | None = None,
        task_service: object | None = None,
        workflow_service: object | None = None,
        cognitive_cycle_orchestrator: object | None = None,
        memory_governance_engine: object | None = None,
        memory_conflict_service: object | None = None,
        capability_runtime_gateway: object | None = None,
        trace_service: object | None = None,
        outbox_service: object | None = None,
    ) -> None:
        self._attention_controller = attention_controller
        self._interrupt_router = interrupt_router
        self._task_service = task_service
        self._workflow_service = workflow_service
        self._cognitive_cycle_orchestrator = cognitive_cycle_orchestrator
        self._memory_governance_engine = memory_governance_engine
        self._memory_conflict_service = memory_conflict_service
        self._capability_runtime_gateway = capability_runtime_gateway
        self._trace_service = trace_service
        self._outbox_service = outbox_service

    def set_outbox_service(self, outbox_service: object | None) -> None:
        """Attach the transactional outbox boundary after kernel assembly."""
        self._outbox_service = outbox_service

    def run(
        self,
        *,
        action: EventReactionAction,
        event: AIONEvent,
        subscription: EventSubscription,
    ) -> EventReactionAction:
        """Run one approved controlled reaction action."""
        try:
            status, output = self._run(action, event, subscription)
            updated = action.model_copy(
                update={
                    "status": cast(EventReactionActionStatus, status),
                    "output": output,
                    "completed_at": datetime.now(UTC),
                }
            )
            self._enqueue_lifecycle(updated, event, subscription)
            return updated
        except Exception as exc:
            updated = action.model_copy(
                update={
                    "status": "failed",
                    "error": {"reason": type(exc).__name__, "message": str(exc)},
                    "completed_at": datetime.now(UTC),
                }
            )
            self._enqueue_lifecycle(updated, event, subscription)
            return updated

    def dry_run(
        self,
        *,
        action: EventReactionAction,
        event: AIONEvent,
        subscription: EventSubscription,
    ) -> EventReactionAction:
        """Return a non-mutating projection of an action."""
        updated = action.model_copy(
            update={
                "status": "dry_run",
                "output": {
                    "dry_run": True,
                    "target_type": subscription.target_type,
                    "target_id": subscription.target_id,
                    "event_id": event.event_id,
                    "planned_action_type": action.action_type,
                },
                "completed_at": datetime.now(UTC),
            }
        )
        self._enqueue_lifecycle(updated, event, subscription)
        return updated

    def _run(
        self,
        action: EventReactionAction,
        event: AIONEvent,
        subscription: EventSubscription,
    ) -> tuple[ActionRunResultStatus, dict[str, Any]]:
        if subscription.target_type == "attention_signal":
            return self._create_attention_signal(event, subscription)
        if subscription.target_type == "interrupt":
            return self._create_interrupt(event, subscription)
        if subscription.target_type == "task":
            return self._create_task(event, subscription)
        if subscription.target_type == "workflow":
            return self._run_workflow(action, event, subscription)
        if subscription.target_type == "cognitive_cycle":
            return self._run_cycle(action, event, subscription)
        if subscription.target_type == "memory_governance":
            return self._evaluate_memory_governance(event, subscription)
        if subscription.target_type == "capability":
            return self._invoke_capability(action, event, subscription)
        if subscription.target_type == "trace":
            return self._attach_trace_event(event)
        if subscription.target_type == "noop":
            return "completed", {"noop": True, "event_id": event.event_id}
        return "blocked_by_policy", {"reason": "unknown_target_type"}

    def _enqueue_lifecycle(
        self,
        action: EventReactionAction,
        event: AIONEvent,
        subscription: EventSubscription,
    ) -> None:
        enqueue = getattr(self._outbox_service, "enqueue", None)
        if not callable(enqueue):
            return
        try:
            enqueue(
                OutboxPublishRequest(
                    message_type="event.reaction.lifecycle",
                    destination="internal",
                    subject="aion.event_reactions.lifecycle",
                    payload={
                        "reaction_action_id": action.reaction_action_id,
                        "dispatch_id": action.dispatch_id,
                        "event_id": event.event_id,
                        "subscription_id": subscription.subscription_id,
                        "status": action.status,
                    },
                    headers={"source": "event_reaction_router"},
                    trace_id=event.trace_id,
                    correlation_id=event.correlation_id,
                )
            )
        except Exception:
            return

    def _create_attention_signal(
        self,
        event: AIONEvent,
        subscription: EventSubscription,
    ) -> tuple[ActionRunResultStatus, dict[str, Any]]:
        create_signal = getattr(self._attention_controller, "create_signal", None)
        if not callable(create_signal):
            return "skipped", {"reason": "attention_controller_unavailable"}
        signal = create_signal(
            AttentionSignalCreateRequest(
                trace_id=event.trace_id,
                actor_id=event.actor_id,
                workspace_id=event.workspace_id,
                signal_type="event_received",
                source_type="event_reaction",
                source_id=event.event_id,
                title=f"Event reaction for {event.event_type}",
                payload={"event_id": event.event_id, "event_type": event.event_type},
                urgency=0.5,
                importance=0.5,
                confidence=0.8,
                risk_level=subscription.risk_level,
                owner_scope=subscription.owner_scope,
                metadata={"subscription_id": subscription.subscription_id},
            )
        )
        return "completed", {"attention_signal": _serialize(signal)}

    def _create_interrupt(
        self,
        event: AIONEvent,
        subscription: EventSubscription,
    ) -> tuple[ActionRunResultStatus, dict[str, Any]]:
        create_interrupt = getattr(self._interrupt_router, "create_interrupt", None)
        if not callable(create_interrupt):
            return "skipped", {"reason": "interrupt_router_unavailable"}
        interrupt = create_interrupt(
            InterruptCreateRequest(
                trace_id=event.trace_id,
                actor_id=event.actor_id,
                workspace_id=event.workspace_id,
                interrupt_type="generic",
                source_type="event_reaction",
                source_id=event.event_id,
                payload={
                    "event_id": event.event_id,
                    "event_type": event.event_type,
                    "subscription_id": subscription.subscription_id,
                },
                owner_scope=subscription.owner_scope,
                metadata={"target_id": subscription.target_id},
            )
        )
        return "completed", {"interrupt": _serialize(interrupt)}

    def _create_task(
        self,
        event: AIONEvent,
        subscription: EventSubscription,
    ) -> tuple[ActionRunResultStatus, dict[str, Any]]:
        create_task = getattr(self._task_service, "create_task", None)
        if not callable(create_task):
            return "skipped", {"reason": "task_service_unavailable"}
        task = create_task(
            TaskCreateRequest(
                trace_id=event.trace_id,
                actor_id=event.actor_id,
                workspace_id=event.workspace_id,
                title=f"Reaction task for {event.event_type}",
                description="Generic event reaction task created by the router.",
                task_type="generic",
                priority="normal",
                risk_level=subscription.risk_level,
                owner_scope=subscription.owner_scope,
                input={
                    "event_id": event.event_id,
                    "subscription_id": subscription.subscription_id,
                    "target_id": subscription.target_id,
                },
                constraints=subscription.constraints,
                metadata={"created_by": "event_reaction_router"},
            )
        )
        return "completed", {"task": _serialize(task), "ran": False}

    def _run_workflow(
        self,
        action: EventReactionAction,
        event: AIONEvent,
        subscription: EventSubscription,
    ) -> tuple[ActionRunResultStatus, dict[str, Any]]:
        if subscription.target_id is None:
            return "skipped", {"reason": "workflow_target_id_missing"}
        run_workflow = getattr(self._workflow_service, "run_workflow", None)
        if not callable(run_workflow):
            return "skipped", {"reason": "workflow_service_unavailable"}
        requested_mode = _execution_mode(
            action.mode,
            subscription.metadata,
            "allow_controlled_workflow",
        )
        run = run_workflow(
            WorkflowRunRequest(
                workflow_id=subscription.target_id,
                trace_id=event.trace_id,
                actor_id=event.actor_id,
                workspace_id=event.workspace_id,
                mode=cast(WorkflowRunMode, requested_mode),
                input={"event_id": event.event_id, "subscription_id": subscription.subscription_id},
                approval_present=bool(action.input.get("approval_present")),
                metadata={"source": "event_reaction_router"},
            )
        )
        return "completed", {"workflow_run": _serialize(run), "mode": requested_mode}

    def _run_cycle(
        self,
        action: EventReactionAction,
        event: AIONEvent,
        subscription: EventSubscription,
    ) -> tuple[ActionRunResultStatus, dict[str, Any]]:
        run_cycle = getattr(self._cognitive_cycle_orchestrator, "run_cycle", None)
        if not callable(run_cycle):
            return "skipped", {"reason": "cognitive_cycle_orchestrator_unavailable"}
        requested_mode = _execution_mode(
            action.mode,
            subscription.metadata,
            "allow_controlled_cycle",
        )
        cycle_type = str(subscription.metadata.get("cycle_type", "active"))
        cycle = run_cycle(
            CognitiveCycleRunRequest(
                trace_id=event.trace_id,
                actor_id=event.actor_id,
                workspace_id=event.workspace_id,
                cycle_type=cast(CycleType, cycle_type),
                mode=cast(CycleMode, requested_mode),
                owner_scope=subscription.owner_scope,
                input={"event_id": event.event_id, "subscription_id": subscription.subscription_id},
                approval_present=bool(action.input.get("approval_present")),
                metadata={"source": "event_reaction_router"},
            )
        )
        return "completed", {"cycle_run": _serialize(cycle), "mode": requested_mode}

    def _evaluate_memory_governance(
        self,
        event: AIONEvent,
        subscription: EventSubscription,
    ) -> tuple[ActionRunResultStatus, dict[str, Any]]:
        react = getattr(self._memory_governance_engine, "react_to_event", None)
        if callable(react):
            result = react(event, subscription)
            return "completed", {"memory_governance": _serialize(result)}
        scan = getattr(self._memory_conflict_service, "scan", None)
        if callable(scan):
            result = scan(subscription.owner_scope)
            return "completed", {"memory_conflict_scan": _serialize(result)}
        return "skipped", {"reason": "memory_governance_service_unavailable"}

    def _invoke_capability(
        self,
        action: EventReactionAction,
        event: AIONEvent,
        subscription: EventSubscription,
    ) -> tuple[ActionRunResultStatus, dict[str, Any]]:
        if subscription.target_id is None:
            return "skipped", {"reason": "capability_target_id_missing"}
        invoke = getattr(self._capability_runtime_gateway, "invoke", None)
        if not callable(invoke):
            return "skipped", {"reason": "capability_runtime_gateway_unavailable"}
        requested_mode = _execution_mode(
            action.mode,
            subscription.metadata,
            "allow_controlled_capability",
        )
        result = invoke(
            CapabilityInvocationRequest(
                invocation_id=f"event-reaction-invocation-{uuid4().hex}",
                trace_id=event.trace_id,
                capability_id=subscription.target_id,
                actor_id=event.actor_id,
                workspace_id=event.workspace_id,
                mode=cast(InvocationMode, requested_mode),
                payload={
                    "event_id": event.event_id,
                    "event_type": event.event_type,
                    "payload": event.payload,
                },
                approval_present=bool(action.input.get("approval_present")),
                metadata={"source": "event_reaction_router"},
            )
        )
        return "completed", {"capability_invocation": _serialize(result), "mode": requested_mode}

    def _attach_trace_event(self, event: AIONEvent) -> tuple[ActionRunResultStatus, dict[str, Any]]:
        attach = getattr(self._trace_service, "attach_event_ref", None)
        if not callable(attach):
            return "skipped", {"reason": "trace_attachment_unsupported"}
        result = attach(event.trace_id, event.event_id)
        return "completed", {"trace": _serialize(result)}


def action_type_for_target(target_type: str) -> str:
    """Return a generic action type for one reaction target."""
    return {
        "attention_signal": "attention.signal.create",
        "interrupt": "interrupt.create",
        "task": "task.create",
        "workflow": "workflow.run",
        "cognitive_cycle": "cycle.run",
        "memory_governance": "memory.governance.evaluate",
        "capability": "capability.invoke",
        "trace": "trace.read",
        "noop": "event.reaction.noop",
    }.get(target_type, "event.reaction.unknown")


def _execution_mode(
    requested_mode: str,
    metadata: dict[str, Any],
    controlled_flag: str,
) -> str:
    if requested_mode == "controlled" and metadata.get(controlled_flag) is True:
        return "controlled"
    return "dry_run"


def _serialize(value: object) -> dict[str, Any]:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return cast(dict[str, Any], value)
    if value is None:
        return {}
    return {"value": str(value)}
