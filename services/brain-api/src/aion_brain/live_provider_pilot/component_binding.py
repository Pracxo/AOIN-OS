"""Component lineage bindings for the AION-248 pilot."""

from __future__ import annotations

from datetime import datetime

from aion_brain.contracts.live_provider_pilot import (
    LiveProviderComponentBinding,
    ensure_sha256,
)


def bind_components(
    *,
    binding_id: str,
    external_cognition_component_fingerprint: str,
    existing_model_gateway_component_fingerprint: str,
    operator_identity_fingerprint: str,
    created_at: datetime,
) -> LiveProviderComponentBinding:
    """Bind external cognition and the existing model gateway by fingerprint only."""

    return LiveProviderComponentBinding(
        binding_id=binding_id,
        external_cognition_component_fingerprint=ensure_sha256(
            external_cognition_component_fingerprint
        ),
        existing_model_gateway_component_fingerprint=ensure_sha256(
            existing_model_gateway_component_fingerprint
        ),
        operator_identity_fingerprint=ensure_sha256(operator_identity_fingerprint),
        created_at=created_at,
    )
