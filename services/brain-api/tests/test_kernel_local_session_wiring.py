from __future__ import annotations

from tests.kernel_fakes import kernel_container


def test_kernel_wires_local_session_services_and_diagnostics() -> None:
    container = kernel_container()
    names = {check.name for check in container.diagnostics.run()}

    assert hasattr(container, "local_session_preview_service")
    assert hasattr(container, "local_session_context_service")
    assert hasattr(container, "local_session_boundary_service")
    assert hasattr(container, "local_session_audit_service")
    assert hasattr(container, "local_session_query_service")
    assert "local_session_preview_service_present" in names
    assert "local_session_context_service_present" in names
    assert "local_session_boundary_service_present" in names
    assert "local_session_audit_service_present" in names
    assert "local_session_query_service_present" in names
    assert "local_session_services_present" in names
    assert "local_session_preview_enabled" in names
    assert "local_session_tokens_enabled" in names
    assert "local_session_cookies_enabled" in names
    assert "local_session_persistence_enabled" in names
