"""Command handler tests."""

from datetime import UTC, datetime

from aion_brain.commands.handlers import CommandHandlerRegistry
from aion_brain.contracts.commands import BrainCommand


def test_command_handler_runs_noop() -> None:
    """Noop command completes without side effects."""
    result = CommandHandlerRegistry().execute(command())

    assert result.status == "completed"
    assert result.result["reason"] == "noop"


def command() -> BrainCommand:
    return BrainCommand(
        command_id="command-1",
        command_type="noop",
        target_type="noop",
        mode="dry_run",
        status="running",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
