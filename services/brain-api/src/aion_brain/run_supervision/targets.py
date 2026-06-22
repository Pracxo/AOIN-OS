"""Provider-neutral run target status adapter."""

from __future__ import annotations

from datetime import UTC, datetime
from time import monotonic
from typing import Any, cast
from uuid import uuid4

from aion_brain.contracts.run_supervision import ObservedRunStatus, RunStatusSample, RunTargetSystem


class RunTargetStatusAdapter:
    """Read target subsystem status without owning target execution semantics."""

    def __init__(
        self,
        *,
        command_bus: object | None = None,
        workflow_service: object | None = None,
        execution_orchestrator: object | None = None,
        capability_runtime: object | None = None,
        mcp_service: object | None = None,
        cycle_orchestrator: object | None = None,
        sandbox_service: object | None = None,
    ) -> None:
        self._services = {
            "command_bus": command_bus,
            "workflow_engine": workflow_service,
            "execution_orchestrator": execution_orchestrator,
            "capability_runtime": capability_runtime,
            "mcp_adapter": mcp_service,
            "cognitive_cycle": cycle_orchestrator,
            "sandbox": sandbox_service,
        }

    def sample(
        self,
        target_system: str,
        target_run_id: str | None,
        metadata: dict[str, Any],
    ) -> RunStatusSample:
        """Return one local status sample. Missing targets become unknown."""

        started = monotonic()
        if target_system == "noop":
            raw_status: dict[str, Any] = {"status": "completed", "source": "noop"}
        else:
            raw_status = self._read_status(target_system, target_run_id, metadata)
        observed_status = _map_status(raw_status.get("status"))
        return RunStatusSample(
            run_status_sample_id=str(
                metadata.get("run_status_sample_id") or f"run-status-sample-{uuid4().hex}"
            ),
            run_supervision_id=str(metadata.get("run_supervision_id") or "unknown"),
            trace_id=_str_or_none(metadata.get("trace_id")),
            target_system=cast(RunTargetSystem, target_system),
            target_run_id=target_run_id,
            observed_status=observed_status,
            raw_status=raw_status,
            progress=_dict_or_empty(raw_status.get("progress")),
            error=_dict_or_empty(raw_status.get("error")),
            latency_ms=max(0, int((monotonic() - started) * 1000)),
            metadata={"source": "run_target_status_adapter"},
            observed_at=datetime.now(UTC),
        )

    def supports_control(self, target_system: str, control_type: str) -> bool:
        """Return whether a target exposes the requested local control method."""

        if control_type == "request_status":
            return target_system in {
                "command_bus",
                "workflow_engine",
                "execution_orchestrator",
                "capability_runtime",
                "mcp_adapter",
                "cognitive_cycle",
                "sandbox",
                "noop",
            }
        if target_system == "command_bus" and control_type == "cancel":
            return callable(getattr(self._services.get("command_bus"), "cancel", None))
        if target_system == "workflow_engine" and control_type in {"cancel", "pause", "resume"}:
            method = {"cancel": "cancel_run", "pause": "pause_run", "resume": "resume_run"}[
                control_type
            ]
            return callable(getattr(self._services.get("workflow_engine"), method, None))
        return False

    def _read_status(
        self, target_system: str, target_run_id: str | None, metadata: dict[str, Any]
    ) -> dict[str, Any]:
        if not target_run_id:
            return {"status": "unknown", "reason": "missing_target_run_id"}
        service = self._services.get(target_system)
        if service is None:
            return {"status": "unknown", "reason": "target_service_unavailable"}
        if target_system == "command_bus":
            return _object_status(getattr(service, "get", None), target_run_id)
        if target_system == "workflow_engine":
            get_run = getattr(service, "get_run", None)
            if callable(get_run):
                scope = list(metadata.get("scope") or ["workspace:main"])
                return _status_from_object(get_run(target_run_id, scope))
        for method_name in (
            "get_run",
            "get",
            "get_invocation",
            "get_cycle_run",
            "get_sandbox_run",
        ):
            method = getattr(service, method_name, None)
            if callable(method):
                try:
                    return _status_from_object(method(target_run_id))
                except TypeError:
                    continue
        return {"status": "unknown", "reason": "target_status_unavailable"}


def _object_status(method: object, target_run_id: str) -> dict[str, Any]:
    if not callable(method):
        return {"status": "unknown", "reason": "target_status_unavailable"}
    return _status_from_object(method(target_run_id))


def _status_from_object(value: object) -> dict[str, Any]:
    if value is None:
        return {"status": "unknown", "reason": "target_not_found"}
    if isinstance(value, dict):
        return value
    status = getattr(value, "status", None)
    raw: dict[str, Any] = {"status": status or "unknown"}
    for name in ("progress", "error", "result", "completed_at", "started_at"):
        nested = getattr(value, name, None)
        if nested is not None:
            raw[name] = (
                nested if isinstance(nested, (dict, list, str, int, float, bool)) else str(nested)
            )
    return raw


def _map_status(status: object) -> ObservedRunStatus:
    value = str(status or "unknown").lower()
    mapping = {
        "created": "pending",
        "queued": "pending",
        "scheduled": "pending",
        "pending": "pending",
        "retry_scheduled": "pending",
        "running": "running",
        "processing": "running",
        "in_progress": "running",
        "waiting_for_approval": "waiting_for_approval",
        "paused": "paused",
        "completed": "completed",
        "dry_run": "completed",
        "handed_off": "running",
        "failed": "failed",
        "error": "failed",
        "cancelled": "cancelled",
        "blocked": "blocked",
        "blocked_by_policy": "blocked",
        "blocked_by_autonomy": "blocked",
        "unsupported": "blocked",
    }
    return cast(ObservedRunStatus, mapping.get(value, "unknown"))


def _dict_or_empty(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _str_or_none(value: object) -> str | None:
    return value if isinstance(value, str) else None


__all__ = ["RunTargetStatusAdapter"]
