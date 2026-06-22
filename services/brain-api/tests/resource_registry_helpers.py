"""Shared helpers for registry tests."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.resource_registry import ResourceDescriptor
from aion_brain.resource_registry.repository import ResourceRegistryRepository
from aion_brain.resource_registry.uri import build_resource_uri


class DenyPolicy:
    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        return PolicyDecision(
            decision_id=f"deny-{request.request_id}",
            trace_id=request.trace_id or "",
            allow=False,
            approval_required=False,
            reason="test_denied",
            constraints=[],
            audit_level="high",
        )


class FakeTelemetry:
    def __init__(self) -> None:
        self.events: list[object] = []

    def emit(self, event: object) -> None:
        self.events.append(event)


def repository() -> ResourceRegistryRepository:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    return ResourceRegistryRepository(engine=engine)


def descriptor(resource_id: str = "res-1", *, refs: list[str] | None = None) -> ResourceDescriptor:
    now = datetime.now(UTC)
    return ResourceDescriptor(
        resource_uri=build_resource_uri("generic", resource_id),
        resource_type="generic",
        resource_id=resource_id,
        trace_id="trace-registry",
        actor_id="actor",
        workspace_id="workspace",
        source_system="test",
        status="active",
        visibility="internal",
        sensitivity="internal",
        title=f"Resource {resource_id}",
        summary="A safe registry test descriptor.",
        owner_scope=["workspace:main"],
        tags=["test"],
        refs=refs or [],
        metadata={"test": True},
        first_seen_at=now,
        last_seen_at=now,
    )


__all__ = ["DenyPolicy", "FakeTelemetry", "descriptor", "repository"]
