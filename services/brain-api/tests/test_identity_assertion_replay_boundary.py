from __future__ import annotations

from aion_brain.production_auth.identity_assertion_verifier import (
    OfflineEd25519IdentityAssertionVerifier,
)
from tests.test_identity_assertion_contracts import NOW, make_envelope, make_key_pair, make_policy


def test_repeat_verification_is_allowed_without_replay_state() -> None:
    signing_material, public_key = make_key_pair()
    verifier = OfflineEd25519IdentityAssertionVerifier(
        public_keys=(public_key,),
        policy=make_policy(),
        clock=lambda: NOW,
    )
    envelope = make_envelope(signing_material)

    first = verifier.verify(envelope)
    second = verifier.verify(envelope)

    assert first.result.verified is True
    assert second.result.verified is True
    assert first.result.replay_check_performed is False
    assert second.result.replay_check_performed is False
    assert first.result.replay_protection_required_before_request_integration is True
    assert second.result.replay_protection_required_before_request_integration is True
    assert first.result.verification_id != second.result.verification_id
