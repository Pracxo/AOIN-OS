"""Shared helpers for decision services."""

from __future__ import annotations

from typing import Any

from aion_brain.dialogue._shared import authorize, emit_telemetry

LOW_TO_HIGH_RISK = {"low": 0, "medium": 1, "high": 2, "critical": 3}


def scope_matches(owner_scope: list[str], requested_scope: list[str]) -> bool:
    """Return true when scopes intersect."""
    return bool(set(owner_scope).intersection(set(requested_scope)))


def call_optional(
    target: object | None,
    names: tuple[str, ...],
    *args: object,
    **kwargs: object,
) -> Any:
    """Call the first named method that exists, swallowing integration failures."""
    for name in names:
        method = getattr(target, name, None)
        if callable(method):
            try:
                return method(*args, **kwargs)
            except Exception:
                return None
    return None


def audit_optional(audit_sink: object | None, event_type: str, payload: dict[str, object]) -> None:
    """Record a best-effort audit entry without making decisions depend on audit storage."""
    for name in ("record", "record_event", "append", "add_entry"):
        method = getattr(audit_sink, name, None)
        if callable(method):
            try:
                method(event_type=event_type, payload=payload)
            except TypeError:
                try:
                    method(event_type, payload)
                except Exception:
                    return
            except Exception:
                return
            return


def provenance_optional(
    provenance_service: object | None,
    source_id: str,
    target_id: str,
    relation_type: str,
) -> None:
    """Create a best-effort provenance link."""
    for name in ("create_link", "link", "record_link"):
        method = getattr(provenance_service, name, None)
        if callable(method):
            try:
                method(source_id=source_id, target_id=target_id, relation_type=relation_type)
            except TypeError:
                try:
                    method(source_id, target_id, relation_type)
                except Exception:
                    return
            except Exception:
                return
            return


__all__ = [
    "LOW_TO_HIGH_RISK",
    "audit_optional",
    "authorize",
    "call_optional",
    "emit_telemetry",
    "provenance_optional",
    "scope_matches",
]
