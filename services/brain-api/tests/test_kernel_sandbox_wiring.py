"""Kernel sandbox wiring tests."""

from tests.kernel_fakes import kernel_container


def test_kernel_container_wires_sandbox_secret_and_connector_services() -> None:
    container = kernel_container()

    assert container.sandbox_service is not None
    assert container.sandbox_validator is not None
    assert container.secret_ref_service is not None
    assert container.connector_service is not None
    assert container.local_noop_sandbox_adapter is not None
    assert container.docker_sandbox_adapter is not None
    assert container.firecracker_sandbox_adapter is not None


def test_kernel_diagnostics_include_sandbox_checks() -> None:
    names = {check.name for check in kernel_container().diagnostics.run()}

    assert "sandbox_control_plane_enabled" in names
    assert "sandbox_execution_enabled" in names
    assert "sandbox_default_type" in names
    assert "no_sandbox_execution_by_default" in names
    assert "secret_ref_vault_enabled" in names
    assert "connector_registry_enabled" in names
    assert "runtime_permissions_enabled" in names
