from __future__ import annotations

from tests.kernel_fakes import kernel_container


def test_kernel_diagnostics_include_operator_console_checks() -> None:
    container = kernel_container()
    names = {check.name for check in container.diagnostics.run()}

    assert "operator_console_view_models_enabled" in names
    assert "operator_console_contract_audit_enabled" in names
    assert "operator_console_read_only" in names
    assert "operator_console_write_actions_enabled" in names
    assert "operator_console_frontend_enabled" in names
    assert "operator_console_redaction_required" in names
    assert "operator_console_services_present" in names
    assert hasattr(container, "operator_console_view_model_service")
    assert hasattr(container, "operator_console_contract_audit_service")
