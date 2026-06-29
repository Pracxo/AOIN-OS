"""Blocker helpers for disabled external connector runtime."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from aion_brain.contracts.connector_runtime import ConnectorRuntimeBlocker, utc_now

_FINDING_TO_BLOCKER = {
    "secret_detected": "unsafe_payload",
    "raw_prompt_detected": "unsafe_payload",
    "hidden_reasoning_detected": "unsafe_payload",
    "unsafe_payload": "unsafe_payload",
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
    recommended_action: str = "Keep connector runtime disabled.",
    metadata: dict[str, Any] | None = None,
) -> ConnectorRuntimeBlocker:
    """Create one safe connector-runtime blocker."""

    return ConnectorRuntimeBlocker(
        connector_runtime_blocker_id=f"connector-runtime-blocker-{uuid4().hex}",
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
) -> list[ConnectorRuntimeBlocker]:
    """Map unsafe preview findings into connector-runtime blockers."""

    result: list[ConnectorRuntimeBlocker] = []
    for finding in findings:
        finding_key = str(finding.get("finding") or "unsafe_payload")
        blocker_type = _FINDING_TO_BLOCKER.get(finding_key, "unsafe_payload")
        result.append(
            blocker(
                blocker_type,
                _FINDING_REASONS.get(finding_key, "unsafe_payload_detected"),
                source_type="connector_runtime_payload",
                source_id=source_id,
                severity="critical" if finding_key == "secret_detected" else "high",
                recommended_action="Remove unsafe synthetic connector payload before previewing.",
            )
        )
    return result


def disabled_runtime_blockers() -> list[ConnectorRuntimeBlocker]:
    """Return standard hard-off connector runtime blockers."""

    return [
        blocker(
            "connector_runtime_disabled",
            "connector_runtime_disabled_by_default",
            source_type="settings",
            severity="critical",
            recommended_action="Complete connector runtime release gates before enabling.",
        ),
        blocker("external_calls_disabled", "external_calls_disabled", source_type="settings"),
        blocker("credentials_disabled", "connector_credentials_disabled", source_type="settings"),
        blocker(
            "token_storage_disabled",
            "connector_token_storage_disabled",
            source_type="settings",
        ),
        blocker("activation_disabled", "connector_activation_disabled", source_type="settings"),
        blocker(
            "route_registration_disabled",
            "connector_route_registration_disabled",
            source_type="settings",
        ),
    ]


__all__ = ["blocker", "blockers_for_findings", "disabled_runtime_blockers"]
