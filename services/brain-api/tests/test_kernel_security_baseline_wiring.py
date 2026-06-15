"""Kernel security baseline wiring tests."""

from __future__ import annotations

from tests.kernel_fakes import kernel_container


def test_kernel_diagnostics_include_security_baseline_checks() -> None:
    diagnostics = kernel_container().diagnostics.run()
    names = {check.name for check in diagnostics}

    assert "security_baseline_enabled" in names
    assert "secret_scanner_enabled" in names
    assert "hardening_gate_enabled" in names
    assert "security_services_present" in names
