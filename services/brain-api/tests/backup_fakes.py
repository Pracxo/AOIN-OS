"""Shared fakes for local backup tests."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from aion_brain.backups.exporter import BackupExporter
from aion_brain.backups.repository import BackupRepository
from aion_brain.backups.resource_readers import ResourceReaderRegistry
from aion_brain.backups.restore_preview import RestorePreviewService
from aion_brain.backups.restore_service import RestoreService
from aion_brain.backups.validator import BackupValidator
from aion_brain.config import Settings
from aion_brain.contracts.backups import BackupResourceType
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest

SCOPE = ["workspace:main"]


class AllowPolicy:
    """Always-allow policy fake."""

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


class DenyPolicy:
    """Always-deny policy fake."""

    def authorize(self, request: PolicyRequest) -> PolicyDecision:
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
    """Collect emitted telemetry."""

    def __init__(self) -> None:
        self.events: list[object] = []

    def emit(self, event: object) -> None:
        self.events.append(event)


def repository() -> BackupRepository:
    """Return an in-memory backup repository."""
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    return BackupRepository(engine=engine)


def settings(*, apply_enabled: bool = False) -> Settings:
    """Return local backup test settings."""
    return Settings(  # type: ignore[call-arg]
        _env_file=None,
        DATABASE_URL="sqlite+pysqlite:///:memory:",
        AION_BACKUP_RESTORE_APPLY_ENABLED=apply_enabled,
    )


def readers(
    records: dict[BackupResourceType, list[dict[str, object]]] | None = None,
) -> ResourceReaderRegistry:
    """Return a resource reader registry with generic fake records."""
    payload = records or {
        "events": [
            {
                "event_id": "event-1",
                "event_type": "test.received",
                "owner_scope": SCOPE,
                "payload": {"summary": "hello"},
            }
        ],
        "memory": [
            {
                "memory_id": "memory-1",
                "memory_type": "semantic",
                "owner_scope": SCOPE,
                "summary": "remember the generic note",
                "api_key": "secret-value",
            }
        ],
        "traces": [{"trace_id": "trace-1", "owner_scope": SCOPE, "status": "planned"}],
    }

    registry = ResourceReaderRegistry()

    def read(resource_type: BackupResourceType, scope: list[str]) -> list[dict[str, object]]:
        return list(payload.get(resource_type, []))

    for resource_type in payload:
        registry.register(resource_type, read)
    return registry


def exporter(
    root: Path,
    *,
    policy: object | None = None,
    telemetry: FakeTelemetry | None = None,
    registry: ResourceReaderRegistry | None = None,
) -> BackupExporter:
    """Return a backup exporter with fakes."""
    return BackupExporter(
        repository(),
        registry or readers(),
        policy or AllowPolicy(),  # type: ignore[arg-type]
        telemetry_service=telemetry,
        settings=settings(),
        root_dir=root,
    )


def services(
    root: Path,
    *,
    registry: ResourceReaderRegistry | None = None,
    apply_enabled: bool = False,
) -> tuple[
    BackupRepository,
    BackupExporter,
    RestorePreviewService,
    RestoreService,
    BackupValidator,
]:
    """Return backup services sharing one repository."""
    repo = repository()
    policy = AllowPolicy()
    service_settings = settings(apply_enabled=apply_enabled)
    resource_readers = registry or readers()
    export_service = BackupExporter(
        repo,
        resource_readers,
        policy,
        settings=service_settings,
        root_dir=root,
    )
    preview_service = RestorePreviewService(
        repo,
        policy,
        resource_readers,
        settings=service_settings,
        root_dir=root,
    )
    restore_service = RestoreService(repo, policy, settings=service_settings)
    validator = BackupValidator(repo, policy, settings=service_settings, root_dir=root)
    return repo, export_service, preview_service, restore_service, validator
