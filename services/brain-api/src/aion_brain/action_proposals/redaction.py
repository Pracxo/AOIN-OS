"""Payload redaction for action proposals and execution handoffs."""

from __future__ import annotations

from typing import Any

from aion_brain.model_outputs.redaction import redact_output_payload


def redact_action_payload(payload: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Redact proposal or handoff payloads without retaining removed values."""

    redacted, findings = redact_output_payload(payload)
    return redacted, findings


__all__ = ["redact_action_payload"]
