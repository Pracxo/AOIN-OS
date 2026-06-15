"""Shared fakes for audit integrity tests."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from aion_brain.audit_integrity.checkpoints import AuditCheckpointService
from aion_brain.audit_integrity.ledger import AuditIntegrityLedger
from aion_brain.audit_integrity.repository import AuditIntegrityRepository
from aion_brain.config import Settings
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest


class AllowPolicy:
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


class DenyPolicy(AllowPolicy):
    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        self.requests.append(request)
        return PolicyDecision(
            decision_id=f"decision-{request.request_id}",
            trace_id=request.trace_id or "",
            allow=False,
            approval_required=False,
            reason="denied",
            constraints=["test"],
            audit_level="high",
        )


class FakeTelemetry:
    def __init__(self) -> None:
        self.events: list[object] = []

    def emit(self, event: object) -> None:
        self.events.append(event)


def repository() -> AuditIntegrityRepository:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    return AuditIntegrityRepository(engine=engine)


def settings(**overrides: object) -> Settings:
    return Settings(
        _env_file=None,
        DATABASE_URL="sqlite+pysqlite:///:memory:",
        AION_DEFAULT_SEMANTIC_ADAPTER="in_memory",
        AION_GRAPH_MEMORY_ADAPTER="in_memory",
        **overrides,
    )


def ledger(
    repo: AuditIntegrityRepository | None = None,
    *,
    checkpoint_interval: int = 1000,
) -> tuple[AuditIntegrityLedger, AuditIntegrityRepository, FakeTelemetry]:
    selected_repo = repo or repository()
    telemetry = FakeTelemetry()
    service = AuditIntegrityLedger(
        selected_repo,
        AllowPolicy(),
        telemetry,
        settings(AION_AUDIT_CHECKPOINT_INTERVAL=checkpoint_interval),
    )
    service.set_checkpoint_service(AuditCheckpointService(selected_repo))
    return service, selected_repo, telemetry
