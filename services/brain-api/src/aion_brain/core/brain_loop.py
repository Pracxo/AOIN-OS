"""Deterministic implementation of the AION Brain loop."""

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.attention.controller import AttentionController
from aion_brain.attention.focus import FocusService
from aion_brain.audit.ledger import AuditLedger
from aion_brain.context.compiler import ContextCompiler, EmptyCapabilityCatalog
from aion_brain.contracts.attention import (
    AttentionRiskLevel,
    AttentionSignalCreateRequest,
    AttentionSignalType,
    FocusSessionCreateRequest,
)
from aion_brain.contracts.autonomy import AutonomyDecision, AutonomyDecisionRequest
from aion_brain.contracts.evaluation import EvaluationRecord
from aion_brain.contracts.events import AIONEvent
from aion_brain.contracts.goals import (
    GoalCreateRequest,
    LifecyclePriority,
    LifecycleRiskLevel,
)
from aion_brain.contracts.learning import LearningSignal
from aion_brain.contracts.observability import ObservabilityEvent, ObservabilityLevel
from aion_brain.contracts.policy import PolicyDecision
from aion_brain.contracts.reflection import ReflectionRequest
from aion_brain.contracts.state import BrainState
from aion_brain.contracts.tasks import TaskCreateRequest, TaskType
from aion_brain.contracts.telemetry import VisualTelemetryEvent
from aion_brain.contracts.traces import DecisionTrace
from aion_brain.contracts.working_memory import WorkingMemoryWriteRequest
from aion_brain.evaluation.evaluator import Evaluator
from aion_brain.goals.service import GoalService
from aion_brain.intent.engine import IntentEngine
from aion_brain.learning.engine import LearningEngine
from aion_brain.observability.base import ObservabilityAdapter
from aion_brain.planning.planner import Planner
from aion_brain.policy.base import PolicyAdapter
from aion_brain.reflection.engine import ReflectionEngine
from aion_brain.runtime.langgraph_runtime import LangGraphRuntimeAdapter
from aion_brain.skills.service import SkillService
from aion_brain.tasks.service import TaskService
from aion_brain.telemetry.visual import VisualTelemetryBuilder
from aion_brain.working_memory.service import WorkingMemoryService


def run_brain_loop(event: AIONEvent, policy_adapter: PolicyAdapter) -> DecisionTrace:
    """Run the deterministic Brain runtime through the configured adapter."""
    runtime = LangGraphRuntimeAdapter(
        intent_engine=IntentEngine(),
        context_compiler=ContextCompiler(
            policy_adapter=policy_adapter,
            capability_catalog=EmptyCapabilityCatalog(),
        ),
        planner=Planner(),
        policy_adapter=policy_adapter,
    )
    return runtime.run(event)


