"""Observability contract tests."""

import pytest
from pydantic import ValidationError

from aion_brain.contracts.observability import ObservabilityEvent


def test_observability_event_rejects_empty_fields_and_secrets() -> None:
    """Observability contracts reject empty fields and secret-like payload keys."""
    with pytest.raises(ValidationError):
        event(message="")
    with pytest.raises(ValidationError):
        event(payload={"nested": {"api_key": "not-allowed"}})


def event(**updates: object) -> ObservabilityEvent:
    values = {
        "observability_event_id": "obs-1",
        "trace_id": "trace-1",
        "correlation_id": "corr-1",
        "event_type": "brain_loop_started",
        "component": "brain_loop",
        "level": "info",
        "message": "Started.",
        "payload": {},
        "created_at": None,
        **updates,
    }
    return ObservabilityEvent.model_validate(values)
