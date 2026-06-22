"""Kernel service registry."""

from datetime import UTC, datetime
from typing import cast
from uuid import uuid4

from aion_brain.contracts.kernel import KernelServiceRecord, KernelServiceStatus, KernelServiceType
from aion_brain.kernel.repository import KernelRepository


class KernelServiceRegistry:
    """Register and report every service assembled by the composition root."""

    def __init__(
        self,
        repository: KernelRepository | None = None,
        telemetry_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._telemetry_service = telemetry_service
        self._records: dict[str, KernelServiceRecord] = {}

    def register(self, record: KernelServiceRecord) -> KernelServiceRecord:
        """Register a service record."""
        now = datetime.now(UTC)
        stored = record.model_copy(
            update={"created_at": record.created_at or now, "updated_at": now}
        )
        self._records[stored.service_record_id] = stored
        if self._repository is not None:
            self._repository.save_service(stored)
        self._emit(stored)
        return stored

    def register_service(
        self,
        service_name: str,
        service_type: KernelServiceType,
        adapter_name: str,
        *,
        status: KernelServiceStatus = "registered",
        health: dict[str, object] | None = None,
        metadata: dict[str, object] | None = None,
    ) -> KernelServiceRecord:
        """Create and register a service record."""
        return self.register(
            KernelServiceRecord(
                service_record_id=f"service-{uuid4().hex}",
                service_name=service_name,
                service_type=service_type,
                adapter_name=adapter_name,
                status=status,
                health=health or {},
                metadata=metadata or {},
                created_at=None,
                updated_at=None,
            )
        )

    def list_services(
        self,
        status: str | None = None,
        service_type: str | None = None,
    ) -> list[KernelServiceRecord]:
        """Return services matching optional filters."""
        records = list(self._records.values())
        if not records and self._repository is not None:
            records = self._repository.list_services()
        if status:
            records = [record for record in records if record.status == status]
        if service_type:
            records = [record for record in records if record.service_type == service_type]
        return sorted(records, key=lambda record: record.service_name)

    def update_health(
        self,
        service_name: str,
        health: dict[str, object],
        status: str,
    ) -> KernelServiceRecord:
        """Update one registered service health record."""
        record = next(
            (item for item in self.list_services() if item.service_name == service_name),
            None,
        )
        if record is None:
            raise LookupError("kernel_service_not_found")
        return self.register(
            record.model_copy(
                update={
                    "health": health,
                    "status": cast(KernelServiceStatus, status),
                    "updated_at": datetime.now(UTC),
                }
            )
        )

    def _emit(self, record: KernelServiceRecord) -> None:
        emit = getattr(self._telemetry_service, "emit", None)
        if not callable(emit):
            return
        try:
            from aion_brain.contracts.telemetry import VisualTelemetryEvent

            emit(
                VisualTelemetryEvent(
                    telemetry_id=f"telemetry-{record.service_record_id}-registered",
                    trace_id=record.service_record_id,
                    event_type="kernel_service_registered",
                    node_type="service",
                    node_id=record.service_record_id,
                    edge_from=None,
                    edge_to=None,
                    intensity=0.5,
                    payload={"service_name": record.service_name, "status": record.status},
                    created_at=datetime.now(UTC),
                )
            )
        except Exception:
            return