class BrainLoopService:
    """Completes the deterministic Brain loop and records its artifacts."""

    def __init__(
        self,
        *,
        runtime: LangGraphRuntimeAdapter,
        audit_ledger: AuditLedger,
        evaluator: Evaluator,
        learning_engine: LearningEngine,
        telemetry_builder: VisualTelemetryBuilder,
        goal_service: GoalService | None = None,
        task_service: TaskService | None = None,
        reflection_engine: ReflectionEngine | None = None,
        skill_service: SkillService | None = None,
        observability_adapter: ObservabilityAdapter | None = None,
        focus_service: FocusService | None = None,
        attention_controller: AttentionController | None = None,
        working_memory_service: WorkingMemoryService | None = None,
        autonomy_governor: object | None = None,
    ) -> None:
        self._runtime = runtime
        self._audit_ledger = audit_ledger
        self._evaluator = evaluator
        self._learning_engine = learning_engine
        self._telemetry_builder = telemetry_builder
        self._goal_service = goal_service
        self._task_service = task_service
        self._reflection_engine = reflection_engine
        self._skill_service = skill_service
        self._observability_adapter = observability_adapter
        self._focus_service = focus_service
        self._attention_controller = attention_controller
        self._working_memory_service = working_memory_service
        self._autonomy_governor = autonomy_governor

    def think(self, event: AIONEvent, *, replay_mode: bool = False) -> DecisionTrace:
        """Run, evaluate, learn, emit telemetry, persist, and return the trace."""
        state = self.run_full_loop(event, replay_mode=replay_mode)
        if state.trace is None:
            raise RuntimeError("Brain runtime returned no trace")
        return state.trace

    def run_full_loop(self, event: AIONEvent, *, replay_mode: bool = False) -> BrainState:
        """Run the full deterministic loop and persist every AION-009 artifact."""
        self._observe(event, "brain_loop_started", "brain_loop", "Brain loop started.")
        focus_session_id = self._prepare_focus(event)
        self._create_attention_signal(event, focus_session_id)
        autonomy = self._autonomy_decision(event)
        if autonomy is not None and (
            not autonomy.allow or autonomy.resolved_mode in {"disabled", "observe"}
        ):
            trace = _autonomy_trace(event, autonomy)
            if autonomy.resolved_mode == "observe" and autonomy.allow:
                trace = trace.model_copy(
                    update={
                        "outcome": {
                            **trace.outcome,
                            "status": "observed",
                            "message": (
                                "AION Brain observed the event without reasoning or planning."
                            ),
                        }
                    }
                )
            evaluation = self._evaluator.evaluate(trace)
            learning_signal = self._learning_engine.create_signal(
                trace=trace,
                evaluation=evaluation,
            )
            self._persist(
                trace=trace,
                policy_decisions=[],
                evaluation=evaluation,
                learning_signal=learning_signal,
                telemetry_events=[],
            )
            return BrainState(
                event=event,
                intent=None,
                context=None,
                plan=None,
                policy_decisions=[],
                trace=trace,
                errors=[],
                status=str(trace.outcome.get("status", "blocked_by_autonomy")),
            )
        self._write_working_memory(
            event,
            focus_session_id=focus_session_id,
            slot_type="recent_event",
            source_type="event",
            source_id=event.event_id,
            summary=f"Event received: {event.event_type}",
            priority=0.55,
            content={"event_id": event.event_id, "event_type": event.event_type},
        )
        try:
            state = self._runtime.run_state(event)
        except Exception:
            self._observe(
                event,
                "brain_loop_failed",
                "brain_loop",
                "Brain loop failed.",
                level="error",
            )
            raise
        if state.trace is None:
            return state

        trace = (
            state.trace.model_copy(
                update={
                    "outcome": {
                        **state.trace.outcome,
                        "replay": True,
                        "side_effects": "disabled",
                    }
                }
            )
            if replay_mode
            else self._attach_lifecycle_metadata(event, state.trace)
        )
        trace = self._attach_attention_metadata(trace, state, focus_session_id)
        if autonomy is not None:
            trace = _attach_autonomy_metadata(trace, autonomy)
        state = state.model_copy(update={"trace": trace})
        if state.intent is not None:
            self._observe(event, "intent_classified", "intent", "Intent classified.", trace)
            self._write_working_memory(
                event,
                focus_session_id=focus_session_id,
                slot_type="reasoning_note",
                source_type="reasoning",
                source_id=state.intent.intent_id,
                summary=f"Intent classified: {state.intent.intent_type}",
                priority=0.55,
                content={
                    "intent_id": state.intent.intent_id,
                    "intent_type": state.intent.intent_type,
                    "risk_level": state.intent.risk_level,
                },
            )
        if state.context is not None:
            self._observe(event, "context_compiled", "context", "Context compiled.", trace)
            self._write_working_memory(
                event,
                focus_session_id=focus_session_id,
                slot_type="retrieved_context",
                source_type="retrieval",
                source_id=state.context.context_id,
                summary=f"Context compiled for goal: {state.context.goal}",
                priority=0.60,
                content={
                    "context_id": state.context.context_id,
                    "memory_ids": state.context.retrieved_memory_ids,
                    "capability_ids": state.context.available_capability_ids,
                },
            )
        if trace.reasoning_refs:
            self._observe(event, "reasoning_completed", "reasoning", "Reasoning completed.", trace)
            self._write_working_memory(
                event,
                focus_session_id=focus_session_id,
                slot_type="reasoning_note",
                source_type="reasoning",
                source_id=trace.reasoning_refs[0],
                summary="Reasoning completed for deterministic Brain loop.",
                priority=0.50,
                content={"reasoning_id": trace.reasoning_refs[0]},
            )
        if state.plan is not None:
            self._observe(event, "plan_created", "planning", "Plan created.", trace)
            self._write_working_memory(
                event,
                focus_session_id=focus_session_id,
                slot_type="plan_note",
                source_type="plan",
                source_id=state.plan.plan_id,
                summary=f"Plan created with {len(state.plan.steps)} steps.",
                priority=0.65,
                content={"plan_id": state.plan.plan_id, "step_count": len(state.plan.steps)},
            )
        self._observe(
            event,
            "policy_checked",
            "policy",
            "Policy checks completed.",
            trace,
            level=(
                "warning"
                if any(not decision.allow for decision in state.policy_decisions)
                else "info"
            ),
        )
        if any(not decision.allow for decision in state.policy_decisions):
            self._write_working_memory(
                event,
                focus_session_id=focus_session_id,
                slot_type="approval_note",
                source_type="policy",
                source_id=trace.trace_id,
                summary="Policy blocked part of the Brain loop.",
                priority=0.85,
                content={"trace_id": trace.trace_id, "status": "blocked_by_policy"},
            )
        self._observe(event, "trace_created", "trace", "Decision trace created.", trace)
        evaluation = self._evaluator.evaluate(trace)
        self._observe(event, "evaluation_completed", "evaluation", "Evaluation completed.", trace)
        learning_signal = self._learning_engine.create_signal(
            trace=trace,
            evaluation=evaluation,
        )
        self._observe(
            event,
            "learning_signal_created",
            "learning",
            "Learning signal created.",
            trace,
        )
        if not replay_mode:
            trace = self._attach_reflection_metadata(
                event=event,
                trace=trace,
                evaluation=evaluation,
                learning_signal=learning_signal,
            )
        state = state.model_copy(update={"trace": trace})
        telemetry_events = self._telemetry_builder.build(
            trace=trace,
            policy_decisions=state.policy_decisions,
            evaluation=evaluation,
            learning_signal=learning_signal,
        )

        self._persist(
            trace=trace,
            policy_decisions=state.policy_decisions,
            evaluation=evaluation,
            learning_signal=learning_signal,
            telemetry_events=telemetry_events,
        )
        self._observe(event, "brain_loop_completed", "brain_loop", "Brain loop completed.", trace)
        return state

    def _autonomy_decision(self, event: AIONEvent) -> AutonomyDecision | None:
        decide = getattr(self._autonomy_governor, "decide", None)
        if not callable(decide):
            return None
        requested_mode = _optional_payload_str(
            event.payload,
            "requested_mode",
        ) or _optional_payload_str(
            event.payload,
            "autonomy_mode",
        )
        try:
            decision = decide(
                AutonomyDecisionRequest(
                    trace_id=event.trace_id,
                    actor_id=event.actor_id,
                    workspace_id=event.workspace_id,
                    requested_mode=cast(Any, requested_mode or "assist"),
                    action_type="brain.think",
                    resource_type="brain_loop",
                    resource_id=event.event_id,
                    risk_level="low",
                    approval_present=bool(event.payload.get("approval_present", False)),
                    delegation_id=_optional_payload_str(event.payload, "delegation_id"),
                    context={"security_scope": event.security_scope or ["workspace:main"]},
                    metadata={"event_id": event.event_id},
                )
            )
        except Exception:
            return None
        return decision if isinstance(decision, AutonomyDecision) else None

    def _prepare_focus(self, event: AIONEvent) -> str | None:
        payload_focus_id = _optional_payload_str(event.payload, "focus_session_id")
        if payload_focus_id:
            return payload_focus_id
        if event.payload.get("create_focus") is not True or self._focus_service is None:
            return None
        try:
            session = self._focus_service.create_focus_session(
                FocusSessionCreateRequest(
                    focus_session_id=None,
                    trace_id=event.trace_id,
                    actor_id=event.actor_id,
                    workspace_id=event.workspace_id,
                    focus_type="general",
                    active_goal_id=_optional_payload_str(event.payload, "goal_id"),
                    active_task_id=_optional_payload_str(event.payload, "task_id"),
                    active_workflow_run_id=_optional_payload_str(
                        event.payload,
                        "workflow_run_id",
                    ),
                    active_trace_id=event.trace_id,
                    owner_scope=event.security_scope or ["workspace:main"],
                    title=_lifecycle_title(event),
                    description=_lifecycle_description(event),
                    constraints=[],
                    metadata={"source_event_id": event.event_id},
                )
            )
            return session.focus_session_id
        except Exception:
            return None

    def _create_attention_signal(
        self,
        event: AIONEvent,
        focus_session_id: str | None,
    ) -> None:
        if self._attention_controller is None:
            return
        signal_type = _signal_type_from_event(event.event_type)
        try:
            self._attention_controller.create_signal(
                AttentionSignalCreateRequest(
                    attention_signal_id=None,
                    trace_id=event.trace_id,
                    actor_id=event.actor_id,
                    workspace_id=event.workspace_id,
                    signal_type=signal_type,
                    source_type="event",
                    source_id=event.event_id,
                    title=f"Event received: {event.event_type}",
                    payload={
                        "event_id": event.event_id,
                        "event_type": event.event_type,
                        "focus_session_id": focus_session_id,
                    },
                    urgency=_urgency_for_event(event.event_type),
                    importance=_importance_for_event(event.event_type),
                    confidence=0.8,
                    risk_level=_attention_risk_for_event(event.event_type),
                    owner_scope=event.security_scope or ["workspace:main"],
                    metadata={"payload_type": event.payload_type},
                )
            )
        except Exception:
            return

    def _write_working_memory(
        self,
        event: AIONEvent,
        *,
        focus_session_id: str | None,
        slot_type: str,
        source_type: str,
        source_id: str | None,
        summary: str,
        priority: float,
        content: dict[str, object],
    ) -> None:
        if self._working_memory_service is None:
            return
        try:
            self._working_memory_service.write_slot(
                WorkingMemoryWriteRequest(
                    slot_id=None,
                    focus_session_id=focus_session_id,
                    trace_id=event.trace_id,
                    actor_id=event.actor_id,
                    workspace_id=event.workspace_id,
                    slot_type=cast(Any, slot_type),
                    source_type=cast(Any, source_type),
                    source_id=source_id,
                    content=content,
                    summary=summary,
                    priority=priority,
                    confidence=0.8,
                    ttl_seconds=None,
                    pinned=False,
                    owner_scope=event.security_scope or ["workspace:main"],
                    metadata={"source_event_id": event.event_id},
                )
            )
        except Exception:
            return

    def _attach_attention_metadata(
        self,
        trace: DecisionTrace,
        state: BrainState,
        focus_session_id: str | None,
    ) -> DecisionTrace:
        attention_context = _attention_context_from_state(state)
        outcome = dict(trace.outcome)
        if focus_session_id:
            outcome["focus_session_id"] = focus_session_id
        outcome.update(attention_context)
        return trace.model_copy(update={"outcome": outcome})

    def _observe(
        self,
        event: AIONEvent,
        event_type: str,
        component: str,
        message: str,
        trace: DecisionTrace | None = None,
        *,
        level: str = "info",
    ) -> None:
        if self._observability_adapter is None:
            return
        try:
            self._observability_adapter.record_event(
                ObservabilityEvent(
                    observability_event_id=f"observability-{uuid4().hex}",
                    trace_id=(trace.trace_id if trace else event.trace_id),
                    correlation_id=event.correlation_id,
                    event_type=event_type,
                    component=component,
                    level=cast(ObservabilityLevel, level),
                    message=message,
                    payload={
                        "event_id": event.event_id,
                        "workspace_id": event.workspace_id,
                        "status": trace.outcome.get("status") if trace else "started",
                    },
                    created_at=None,
                )
            )
        except Exception:
            return

    def _attach_lifecycle_metadata(
        self,
        event: AIONEvent,
        trace: DecisionTrace,
    ) -> DecisionTrace:
        outcome = {
            **trace.outcome,
            "actor_id": event.actor_id,
            "workspace_id": event.workspace_id,
            "security_scope": event.security_scope,
            "permission_context_present": bool(event.actor_id or event.security_scope),
            "can_create_goal": True,
            "can_create_task": True,
            "goal_endpoint": "/brain/goals",
            "task_endpoint": "/brain/tasks",
        }
        payload = event.payload
        if payload.get("create_goal") is True and self._goal_service is not None:
            try:
                goal = self._goal_service.create_goal(
                    GoalCreateRequest(
                        goal_id=_optional_payload_str(payload, "goal_id"),
                        trace_id=trace.trace_id,
                        actor_id=event.actor_id,
                        workspace_id=event.workspace_id,
                        title=_lifecycle_title(event),
                        description=_lifecycle_description(event),
                        priority=_priority(payload),
                        risk_level=_risk_level(payload),
                        owner_scope=event.security_scope or ["workspace:main"],
                        constraints=[],
                        success_criteria=[],
                        metadata={"source_event_id": event.event_id},
                    )
                )
                outcome["goal_id"] = goal.goal_id
            except Exception as exc:
                outcome["goal_error"] = str(exc)
        if payload.get("create_task") is True and self._task_service is not None:
            try:
                task = self._task_service.create_task(
                    TaskCreateRequest(
                        task_id=_optional_payload_str(payload, "task_id"),
                        goal_id=_optional_payload_str(payload, "goal_id")
                        or _optional_outcome_str(outcome, "goal_id"),
                        trace_id=trace.trace_id,
                        plan_id=trace.plan_id,
                        execution_id=None,
                        actor_id=event.actor_id,
                        workspace_id=event.workspace_id,
                        title=_lifecycle_title(event),
                        description=_lifecycle_description(event),
                        task_type=_task_type(payload),
                        priority=_priority(payload),
                        risk_level=_risk_level(payload),
                        owner_scope=event.security_scope or ["workspace:main"],
                        input={"event_id": event.event_id, "plan_id": trace.plan_id},
                        constraints=[],
                        metadata={"source_event_id": event.event_id},
                    )
                )
                outcome["task_id"] = task.task_id
            except Exception as exc:
                outcome["task_error"] = str(exc)
        return trace.model_copy(update={"outcome": outcome})

    def _attach_reflection_metadata(
        self,
        *,
        event: AIONEvent,
        trace: DecisionTrace,
        evaluation: EvaluationRecord,
        learning_signal: LearningSignal,
    ) -> DecisionTrace:
        outcome = dict(trace.outcome)
        if event.payload.get("reflect") is not True or self._reflection_engine is None:
            return trace
        try:
            reflection = self._reflection_engine.reflect(
                ReflectionRequest(
                    event=event,
                    trace=trace,
                    evaluation=evaluation,
                    learning_signals=[learning_signal],
                    reflection_type="trace_review",
                    metadata={"source_event_id": event.event_id},
                )
            )
            outcome["reflection_id"] = reflection.reflection_id
        except Exception as exc:
            outcome["reflection_error"] = str(exc)
            return trace.model_copy(update={"outcome": outcome})
        if event.payload.get("create_skill_candidate") is True and self._skill_service is not None:
            try:
                candidate = self._skill_service.create_candidate_from_reflection(
                    reflection.reflection_id
                )
                if candidate is not None:
                    outcome["candidate_id"] = candidate.candidate_id
            except Exception as exc:
                outcome["candidate_error"] = str(exc)
        return trace.model_copy(update={"outcome": outcome})

    def _persist(
        self,
        *,
        trace: DecisionTrace,
        policy_decisions: list[PolicyDecision],
        evaluation: EvaluationRecord,
        learning_signal: LearningSignal,
        telemetry_events: list[VisualTelemetryEvent],
    ) -> None:
        self._audit_ledger.record(trace)
        self._audit_ledger.record_policy_decisions(trace.trace_id, policy_decisions)
        self._audit_ledger.record_evaluation(evaluation)
        self._audit_ledger.record_learning_signal(learning_signal)
        self._audit_ledger.record_visual_telemetry(trace.trace_id, telemetry_events)


