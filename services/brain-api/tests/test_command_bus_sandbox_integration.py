"""Command Bus sandbox integration tests."""

from datetime import UTC, datetime
from types import SimpleNamespace

from aion_brain.commands.bus import CommandBus
from aion_brain.config import Settings
from aion_brain.contracts.commands import BrainCommand, CommandDispatchRequest
from tests.sandbox_fakes import FakePolicyAdapter


class FailingSandbox:
    """Sandbox fake that blocks command runs."""

    def has_active_grant(self, **kwargs: object) -> bool:
        return True

    def run(self, request: object) -> object:
        return SimpleNamespace(status="failed", sandbox_run_id="sandbox-run-1")


def test_command_bus_validates_sandbox_boundary_for_capability_command() -> None:
    bus = CommandBus(
        command_repository=object(),
        command_handlers=object(),
        idempotency_service=object(),
        policy_adapter=FakePolicyAdapter(),
        autonomy_governor=None,
        risk_engine=None,
        approval_service=None,
        outbox_service=object(),
        telemetry_service=None,
        settings=Settings(_env_file=None),
        sandbox_service=FailingSandbox(),
    )
    command = BrainCommand(
        command_id="command-1",
        command_type="capability.invoke",
        target_type="capability",
        target_id="test.echo",
        mode="controlled",
        status="pending",
        payload={},
        result={},
        error={},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    request = CommandDispatchRequest(
        command_type="capability.invoke",
        target_type="capability",
        target_id="test.echo",
        mode="controlled",
        owner_scope=["workspace:main"],
        metadata={"sandbox_profile_id": "sandbox-profile-1"},
    )

    error = bus._sandbox_boundary_error(command, request)  # noqa: SLF001

    assert error is not None
    assert error["reason"] == "sandbox_validation_failed"
