"""Runtime config drift tests."""

from __future__ import annotations

from aion_brain.runtime_config.drift import compare_config_snapshots


def test_config_drift_reports_changed_values() -> None:
    drift = compare_config_snapshots(
        {"settings": {"a": 1}, "feature_flags": {}, "adapter_status": {}},
        {"settings": {"a": 2}, "feature_flags": {}, "adapter_status": {}},
    )

    assert drift["has_drift"] is True
    assert drift["changed"]["settings"]["a"] == {"from": 1, "to": 2}
