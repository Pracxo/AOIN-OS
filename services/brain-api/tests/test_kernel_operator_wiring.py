"""Kernel operator wiring tests."""

from tests.kernel_fakes import kernel_container


def test_kernel_diagnostics_include_operator_checks() -> None:
    container = kernel_container()

    names = {check.name for check in container.diagnostics.run()}

    assert "operator_control_tower_enabled" in names
    assert "operator_services_present" in names


def test_kernel_registers_operator_services() -> None:
    container = kernel_container()

    assert container.operator_control_tower_service is not None
    assert container.operator_action_center_service is not None
    assert container.operator_snapshot_service is not None
