"""Cognitive replay service tests."""

from datetime import UTC, datetime

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from aion_brain.contracts.events import AIONEvent
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.replay import ReplayRequest
from aion_brain.contracts.traces import DecisionTrace
from aion_brain.replay.comparator import TraceComparator
from aion_brain.replay.repository import ReplayRepository
from aion_brain.replay.service import ReplayService
from aion_brain.replay.snapshot import SnapshotService


class Policy:
    def __init__(self, allow: bool = True) -> None:
        self.allow = allow
        self.requests: list[PolicyRequest] = []

    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        self.requests.append(request)
        return PolicyDecision(
            decision_id="decision-1",
            trace_id=request.trace_id or "",
            allow=self.allow,
            approval_required=False,
            reason="allowed" if self.allow else "denied",
            constraints=[],
            audit_level="standard",
        )


class Traces:
    def get_trace(self, trace_id: str) -> DecisionTrace:
        return trace(trace_id, "event-1")


class Events:
    def __init__(self, event: AIONEvent | None) -> None:
        self.event = event

    def get(self, event_id: str) -> AIONEvent | None:
        return self.event

    def list_by_trace(self, trace_id: str) -> list[AIONEvent]:
        return [self.event] if self.event else []


class BrainLoop:
    def __init__(self) -> None:
        self.event: AIONEvent | None = None

    def think(self, event: AIONEvent, *, replay_mode: bool = False) -> DecisionTrace:
        self.event = event
        assert replay_mode is True
        return trace(event.trace_id or "", event.event_id)


def repository() -> ReplayRepository:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    return ReplayRepository(engine=engine)


def make_service(*, allow: bool = True, event: AIONEvent | None = None):
    repo = repository()
    policy = Policy(allow)
    traces = Traces()
    events = Events(event)
    loop = BrainLoop()
    snapshots = SnapshotService(
        repo,
        policy,
        trace_repository=traces,
        event_repository=events,
    )
    return (
        ReplayService(repo, snapshots, traces, events, loop, TraceComparator(), policy),
        policy,
        loop,
    )


def test_replay_calls_policy_and_blocks_when_denied() -> None:
    """Policy denial creates a persisted blocked replay run."""
    service, policy, _ = make_service(allow=False, event=source_event())
    result = service.replay(request())
    assert result.status == "blocked_by_policy"
    assert policy.requests[0].action_type == "replay.run"


def test_replay_fails_cleanly_without_source_event() -> None:
    """Missing canonical source events create a failed replay run."""
    service, _, _ = make_service(event=None)
    result = service.replay(request())
    assert result.status == "failed"
    assert result.comparison["error"] == "source_event_missing"


def test_replay_creates_snapshots_and_suppresses_side_effect_flags() -> None:
    """Replay produces snapshots without forwarding lifecycle triggers."""
    service, _, loop = make_service(event=source_event())
    result = service.replay(request())
    assert result.status == "completed"
    assert result.input_snapshot_id
    assert result.output_snapshot_id
    assert result.drift_detected is False
    assert loop.event is not None
    assert "create_goal" not in loop.event.payload
    assert loop.event.payload["replay"] is True


def request() -> ReplayRequest:
    return ReplayRequest(source_trace_id="trace-1", owner_scope=["workspace:main"])


def source_event() -> AIONEvent:
    return AIONEvent(
        event_id="event-1",
        source="test",
        event_type="question",
        payload_type="json",
        payload={"question": "what is known", "create_goal": True},
        timestamp=datetime.now(UTC),
        trace_id="trace-1",
        security_scope=["workspace:main"],
    )


def trace(trace_id: str, event_id: str) -> DecisionTrace:
    return DecisionTrace(
        trace_id=trace_id,
        event_id=event_id,
        intent_id=None,
        context_id=None,
        plan_id=None,
        memory_refs=[],
        capability_refs=[],
        policy_decisions=[],
        outcome={"status": "planned"},
        created_at=datetime.now(UTC),
    )
