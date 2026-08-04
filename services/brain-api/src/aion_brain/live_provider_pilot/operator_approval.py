"""Operator approval records for AION-248."""

from __future__ import annotations

from datetime import datetime

from aion_brain.contracts.live_provider_pilot import (
    PILOT_CONFIRMATION_TEXT,
    LiveProviderModelSelection,
    LiveProviderOperatorApproval,
    content_fingerprint,
)


def create_operator_approval(
    *,
    approval_id: str,
    confirmation_text: str,
    selection: LiveProviderModelSelection,
    created_at: datetime,
) -> LiveProviderOperatorApproval:
    """Record operator approval using only fingerprints."""

    if confirmation_text != PILOT_CONFIRMATION_TEXT:
        raise ValueError("operator confirmation text mismatch")
    return LiveProviderOperatorApproval(
        approval_id=approval_id,
        confirmation_text_fingerprint=content_fingerprint(
            "live_provider_confirmation", confirmation_text
        ),
        selected_model_fingerprint=selection.selection_fingerprint or "",
        created_at=created_at,
    )
