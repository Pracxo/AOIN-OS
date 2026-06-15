"""Kernel autonomy wiring tests."""

from tests.kernel_fakes import kernel_container


def test_kernel_container_wires_autonomy_components() -> None:
    """KernelContainer exposes autonomy services and passes them to integration points."""
    container = kernel_container()

    assert container.autonomy_repository is not None
    assert container.autonomy_governor is not None
    assert container.delegation_service is not None
    assert container.run_level_service is not None
    assert container.execution_orchestrator._autonomy_governor is container.autonomy_governor  # noqa: SLF001
    assert container.model_gateway_service._autonomy_governor is container.autonomy_governor  # noqa: SLF001
    assert container.mcp_service._autonomy_governor is container.autonomy_governor  # noqa: SLF001