def _optional_payload_str(payload: dict[str, object], key: str) -> str | None:
    value = payload.get(key)
    if isinstance(value, str) and value:
        return value
    return None


def _optional_outcome_str(outcome: dict[str, object], key: str) -> str | None:
    value = outcome.get(key)
    if isinstance(value, str) and value:
        return value
    return None


def _lifecycle_title(event: AIONEvent) -> str:
    for key in ("goal", "title", "question"):
        value = event.payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return event.event_type


def _lifecycle_description(event: AIONEvent) -> str:
    value = event.payload.get("description")
    if isinstance(value, str) and value.strip():
        return value.strip()
    return f"Lifecycle record created from event {event.event_id}."


def _priority(payload: dict[str, object]) -> LifecyclePriority:
    value = payload.get("priority")
    if value in {"low", "normal", "high", "urgent"}:
        return cast(LifecyclePriority, value)
    return "normal"


def _risk_level(payload: dict[str, object]) -> LifecycleRiskLevel:
    value = payload.get("risk_level")
    if value in {"low", "medium", "high", "critical"}:
        return cast(LifecycleRiskLevel, value)
    return "medium"


def _task_type(payload: dict[str, object]) -> TaskType:
    value = payload.get("task_type")
    if value in {
        "brain.think",
        "brain.plan",
        "brain.execute",
        "brain.retrieve",
        "brain.evaluate",
        "brain.learn",
        "capability.invoke",
        "generic",
    }:
        return cast(TaskType, value)
    return "generic"


