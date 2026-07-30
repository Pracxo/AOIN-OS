from __future__ import annotations

import pytest

from aion_brain.contracts.secure_runtime import bind_verified_local_operator_identity
from tests.secure_runtime_test_support import (
    build_identity_pipeline,
    make_authorization,
    make_signed_assertion,
    secure_runtime_fixture,
)


def test_identity_binding_uses_real_pipeline_once_and_redacts_material() -> None:
    fixture = secure_runtime_fixture()

    assert fixture.operator_identity.cryptographic_verification_passed is True
    assert fixture.operator_identity.replay_validation_passed is True
    assert fixture.operator_identity.local_operator_authenticated is True
    assert fixture.operator_identity.production_request_authenticated is False
    assert fixture.operator_identity.redacted is True


def test_identity_binding_rejects_assertion_fingerprint_mismatch() -> None:
    pipeline, signing_material = build_identity_pipeline()
    assertion = make_signed_assertion(signing_material)
    authorization = make_authorization(assertion).model_copy(
        update={"assertion_fingerprint": "1" * 64}
    )

    with pytest.raises(ValueError, match="assertion fingerprint mismatch"):
        bind_verified_local_operator_identity(
            authorization_envelope=authorization,
            assertion_envelope=assertion,
            verification_pipeline=pipeline,
        )
