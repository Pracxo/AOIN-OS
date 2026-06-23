"""Redaction helpers for governed operator action requests."""

from __future__ import annotations

from typing import Any

from aion_brain.model_outputs.redaction import redact_output_payload


def redact_operator_action_payload(
    payload: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Redact payload before it enters an operator action request record."""

    return redact_output_payload(payload)


__all__ = ["redact_operator_action_payload"]
