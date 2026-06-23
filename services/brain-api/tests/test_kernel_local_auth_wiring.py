from __future__ import annotations

from tests.kernel_fakes import kernel_container


def test_kernel_wires_local_auth_services_and_diagnostics() -> None:
    container = kernel_container()
    names = {check.name for check in container.diagnostics.run()}

    assert hasattr(container, "local_role_service")
    assert hasattr(container, "dev_identity_simulator")
    assert hasattr(container, "console_role_filter")
    assert hasattr(container, "local_auth_audit_service")
    assert hasattr(container, "local_auth_query_service")
    assert "local_role_service_present" in names
    assert "dev_identity_simulator_present" in names
    assert "console_role_filter_present" in names
    assert "local_auth_audit_service_present" in names
    assert "local_auth_query_service_present" in names
    assert "local_auth_services_present" in names
    assert "production_auth_enabled" in names
    assert "auth_sessions_enabled" in names
