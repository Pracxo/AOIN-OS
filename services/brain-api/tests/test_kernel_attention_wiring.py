"""Kernel attention wiring tests."""

from tests.kernel_fakes import kernel_container


def test_kernel_wires_attention_services_and_diagnostics() -> None:
    """Kernel container exposes attention and working-memory services."""
    container = kernel_container()
    names = {check.name for check in container.diagnostics.run()}

    assert container.focus_service is not None
    assert container.attention_controller is not None
    assert container.working_memory_service is not None
    assert container.context_budgeter is not None
    assert "attention_enabled" in names
    assert "working_memory_enabled" in names
    assert "focus_service_present" in names
    assert "attention_controller_present" in names
    assert "working_memory_service_present" in names
    assert "context_budgeter_present" in names
