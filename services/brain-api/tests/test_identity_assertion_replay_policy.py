from __future__ import annotations

from datetime import timedelta

import pytest
from pydantic import ValidationError

from aion_brain.contracts.identity_assertion_replay import (
    DEFAULT_ALLOWED_CLOCK_SKEW_SECONDS,
    DEFAULT_CLEANUP_BATCH_SIZE,
    DEFAULT_MAXIMUM_RETENTION_SECONDS,
    DEFAULT_MINIMUM_RETENTION_SECONDS,
    IdentityAssertionReplayPolicy,
)
from aion_brain.production_auth.identity_assertion_replay import (
    compute_identity_assertion_retain_until,
)
from tests.test_identity_assertion_replay_contracts import NOW


def test_replay_policy_defaults_are_authorized() -> None:
    policy = IdentityAssertionReplayPolicy()
    assert policy.minimum_retention_seconds == DEFAULT_MINIMUM_RETENTION_SECONDS
    assert policy.maximum_retention_seconds == DEFAULT_MAXIMUM_RETENTION_SECONDS
    assert policy.cleanup_batch_size == DEFAULT_CLEANUP_BATCH_SIZE
    assert policy.allowed_clock_skew_seconds == DEFAULT_ALLOWED_CLOCK_SKEW_SECONDS


def test_replay_policy_rejects_invalid_ranges() -> None:
    with pytest.raises(ValidationError):
        IdentityAssertionReplayPolicy(minimum_retention_seconds=299)
    with pytest.raises(ValidationError):
        IdentityAssertionReplayPolicy(maximum_retention_seconds=2_592_001)
    with pytest.raises(ValidationError):
        IdentityAssertionReplayPolicy(cleanup_batch_size=0)
    with pytest.raises(ValidationError):
        IdentityAssertionReplayPolicy(allowed_clock_skew_seconds=31)
    with pytest.raises(ValidationError):
        IdentityAssertionReplayPolicy(
            minimum_retention_seconds=604800,
            maximum_retention_seconds=300,
        )


def test_retain_until_uses_expiry_plus_skew_and_minimum_retention() -> None:
    policy = IdentityAssertionReplayPolicy(minimum_retention_seconds=86400)
    retain_until = compute_identity_assertion_retain_until(
        claimed_at=NOW,
        assertion_expires_at=NOW + timedelta(minutes=5),
        policy=policy,
    )
    assert retain_until == NOW + timedelta(seconds=policy.minimum_retention_seconds)


def test_retain_until_fails_when_maximum_would_be_exceeded() -> None:
    policy = IdentityAssertionReplayPolicy(
        minimum_retention_seconds=300,
        maximum_retention_seconds=300,
        allowed_clock_skew_seconds=30,
    )
    with pytest.raises(ValueError, match="retention exceeds maximum"):
        compute_identity_assertion_retain_until(
            claimed_at=NOW,
            assertion_expires_at=NOW + timedelta(minutes=6),
            policy=policy,
        )
