"""Trace timeline projection."""

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.scopes import ActorContext
from aion_brain.contracts.visual import (
    BrainVisualStatus,
    TraceTimeline,
    TraceTimelineEvent,
    TraceTimelineRequest,
)
from aion_brain.policy.base import PolicyAdapter
from aion_brain.policy.enrichment import PolicyInputEnricher
from aion_brain.visual.intensity import status_from_event_type
from aion_brain.visual.repository import VisualRepository
from aion_brain.visual.service import VisualPolicyDenied


class TraceTimelineBuilder:
    """Build ordered trace timelines from available local artifacts."""

    def __init__(
        self,
        trace_repository: object,
        visual_repository: VisualRepository,
        policy_adapter: PolicyAdapter,
        actor_context: ActorContext | None = None,
    ) -> None:
        self._trace_repository = trace_repository
        self._visual_repository = visual_repository
        self._policy_adapter = policy_adapter
        self._actor_context = actor_context or ActorContext()

    def with_actor_context(self, actor_context: ActorContext) -> "TraceTimelineBuilder":
        """Return a request-scoped builder."""
        return TraceTimelineBuilder(
            self._trace_repository,
            self._visual_repository,
            self._policy_adapter,
            actor_context,
        )

    def build(self, request: TraceTimelineRequest) -> TraceTimeline:
        """Build and persist a policy-authorized trace timeline."""
        self._authorize(request)
        events: list[TraceTimelineEvent] = []
        trace = _call_optional(self._trace_repository, "get_trace", request.trace_id)
        trace_time = trace.created_at if trace is not None else datetime.now(UTC)
        if trace is not None:
            events.append(
                TraceTimelineEvent(
                    event_id=f"timeline-trace-{request.trace_id}",
                    trace_id=request.trace_id,
                    event_type="trace_created",
                    component="trace",
                    title="Decision trace",
                    timestamp=trace.created_at,
                    status=cast(BrainVisualStatus, _status_from_outcome(trace.outcome)),
                    payload={"source": "decision_trace", "outcome": _safe_payload(trace.outcome)},
                )
            )
        if request.include_telemetry:
            telemetry = (
                _call_optional(
                    self._trace_repository,
                    "list_visual_telemetry",
                    request.trace_id,
                )
                or []
            )
            for item in telemetry:
                if not _include_telemetry(item.node_type, request):
                    continue
                events.append(
                    TraceTimelineEvent(
                        event_id=item.telemetry_id,
                        trace_id=item.trace_id,
                        event_type=item.event_type,
                        component=item.node_type,
                        title=item.event_type.replace("_", " "),
                        timestamp=item.created_at,
                        status=status_from_event_type(item.event_type),
                        payload={"source": "visual_telemetry", **_safe_payload(item.payload)},
                    )
                )
        if request.include_policy:
            decisions = (
                _call_optional(
                    self._trace_repository,
                    "list_policy_decisions",
                    request.trace_id,
                )
                or []
            )
            for decision in decisions:
                events.append(
                    TraceTimelineEvent(
                        event_id=decision.decision_id,
                        trace_id=request.trace_id,
                        event_type="policy_checked" if decision.allow else "policy_blocked",
                        component="policy",
                        title="Policy decision",
                        timestamp=trace_time,
                        status="completed" if decision.allow else "blocked",
                        payload={
                            "source": "policy_decision",
                            "allow": decision.allow,
                            "reason": decision.reason,
                        },
                    )
                )
        if trace is not None and request.include_reasoning:
            events.extend(
                _reference_events(
                    request.trace_id,
                    trace.reasoning_refs,
                    "reasoning",
                    "reasoning_completed",
                    trace_time,
                )
            )
        if trace is not None and request.include_execution:
            events.extend(
                _reference_events(
                    request.trace_id,
                    trace.execution_refs,
                    "execution",
                    "execution_completed",
                    trace_time,
                )
            )
        if request.include_evaluation:
            evaluation = _call_optional(self._trace_repository, "get_evaluation", request.trace_id)
            if evaluation is not None:
                events.append(
                    TraceTimelineEvent(
                        event_id=evaluation.evaluation_id,
                        trace_id=request.trace_id,
                        event_type="evaluation_completed",
                        component="evaluation",
                        title="Evaluation completed",
                        timestamp=evaluation.created_at,
                        status="completed",
                        payload={"source": "evaluation", "scores": evaluation.scores},
                    )
                )
        if request.include_learning:
            learning = (
                _call_optional(
                    self._trace_repository,
                    "list_learning_signals",
                    request.trace_id,
                )
                or []
            )
            for signal in learning:
                events.append(
                    TraceTimelineEvent(
                        event_id=signal.learning_id,
                        trace_id=request.trace_id,
                        event_type="learning_signal_created",
                        component="learning",
                        title="Learning signal created",
                        timestamp=signal.created_at,
                        status="completed",
                        payload={"source": "learning", "learning_type": signal.learning_type},
                    )
                )
        events.sort(key=lambda item: item.timestamp)
        duration_ms = None
        if len(events) >= 2:
            elapsed = (events[-1].timestamp - events[0].timestamp).total_seconds()
            duration_ms = max(0, int(elapsed * 1000))
        timeline = TraceTimeline(
            timeline_id=f"timeline-{uuid4().hex}",
            trace_id=request.trace_id,
            owner_scope=request.scope,
            events=events,
            duration_ms=duration_ms,
            status=cast(BrainVisualStatus, _timeline_status(events)),
            created_at=datetime.now(UTC),
        )
        return self._visual_repository.save_timeline(timeline)

    def _authorize(self, request: TraceTimelineRequest) -> None:
        policy_request = PolicyRequest(
            request_id=f"request-{uuid4().hex}",
            trace_id=request.trace_id,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            action_type="trace.read",
            resource_type="trace_timeline",
            resource_id=request.trace_id,
            risk_level="low",
            approval_present=False,
            requested_permissions=[],
            security_scope=request.scope,
            context={},
        )
        decision = self._policy_adapter.authorize(
            PolicyInputEnricher().enrich(policy_request, self._actor_context)
        )
        if not decision.allow:
            raise VisualPolicyDenied(decision)


