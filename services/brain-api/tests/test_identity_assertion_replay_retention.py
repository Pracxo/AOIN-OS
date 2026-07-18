from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from aion_brain.contracts.identity_assertion_replay import IdentityAssertionReplayPolicy
from aion_brain.production_auth.identity_assertion_replay import (
    compute_identity_assertion_retain_until,
)
from tests.test_identity_assertion_replay_contracts import NOW


def test_retention_uses_minimum_window_for_short_assertions() -> None:
    policy = IdentityAssertionReplayPolicy(minimum_retention_seconds=86400)
    assert compute_identity_assertion_retain_until(
        claimed_at=NOW,
        assertion_expires_at=NOW + timedelta(minutes=5),
        policy=policy,
    ) == NOW + timedelta(days=1)


def test_retention_includes_expiration_plus_skew() -> None:
    policy = IdentityAssertionReplayPolicy(
        minimum_retention_seconds=300,
        maximum_retention_seconds=604800,
        allowed_clock_skew_seconds=30,
    )
    assert compute_identity_assertion_retain_until(
        claimed_at=NOW,
        assertion_expires_at=NOW + timedelta(minutes=5),
        policy=policy,
    ) == NOW + timedelta(minutes=5, seconds=30)


def test_retention_rejects_naive_datetime_inputs() -> None:
    with pytest.raises(ValueError, match="timezone-aware UTC"):
        compute_identity_assertion_retain_until(
            claimed_at=datetime(2026, 7, 17, 12, 0),
            assertion_expires_at=NOW,
            policy=IdentityAssertionReplayPolicy(),
        )
