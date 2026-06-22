"""Kernel audit integrity wiring tests."""

from __future__ import annotations

from tests.kernel_fakes import kernel_container


def test_kernel_diagnostics_include_audit_integrity_checks() -> None:
    container = kernel_container()

    names = {check.name for check in container.diagnostics.run()}

    assert "audit_integrity_enabled" in names
    assert "audit_hash_algorithm" in names
    assert "audit_integrity_ledger_present" in names


def test_kernel_registers_audit_integrity_services() -> None:
    container = kernel_container()

    assert container.audit_integrity_ledger is not None
    assert container.audit_verifier is not None
    assert container.provenance_service is not None
