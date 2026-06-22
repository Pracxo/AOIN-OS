"""Kernel boot sequence."""

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.contracts.kernel import KernelBootRecord, KernelBootStatus
from aion_brain.contracts.telemetry import VisualTelemetryEventType
from aion_brain.kernel.diagnostics import KernelDiagnostics
from aion_brain.kernel.repository import KernelRepository
from aion_brain.kernel.service_registry import KernelServiceRegistry


class KernelBootService:
    """Run and persist the lightweight AION Brain boot sequence."""

    def __init__(
        self,
        *,
        container: object,
        repository: KernelRepository,
        registry: KernelServiceRegistry,
        diagnostics: KernelDiagnostics,
        telemetry_service: object | None = None,
    ) -> None:
        self._container = container
        self._repository = repository
        self._registry = registry
        self._diagnostics = diagnostics
        self._telemetry_service = telemetry_service

    def boot(self) -> KernelBootRecord:
        """Run deterministic diagnostics and record the boot outcome."""
        started = datetime.now(UTC)
        boot_id = f"boot-{uuid4().hex}"
        self._emit("kernel_boot_started", boot_id, 0.4, {"status": "starting"})
        checks = self._diagnostics.run()
        critical_failed = any(
            check.status == "failed" and check.severity == "critical" for check in checks
        )
        noncritical_failed = any(check.status in {"failed", "warning"} for check in checks)
        status = "failed" if critical_failed else ("degraded" if noncritical_failed else "ready")
        container = cast(Any, self._container)
        settings = container.settings
        record = KernelBootRecord(
            boot_id=boot_id,
            service_name=settings.service_name,
            version=settings.version,
            env=settings.env,
            status=cast(KernelBootStatus, status),
            adapter_config=container.adapter_config,
            diagnostics={"checks": [check.model_dump(mode="json") for check in checks]},
            started_at=started,
            completed_at=datetime.now(UTC),
        )
        stored = self._repository.save_boot(record)
        intensity = {"ready": 0.8, "degraded": 0.5, "failed": 1.0}[status]
        self._emit("kernel_boot_completed", boot_id, intensity, {"status": status})
        return stored

    def get_latest_boot(self) -> KernelBootRecord | None:
        """Return the latest boot record."""
        return self._repository.get_latest_boot()

    def _emit(
        self,
        event_type: str,
        node_id: str,
        intensity: float,
        payload: dict[str, object],
    ) -> None:
        emit = getattr(self._telemetry_service, "emit", None)
        if not callable(emit):
            return
        try:
            from aion_brain.contracts.telemetry import VisualTelemetryEvent

            emit(
                VisualTelemetryEvent(
                    telemetry_id=f"telemetry-{node_id}-{event_type}",
                    trace_id=node_id,
                    event_type=cast(VisualTelemetryEventType, event_type),
                    node_type="kernel",
                    node_id=node_id,
                    edge_from=None,
                    edge_to=None,
                    intensity=intensity,
                    payload=payload,
                    created_at=datetime.now(UTC),
                )
            )
        except Exception:
            return
