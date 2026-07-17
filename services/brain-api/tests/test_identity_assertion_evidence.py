from __future__ import annotations

import pytest
from pydantic import ValidationError

from aion_brain.contracts.identity_assertion import (
    IdentityAssertionVerificationResult,
    validate_reason_codes,
)
from aion_brain.production_auth.identity_assertion_verifier import (
    OfflineEd25519IdentityAssertionVerifier,
)
from tests.test_identity_assertion_contracts import NOW, make_envelope, make_key_pair, make_policy


def test_evidence_is_redacted_and_fingerprinted() -> None:
    signing_material, public_key = make_key_pair()
    verifier = OfflineEd25519IdentityAssertionVerifier(
        public_keys=(public_key,),
        policy=make_policy(),
        clock=lambda: NOW,
        id_factory=lambda slot: f"{slot}-evidence",
    )
    bundle = verifier.verify(make_envelope(signing_material))

    assert bundle.fingerprint and len(bundle.fingerprint) == 64
    assert bundle.result.fingerprint and len(bundle.result.fingerprint) == 64
    rendered = bundle.model_dump_json()
    for forbidden in (
        "subject-001",
        "actor-001",
        "workspace-001",
        "operator",
        "viewer",
        "read:evidence",
        "offline:verify",
    ):
        assert forbidden not in rendered


def test_unknown_reason_code_and_mismatched_fingerprint_rejected() -> None:
    with pytest.raises(ValueError):
        validate_reason_codes(("unknown",))  # type: ignore[arg-type]
    signing_material, public_key = make_key_pair()
    verifier = OfflineEd25519IdentityAssertionVerifier(
        public_keys=(public_key,),
        policy=make_policy(),
        clock=lambda: NOW,
    )
    result = verifier.verify(make_envelope(signing_material)).result
    payload = result.model_dump(mode="python")
    payload["fingerprint"] = "0" * 64
    with pytest.raises(ValidationError):
        IdentityAssertionVerificationResult(**payload)
