"""Deterministic AION Attention Controller."""

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.attention.focus import FocusService
from aion_brain.attention.repository import AttentionRepository
from aion_brain.attention.scoring import score_attention_signal, score_working_memory_slot
from aion_brain.config import Settings
from aion_brain.contracts.attention import (
    AttentionDecision,
    AttentionDecisionRequest,
    AttentionDecisionType,
    AttentionSignal,
    AttentionSignalCreateRequest,
)
from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.telemetry import (
    VisualTelemetryEvent,
    VisualTelemetryEventType,
)
from aion_brain.contracts.working_memory import WorkingMemoryQuery, WorkingMemorySlot
from aion_brain.policy.base import PolicyAdapter
from aion_brain.working_memory.service import WorkingMemoryService

_INTERRUPT_SIGNAL_TYPES = {
    "approval_pending",
    "policy_block",
    "risk_alert",
    "execution_failed",
    "regression_drift",
    "replay_drift",
    "memory_conflict",
    "system_diagnostic",
}


class AttentionController:
    """Score competing signals and decide current focus."""

    def __init__(
        self,
        repository: AttentionRepository,
        policy_adapter: PolicyAdapter,
        *,
        working_memory_service: WorkingMemoryService | None = None,
        focus_service: FocusService | None = None,
        settings: Settings | None = None,
        telemetry_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._working_memory_service = working_memory_service
        self._focus_service = focus_service
        self._settings = settings
        self._telemetry_service = telemetry_service

    def create_signal(self, request: AttentionSignalCreateRequest) -> AttentionSignal:
        """Create one normalized attention signal."""
        self._authorize(
            action_type="attention.signal.create",
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            scope=request.owner_scope,
            resource_id=request.attention_signal_id,
            context={"signal_type": request.signal_type, "source_type": request.source_type},
        )
        signal = AttentionSignal(
            attention_signal_id=request.attention_signal_id or f"attention-{uuid4().hex}",
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            signal_type=request.signal_type,
            source_type=request.source_type,
            source_id=request.source_id,
            title=request.title,
            payload=request.payload,
            urgency=request.urgency,
            importance=request.importance,
            confidence=request.confidence,
            risk_level=request.risk_level,
            owner_scope=request.owner_scope,
            metadata=request.metadata,
            created_at=datetime.now(UTC),
            handled_at=None,
        )
        stored = self._repository.save_signal(signal)
        self._emit_attention(
            "attention_signal_created",
            stored.attention_signal_id,
            stored.trace_id,
            max(stored.urgency, stored.importance),
            {
                "signal_type": stored.signal_type,
                "source_type": stored.source_type,
                "owner_scope": stored.owner_scope,
            },
        )
        return stored

    def list_signals(
        self,
        scope: list[str],
        handled: bool | None = None,
        limit: int = 100,
    ) -> list[AttentionSignal]:
        """List attention signals."""
        self._authorize(
            action_type="attention.signal.read",
            trace_id=None,
            actor_id=None,
            workspace_id=None,
            scope=scope,
            resource_id=None,
            context={"operation": "list_signals"},
        )
        return self._repository.list_signals(scope=scope, handled=handled, limit=limit)

    def decide(self, request: AttentionDecisionRequest) -> AttentionDecision:
        """Choose the next deterministic attention decision."""
        self._authorize(
            action_type="attention.decide",
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            scope=request.scope,
            resource_id=request.focus_session_id,
            context={"intent_type": request.intent_type, "goal_present": bool(request.goal)},
        )
        now = datetime.now(UTC)
        focus = None
        if request.focus_session_id is not None and self._focus_service is not None:
            focus = self._focus_service.get_focus_session(request.focus_session_id, request.scope)
        elif self._focus_service is not None:
            focus = self._focus_service.get_active_focus(
                request.actor_id,
                request.workspace_id,
                request.scope,
            )

        signals = self._repository.list_signals(
            scope=request.scope,
            handled=False,
            limit=max(100, request.max_signals),
        )
        scored_signals = sorted(
            ((score_attention_signal(signal, now), signal) for signal in signals),
            key=lambda item: (-item[0], item[1].created_at or now, item[1].attention_signal_id),
        )
        selected_signals = [
            signal for score, signal in scored_signals[: request.max_signals] if score > 0
        ]

        slots = self._load_slots(request)
        scored_slots = sorted(
            ((score_working_memory_slot(slot, now), slot) for slot in slots),
            key=lambda item: (-item[0], item[1].created_at or now, item[1].slot_id),
        )
        selected_slots = [slot for score, slot in scored_slots[: request.max_slots] if score > 0]
        top_score = max(
            [0.0]
            + [score for score, _signal in scored_signals[:1]]
            + [score for score, _slot in scored_slots[:1]]
        )
        decision_type = _decision_type(
            top_score=top_score,
            selected_signals=selected_signals,
            selected_slots=selected_slots,
            goal=request.goal,
            active_focus_present=focus is not None,
            threshold=_interrupt_threshold(self._settings),
        )
        selected_ids = _collect_selected_ids(selected_slots, request)
        decision = AttentionDecision(
            attention_decision_id=f"attention-decision-{uuid4().hex}",
            trace_id=request.trace_id,
            focus_session_id=request.focus_session_id or getattr(focus, "focus_session_id", None),
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            decision_type=decision_type,
            selected_signal_ids=[signal.attention_signal_id for signal in selected_signals],
            selected_slot_ids=[slot.slot_id for slot in selected_slots],
            selected_memory_ids=selected_ids["memory"],
            selected_evidence_ids=selected_ids["evidence"],
            selected_skill_ids=selected_ids["skill"],
            selected_capability_ids=selected_ids["capability"],
            priority_score=top_score,
            reason=_reason(decision_type),
            constraints=[],
            metadata={
                **request.metadata,
                "intent_type": request.intent_type,
                "goal": request.goal,
                "active_focus_present": focus is not None,
            },
            created_at=datetime.now(UTC),
        )
        stored = self._repository.save_decision(decision)
        self._emit_attention(
            "attention_decision_made",
            stored.attention_decision_id,
            stored.trace_id,
            stored.priority_score,
            {
                "decision_type": stored.decision_type,
                "selected_signal_ids": stored.selected_signal_ids,
                "selected_slot_ids": stored.selected_slot_ids,
                "owner_scope": request.scope,
            },
        )
        return stored

    def mark_signal_handled(
        self,
        attention_signal_id: str,
        scope: list[str],
    ) -> AttentionSignal:
        """Mark one signal handled."""
        signal = self._repository.get_signal(attention_signal_id)
        if signal is None or not _scope_matches(signal.owner_scope, scope):
            raise ValueError("attention_signal_not_found")
        self._authorize(
            action_type="attention.signal.update",
            trace_id=signal.trace_id,
            actor_id=signal.actor_id,
            workspace_id=signal.workspace_id,
            scope=scope,
            resource_id=signal.attention_signal_id,
            context={"operation": "mark_handled"},
        )
        return self._repository.save_signal(
            signal.model_copy(update={"handled_at": datetime.now(UTC)})
        )

    def _load_slots(self, request: AttentionDecisionRequest) -> list[WorkingMemorySlot]:
        if self._working_memory_service is None:
            return []
        return self._working_memory_service.query_slots(
            WorkingMemoryQuery(
                focus_session_id=request.focus_session_id,
                scope=request.scope,
                limit=max(1, min(100, request.max_slots or 1)),
            )
        )

    def _authorize(
        self,
        *,
        action_type: str,
        trace_id: str | None,
        actor_id: str | None,
        workspace_id: str | None,
        scope: list[str],
        resource_id: str | None,
        context: dict[str, object],
    ) -> None:
        decision = self._policy_adapter.authorize(
            PolicyRequest(
                request_id=f"{action_type}-{resource_id or uuid4().hex}",
                trace_id=trace_id,
                actor_id=actor_id,
                workspace_id=workspace_id,
                action_type=action_type,
                resource_type="attention",
                resource_id=resource_id,
                risk_level="low",
                approval_present=False,
                requested_permissions=[],
                security_scope=scope,
                context=context,
            )
        )
        if not decision.allow:
            raise PermissionError(decision.reason)

    def _emit_attention(
        self,
        event_type: str,
        node_id: str,
        trace_id: str | None,
        intensity: float,
        payload: dict[str, object],
    ) -> None:
        if self._telemetry_service is None:
            return
        resolved_trace_id = trace_id or node_id
        event = VisualTelemetryEvent(
            telemetry_id=f"telemetry-{resolved_trace_id}-{event_type}-{node_id}",
            trace_id=resolved_trace_id,
            event_type=cast(VisualTelemetryEventType, event_type),
            node_type="attention",
            node_id=node_id,
            edge_from=None,
            edge_to=None,
            intensity=max(0.0, min(1.0, intensity)),
            payload=payload,
            created_at=datetime.now(UTC),
        )
        _emit(self._telemetry_service, event)


def _decision_type(
    *,
    top_score: float,
    selected_signals: list[AttentionSignal],
    selected_slots: list[WorkingMemorySlot],
    goal: str | None,
    active_focus_present: bool,
    threshold: float,
) -> AttentionDecisionType:
    if (
        selected_signals
        and top_score >= threshold
        and selected_signals[0].signal_type in _INTERRUPT_SIGNAL_TYPES
    ):
        return "interrupt"
    if not goal and not selected_signals and not selected_slots:
        return "clarify"
    if active_focus_present:
        return "continue"
    return "focus"


def _collect_selected_ids(
    slots: list[WorkingMemorySlot],
    request: AttentionDecisionRequest,
) -> dict[str, list[str]]:
    selected: dict[str, list[str]] = {"memory": [], "evidence": [], "skill": [], "capability": []}
    for slot in slots:
        payload = {**slot.content, **slot.metadata}
        if request.include_memory:
            _add_ids(selected["memory"], payload, "memory")
            if slot.source_type == "memory" and slot.source_id:
                _append_unique(selected["memory"], slot.source_id)
        if request.include_evidence:
            _add_ids(selected["evidence"], payload, "evidence")
            if slot.source_type == "evidence" and slot.source_id:
                _append_unique(selected["evidence"], slot.source_id)
        if request.include_skills:
            _add_ids(selected["skill"], payload, "skill")
            if slot.source_type == "skill" and slot.source_id:
                _append_unique(selected["skill"], slot.source_id)
        if request.include_capabilities:
            _add_ids(selected["capability"], payload, "capability")
    return selected


def _add_ids(target: list[str], payload: dict[str, Any], prefix: str) -> None:
    for key in (f"{prefix}_id", f"{prefix}_ids"):
        value = payload.get(key)
        if isinstance(value, str):
            _append_unique(target, value)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    _append_unique(target, item)


def _append_unique(target: list[str], value: str) -> None:
    if value and value not in target:
        target.append(value)


def _reason(decision_type: str) -> str:
    reasons = {
        "interrupt": "high_priority_signal_selected",
        "clarify": "insufficient_goal_or_context",
        "continue": "active_focus_continues",
        "focus": "attention_focus_selected",
        "defer": "attention_deferred",
        "block": "attention_blocked",
    }
    return reasons.get(decision_type, "attention_decision_made")


def _interrupt_threshold(settings: Settings | None) -> float:
    return float(getattr(settings, "interrupt_priority_threshold", 0.75))


def _scope_matches(owner_scope: list[str], requested_scope: list[str]) -> bool:
    return bool(set(owner_scope) & set(requested_scope))


def _emit(telemetry_service: object, event: VisualTelemetryEvent) -> None:
    try:
        emit = getattr(telemetry_service, "emit", None)
        if callable(emit):
            emit(event)
            return
        save = getattr(telemetry_service, "save_visual_telemetry", None)
        if callable(save):
            save(event.trace_id, [event])
    except Exception:
        return
