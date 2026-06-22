"""Shared helpers for explanation services."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.telemetry import VisualTelemetryEvent
from aion_brain.dialogue._shared import emit_telemetry


def authorize(
    policy_adapter: object | None,
    *,
    action_type: str,
    resource_type: str,
    resource_id: str | None,
    scope: list[str],
    trace_id: str | None = None,
    actor_id: str | None = None,
    workspace_id: str | None = None,
    risk_level: str = "low",
    context: dict[str, Any] | None = None,
) -> PolicyDecision:
    """Authorize an explanation action and fail closed on deny."""

    authorize_call = getattr(policy_adapter, "authorize", None)
    if not callable(authorize_call):
        raise PermissionError("policy_adapter_unavailable")
    decision = authorize_call(
        PolicyRequest(
            request_id=f"{action_type}-{resource_id or uuid4().hex}",
            trace_id=trace_id,
            actor_id=actor_id,
            workspace_id=workspace_id,
            action_type=action_type,
            resource_type=resource_type,
            resource_id=resource_id,
            risk_level=risk_level,
            approval_present=False,
            requested_permissions=[action_type],
            security_scope=scope,
            context=context or {},
        )
    )
    if not isinstance(decision, PolicyDecision):
        raise TypeError("policy adapter returned a non-PolicyDecision value")
    if not decision.allow:
        raise PermissionError(decision.reason)
    return decision


def emit_explanation_telemetry(
    telemetry_service: object | None,
    *,
    event_type: str,
    node_type: str,
    node_id: str,
    intensity: float,
    trace_id: str | None,
    owner_scope: list[str],
    payload: dict[str, object] | None = None,
) -> None:
    """Emit explanation visual telemetry."""

    emit_telemetry(
        telemetry_service,
        event_type=event_type,
        node_type=node_type,
        node_id=node_id,
        intensity=clamp(intensity),
        trace_id=trace_id,
        payload={"owner_scope": owner_scope, **(payload or {})},
    )


def emit_raw_telemetry(
    telemetry_service: object | None,
    event: VisualTelemetryEvent,
) -> None:
    """Best-effort raw telemetry emit for test fakes."""

    emit = getattr(telemetry_service, "emit", None)
    if callable(emit):
        try:
            emit(event)
        except Exception:
            return


def clamp(value: float) -> float:
    """Clamp a confidence or intensity value to 0..1."""

    return max(0.0, min(1.0, value))


def now_utc() -> datetime:
    """Return the current UTC time."""

    return datetime.now(UTC)


def safe_call(
    source: object | None, method_names: tuple[str, ...], *args: Any, **kwargs: Any
) -> Any:
    """Call the first available method on a source and swallow lookup failures."""

    for name in method_names:
        method = getattr(source, name, None)
        if not callable(method):
            continue
        try:
            return method(*args, **kwargs)
        except TypeError:
            try:
                return method(*args)
            except Exception:
                continue
        except Exception:
            continue
    return None


def items_from_source(
    source: object | None,
    method_names: tuple[str, ...],
    *args: Any,
    **kwargs: Any,
) -> list[Any]:
    """Return a list from a tolerant source method call."""

    result = safe_call(source, method_names, *args, **kwargs)
    if result is None:
        return []
    if isinstance(result, list):
        return result
    if isinstance(result, tuple):
        return list(result)
    return [result]


def string_refs(value: Any) -> list[str]:
    """Convert list-like refs into strings."""

    if isinstance(value, list):
        return [str(item) for item in value if item is not None]
    if isinstance(value, tuple):
        return [str(item) for item in value if item is not None]
    if isinstance(value, str) and value:
        return [value]
    return []


def unique(values: list[str]) -> list[str]:
    """Return stable unique non-empty strings."""

    return list(dict.fromkeys(value for value in values if value))


def object_id(value: object, *names: str) -> str | None:
    """Return the first string id from object attributes or dict keys."""

    if isinstance(value, dict):
        for name in names:
            raw = value.get(name)
            if raw:
                return str(raw)
        return None
    for name in names:
        raw = getattr(value, name, None)
        if raw:
            return str(raw)
    return None


def object_value(value: object, name: str, default: Any = None) -> Any:
    """Return an attribute or dict value."""

    if isinstance(value, dict):
        return value.get(name, default)
    return getattr(value, name, default)


def refs_from_object(value: object | None, *names: str) -> list[str]:
    """Extract refs from an object or dict."""

    if value is None:
        return []
    refs: list[str] = []
    for name in names:
        refs.extend(string_refs(object_value(value, name, [])))
    return unique(refs)


def payload_scope(payload: dict[str, Any], fallback: list[str]) -> list[str]:
    """Return owner scope from metadata-like payload."""

    for key in ("owner_scope", "security_scope", "scope", "resolved_security_scope"):
        value = payload.get(key)
        if isinstance(value, list) and value:
            return [str(item) for item in value]
    return fallback


__all__ = [
    "authorize",
    "clamp",
    "emit_explanation_telemetry",
    "emit_raw_telemetry",
    "items_from_source",
    "now_utc",
    "object_id",
    "object_value",
    "payload_scope",
    "refs_from_object",
    "safe_call",
    "string_refs",
    "unique",
]
