from __future__ import annotations

import inspect

from aion_brain.production_auth.identity_assertion_verifier import (
    OfflineEd25519IdentityAssertionVerifier,
)
from tests.test_identity_assertion_contracts import (
    NOW,
    make_envelope,
    make_key_pair,
    make_policy,
    tamper_signature,
)


def test_valid_signature_verifies_without_runtime_authentication() -> None:
    signing_material, public_key = make_key_pair()
    verifier = OfflineEd25519IdentityAssertionVerifier(
        public_keys=(public_key,),
        policy=make_policy(),
        clock=lambda: NOW,
        id_factory=lambda slot: f"{slot}-001",
    )

    bundle = verifier.verify(make_envelope(signing_material))

    assert bundle.result.verified is True
    assert bundle.result.rejected is False
    assert bundle.result.request_authenticated is False
    assert bundle.result.actor_context_applied is False
    assert bundle.result.request_identity_context_applied is False
    assert bundle.result.runtime_effect is False
    assert bundle.result.runtime_integration_allowed is False


def test_signature_tampering_is_rejected_fail_closed() -> None:
    signing_material, public_key = make_key_pair()
    verifier = OfflineEd25519IdentityAssertionVerifier(
        public_keys=(public_key,),
        policy=make_policy(),
        clock=lambda: NOW,
    )
    envelope = make_envelope(signing_material)
    tampered = envelope.model_copy(update={"signature": tamper_signature(envelope.signature)})

    bundle = verifier.verify(tampered)

    assert bundle.result.verified is False
    assert bundle.result.primary_reason_code == "signature_invalid"
    assert "runtime_authentication_disabled" in bundle.result.reason_codes


def test_verifier_has_no_algorithm_parameter() -> None:
    signature = inspect.signature(OfflineEd25519IdentityAssertionVerifier)
    assert "algorithm" not in signature.parameters
    assert "alg" not in signature.parameters
