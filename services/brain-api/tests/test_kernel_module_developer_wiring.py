"""Kernel wiring tests for the module developer kit."""

from tests.kernel_fakes import kernel_container


def test_kernel_diagnostics_include_module_developer_checks() -> None:
    container = kernel_container()

    check_names = {check.name for check in container.diagnostics.run()}

    assert "module_developer_kit_present" in check_names
    assert "module_certifier_present" in check_names
    assert "module_scaffold_generator_present" in check_names
    assert "module_contract_test_harness_present" in check_names

