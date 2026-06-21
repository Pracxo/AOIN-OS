"""Interface inventory service tests."""

from __future__ import annotations

from aion_brain.contract_registry.inventory import InterfaceInventoryService
from tests.contract_registry_helpers import (
    SCOPE,
    AllowPolicy,
    FakeTelemetry,
    contract_record,
    interface_record,
    repository,
)


def test_interface_inventory_upserts_and_lists_records() -> None:
    repo = repository()
    telemetry = FakeTelemetry()
    service = InterfaceInventoryService(repo, AllowPolicy(), telemetry_service=telemetry)

    service.upsert_contract(contract_record())
    service.upsert_interface(interface_record())

    assert service.list_contracts(SCOPE)[0].contract_key == "aion.contract.Test"
    assert service.list_interfaces(SCOPE)[0].interface_key == "GET /brain/example"
    assert [getattr(event, "event_type", None) for event in telemetry.events] == [
        "contract_indexed",
        "interface_indexed",
    ]
