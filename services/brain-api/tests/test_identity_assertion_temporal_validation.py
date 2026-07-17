from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from aion_brain.production_auth.identity_assertion_verifier import (
    OfflineEd25519IdentityAssertionVerifier,
)
from tests.test_identity_assertion_contracts import (
    NOW,
    make_envelope,
    make_key_pair,
    make_payload,
    make_policy,
)


def test_payload_rejects_naive_and_non_utc_datetimes() -> None:
    with pytest.raises(ValidationError):
        make_payload(issued_at=datetime(2026, 7, 17, 12, 0))
    with pytest.raises(ValidationError):
        make_payload(issued_at=datetime(2026, 7, 17, 13, 0, tzinfo=timezone(timedelta(hours=1))))


def test_payload_rejects_bad_ordering_and_excessive_lifetime() -> None:
    with pytest.raises(ValidationError):
        make_payload(issued_at=NOW + timedelta(seconds=1), not_before=NOW)
    with pytest.raises(ValidationError):
        make_payload(expires_at=NOW + timedelta(seconds=301))


@pytest.mark.parametrize(
    ("payload_kwargs", "reason"),
    [
        (
            {
                "issued_at": NOW + timedelta(seconds=31),
                "not_before": NOW + timedelta(seconds=31),
                "expires_at": NOW + timedelta(seconds=120),
            },
            "future_issued_at",
        ),
        (
            {
                "not_before": NOW + timedelta(seconds=31),
                "expires_at": NOW + timedelta(seconds=120),
            },
            "not_yet_valid",
        ),
        (
            {
                "issued_at": NOW - timedelta(seconds=300),
                "not_before": NOW - timedelta(seconds=300),
                "expires_at": NOW - timedelta(seconds=31),
            },
            "assertion_expired",
        ),
    ],
)
def test_verifier_temporal_rejections(payload_kwargs: dict[str, object], reason: str) -> None:
    signing_material, public_key = make_key_pair()
    payload = make_payload(**payload_kwargs)
    verifier = OfflineEd25519IdentityAssertionVerifier(
        public_keys=(public_key,),
        policy=make_policy(),
        clock=lambda: NOW,
    )
    bundle = verifier.verify(make_envelope(signing_material, payload))
    assert bundle.result.primary_reason_code == reason


def test_verifier_rejects_naive_clock() -> None:
    signing_material, public_key = make_key_pair()
    verifier = OfflineEd25519IdentityAssertionVerifier(
        public_keys=(public_key,),
        policy=make_policy(),
        clock=lambda: datetime(2026, 7, 17, 12, 0),
    )
    with pytest.raises(ValueError):
        verifier.verify(make_envelope(signing_material))


def test_utc_datetime_normalizes_to_utc() -> None:
    payload = make_payload(issued_at=datetime(2026, 7, 17, 12, 0, tzinfo=UTC))
    assert payload.issued_at.tzinfo is UTC
