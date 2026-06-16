from __future__ import annotations

from aion_brain.contracts.commands import CommandDispatchRequest
from tests.kernel_fakes import kernel_container


def test_command_bus_creates_outcome_once_per_command_id() -> None:
    container = kernel_container()
    request = CommandDispatchRequest(
        command_id="command-outcome-1",
        command_type="noop",
        target_type="noop",
        mode="dry_run",
        owner_scope=["workspace:main"],
    )

    first = container.command_bus.dispatch(request)
    second = container.command_bus.dispatch(request)

    assert first.command.command_id == second.command.command_id
    outcomes = container.outcome_repository.list_outcomes(scope=["workspace:main"])
    assert len([item for item in outcomes if item.source_id == "command-outcome-1"]) == 1
