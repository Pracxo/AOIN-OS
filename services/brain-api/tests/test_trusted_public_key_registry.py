from __future__ import annotations

from datetime import timedelta

import pytest

from aion_brain.production_auth.trusted_public_keys import (
    TrustedPublicKeyRegistry,
    TrustedPublicKeyResolutionError,
)
from tests.test_identity_assertion_contracts import NOW, make_key_pair


def test_registry_resolves_exact_active_key() -> None:
    _signing_material, public_key = make_key_pair()
    registry = TrustedPublicKeyRegistry((public_key,))
    assert registry.key_ids() == ("key-001",)
    assert registry.resolve("key-001", "issuer.aion.local", NOW) == public_key


def test_registry_rejects_duplicate_key_id() -> None:
    _first_signing, first = make_key_pair()
    _second_signing, second = make_key_pair()
    with pytest.raises(ValueError):
        TrustedPublicKeyRegistry((first, second.model_copy(update={"key_id": first.key_id})))


@pytest.mark.parametrize(
    ("key_kwargs", "reason"),
    [
        ({}, "public_key_unknown"),
        ({"issuer": "other.issuer"}, "public_key_issuer_mismatch"),
        ({"revoked": True}, "public_key_revoked"),
        (
            {
                "active_from": NOW + timedelta(days=1),
                "active_until": NOW + timedelta(days=2),
            },
            "public_key_inactive",
        ),
        ({"active_until": NOW - timedelta(seconds=1)}, "public_key_retired"),
    ],
)
def test_registry_fails_closed(key_kwargs: dict[str, object], reason: str) -> None:
    if reason == "public_key_unknown":
        _signing_material, public_key = make_key_pair()
        registry = TrustedPublicKeyRegistry((public_key,))
        with pytest.raises(TrustedPublicKeyResolutionError) as exc:
            registry.resolve("missing", "issuer.aion.local", NOW)
    else:
        _signing_material, public_key = make_key_pair(**key_kwargs)
        registry = TrustedPublicKeyRegistry((public_key,))
        with pytest.raises(TrustedPublicKeyResolutionError) as exc:
            registry.resolve("key-001", "issuer.aion.local", NOW)
    assert exc.value.reason_code == reason


def test_registry_mapping_is_immutable() -> None:
    _signing_material, public_key = make_key_pair()
    registry = TrustedPublicKeyRegistry((public_key,))
    ids = registry.key_ids()
    assert ids == ("key-001",)
    assert ids + ("other",) == ("key-001", "other")
    assert registry.key_ids() == ("key-001",)
