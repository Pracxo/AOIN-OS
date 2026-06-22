"""Policy-gated, content-addressed Brain snapshot service."""

import hashlib
import json
from datetime import UTC, datetime
from typing import Any, Protocol, cast
from uuid import uuid4

from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.replay import BrainSnapshot, SnapshotCreateRequest, SnapshotType
from aion_brain.contracts.scopes import ActorContext
from aion_brain.contracts.telemetry import (
    VisualNodeType,
    VisualTelemetryEvent,
    VisualTelemetryEventType,
)
from aion_brain.policy.base import PolicyAdapter
from aion_brain.policy.enrichment import PolicyInputEnricher


class SnapshotRepository(Protocol):
    """Persistence boundary required by SnapshotService."""

    def save_snapshot(self, snapshot: BrainSnapshot) -> BrainSnapshot: ...

    def get_snapshot(self, snapshot_id: str) -> BrainSnapshot | None: ...

    def list_snapshots(
        self,
        *,
        trace_id: str | None = None,
        snapshot_type: str | None = None,
        limit: int = 50,
    ) -> list[BrainSnapshot]: ...


class ReplayPolicyDenied(RuntimeError):
    """Raised when policy denies replay or regression behavior."""

    def __init__(self, decision: PolicyDecision) -> None:
        super().__init__(decision.reason)
        self.decision = decision


class SnapshotService:
    """Create and retrieve deterministic Brain state snapshots."""

    def __init__(
        self,
        snapshot_repository: SnapshotRepository,
        policy_adapter: PolicyAdapter,
        telemetry_service: object | None = None,
        actor_context: ActorContext | None = None,
        *,
        trace_repository: object | None = None,
        event_repository: object | None = None,
    ) -> None:
        self._repository = snapshot_repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._actor_context = actor_context or ActorContext()
        self._trace_repository = trace_repository
        self._event_repository = event_repository

    def with_actor_context(self, actor_context: ActorContext) -> "SnapshotService":
        """Return a request-scoped snapshot service."""
        return SnapshotService(
            self._repository,
            self._policy_adapter,
            self._telemetry_service,
            actor_context,
            trace_repository=self._trace_repository,
            event_repository=self._event_repository,
        )

    def create_snapshot(self, request: SnapshotCreateRequest) -> BrainSnapshot:
        """Authorize, sanitize, hash, and persist a snapshot."""
        self._authorize("snapshot.create", request.trace_id, request.owner_scope, "snapshot")
        state = sanitize_state(request.state)
        snapshot = BrainSnapshot(
            snapshot_id=request.snapshot_id or f"snapshot-{uuid4().hex}",
            trace_id=request.trace_id,
            workspace_id=request.workspace_id or self._actor_context.workspace_id,
            owner_scope=request.owner_scope,
            snapshot_type=request.snapshot_type,
            state=state,
            content_hash=content_hash(state),
            created_by=request.created_by or self._actor_context.actor_id,
            created_at=datetime.now(UTC),
        )
        stored = self._repository.save_snapshot(snapshot)
        _emit(
            self._telemetry_service,
            "snapshot_created",
            "snapshot",
            stored.snapshot_id,
            stored.trace_id or f"snapshot-{stored.snapshot_id}",
            stored.owner_scope,
            0.5,
        )
        return stored

    def get_snapshot(self, snapshot_id: str, scope: list[str]) -> BrainSnapshot | None:
        """Return a policy-authorized in-scope snapshot."""
        self._authorize("snapshot.read", snapshot_id, scope, "snapshot")
        snapshot = self._repository.get_snapshot(snapshot_id)
        if snapshot is None or not set(snapshot.owner_scope) & set(scope):
            return None
        return snapshot

    def list_snapshots(
        self,
        trace_id: str | None = None,
        snapshot_type: str | None = None,
        scope: list[str] | None = None,
        limit: int = 50,
    ) -> list[BrainSnapshot]:
        """Return policy-authorized snapshots within the requested scope."""
        requested_scope = scope or self._actor_context.security_scope
        self._authorize("snapshot.read", trace_id, requested_scope, "snapshot")
        return [
            snapshot
            for snapshot in self._repository.list_snapshots(
                trace_id=trace_id,
                snapshot_type=snapshot_type,
                limit=limit,
            )
            if set(snapshot.owner_scope) & set(requested_scope)
        ]

    def create_trace_snapshot(
        self,
        trace_id: str,
        snapshot_type: str,
        scope: list[str],
        created_by: str | None = None,
    ) -> BrainSnapshot:
        """Create a snapshot assembled from available canonical trace artifacts."""
        state = self._trace_state(trace_id)
        selected_state = select_snapshot_state(state, snapshot_type)
        return self.create_snapshot(
            SnapshotCreateRequest(
                trace_id=trace_id,
                workspace_id=self._actor_context.workspace_id,
                owner_scope=scope,
                snapshot_type=cast(SnapshotType, snapshot_type),
                state=selected_state,
                created_by=created_by,
                metadata={},
            )
        )

    def _trace_state(self, trace_id: str) -> dict[str, Any]:
        trace = _call(self._trace_repository, "get_trace", trace_id)
        event = None
        if trace is not None:
            event = _call(self._event_repository, "get", getattr(trace, "event_id", ""))
        if event is None:
            events = _call(self._event_repository, "list_by_trace", trace_id)
            if isinstance(events, list) and events:
                event = events[0]
        policy = _call(self._trace_repository, "list_policy_decisions", trace_id) or []
        evaluation = _call(self._trace_repository, "get_evaluation", trace_id)
        learning = _call(self._trace_repository, "list_learning_signals", trace_id) or []
        visual = _call(self._trace_repository, "list_visual_telemetry", trace_id) or []
        sections: dict[str, Any] = {
            "trace": _dump(trace),
            "event": _dump(event),
            "policy_decisions": _dump(policy),
            "evaluation": _dump(evaluation),
            "learning_signals": _dump(learning),
            "visual_telemetry": _dump(visual),
        }
        for name in (
            "intent",
            "context",
            "retrieval",
            "reasoning",
            "plan",
            "execution",
            "evidence",
            "skills",
            "goals",
            "tasks",
        ):
            sections[name] = {"section_missing": True, "section": name}
        for name, value in list(sections.items()):
            if value is None or value == []:
                sections[name] = {"section_missing": True, "section": name}
        return sections

    def _authorize(
        self,
        action_type: str,
        resource_id: str | None,
        scope: list[str],
        resource_type: str,
    ) -> None:
        request = PolicyRequest(
            request_id=f"request-{uuid4().hex}",
            trace_id=self._actor_context.trace_id or resource_id,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            action_type=action_type,
            resource_type=resource_type,
            resource_id=resource_id,
            risk_level="low",
            approval_present=False,
            requested_permissions=[],
            security_scope=scope,
            context={},
        )
        decision = self._policy_adapter.authorize(
            PolicyInputEnricher().enrich(request, self._actor_context)
        )
        if not decision.allow:
            raise ReplayPolicyDenied(decision)


