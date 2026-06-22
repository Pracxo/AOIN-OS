"""Command contract tests."""

import pytest

from aion_brain.contracts.commands import BrainCommand, CommandDispatchRequest


def test_brain_command_validates_command_type() -> None:
    """BrainCommand rejects unknown command types."""
    with pytest.raises(ValueError):
        BrainCommand(
            command_id="command-1",
            command_type="unknown",  # type: ignore[arg-type]
            target_type="brain",
            mode="dry_run",
            status="pending",
        )


def test_brain_command_rejects_domain_specific_command_type() -> None:
    """Command types remain generic."""
    with pytest.raises(ValueError):
        BrainCommand(
            command_id="command-1",
            command_type="finance.run",  # type: ignore[arg-type]
            target_type="brain",
            mode="dry_run",
            status="pending",
        )


def test_command_dispatch_request_rejects_empty_owner_scope() -> None:
    """Command dispatch requires a non-empty owner scope."""
    with pytest.raises(ValueError):
        CommandDispatchRequest(
            command_type="noop",
            target_type="noop",
            owner_scope=[],
        )
