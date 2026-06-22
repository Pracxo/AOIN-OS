"""Runtime config hashing tests."""

from __future__ import annotations

from aion_brain.runtime_config.hash import hash_config_snapshot


def test_config_hash_is_deterministic() -> None:
    first = hash_config_snapshot({"b": 2, "a": 1}, {"x": True}, {"adapter": "local"})
    second = hash_config_snapshot({"a": 1, "b": 2}, {"x": True}, {"adapter": "local"})

    assert first == second