def content_hash(state: dict[str, Any]) -> str:
    """Return a deterministic SHA-256 hash for normalized JSON state."""
    payload = json.dumps(state, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode()).hexdigest()


def sanitize_state(value: dict[str, Any]) -> dict[str, Any]:
    """Remove secret-like keys and raw headers from snapshot state."""
    return cast(dict[str, Any], _sanitize(value))


def select_snapshot_state(state: dict[str, Any], snapshot_type: str) -> dict[str, Any]:
    """Select the state section represented by a snapshot type."""
    section_by_type = {
        "event_only": "event",
        "context_only": "context",
        "reasoning_only": "reasoning",
        "plan_only": "plan",
        "execution_only": "execution",
        "evaluation_only": "evaluation",
        "learning_only": "learning_signals",
        "visual_only": "visual_telemetry",
    }
    section = section_by_type.get(snapshot_type)
    if section is None:
        return state
    return {section: state.get(section, {"section_missing": True, "section": section})}


def _sanitize(value: Any) -> Any:
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, item in value.items():
            normalized = str(key).lower()
            if normalized in {"headers", "authorization", "cookie", "set-cookie"}:
                continue
            if any(term in normalized for term in ("secret", "password", "token", "api_key")):
                result[str(key)] = "[redacted]"
            else:
                result[str(key)] = _sanitize(item)
        return result
    if isinstance(value, list):
        return [_sanitize(item) for item in value]
    return value


def _dump(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, list):
        return [_dump(item) for item in value]
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        return model_dump(mode="json")
    return value


def _call(target: object | None, method: str, *args: object) -> Any:
    if target is None:
        return None
    function = getattr(target, method, None)
    if not callable(function):
        return None
    try:
        return function(*args)
    except Exception:
        return None


def _emit(
    telemetry_service: object | None,
    event_type: str,
    node_type: str,
    node_id: str,
    trace_id: str,
    scope: list[str],
    intensity: float,
) -> None:
    if telemetry_service is None:
        return
    emit = getattr(telemetry_service, "emit", None)
    if not callable(emit):
        return
    emit(
        VisualTelemetryEvent(
            telemetry_id=f"telemetry-{event_type}-{node_id}",
            trace_id=trace_id,
            event_type=cast(VisualTelemetryEventType, event_type),
            node_type=cast(VisualNodeType, node_type),
            node_id=node_id,
            edge_from=trace_id,
            edge_to=node_id,
            intensity=intensity,
            payload={"owner_scope": scope},
            created_at=datetime.now(UTC),
        )
    )