def _signal_type_from_event(event_type: str) -> AttentionSignalType:
    if event_type in {
        "policy_block",
        "execution_failed",
        "workflow_failed",
        "approval_pending",
        "regression_drift",
        "memory_conflict",
    }:
        mapping: dict[str, AttentionSignalType] = {
            "policy_block": "policy_block",
            "execution_failed": "execution_failed",
            "workflow_failed": "execution_failed",
            "approval_pending": "approval_pending",
            "regression_drift": "regression_drift",
            "memory_conflict": "memory_conflict",
        }
        return mapping[event_type]
    return "event_received"


def _urgency_for_event(event_type: str) -> float:
    if event_type in {"execution_failed", "workflow_failed", "policy_block"}:
        return 0.85
    if event_type in {"approval_pending", "regression_drift", "memory_conflict"}:
        return 0.75
    return 0.45


def _importance_for_event(event_type: str) -> float:
    if event_type in {
        "policy_block",
        "execution_failed",
        "workflow_failed",
        "approval_pending",
        "regression_drift",
        "memory_conflict",
    }:
        return 0.80
    return 0.50


def _attention_risk_for_event(event_type: str) -> AttentionRiskLevel:
    if event_type in {"execution_failed", "workflow_failed", "policy_block"}:
        return "high"
    if event_type in {"approval_pending", "regression_drift", "memory_conflict"}:
        return "medium"
    return "low"


