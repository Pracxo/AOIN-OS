"""Registry snapshot service tests."""

from __future__ import annotations

from aion_brain.contracts.resource_registry import ResourceIndexRecord
from aion_brain.resource_registry.snapshots import RegistrySnapshotService
from tests.kernel_fakes import AllowPolicy
from tests.resource_registry_helpers import FakeTelemetry, descriptor, repository


def test_snapshot_service_creates_deterministic_snapshot() -> None:
    repo = repository()
    repo.save_resource(ResourceIndexRecord(resource_index_id="idx-1", descriptor=descriptor()))

    snapshot = RegistrySnapshotService(repo, AllowPolicy()).create_snapshot(["workspace:main"])

    assert snapshot.resource_count == 1
    assert len(snapshot.root_hash) == 64
    assert snapshot.report["source_records_mutated"] is False


def test_snapshot_service_emits_visual_telemetry() -> None:
    telemetry = FakeTelemetry()

    snapshot = RegistrySnapshotService(
        repository(),
        AllowPolicy(),
        telemetry_service=telemetry,
    ).create_snapshot(["workspace:main"])

    assert snapshot.link_count == 0
    assert telemetry.events[0].event_type == "registry_snapshot_created"
