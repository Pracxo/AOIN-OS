"""Redaction helpers for scheduler-created local records."""

from __future__ import annotations

from typing import Any, cast

from aion_brain.notifications.redaction import redact_payload, redact_text


def scheduler_safe_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a redacted copy safe for notifications, telemetry, and audit."""

    return cast(dict[str, Any], redact_payload(payload))


def scheduler_safe_text(value: str) -> str:
    """Return a redacted scheduler text value."""

    return redact_text(value)
