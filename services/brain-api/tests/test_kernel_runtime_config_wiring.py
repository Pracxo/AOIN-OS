"""Kernel runtime config wiring tests."""

from __future__ import annotations

from tests.kernel_fakes import kernel_container


def test_kernel_diagnostics_include_runtime_config_checks() -> None:
    container = kernel_container()
    checks = container.diagnostics.run()
    names = {check.name for check in checks}

    assert "runtime_config_services_present" in names
    assert "runtime_config_enabled" in names
    assert container.config_validator is not None
