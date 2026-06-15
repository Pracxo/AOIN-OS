"""Processing lease service."""

from datetime import UTC, datetime, timedelta
from typing import cast
from uuid import uuid4

from aion_brain.config import Settings
from aion_brain.consistency.repository import ConsistencyRepository
from aion_brain.contracts.consistency import ProcessingLease
from aion_brain.contracts.telemetry import (
    VisualTelemetryEvent,
    VisualTelemetryEventType,
)


class ProcessingLeaseService:
    """Local DB-backed lease service for duplicate processing prevention."""

    def __init__(
        self,
        repository: ConsistencyRepository,
        *,
        settings: Settings,
        telemetry_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._settings = settings
        self._telemetry_service = telemetry_service

    def acquire(
        self,
        resource_type: str,
        resource_id: str,
        owner_id: str,
        ttl_seconds: int | None = None,
    ) -> ProcessingLease:
        """Acquire a lease when no active unexpired lease exists."""
        now = datetime.now(UTC)
        active = self._repository.get_active_lease(resource_type, resource_id)
        if active is not None:
            if active.expires_at <= now:
                self._repository.save_lease(
                    active.model_copy(update={"status": "expired", "released_at": now})
                )
                self._emit("processing_lease_expired", active, 0.7)
            else:
                raise ValueError("active_processing_lease_exists")
        ttl = ttl_seconds or self._settings.processing_lease_ttl_seconds
        lease = ProcessingLease(
            lease_id=f"lease-{uuid4().hex}",
            resource_type=resource_type,
            resource_id=resource_id,
            owner_id=owner_id,
            status="active",
            expires_at=now + timedelta(seconds=ttl),
            metadata={},
            created_at=now,
            released_at=None,
        )
        saved = self._repository.save_lease(lease)
        self._emit("processing_lease_acquired", saved, 0.5)
        return saved

    def release(self, lease_id: str, owner_id: str) -> ProcessingLease:
        """Release an active lease."""
        lease = self._repository.get_lease(lease_id)
        if lease is None:
            raise ValueError("processing_lease_not_found")
        if lease.owner_id != owner_id:
            raise PermissionError("processing_lease_owner_mismatch")
        saved = self._repository.save_lease(
            lease.model_copy(update={"status": "released", "released_at": datetime.now(UTC)})
        )
        self._emit("processing_lease_released", saved, 0.4)
        return saved

    def expire_old(self, now: datetime | None = None, limit: int = 100) -> int:
        """Expire stale active leases."""
        current = now or datetime.now(UTC)
        count = 0
        for lease in self._repository.list_leases(status="active", limit=limit):
            if lease.expires_at <= current:
                saved = self._repository.save_lease(
                    lease.model_copy(update={"status": "expired", "released_at": current})
                )
                self._emit("processing_lease_expired", saved, 0.7)
                count += 1
        return count

    def get_active(self, resource_type: str, resource_id: str) -> ProcessingLease | None:
        """Return the active lease when present."""
        active = self._repository.get_active_lease(resource_type, resource_id)
        if active is not None and active.expires_at <= datetime.now(UTC):
            self._repository.save_lease(
                active.model_copy(update={"status": "expired", "released_at": datetime.now(UTC)})
            )
            return None
        return active

    def _emit(self, event_type: str, lease: ProcessingLease, intensity: float) -> None:
        if self._telemetry_service is None:
            return
        event = VisualTelemetryEvent(
            telemetry_id=f"telemetry-{event_type}-{lease.lease_id}",
            trace_id=lease.lease_id,
            event_type=cast(VisualTelemetryEventType, event_type),
            node_type="lease",
            node_id=lease.lease_id,
            edge_from=lease.resource_id,
            edge_to=lease.lease_id,
            intensity=intensity,
            payload={"resource_type": lease.resource_type, "resource_id": lease.resource_id},
            created_at=datetime.now(UTC),
        )
        try:
            emit = getattr(self._telemetry_service, "emit", None)
            if callable(emit):
                emit(event)
        except Exception:
            return