def _call_optional(target: object, method: str, *args: object) -> Any:
    callable_method = getattr(target, method, None)
    if callable(callable_method):
        try:
            return callable_method(*args)
        except Exception:
            return None
    return None


def _safe_payload(payload: dict[str, Any]) -> dict[str, Any]:
    blocked = {"password", "secret", "token", "api_key", "private_key", "authorization"}
    return {
        str(key): value
        for key, value in payload.items()
        if not any(term in str(key).lower().replace("-", "_") for term in blocked)
    }


def _status_from_outcome(outcome: dict[str, Any]) -> str:
    status = str(outcome.get("status", "unknown"))
    if "block" in status:
        return "blocked"
    if "fail" in status or "error" in status:
        return "failed"
    if status in {"planned", "completed"}:
        return "completed"
    return "unknown"


def _timeline_status(events: list[TraceTimelineEvent]) -> str:
    if any(event.status == "failed" for event in events):
        return "failed"
    if any(event.status == "blocked" for event in events):
        return "blocked"
    return "completed" if events else "unknown"


def _include_telemetry(node_type: str, request: TraceTimelineRequest) -> bool:
    if node_type in {"policy", "risk", "guardrail"}:
        return request.include_policy
    if node_type in {"reasoning", "model"}:
        return request.include_reasoning
    if node_type in {"execution", "step", "approval", "capability", "module", "runtime"}:
        return request.include_execution
    if node_type == "evaluation":
        return request.include_evaluation
    if node_type in {"learning", "reflection", "candidate", "skill"}:
        return request.include_learning
    return True


def _reference_events(
    trace_id: str,
    refs: list[str],
    component: str,
    event_type: str,
    timestamp: datetime,
) -> list[TraceTimelineEvent]:
    return [
        TraceTimelineEvent(
            event_id=f"timeline-reference-{reference}",
            trace_id=trace_id,
            event_type=event_type,
            component=component,
            title=f"{component.title()} reference",
            timestamp=timestamp,
            status="completed",
            payload={"source": "decision_trace_reference", "reference_id": reference},
        )
        for reference in refs
    ]
