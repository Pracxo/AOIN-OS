"""Model provider hardening hash tests."""

from __future__ import annotations

from aion_brain.model_provider_hardening.hash import hash_provider_payload


def test_hash_provider_payload_is_deterministic() -> None:
    left = hash_provider_payload({"b": 2, "a": 1})
    right = hash_provider_payload({"a": 1, "b": 2})

    assert left == right
    assert len(left) == 64
