"""Degraded mode service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.api_support.errors import AIONNotFoundException
from aion_brain.contracts.resilience import DegradedModeEvent, ResilienceStatus
from aion_brain.resilience._shared import emit_resilience_event
from aion_brain.resilience.repository import ResilienceRepository


class DegradedModeService:
    """Track degraded mode metadata without automatic remediation."""

    def __init__(
        self,
        repository: ResilienceRepository,
        *,
        dependency_health_service: object | None = None,
        circuit_breaker_service: object | None = None,
        fault_injection_service: object | None = None,
        telemetry_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._dependency_health_service = dependency_health_service
        self._circuit_breaker_service = circuit_breaker_service
        self._fault_injection_service = fault_injection_service
        self._telemetry_service = telemetry_service

    def enter(
        self,
        component: str,
        severity: str,
        reason: str,
        dependencies: list[str],
        fallbacks_active: list[str],
        constraints: list[str],
        trace_id: str | None = None,
    ) -> DegradedModeEvent:
        """Enter degraded mode for a component."""
        existing = [
            event
            for event in self.list_active(component)
            if event.reason == reason and event.status == "active"
        ]
        if existing:
            return existing[0]
        event = DegradedModeEvent(
            degraded_event_id=f"degraded-{uuid4().hex}",
            trace_id=trace_id,
            component=component,
            status="active",
            severity=cast(Any, severity),
            reason=reason,
            dependencies=dependencies,
            fallbacks_active=fallbacks_active,
            constraints=constraints,
            metadata={},
            created_at=datetime.now(UTC),
            resolved_at=None,
        )
        saved = self._repository.save_degraded_event(event)
        emit_resilience_event(
            self._telemetry_service,
            event_type="degraded_mode_entered",
            node_type="degraded_mode",
            node_id=saved.degraded_event_id,
            intensity=1.0 if saved.severity == "critical" else 0.7,
            payload={"component": component, "severity": saved.severity},
            trace_id=trace_id,
        )
        return saved

    def resolve(
        self,
        degraded_event_id: str,
        actor_id: str | None,
        reason: str,
    ) -> DegradedModeEvent:
        """Resolve one degraded event."""
        event = self._repository.get_degraded_event(degraded_event_id)
        if event is None:
            raise AIONNotFoundException("degraded_event_not_found")
        saved = self._repository.save_degraded_event(
            event.model_copy(
                update={
                    "status": cast(Any, "resolved"),
                    "resolved_at": datetime.now(UTC),
                    "metadata": {
                        **event.metadata,
                        "resolved_by": actor_id,
                        "resolve_reason": reason,
                    },
                }
            )
        )
        emit_resilience_event(
            self._telemetry_service,
            event_type="degraded_mode_resolved",
            node_type="degraded_mode",
            node_id=saved.degraded_event_id,
            intensity=0.4,
            payload={"component": saved.component},
            trace_id=saved.trace_id,
        )
        return saved

    def list_active(self, component: str | None = None) -> list[DegradedModeEvent]:
        """List active degraded events."""
        return self._repository.list_degraded_events(status="active", component=component)

    def status(self) -> ResilienceStatus:
        """Return combined resilience status."""
        dependencies = _call_list(self._dependency_health_service, "list_latest")
        active_events = self.list_active()
        open_breakers = _call_list(
            self._circuit_breaker_service,
            "list_breakers",
            status="open",
        )
        active_faults = _call_list(self._fault_injection_service, "list_rules", status="active")
        critical_unhealthy = [
            item
            for item in dependencies
            if getattr(item, "criticality", None) == "critical"
            and getattr(item, "status", None) in {"unhealthy", "unavailable"}
        ]
        critical_degraded = [
            event for event in active_events if getattr(event, "severity", None) == "critical"
        ]
        overall = "healthy"
        if critical_unhealthy or critical_degraded:
            overall = "unhealthy"
        elif active_events or open_breakers or active_faults:
            overall = "degraded"
        return ResilienceStatus(
            overall_status=cast(Any, overall),
            dependencies=dependencies,
            active_degraded_events=active_events,
            open_circuit_breakers=open_breakers,
            active_fault_rules=active_faults,
            generated_at=datetime.now(UTC),
        )


def _call_list(service: object | None, method_name: str, **kwargs: Any) -> list[Any]:
    method = getattr(service, method_name, None)
    if not callable(method):
        return []
    try:
        return list(method(**kwargs))
    except Exception:
        return []
