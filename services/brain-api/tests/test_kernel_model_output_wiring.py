"""Kernel wiring tests for model output governance."""

from __future__ import annotations

from aion_brain.kernel.app_factory import create_app
from tests.kernel_fakes import kernel_container


def test_kernel_registers_model_output_services() -> None:
    container = kernel_container()

    assert container.output_governance_service is not None
    assert container.model_output_query_service is not None
    names = {record.service_name for record in container.service_registry.list_services()}
    assert "output_governance_service" in names


def test_contract_export_contains_model_output_contracts() -> None:
    container = kernel_container()
    exported = container.contract_export_service.export_contracts(create_app(container))

    assert "ModelOutputRecord" in exported.contracts
    assert "OutputGovernanceRun" in exported.contracts
    assert "/brain/model-outputs" in exported.openapi["paths"]
