"""Kernel wiring tests for Contract Registry."""

from __future__ import annotations

from tests.kernel_fakes import kernel_container


def test_kernel_container_registers_contract_registry_services() -> None:
    container = kernel_container()

    assert container.contract_registry_repository is not None
    assert container.contract_scanner is not None
    assert container.interface_inventory_service is not None
    assert container.contract_snapshot_service is not None
    assert container.compatibility_scanner is not None
    assert container.contract_registry_report_service is not None
    assert "contract_registry_repository" in container._services
