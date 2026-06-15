"""Kernel MCP wiring tests."""

from tests.kernel_fakes import kernel_container


def test_kernel_diagnostics_include_mcp_checks() -> None:
    checks = kernel_container().diagnostics.run()
    names = {check.name for check in checks}

    assert "mcp_enabled" in names
    assert "mcp_package_available" in names
    assert "mcp_network_allowed" in names
    assert "mcp_stdio_allowed" in names
    assert "mcp_runtime_registered" in names
    assert "mcp_external_execution_disabled_by_default" in names
    assert kernel_container().get("mcp_service") is not None
