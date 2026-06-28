"""Blocker helpers for dry-run action authorization."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from aion_brain.contracts.action_authorization import ActionAuthorizationBlocker, utc_now

_FINDING_TO_BLOCKER = {
    "raw_prompt_detected": "raw_prompt_detected",
    "hidden_reasoning_detected": "hidden_reasoning_detected",
    "secret_detected": "secret_detected",
}
_FINDING_REASONS = {
    "raw_prompt_detected": "unsafe_payload_text_detected",
    "hidden_reasoning_detected": "unsafe_reasoning_material_detected",
    "secret_detected": "protected_material_detected",
}


def blocker(
    blocker_type: str,
    reason: str,
    *,
    trace_id: str | None = None,
    source_type: str | None = None,
    source_id: str | None = None,
    severity: str = "high",
    recommended_action: str = "Use dry-run authorization records only.",
    metadata: dict[str, Any] | None = None,
) -> ActionAuthorizationBlocker:
    """Create one safe authorization blocker."""

    return ActionAuthorizationBlocker(
        authz_blocker_id=f"action-authorization-blocker-{uuid4().hex}",
        trace_id=trace_id,
        source_type=source_type,
        source_id=source_id,
        blocker_type=blocker_type,  # type: ignore[arg-type]
        severity=severity,  # type: ignore[arg-type]
        status="open",
        reason=reason,
        recommended_action=recommended_action,
        metadata=metadata or {},
        created_at=utc_now(),
    )


def blockers_for_findings(
    findings: list[dict[str, object]],
    *,
    trace_id: str | None = None,
    source_id: str | None = None,
) -> list[ActionAuthorizationBlocker]:
    """Map unsafe payload findings to safe authorization blockers."""

    result: list[ActionAuthorizationBlocker] = []
    for finding in findings:
        finding_key = str(finding.get("finding") or "unsafe_payload")
        blocker_type = _FINDING_TO_BLOCKER.get(finding_key, "unsafe_payload")
        result.append(
            blocker(
                blocker_type,
                _FINDING_REASONS.get(finding_key, "unsafe_payload_detected"),
                trace_id=trace_id,
                source_type="authorization_payload",
                source_id=source_id,
                severity="critical" if blocker_type == "secret_detected" else "high",
                recommended_action=(
                    "Remove unsafe payload material before requesting authorization."
                ),
            )
        )
    return result


__all__ = ["blocker", "blockers_for_findings"]
