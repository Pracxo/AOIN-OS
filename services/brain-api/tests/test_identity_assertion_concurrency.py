from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from aion_brain.production_auth.identity_assertion_verifier import (
    OfflineEd25519IdentityAssertionVerifier,
)
from tests.test_identity_assertion_contracts import NOW, make_envelope, make_key_pair, make_policy


def test_concurrent_verifications_are_independent() -> None:
    signing_material, public_key = make_key_pair()
    verifier = OfflineEd25519IdentityAssertionVerifier(
        public_keys=(public_key,),
        policy=make_policy(),
        clock=lambda: NOW,
    )
    envelope = make_envelope(signing_material)

    with ThreadPoolExecutor(max_workers=8) as executor:
        bundles = list(executor.map(lambda _index: verifier.verify(envelope), range(32)))

    assert all(bundle.result.verified for bundle in bundles)
    assert len({bundle.result.verification_id for bundle in bundles}) == 32
    assert len({id(bundle.audit_event) for bundle in bundles}) == 32
    assert verifier.public_key_registry.key_ids() == ("key-001",)


def test_concurrent_invalid_verifications_are_independent() -> None:
    signing_material, public_key = make_key_pair()
    verifier = OfflineEd25519IdentityAssertionVerifier(
        public_keys=(public_key,),
        policy=make_policy(),
        clock=lambda: NOW,
    )
    envelope = make_envelope(signing_material).model_copy(update={"signature": "AAAA"})

    with ThreadPoolExecutor(max_workers=8) as executor:
        bundles = list(executor.map(lambda _index: verifier.verify(envelope), range(32)))

    assert all(bundle.result.rejected for bundle in bundles)
    assert len({bundle.result.verification_id for bundle in bundles}) == 32
