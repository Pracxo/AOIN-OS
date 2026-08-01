"""Component-authority binding helpers for the AION-237 local console."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime

from aion_brain.contracts.operator_console_integration import (
    ZERO_FINGERPRINT,
    OperatorConsoleComponentBinding,
    fingerprint_mapping,
    utc_now,
)


def build_component_binding(
    *,
    secure_runtime_session_id: str,
    operator_identity_fingerprint: str,
    actor_context_fingerprint: str,
    secure_runtime_kill_switch_fingerprint: str,
    model_gateway_session_fingerprint: str | None = None,
    model_gateway_provider_manifest_fingerprint: str | None = None,
    model_gateway_model_manifest_fingerprint: str | None = None,
    capability_runtime_session_fingerprint: str | None = None,
    capability_manifest_fingerprint: str | None = None,
    connector_manifest_fingerprint: str | None = None,
    receipt_chain_heads: Mapping[str, str] | None = None,
    audit_chain_heads: Mapping[str, str] | None = None,
    bound_at: datetime | None = None,
) -> OperatorConsoleComponentBinding:
    """Bind AION-231, AION-233, and AION-235 without creating new authority."""

    created_at = bound_at or utc_now()
    return OperatorConsoleComponentBinding(
        secure_runtime_session_id=secure_runtime_session_id,
        secure_runtime_request_identity_fingerprint=operator_identity_fingerprint,
        actor_context_fingerprint=actor_context_fingerprint,
        secure_runtime_kill_switch_fingerprint=secure_runtime_kill_switch_fingerprint,
        model_gateway_session_fingerprint=model_gateway_session_fingerprint
        or fingerprint_mapping("model-gateway-session", {"session": secure_runtime_session_id}),
        model_gateway_provider_manifest_fingerprint=model_gateway_provider_manifest_fingerprint
        or fingerprint_mapping("model-gateway-provider", {"provider": "deterministic-reference"}),
        model_gateway_model_manifest_fingerprint=model_gateway_model_manifest_fingerprint
        or fingerprint_mapping("model-gateway-models", {"models": ["text", "structured_json"]}),
        capability_runtime_session_fingerprint=capability_runtime_session_fingerprint
        or fingerprint_mapping(
            "capability-runtime-session", {"session": secure_runtime_session_id}
        ),
        capability_manifest_fingerprint=capability_manifest_fingerprint
        or fingerprint_mapping("capability-manifest", {"authorized": "reference-only"}),
        connector_manifest_fingerprint=connector_manifest_fingerprint
        or fingerprint_mapping("connector-manifest", {"authorized": "synthetic-only"}),
        receipt_chain_heads=dict(receipt_chain_heads or {"secure_runtime": ZERO_FINGERPRINT}),
        audit_chain_heads=dict(audit_chain_heads or {"operator_console": ZERO_FINGERPRINT}),
        bound_at=created_at,
    )
