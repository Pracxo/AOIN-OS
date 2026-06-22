"""Autonomy mode helper tests."""

import pytest

from aion_brain.autonomy.modes import (
    min_mode,
    mode_allows,
    mode_rank,
    risk_allows,
    risk_rank,
)


def test_mode_order_prevents_escalation_past_ceiling() -> None:
    """Mode ranking is monotonic from disabled to delegated control."""
    assert mode_rank("disabled") < mode_rank("dry_run")
    assert min_mode("supervised_controlled", "dry_run") == "dry_run"
    assert mode_allows("dry_run", "dry_run") is True
    assert mode_allows("supervised_controlled", "dry_run") is False


def test_risk_order_prevents_escalation_past_ceiling() -> None:
    """Risk ranking is monotonic from low to critical."""
    assert risk_rank("low") < risk_rank("critical")
    assert risk_allows("medium", "medium") is True
    assert risk_allows("high", "medium") is False


def test_unknown_mode_or_risk_fails_closed() -> None:
    """Unknown vocabulary raises instead of silently allowing."""
    with pytest.raises(ValueError):
        mode_rank("autopilot")
    with pytest.raises(ValueError):
        risk_rank("unknown")
