"""Blocker helpers for disabled production auth runtime."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from aion_brain.contracts.auth_runtime import AuthRuntimeBlocker, utc_now

_FINDING_TO_BLOCKER = {
    "secret_detected": "secret_detected",
    "raw_prompt_detected": "unsafe_claims",
    "hidden_reasoning_detected": "unsafe_claims",
    "unsafe_payload": "unsafe_claims",
}
_FINDING_REASONS = {
    "secret_detected": "protected_material_detected",
    "raw_prompt_detected": "unsafe_payload_text_detected",
    "hidden_reasoning_detected": "unsafe_reasoning_material_detected",
    "unsafe_payload": "unsafe_payload_detected",
}


def blocker(
    blocker_type: str,
    reason: str,
    *,
    source_type: str | None = None,
    source_id: str | None = None,
    severity: str = "high",
    recommended_action: str = "Keep production auth runtime disabled.",
    metadata: dict[str, Any] | None = None,
) -> AuthRuntimeBlocker:
    """Create one safe auth-runtime blocker."""

    return AuthRuntimeBlocker(
        auth_runtime_blocker_id=f"auth-runtime-blocker-{uuid4().hex}",
        blocker_type=blocker_type,  # type: ignore[arg-type]
        severity=severity,  # type: ignore[arg-type]
        status="open",
        reason=reason,
        recommended_action=recommended_action,
        source_type=source_type,
        source_id=source_id,
        metadata=metadata or {},
        created_at=utc_now(),
    )


def blockers_for_findings(
    findings: list[dict[str, object]],
    *,
    source_id: str | None = None,
) -> list[AuthRuntimeBlocker]:
    """Map unsafe mock-claims payload findings into blockers."""

    result: list[AuthRuntimeBlocker] = []
    for finding in findings:
        finding_key = str(finding.get("finding") or "unsafe_payload")
        blocker_type = _FINDING_TO_BLOCKER.get(finding_key, "unsafe_claims")
        result.append(
            blocker(
                blocker_type,
                _FINDING_REASONS.get(finding_key, "unsafe_payload_detected"),
                source_type="mock_claims_payload",
                source_id=source_id,
                severity="critical" if blocker_type == "secret_detected" else "high",
                recommended_action="Remove unsafe synthetic claims before previewing.",
            )
        )
    return result


__all__ = ["blocker", "blockers_for_findings"]
