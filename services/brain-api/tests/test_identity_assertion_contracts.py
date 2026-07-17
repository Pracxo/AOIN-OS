from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from pydantic import ValidationError

from aion_brain.contracts.identity_assertion import (
    AUTHORIZATION_SCOPE,
    AUTHORIZATION_TRANSACTION_ID,
    DOMAIN_SEPARATOR,
    IMPLEMENTATION_TASK,
    IdentityAssertionEnvelope,
    IdentityAssertionPayload,
    IdentityAssertionVerificationPolicy,
    TrustedIdentityAssertionPublicKey,
)
from aion_brain.production_auth.identity_assertion import (
    encode_base64url_unpadded,
    identity_assertion_signing_input,
)

NOW = datetime(2026, 7, 17, 12, 0, tzinfo=UTC)


def make_payload(**overrides: object) -> IdentityAssertionPayload:
    values: dict[str, object] = {
        "assertion_id": "assertion-001",
        "issuer": "issuer.aion.local",
        "audience": "aion-brain",
        "subject": "subject-001",
        "actor_id": "actor-001",
        "workspace_id": "workspace-001",
        "roles": ("operator", "viewer"),
        "permissions": ("read:evidence",),
        "security_scope": ("offline:verify",),
        "issued_at": NOW,
        "not_before": NOW,
        "expires_at": NOW + timedelta(minutes=5),
        "metadata": {"purpose": "test"},
    }
    values.update(overrides)
    return IdentityAssertionPayload(**values)


def make_key_pair(
    *,
    key_id: str = "key-001",
    issuer: str = "issuer.aion.local",
    active_from: datetime = NOW - timedelta(days=1),
    active_until: datetime | None = NOW + timedelta(days=1),
    revoked: bool = False,
) -> tuple[Ed25519PrivateKey, TrustedIdentityAssertionPublicKey]:
    signing_material = Ed25519PrivateKey.generate()
    public_bytes = signing_material.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return signing_material, TrustedIdentityAssertionPublicKey(
        key_id=key_id,
        issuer=issuer,
        public_key_base64url=encode_base64url_unpadded(public_bytes),
        active_from=active_from,
        active_until=active_until,
        revoked=revoked,
        metadata={"purpose": "test"},
    )


def make_envelope(
    signing_material: Ed25519PrivateKey,
    payload: IdentityAssertionPayload | None = None,
    *,
    key_id: str = "key-001",
    signature: str | None = None,
) -> IdentityAssertionEnvelope:
    selected_payload = payload or make_payload()
    selected_signature = signature or encode_base64url_unpadded(
        signing_material.sign(identity_assertion_signing_input(selected_payload))
    )
    return IdentityAssertionEnvelope(
        key_id=key_id,
        payload=selected_payload,
        signature=selected_signature,
    )


def make_policy(**overrides: object) -> IdentityAssertionVerificationPolicy:
    values = {
        "expected_issuer": "issuer.aion.local",
        "expected_audience": "aion-brain",
    }
    values.update(overrides)
    return IdentityAssertionVerificationPolicy(**values)


def test_contract_constants_match_authorization() -> None:
    assert AUTHORIZATION_TRANSACTION_ID == "AION-161-PA-0006"
    assert IMPLEMENTATION_TASK == "AION-162"
    assert AUTHORIZATION_SCOPE == "offline-ed25519-identity-assertion-verification"
    assert DOMAIN_SEPARATOR == b"AION-IDENTITY-ASSERTION-V1\0"


def test_valid_payload_envelope_and_public_key_pass() -> None:
    signing_material, public_key = make_key_pair()
    payload = make_payload(roles=("viewer", "operator"))
    envelope = make_envelope(signing_material, payload)

    assert payload.roles == ("operator", "viewer")
    assert envelope.payload.assertion_id == "assertion-001"
    assert public_key.key_id == "key-001"


@pytest.mark.parametrize("field", ["alg", "algorithm", "typ", "jwt", "token_type"])
def test_envelope_rejects_algorithm_confusion_fields(field: str) -> None:
    signing_material, _public_key = make_key_pair()
    envelope = make_envelope(signing_material)
    payload = envelope.model_dump(mode="python")
    payload[field] = "EdDSA"
    with pytest.raises(ValidationError):
        IdentityAssertionEnvelope(**payload)


@pytest.mark.parametrize(
    "assertion_id",
    ["", "bad id", "bad/id", "bad\\id", "é", "x" * 129],
)
def test_assertion_id_rules(assertion_id: str) -> None:
    with pytest.raises(ValidationError):
        make_payload(assertion_id=assertion_id)


@pytest.mark.parametrize("key_id", ["", "bad:key", "bad/key", "bad key", "é", "x" * 65])
def test_key_id_rules(key_id: str) -> None:
    signing_material, _public_key = make_key_pair()
    with pytest.raises(ValidationError):
        make_envelope(signing_material, key_id=key_id)


def test_unknown_payload_fields_fail() -> None:
    payload = make_payload().model_dump(mode="python")
    payload["unexpected"] = True
    with pytest.raises(ValidationError):
        IdentityAssertionPayload(**payload)


def test_protected_metadata_rejected() -> None:
    with pytest.raises(ValidationError):
        make_payload(metadata={"nested": {"access_token": "hidden"}})
