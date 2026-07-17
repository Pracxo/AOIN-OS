from __future__ import annotations

import time

from aion_brain.production_auth.identity_assertion_verifier import (
    OfflineEd25519IdentityAssertionVerifier,
)
from aion_brain.production_auth.trusted_public_keys import TrustedPublicKeyRegistry
from tests.test_identity_assertion_contracts import NOW, make_envelope, make_key_pair, make_policy


def test_performance_smoke_for_valid_invalid_and_lookup() -> None:
    signing_material, public_key = make_key_pair()
    registry = TrustedPublicKeyRegistry((public_key,))
    verifier = OfflineEd25519IdentityAssertionVerifier(
        public_keys=registry,
        policy=make_policy(),
        clock=lambda: NOW,
    )
    valid = make_envelope(signing_material)
    invalid = valid.model_copy(update={"signature": "A" + valid.signature[1:]})

    start = time.perf_counter()
    for _ in range(1000):
        assert verifier.verify(valid).result.verified is True
    valid_seconds = time.perf_counter() - start

    start = time.perf_counter()
    for _ in range(1000):
        assert verifier.verify(invalid).result.rejected is True
    invalid_seconds = time.perf_counter() - start

    start = time.perf_counter()
    for _ in range(1000):
        assert registry.resolve("key-001", "issuer.aion.local", NOW) == public_key
    lookup_seconds = time.perf_counter() - start

    assert valid_seconds < 30
    assert invalid_seconds < 30
    assert lookup_seconds < 5
