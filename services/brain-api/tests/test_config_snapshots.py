"""Runtime config snapshot service tests."""

from __future__ import annotations

from aion_brain.contracts.runtime_config import ConfigSnapshotRequest, FeatureFlagOverrideRequest
from tests.runtime_config_fakes import SCOPE, services


def test_config_snapshot_service_creates_redacted_snapshot() -> None:
    _, _, _, snapshots, *_ = services()

    snapshot = snapshots.create_snapshot(ConfigSnapshotRequest(owner_scope=SCOPE))

    assert snapshot.config_hash
    assert snapshot.settings["database_url"] == {"redacted": True}


def test_config_snapshot_service_detects_drift_between_snapshots() -> None:
    _, _, feature_overrides, snapshots, *_ = services()
    first = snapshots.create_snapshot(ConfigSnapshotRequest(owner_scope=SCOPE))
    feature_overrides.create_override(
        FeatureFlagOverrideRequest(
            feature_key="runtime_config.feature_overrides",
            enabled=False,
            owner_scope=SCOPE,
            reason="drift test",
        )
    )

    second = snapshots.create_snapshot(
        ConfigSnapshotRequest(
            owner_scope=SCOPE,
            compare_to_snapshot_id=first.config_snapshot_id,
        )
    )

    assert second.drift["has_drift"] is True
    assert snapshots.compare(first.config_snapshot_id, second.config_snapshot_id)["has_drift"]
