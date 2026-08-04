"""Provider and model selection for AION-248."""

from __future__ import annotations

from datetime import datetime

from aion_brain.contracts.live_provider_pilot import (
    SELECTED_MODEL_ID,
    LiveProviderModelSelection,
    validate_model_candidate,
    validate_selected_model,
)


def select_model(
    *,
    selection_id: str,
    model_id: str,
    created_at: datetime,
) -> LiveProviderModelSelection:
    """Create a bound model-selection record for the exact pilot model."""

    validate_selected_model(model_id)
    return LiveProviderModelSelection(
        selection_id=selection_id,
        selected_model_id=model_id,
        created_at=created_at,
    )


def reject_unapproved_model(model_id: str) -> None:
    """Reject aliases and models outside the approved GPT-5.6 set."""

    validate_model_candidate(model_id)
    if model_id != SELECTED_MODEL_ID:
        raise ValueError("AION-248 can execute only gpt-5.6-terra")


def reject_model_switch(*, existing_model_id: str, requested_model_id: str) -> None:
    """Fail closed when a session attempts to switch models after start."""

    if existing_model_id != requested_model_id:
        raise ValueError("model switch after live-provider session start is rejected")
