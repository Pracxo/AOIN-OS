"""Kernel consistency wiring tests."""

from tests.kernel_fakes import kernel_container


def test_kernel_wires_command_consistency_services_and_diagnostics() -> None:
    """Kernel exposes command and consistency services."""
    container = kernel_container()
    names = {check.name for check in container.diagnostics.run()}

    assert container.command_bus is not None
    assert container.idempotency_service is not None
    assert container.outbox_service is not None
    assert container.inbox_service is not None
    assert container.processing_lease_service is not None
    assert container.consistency_checker is not None
    assert "command_bus_enabled" in names
    assert "idempotency_enabled" in names
    assert "outbox_enabled" in names
    assert "outbox_process_enabled" in names
    assert "inbox_enabled" in names
    assert "consistency_checker_enabled" in names
    assert "no_outbox_background_processor" in names
    assert "no_inbox_background_processor" in names
