"""Audit canonicalization and hashing tests."""

from __future__ import annotations

from aion_brain.audit_integrity.canonical import canonical_json
from aion_brain.audit_integrity.hashing import hash_entry, hash_payload


def test_canonical_json_is_deterministic() -> None:
    assert canonical_json({"b": 2, "a": 1}) == canonical_json({"a": 1, "b": 2})


def test_hash_payload_is_deterministic() -> None:
    assert hash_payload({"a": 1, "b": 2}) == hash_payload({"b": 2, "a": 1})


def test_hash_entry_changes_when_payload_changes() -> None:
    first = hash_entry(None, hash_payload({"value": 1}), 1, {})
    second = hash_entry(None, hash_payload({"value": 2}), 1, {})

    assert first != second
