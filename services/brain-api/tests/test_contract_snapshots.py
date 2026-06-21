"""Contract snapshot service tests."""

from __future__ import annotations

from aion_brain.contract_registry.snapshots import ContractSnapshotService
from tests.contract_registry_helpers import (
    SCOPE,
    AllowPolicy,
    FakeTelemetry,
    contract_record,
    interface_record,
    repository,
)


class FakeScanner:
    def scan_all(self, owner_scope: list[str]) -> dict[str, object]:
        return {
            "contracts": [contract_record()],
            "interfaces": [interface_record()],
            "warnings": [],
        }


def test_contract_snapshot_service_creates_deterministic_root_hash() -> None:
    repo = repository()
    telemetry = FakeTelemetry()
    service = ContractSnapshotService(
        repo,
        FakeScanner(),
        AllowPolicy(),
        telemetry_service=telemetry,
    )

    first = service.create_snapshot(SCOPE)
    second = service.create_snapshot(SCOPE)

    assert first.root_hash == second.root_hash
    assert first.contract_count == 1
    assert first.interface_count == 1
    assert service.get_snapshot(first.contract_snapshot_id, SCOPE) is not None
    assert service.list_snapshots(SCOPE)
    assert telemetry.events[0].event_type == "contract_snapshot_created"
