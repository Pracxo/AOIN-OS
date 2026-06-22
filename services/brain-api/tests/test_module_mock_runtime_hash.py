"""Module mock runtime hashing tests."""

from __future__ import annotations

from aion_brain.module_mock_runtime.hash import canonical_mock_json, hash_mock_payload


def test_hash_is_deterministic_and_redacts_before_hashing() -> None:
    left = {"b": 2, "a": {"token": "sk-test"}}
    right = {"a": {"token": "sk-other"}, "b": 2}

    assert canonical_mock_json(left) == canonical_mock_json(right)
    assert hash_mock_payload(left) == hash_mock_payload(right)
