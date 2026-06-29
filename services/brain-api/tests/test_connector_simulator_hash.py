from __future__ import annotations

from aion_brain.connector_simulator.hash import stable_hash


def test_stable_hash_is_order_independent() -> None:
    assert stable_hash({"b": 2, "a": 1}) == stable_hash({"a": 1, "b": 2})
    assert stable_hash({"a": 1}) != stable_hash({"a": 2})
