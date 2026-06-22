"""Policy-gated, deterministic, side-effect-free cognitive replay."""

from datetime import UTC, datetime
from typing import Any, Protocol
from uuid import uuid4

from aion_brain.contracts.events import AIONEvent
from aion_brain.contracts.observability import ObservabilityEvent
from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.replay import (
    BrainSnapshot,
    ReplayRequest,
    ReplayRun,
    SnapshotCreateRequest,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.contracts.traces import DecisionTrace
from aion_brain.policy.base import PolicyAdapter
from aion_brain.policy.enrichment import PolicyInputEnricher
from aion_brain.replay.comparator import TraceComparator
from aion_brain.replay.snapshot import ReplayPolicyDenied, SnapshotService, _emit


class ReplayRunRepository(Protocol):
    """Replay run persistence boundary."""

    def save_replay(self, replay: ReplayRun) -> ReplayRun: ...

    def get_replay(self, replay_id: str) -> ReplayRun | None: ...


class BrainLoop(Protocol):
    """Minimal deterministic Brain loop boundary used by replay."""

    def think(self, event: AIONEvent, *, replay_mode: bool = False) -> DecisionTrace: ...


class ReplayService:
    """Replay completed traces locally without external side effects."""

    def __init__(
        self,
        replay_repository: ReplayRunRepository,
        snapshot_service: SnapshotService,
        trace_repository: object,
        event_repository: object,
        brain_loop: BrainLoop,
        comparator: TraceComparator,
        policy_adapter: PolicyAdapter,
        telemetry_service: object | None = None,
        observability_service: object | None = None,
        actor_context: ActorContext | None = None,
    ) -> None:
        self._repository = replay_repository
        self._snapshot_service = snapshot_service
        self._trace_repository = trace_repository
        self._event_repository = event_repository
        self._brain_loop = brain_loop
        self._comparator = comparator
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._observability_service = observability_service
        self._actor_context = actor_context or ActorContext()

    def with_actor_context(self, actor_context: ActorContext) -> "ReplayService":
        """Return a request-scoped replay service."""
        return ReplayService(
            self._repository,
            self._snapshot_service.with_actor_context(actor_context),
            self._trace_repository,
            self._event_repository,
            self._brain_loop,
            self._comparator,
            self._policy_adapter,
            self._telemetry_service,
            self._observability_service,
            actor_context,
        )

    def replay(self, request: ReplayRequest) -> ReplayRun:
        """Run one deterministic, local, side-effect-free replay."""
        replay_id = request.replay_id or f"replay-{uuid4().hex}"
        created_by = request.actor_id or self._actor_context.actor_id
        if not self._allowed(request, replay_id):
            return self._repository.save_replay(
                ReplayRun(
                    replay_id=replay_id,
                    source_trace_id=request.source_trace_id,
                    replay_trace_id=None,
                    mode=request.mode,
                    status="blocked_by_policy",
                    input_snapshot_id=None,
                    output_snapshot_id=None,
                    comparison={"reason": "blocked_by_policy"},
                    drift_detected=False,
                    created_by=created_by,
                    created_at=datetime.now(UTC),
                    completed_at=datetime.now(UTC),
                )
            )

        _emit(
            self._telemetry_service,
            "replay_started",
            "replay",
            replay_id,
            request.source_trace_id,
            request.owner_scope,
            0.5,
        )
        self._observe("replay_started", replay_id, request.source_trace_id)
        try:
            source_snapshot = self._snapshot_service.create_trace_snapshot(
                request.source_trace_id,
                "full_trace",
                request.owner_scope,
                created_by,
            )
            event = self._source_event(request.source_trace_id)
            if event is None:
                return self._failed(
                    request,
                    replay_id,
                    created_by,
                    source_snapshot,
                    "source_event_missing",
                )

            replay_event = _replay_event(event, replay_id, request)
            trace = self._brain_loop.think(replay_event, replay_mode=True)
            output_state = dict(source_snapshot.state)
            output_state["trace"] = trace.model_dump(mode="json")
            output_state["event"] = replay_event.model_dump(mode="json")
            output_snapshot = self._snapshot_service.create_snapshot(
                _output_snapshot_request(
                    trace,
                    request,
                    output_state,
                    created_by,
                )
            )
            comparison = (
                self._comparator.compare(source_snapshot, output_snapshot)
                if request.compare_to_source
                else None
            )
            run = ReplayRun(
                replay_id=replay_id,
                source_trace_id=request.source_trace_id,
                replay_trace_id=trace.trace_id,
                mode=request.mode,
                status="completed",
                input_snapshot_id=source_snapshot.snapshot_id,
                output_snapshot_id=output_snapshot.snapshot_id,
                comparison=comparison.model_dump(mode="json") if comparison else {},
                drift_detected=comparison.drift_detected if comparison else False,
                created_by=created_by,
                created_at=datetime.now(UTC),
                completed_at=datetime.now(UTC),
            )
            stored = self._repository.save_replay(run)
            _emit(
                self._telemetry_service,
                "replay_completed",
                "replay",
                replay_id,
                trace.trace_id,
                request.owner_scope,
                0.8,
            )
            if stored.drift_detected:
                _emit(
                    self._telemetry_service,
                    "replay_drift_detected",
                    "replay",
                    replay_id,
                    trace.trace_id,
                    request.owner_scope,
                    1.0,
                )
            self._observe("replay_completed", replay_id, trace.trace_id)
            return stored
        except ReplayPolicyDenied:
            raise
        except Exception as exc:
            return self._failed(request, replay_id, created_by, None, str(exc))

    def get_replay(self, replay_id: str, scope: list[str]) -> ReplayRun | None:
        """Return a policy-authorized replay run."""
        self._authorize("replay.read", replay_id, scope, {"mode": "dry_run"})
        return self._repository.get_replay(replay_id)

    def _source_event(self, trace_id: str) -> AIONEvent | None:
        trace = _call(self._trace_repository, "get_trace", trace_id)
        if trace is not None:
            event = _call(self._event_repository, "get", getattr(trace, "event_id", ""))
            if isinstance(event, AIONEvent):
                return event
        events = _call(self._event_repository, "list_by_trace", trace_id)
        if isinstance(events, list) and events and isinstance(events[0], AIONEvent):
            return events[0]
        return None

    def _allowed(self, request: ReplayRequest, replay_id: str) -> bool:
        try:
            self._authorize(
                "replay.run",
                replay_id,
                request.owner_scope,
                {"mode": request.mode, "source_trace_id": request.source_trace_id},
            )
        except ReplayPolicyDenied:
            return False
        return True

    def _authorize(
        self,
        action_type: str,
        resource_id: str,
        scope: list[str],
        context: dict[str, Any],
    ) -> None:
        policy_request = PolicyRequest(
            request_id=f"request-{uuid4().hex}",
            trace_id=self._actor_context.trace_id or resource_id,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            action_type=action_type,
            resource_type="cognitive_replay",
            resource_id=resource_id,
            risk_level="low",
            approval_present=False,
            requested_permissions=[],
            security_scope=scope,
            context=context,
        )
        decision = self._policy_adapter.authorize(
            PolicyInputEnricher().enrich(policy_request, self._actor_context)
        )
        if not decision.allow:
            raise ReplayPolicyDenied(decision)

    def _failed(
        self,
        request: ReplayRequest,
        replay_id: str,
        created_by: str | None,
        source_snapshot: BrainSnapshot | None,
        reason: str,
    ) -> ReplayRun:
        self._observe("replay_failed", replay_id, request.source_trace_id, reason)
        return self._repository.save_replay(
            ReplayRun(
                replay_id=replay_id,
                source_trace_id=request.source_trace_id,
                replay_trace_id=None,
                mode=request.mode,
                status="failed",
                input_snapshot_id=source_snapshot.snapshot_id if source_snapshot else None,
                output_snapshot_id=None,
                comparison={"error": reason},
                drift_detected=False,
                created_by=created_by,
                created_at=datetime.now(UTC),
                completed_at=datetime.now(UTC),
            )
        )

    def _observe(
        self,
        event_type: str,
        replay_id: str,
        trace_id: str,
        reason: str | None = None,
    ) -> None:
        record = getattr(self._observability_service, "record_event", None)
        if not callable(record):
            return
        try:
            record(
                ObservabilityEvent(
                    observability_event_id=f"observability-{uuid4().hex}",
                    trace_id=trace_id,
                    correlation_id=None,
                    event_type=event_type,
                    component="cognitive_replay",
                    level="error" if reason else "info",
                    message=reason or event_type,
                    payload={"replay_id": replay_id},
                    created_at=None,
                )
            )
        except Exception:
            return


def _replay_event(event: AIONEvent, replay_id: str, request: ReplayRequest) -> AIONEvent:
    disabled_side_effect_keys = {
        "create_goal",
        "create_task",
        "reflect",
        "create_skill_candidate",
        "promote_skill",
        "create_schedule",
        "execute",
        "controlled_execution",
    }
    payload = {
        key: value for key, value in event.payload.items() if key not in disabled_side_effect_keys
    }
    payload["replay"] = True
    payload["replay_mode"] = request.mode
    payload["source_event_id"] = event.event_id
    return event.model_copy(
        update={
            "event_id": f"event-{replay_id}",
            "actor_id": request.actor_id or event.actor_id,
            "workspace_id": request.workspace_id or event.workspace_id,
            "payload": payload,
            "trace_id": f"trace-{replay_id}",
            "correlation_id": f"correlation-{replay_id}",
            "security_scope": request.owner_scope,
            "timestamp": datetime.now(UTC),
        }
    )


def _output_snapshot_request(
    trace: DecisionTrace,
    request: ReplayRequest,
    state: dict[str, Any],
    created_by: str | None,
) -> SnapshotCreateRequest:
    return SnapshotCreateRequest(
        trace_id=trace.trace_id,
        workspace_id=request.workspace_id,
        owner_scope=request.owner_scope,
        snapshot_type="replay_output",
        state=state,
        created_by=created_by,
        metadata={"replay": True},
    )


def _call(target: object, method: str, *args: object) -> Any:
    function = getattr(target, method, None)
    if not callable(function):
        return None
    try:
        return function(*args)
    except Exception:
        return None
