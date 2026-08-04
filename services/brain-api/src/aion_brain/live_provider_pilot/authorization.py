"""Authorization helpers for AION-248."""

from __future__ import annotations

from aion_brain.contracts.live_provider_pilot import (
    AUTHORIZATION_TRANSACTION_ID,
    LiveProviderAuthorizationEnvelope,
)


def create_authorization_envelope() -> LiveProviderAuthorizationEnvelope:
    """Create the exact active AION-247-AI-0002 envelope."""

    return LiveProviderAuthorizationEnvelope()


def validate_authorization(
    envelope: LiveProviderAuthorizationEnvelope,
) -> LiveProviderAuthorizationEnvelope:
    """Fail closed unless the envelope is the exact AION-248 authorization."""

    if envelope.authorization_transaction_id != AUTHORIZATION_TRANSACTION_ID:
        raise ValueError("live-provider authorization mismatch")
    return envelope
