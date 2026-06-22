"""Contract hash tests."""

from __future__ import annotations

from aion_brain.contract_registry.hash import canonical_schema_json, hash_manifest, hash_schema


def test_hash_schema_is_deterministic() -> None:
    first = {"b": 2, "a": {"z": 1}}
    second = {"a": {"z": 1}, "b": 2}

    assert canonical_schema_json(first) == canonical_schema_json(second)
    assert hash_schema(first) == hash_schema(second)
    assert hash_manifest([first, second]) == hash_manifest([second, first])