def _attention_context_from_state(state: BrainState) -> dict[str, object]:
    context = state.context
    if context is None:
        return {}
    for item in context.known_context:
        if item.get("source") == "attention_decision":
            result: dict[str, object] = {}
            decision_id = item.get("attention_decision_id")
            focus_session_id = item.get("focus_session_id")
            if isinstance(decision_id, str):
                result["attention_decision_id"] = decision_id
            if isinstance(focus_session_id, str):
                result["focus_session_id"] = focus_session_id
            selected_slots = item.get("selected_slot_ids")
            if isinstance(selected_slots, list):
                result["selected_working_memory_slot_ids"] = [
                    str(slot_id) for slot_id in selected_slots
                ]
            return result
    return {}


def _autonomy_trace(event: AIONEvent, decision: AutonomyDecision) -> DecisionTrace:
    status = "blocked_by_autonomy" if not decision.allow else "observed"
    return DecisionTrace(
        trace_id=event.trace_id or f"trace-{uuid4().hex}",
        event_id=event.event_id,
        intent_id=None,
        context_id=None,
        plan_id=None,
        memory_refs=[],
        capability_refs=[],
        reasoning_refs=[],
        execution_refs=[],
        policy_decisions=[],
        outcome={
            "status": status,
            "runtime": "autonomy-governor",
            "message": "AION Brain autonomy governor stopped the full loop.",
            "autonomy_decision_id": decision.autonomy_decision_id,
            "effective_mode": decision.resolved_mode,
            "reason": decision.reason,
        },
        created_at=datetime.now(UTC),
    )


def _attach_autonomy_metadata(trace: DecisionTrace, decision: AutonomyDecision) -> DecisionTrace:
    return trace.model_copy(
        update={
            "outcome": {
                **trace.outcome,
                "autonomy_decision_id": decision.autonomy_decision_id,
                "effective_mode": decision.resolved_mode,
            }
        }
    )
