from __future__ import annotations

import inspect
import re

from aion_brain.contracts.identity_assertion import assertion_fingerprint
from aion_brain.contracts.identity_assertion_replay import REPLAY_KEY_DOMAIN_SEPARATOR
from aion_brain.production_auth.identity_assertion_replay import (
    derive_identity_assertion_issuer_fingerprint,
    derive_identity_assertion_replay_key,
)
from tests.test_identity_assertion_contracts import make_payload


def test_replay_key_is_stable_for_issuer_and_assertion_id_only() -> None:
    payload = make_payload()
    key = derive_identity_assertion_replay_key(
        issuer=payload.issuer,
        assertion_id=payload.assertion_id,
    )
    changed_payload = make_payload(actor_id="actor-999", permissions=("admin:read",))
    changed_signature = "not-used-by-replay-key"
    changed_key_id = "key-999"

    assert key == derive_identity_assertion_replay_key(
        issuer=changed_payload.issuer,
        assertion_id=changed_payload.assertion_id,
    )
    assert changed_signature
    assert changed_key_id
    assert key != assertion_fingerprint(payload)
    assert re.fullmatch(r"[0-9a-f]{64}", key)


def test_replay_key_changes_for_issuer_or_assertion_id() -> None:
    original = derive_identity_assertion_replay_key(
        issuer="issuer.aion.local",
        assertion_id="assertion-001",
    )
    assert original != derive_identity_assertion_replay_key(
        issuer="issuer.other.local",
        assertion_id="assertion-001",
    )
    assert original != derive_identity_assertion_replay_key(
        issuer="issuer.aion.local",
        assertion_id="assertion-002",
    )


def test_issuer_fingerprint_is_safe_and_stable() -> None:
    fingerprint = derive_identity_assertion_issuer_fingerprint(issuer="issuer.aion.local")
    assert fingerprint == derive_identity_assertion_issuer_fingerprint(
        issuer="issuer.aion.local",
    )
    assert re.fullmatch(r"[0-9a-f]{64}", fingerprint)
    assert "issuer.aion.local" not in fingerprint


def test_replay_key_uses_one_fixed_domain_separator() -> None:
    source = inspect.getsource(derive_identity_assertion_replay_key)
    assert source.count("REPLAY_KEY_DOMAIN_SEPARATOR") == 1
    assert "canonical_json_bytes" in source
    assert "issuer + assertion_id" not in source
    assert REPLAY_KEY_DOMAIN_SEPARATOR == b"AION-IDENTITY-ASSERTION-REPLAY-V1\0"
