"""Performance timing helper tests."""

from aion_brain.performance.timing import estimate_json_size_bytes, percentile


def test_percentile_helper_is_deterministic() -> None:
    assert percentile([40, 10, 20, 30], 50) == 25.0
    assert percentile([10, 20, 30, 40], 100) == 40.0
    assert percentile([], 95) == 0.0


def test_json_size_estimate_works_without_logging_payload() -> None:
    assert estimate_json_size_bytes({"b": 2, "a": 1}) == estimate_json_size_bytes(
        {"a": 1, "b": 2}
    )
