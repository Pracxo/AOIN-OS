"""Payload safety helpers for run supervision."""

from __future__ import annotations

from typing import Any

from aion_brain.contracts.model_outputs import reject_secret_like_payload


def ensure_payload_safe(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate a payload and return it unchanged."""

    reject_secret_like_payload(payload)
    return payload


__all__ = ["ensure_payload_safe"]
