"""Replay-key derivation for offline identity assertions."""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta

from aion_brain.contracts.identity_assertion import normalize_utc_datetime
from aion_brain.contracts.identity_assertion_replay import (
    ISSUER_FINGERPRINT_SCHEMA_VERSION,
    REPLAY_KEY_DOMAIN_SEPARATOR,
    REPLAY_KEY_SCHEMA_VERSION,
    IdentityAssertionReplayPolicy,
)
from aion_brain.production_auth.canonical import canonical_json_bytes, sha256_fingerprint

REPLAY_DOMAIN_SEPARATOR = REPLAY_KEY_DOMAIN_SEPARATOR


def derive_identity_assertion_replay_key(*, issuer: str, assertion_id: str) -> str:
    """Derive a domain-separated replay key from issuer and assertion ID only."""

    replay_input = {
        "schema_version": REPLAY_KEY_SCHEMA_VERSION,
        "issuer": issuer,
        "assertion_id": assertion_id,
    }
    return hashlib.sha256(
        REPLAY_KEY_DOMAIN_SEPARATOR + canonical_json_bytes(replay_input)
    ).hexdigest()


def derive_identity_assertion_issuer_fingerprint(*, issuer: str) -> str:
    """Fingerprint the issuer without persisting raw issuer text."""

    return sha256_fingerprint(
        {
            "schema_version": ISSUER_FINGERPRINT_SCHEMA_VERSION,
            "issuer": issuer,
        }
    )


def compute_identity_assertion_retain_until(
    *,
    claimed_at: datetime,
    assertion_expires_at: datetime,
    policy: IdentityAssertionReplayPolicy,
) -> datetime:
    """Compute retention through expiry plus skew and the minimum replay window."""

    safe_claimed_at = normalize_utc_datetime(claimed_at)
    safe_assertion_expires_at = normalize_utc_datetime(assertion_expires_at)
    base_retain_until = max(
        safe_assertion_expires_at + timedelta(seconds=policy.allowed_clock_skew_seconds),
        safe_claimed_at + timedelta(seconds=policy.minimum_retention_seconds),
    )
    maximum_allowed = safe_claimed_at + timedelta(seconds=policy.maximum_retention_seconds)
    if base_retain_until > maximum_allowed:
        raise ValueError("identity assertion replay retention exceeds maximum")
    return base_retain_until


__all__ = [
    "REPLAY_DOMAIN_SEPARATOR",
    "compute_identity_assertion_retain_until",
    "derive_identity_assertion_issuer_fingerprint",
    "derive_identity_assertion_replay_key",
]
