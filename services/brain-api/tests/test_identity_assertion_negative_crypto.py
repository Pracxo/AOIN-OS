from __future__ import annotations

import pytest

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


@pytest.mark.parametrize(
    ("mutation", "reason"),
    [
        ("payload", "signature_invalid"),
        ("wrong_key", "signature_invalid"),
        ("unknown_key", "public_key_unknown"),
        ("issuer_mismatch", "issuer_mismatch"),
        ("audience_mismatch", "audience_mismatch"),
    ],
)
def test_negative_crypto_paths_fail_closed(mutation: str, reason: str) -> None:
    signing_material, public_key = make_key_pair()
    other_signing, other_public_key = make_key_pair(key_id="key-002")
    if mutation == "wrong_key":
        registry = (other_public_key.model_copy(update={"key_id": "key-001"}),)
    elif mutation == "issuer_mismatch":
        registry = (public_key.model_copy(update={"issuer": "issuer.other"}),)
    else:
        registry = (public_key,)
    payload = make_payload()
    key_id = "missing" if mutation == "unknown_key" else "key-001"
    if mutation == "payload":
        envelope = make_envelope(signing_material)
        envelope = envelope.model_copy(update={"payload": make_payload(subject="subject-002")})
    elif mutation == "issuer_mismatch":
        payload = make_payload(issuer="issuer.other")
        envelope = make_envelope(signing_material, payload)
    elif mutation == "audience_mismatch":
        payload = make_payload(audience="other-audience")
        envelope = make_envelope(signing_material, payload)
    elif mutation == "wrong_key":
        envelope = make_envelope(signing_material, payload, key_id=key_id)
    else:
        envelope = make_envelope(signing_material, payload, key_id=key_id)
    verifier = OfflineEd25519IdentityAssertionVerifier(
        public_keys=registry,
        policy=make_policy(),
        clock=lambda: NOW,
    )

    bundle = verifier.verify(envelope)

    assert bundle.result.rejected is True
    assert bundle.result.primary_reason_code == reason
    rendered = bundle.model_dump_json()
    for forbidden in (
        "subject-001",
        "actor-001",
        "workspace-001",
        "read:evidence",
        "offline:verify",
    ):
        assert forbidden not in rendered


def test_malformed_signature_rejected_without_sensitive_error() -> None:
    signing_material, public_key = make_key_pair()
    verifier = OfflineEd25519IdentityAssertionVerifier(
        public_keys=(public_key,),
        policy=make_policy(),
        clock=lambda: NOW,
    )
    envelope = make_envelope(signing_material).model_copy(update={"signature": "AAAA"})
    bundle = verifier.verify(envelope)
    assert bundle.result.primary_reason_code == "malformed_envelope"
