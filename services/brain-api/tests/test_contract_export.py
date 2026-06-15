"""Kernel contract export tests."""

from aion_brain.kernel.app_factory import create_app
from tests.kernel_fakes import kernel_container


def test_contract_export_contains_openapi_and_core_contracts() -> None:
    container = kernel_container()
    exported = container.contract_export_service.export_contracts(create_app(container))
    assert "/brain/kernel/status" in exported.openapi["paths"]
    assert "AIONEvent" in exported.contracts
    assert "KernelStatus" in exported.contracts
