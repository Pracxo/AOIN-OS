"""Kernel action proposal wiring tests."""

from __future__ import annotations

from aion_brain.kernel.app_factory import create_app
from tests.kernel_fakes import kernel_container


def test_kernel_registers_action_proposal_services_and_diagnostics() -> None:
    container = kernel_container()

    names = {record.service_name for record in container.service_registry.list_services()}
    checks = {check.name: check.status for check in container.diagnostics.run()}

    assert "action_proposal_service" in names
    assert "tool_intent_review_service" in names
    assert "execution_handoff_service" in names
    assert checks["action_proposals_enabled"] == "passed"
    assert checks["tool_intent_review_enabled"] == "passed"
    assert checks["execution_handoff_enabled"] == "passed"
    assert checks["action_handoff_controlled_enabled"] == "passed"
    assert checks["action_proposal_services_present"] == "passed"


def test_contract_export_contains_action_proposal_contracts_and_routes() -> None:
    container = kernel_container()
    exported = container.contract_export_service.export_contracts(create_app(container))

    assert "ActionProposal" in exported.contracts
    assert "ExecutionHandoff" in exported.contracts
    assert "/brain/action-proposals" in exported.openapi["paths"]
    assert "/brain/action-proposals/handoff" in exported.openapi["paths"]
