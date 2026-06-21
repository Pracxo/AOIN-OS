"""Audit/provenance integration with Contract Registry."""

from __future__ import annotations

from aion_brain.contract_registry.snapshots import ContractSnapshotService
from tests.contract_registry_helpers import SCOPE, AllowPolicy, contract_record, repository


class FakeScanner:
    def scan_all(self, owner_scope: list[str]) -> dict[str, object]:
        return {"contracts": [contract_record()], "interfaces": [], "warnings": []}


class FakeAudit:
    def __init__(self) -> None:
        self.records: list[dict[str, object]] = []

    def record(self, **payload: object) -> None:
        self.records.append(payload)


class FakeProvenance:
    def __init__(self) -> None:
        self.links: list[dict[str, object]] = []

    def link(self, **payload: object) -> None:
        self.links.append(payload)


def test_contract_snapshot_records_audit_and_provenance() -> None:
    audit = FakeAudit()
    provenance = FakeProvenance()
    service = ContractSnapshotService(
        repository(),
        FakeScanner(),
        AllowPolicy(),
        audit_sink=audit,
        provenance_service=provenance,
    )

    snapshot = service.create_snapshot(SCOPE)

    assert audit.records[0]["event_type"] == "contract_snapshot_created"
    assert provenance.links[0]["source_id"] == snapshot.contract_snapshot_id
