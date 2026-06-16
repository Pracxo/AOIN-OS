from __future__ import annotations

from datetime import timedelta

import pytest
from pydantic import ValidationError

from aion_brain.contracts.temporal_state import (
    StateAtom,
    StateAtomCreateRequest,
    TemporalStateWindowRequest,
)
from tests.situation_helpers import now


def test_state_atom_validates_source_predicate_confidence_and_scope() -> None:
    with pytest.raises(ValidationError):
        StateAtom(
            state_atom_id="atom-1",
            source_id="source-1",
            predicate="",
            value={},
            confidence=0.5,
            observed_at=now(),
            owner_scope=["workspace:main"],
        )


def test_state_atom_create_rejects_secret_values() -> None:
    with pytest.raises(ValidationError):
        StateAtomCreateRequest(
            source_id="source-1",
            predicate="status",
            value={"token": "hidden"},
            owner_scope=["workspace:main"],
        )


def test_temporal_window_requires_ordered_range() -> None:
    timestamp = now()
    with pytest.raises(ValidationError):
        TemporalStateWindowRequest(
            owner_scope=["workspace:main"],
            start_at=timestamp,
            end_at=timestamp - timedelta(minutes=1),
        )
