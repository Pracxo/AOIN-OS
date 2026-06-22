"""Release candidate hashing tests."""

from __future__ import annotations

from aion_brain.release_candidate.hash import hash_rc_report


def test_rc_report_hash_is_deterministic() -> None:
    first = hash_rc_report({"b": 2, "a": 1})
    second = hash_rc_report({"a": 1, "b": 2})

    assert first == second
    assert len(first) == 64
