from __future__ import annotations

from aion_brain.production_auth.identity_assertion import (
    identity_assertion_payload_bytes,
    identity_assertion_signing_input,
)
from tests.test_identity_assertion_contracts import make_payload


def test_canonical_payload_is_deterministic_and_excludes_envelope_material() -> None:
    first = make_payload(roles=("viewer", "operator"))
    second = make_payload(roles=("operator", "viewer"))
    assert identity_assertion_payload_bytes(first) == identity_assertion_payload_bytes(second)
    canonical = identity_assertion_payload_bytes(first)
    assert b"signature" not in canonical
    assert b"key_id" not in canonical


def test_signing_input_uses_domain_separator() -> None:
    payload = make_payload()
    assert identity_assertion_signing_input(payload).startswith(
        b"AION-IDENTITY-ASSERTION-V1\0"
    )
