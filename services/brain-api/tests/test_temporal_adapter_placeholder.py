"""Temporal adapter placeholder tests."""

import sys

import pytest

from aion_brain.execution.temporal_adapter import TemporalAdapter


def test_temporal_adapter_is_placeholder_boundary() -> None:
    """Temporal adapter raises and does not import Temporal SDK."""
    with pytest.raises(NotImplementedError):
        TemporalAdapter().execute(None)  # type: ignore[arg-type]

    assert "AION contracts must remain independent" in (TemporalAdapter.__doc__ or "")
    assert "temporalio" not in sys.modules
