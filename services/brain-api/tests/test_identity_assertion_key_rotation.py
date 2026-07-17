from __future__ import annotations

from datetime import timedelta

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


def test_rotation_selects_exact_key_id() -> None:
    old_signing, old_key = make_key_pair(
        key_id="key-old",
        active_from=NOW - timedelta(days=10),
        active_until=NOW - timedelta(days=1),
    )
    new_signing, new_key = make_key_pair(
        key_id="key-new",
        active_from=NOW - timedelta(days=1),
        active_until=NOW + timedelta(days=10),
    )
    verifier = OfflineEd25519IdentityAssertionVerifier(
        public_keys=(old_key, new_key),
        policy=make_policy(),
        clock=lambda: NOW,
    )

    valid = verifier.verify(make_envelope(new_signing, key_id="key-new"))
    retired = verifier.verify(
        make_envelope(
            old_signing,
            make_payload(issued_at=NOW, not_before=NOW),
            key_id="key-old",
        )
    )

    assert valid.result.verified is True
    assert retired.result.primary_reason_code == "public_key_retired"


def test_revoked_key_fails_even_inside_active_window() -> None:
    signing_material, public_key = make_key_pair(revoked=True)
    verifier = OfflineEd25519IdentityAssertionVerifier(
        public_keys=(public_key,),
        policy=make_policy(),
        clock=lambda: NOW,
    )
    bundle = verifier.verify(make_envelope(signing_material))
    assert bundle.result.primary_reason_code == "public_key_revoked"
