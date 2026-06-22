"""Brain snapshot service tests."""

from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.replay import SnapshotCreateRequest
from aion_brain.contracts.traces import DecisionTrace
from aion_brain.replay.repository import ReplayRepository
from aion_brain.replay.snapshot import ReplayPolicyDenied, SnapshotService


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


class TraceRepository:
    def get_trace(self, trace_id: str) -> DecisionTrace:
        return DecisionTrace(
            trace_id=trace_id,
            event_id="event-1",
            intent_id=None,
            context_id=None,
            plan_id=None,
            memory_refs=[],
            capability_refs=[],
            policy_decisions=[],
            outcome={"status": "planned"},
            created_at=datetime.now(UTC),
        )


def repository() -> ReplayRepository:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    return ReplayRepository(engine=engine)


def test_snapshot_service_hash_is_deterministic_and_calls_policy() -> None:
    """Equivalent normalized state produces the same content hash."""
    policy = Policy()
    service = SnapshotService(repository(), policy)
    first = service.create_snapshot(
        SnapshotCreateRequest(
            owner_scope=["workspace:main"],
            snapshot_type="full_trace",
            state={"b": 2, "a": 1},
        )
    )
    second = service.create_snapshot(
        SnapshotCreateRequest(
            owner_scope=["workspace:main"],
            snapshot_type="full_trace",
            state={"a": 1, "b": 2},
        )
    )
    assert first.content_hash == second.content_hash
    assert policy.requests[0].action_type == "snapshot.create"


def test_trace_snapshot_handles_missing_sections_and_policy_denial() -> None:
    """Trace assembly marks unavailable sections and snapshot creation fails closed."""
    service = SnapshotService(repository(), Policy(), trace_repository=TraceRepository())
    result = service.create_trace_snapshot("trace-1", "full_trace", ["workspace:main"])
    assert result.state["context"]["section_missing"] is True

    denied = SnapshotService(repository(), Policy(False))
    with pytest.raises(ReplayPolicyDenied):
        denied.create_snapshot(
            SnapshotCreateRequest(
                owner_scope=["workspace:main"],
                snapshot_type="full_trace",
                state={"trace": {}},
            )
        )
