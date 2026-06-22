"""Shared fakes for Operator Control Tower tests."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.operator.repository import OperatorRepository

SCOPE = ["workspace:main"]


class AllowPolicy:
    """Always allow policy fake."""

    def __init__(self) -> None:
        self.requests: list[PolicyRequest] = []

    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        self.requests.append(request)
        return PolicyDecision(
            decision_id=f"decision-{request.request_id}",
            trace_id=request.trace_id or "",
            allow=True,
            approval_required=False,
            reason="allowed",
            constraints=[],
            audit_level="standard",
        )


class FakeTelemetry:
    """Collect emitted telemetry."""

    def __init__(self) -> None:
        self.events: list[object] = []

    def emit(self, event: object) -> None:
        self.events.append(event)


@dataclass
class FakeRecord:
    id: str
    status: str
    priority: str = "normal"
    trace_id: str | None = None
    created_at: datetime | None = None
    approval_scope: list[str] | None = None

    @property
    def approval_request_id(self) -> str:
        return self.id

    @property
    def command_id(self) -> str:
        return self.id

    @property
    def outbox_id(self) -> str:
        return self.id

    @property
    def name(self) -> str:
        return self.id

    @property
    def audit_verification_id(self) -> str:
        return self.id


class FakeListService:
    """Return records from common list methods."""

    def __init__(self, records: list[object]) -> None:
        self.records = records
        self.executed = False

    def list_requests(self, *_args: object, **_kwargs: object) -> list[object]:
        return self.records

    def list_commands(self, **_kwargs: object) -> list[object]:
        return self.records

    def list_messages(self, **_kwargs: object) -> list[object]:
        return self.records

    def list_circuit_breakers(self, **_kwargs: object) -> list[object]:
        return self.records

    def execute(self) -> None:
        self.executed = True


class FakeStatusService:
    """Simple status provider."""

    def __init__(self, status: str) -> None:
        self._status = status

    def status(self) -> dict[str, str]:
        return {"status": self._status}


class FakeAuditService:
    """Simple audit verification provider."""

    def __init__(self, record: object | None) -> None:
        self.record = record

    def latest_verification_run(self) -> object | None:
        return self.record


def repository() -> OperatorRepository:
    """Return an in-memory operator repository."""
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    return OperatorRepository(engine=engine)


def now() -> datetime:
    return datetime.now(UTC)
