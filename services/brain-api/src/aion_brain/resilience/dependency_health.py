"""Dependency health reporting for resilience control plane."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from time import monotonic
from typing import Any
from uuid import uuid4

from aion_brain.config import Settings, get_settings
from aion_brain.contracts.resilience import DependencyHealth
from aion_brain.infra import check_nats, check_opa, check_postgres, check_redis
from aion_brain.resilience._shared import emit_resilience_event
from aion_brain.resilience.repository import ResilienceRepository

DependencyChecker = Callable[[], bool]


class DependencyHealthService:
    """Check local dependency health without crashing callers."""

    def __init__(
        self,
        repository: ResilienceRepository,
        *,
        settings: Settings | None = None,
        telemetry_service: object | None = None,
        checkers: dict[str, DependencyChecker] | None = None,
    ) -> None:
        self._repository = repository
        self._settings = settings or get_settings()
        self._telemetry_service = telemetry_service
        self._checkers = checkers

    def check_all(self) -> list[DependencyHealth]:
        """Check all known dependencies."""
        return [self.check_dependency(name) for name in self._dependency_specs()]

    def check_dependency(self, dependency_name: str) -> DependencyHealth:
        """Check one dependency by name."""
        specs = self._dependency_specs()
        spec = specs.get(dependency_name)
        if spec is None:
            return self._record(
                dependency_name,
                "optional_adapter",
                "unknown",
                "optional",
                0,
                {"reason": "unknown_dependency"},
            )
        dependency_type, criticality, checker = spec
        start = monotonic()
        try:
            ok = checker()
            status = "healthy" if ok else "unavailable"
            details: dict[str, Any] = {}
        except Exception as exc:
            status = "unavailable"
            details = {"reason": type(exc).__name__}
        latency_ms = max(0, int((monotonic() - start) * 1000))
        if dependency_name in {"mcp", "sandbox"} and not self._dependency_enabled(dependency_name):
            status = "disabled"
            details = {"reason": f"{dependency_name}_disabled"}
        return self._record(
            dependency_name,
            dependency_type,
            status,
            criticality,
            latency_ms,
            details,
        )

    def list_latest(
        self,
        *,
        dependency_type: str | None = None,
        component: str | None = None,
    ) -> list[DependencyHealth]:
        """List latest persisted health record per dependency."""
        records = self._repository.latest_dependency_health()
        if dependency_type is not None:
            records = [record for record in records if record.dependency_type == dependency_type]
        if component is not None:
            records = [record for record in records if record.dependency_name == component]
        return records

    def _dependency_specs(self) -> dict[str, tuple[str, str, DependencyChecker]]:
        if self._checkers is not None:
            return {
                name: ("optional_adapter", "optional", checker)
                for name, checker in self._checkers.items()
            }
        settings = self._settings
        return {
            "postgres": (
                "database",
                "critical",
                lambda: check_postgres(settings.database_url, timeout_seconds=1.0),
            ),
            "redis": (
                "cache",
                "important",
                lambda: check_redis(settings.redis_url, timeout_seconds=1.0),
            ),
            "nats": (
                "event_bus",
                "important",
                lambda: check_nats(settings.nats_url, timeout_seconds=1.0),
            ),
            "opa": (
                "policy_engine",
                "critical",
                lambda: check_opa(settings.opa_url, timeout_seconds=1.0),
            ),
            "semantic_memory_adapter": ("semantic_memory", "optional", lambda: True),
            "graph_memory_adapter": ("graph_memory", "optional", lambda: True),
            "model_gateway": ("model_gateway", "optional", lambda: True),
            "mcp": ("mcp", "optional", lambda: bool(settings.mcp_enabled)),
            "workflow_engine": ("workflow_engine", "important", lambda: True),
            "sandbox": (
                "sandbox",
                "optional",
                lambda: bool(settings.sandbox_control_plane_enabled),
            ),
            "observability": ("observability", "optional", lambda: True),
        }

    def _dependency_enabled(self, dependency_name: str) -> bool:
        if dependency_name == "mcp":
            return bool(self._settings.mcp_enabled)
        if dependency_name == "sandbox":
            return bool(self._settings.sandbox_control_plane_enabled)
        return True

    def _record(
        self,
        dependency_name: str,
        dependency_type: str,
        status: str,
        criticality: str,
        latency_ms: int,
        details: dict[str, Any],
    ) -> DependencyHealth:
        record = DependencyHealth(
            dependency_health_id=f"dependency-health-{uuid4().hex}",
            dependency_name=dependency_name,
            dependency_type=dependency_type,  # type: ignore[arg-type]
            status=status,  # type: ignore[arg-type]
            criticality=criticality,  # type: ignore[arg-type]
            latency_ms=latency_ms,
            details=details,
            checked_at=datetime.now(UTC),
        )
        saved = self._repository.save_dependency_health(record)
        emit_resilience_event(
            self._telemetry_service,
            event_type="dependency_health_checked",
            node_type="dependency",
            node_id=saved.dependency_name,
            intensity=_dependency_intensity(saved.status),
            payload={"status": saved.status, "criticality": saved.criticality},
        )
        return saved


def _dependency_intensity(status: str) -> float:
    if status == "healthy":
        return 0.3
    if status in {"degraded", "disabled", "unknown"}:
        return 0.7
    return 1.0
