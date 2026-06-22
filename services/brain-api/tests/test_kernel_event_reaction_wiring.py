"""Kernel event reaction wiring tests."""

from tests.kernel_fakes import kernel_container


def test_kernel_wires_event_reaction_router_and_diagnostics() -> None:
    """Kernel container exposes the event reaction router and diagnostics checks."""
    container = kernel_container()
    names = {check.name for check in container.diagnostics.run()}

    assert container.event_reaction_repository is not None
    assert container.event_trigger_matcher is not None
    assert container.event_reaction_action_runner is not None
    assert container.event_dead_letter_service is not None
    assert container.event_reaction_router is not None
    assert "event_reaction_router_present" in names
    assert "event_dead_letter_service_present" in names
    assert "event_auto_dispatch_disabled_by_default" in names
    assert "event_reaction_no_background_consumer" in names
