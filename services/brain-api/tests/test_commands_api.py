"""Command API tests."""

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from aion_brain.api.commands import get_command_bus
from aion_brain.contracts.commands import BrainCommand, CommandDispatchResult
from aion_brain.main import app


class FakeCommandBus:
    """Command Bus fake."""

    def __init__(self) -> None:
        self.command = command()

    def dispatch(self, request):  # type: ignore[no-untyped-def]
        self.command = self.command.model_copy(
            update={
                "command_type": request.command_type,
                "target_type": request.target_type,
            }
        )
        return CommandDispatchResult(
            command=self.command,
            duplicate=False,
            idempotency_key=request.idempotency_key,
            outbox_ids=[],
            message="completed",
            created_at=datetime.now(UTC),
        )

    def get(self, command_id):  # type: ignore[no-untyped-def]
        return self.command if command_id == self.command.command_id else None

    def list_commands(self, status=None, command_type=None, trace_id=None, limit=50):  # type: ignore[no-untyped-def]
        return [self.command]

    def cancel(self, command_id, reason):  # type: ignore[no-untyped-def]
        return self.command.model_copy(update={"status": "cancelled", "error": {"reason": reason}})


def test_command_api_works() -> None:
    """Command API dispatches and reads commands."""
    fake = FakeCommandBus()
    app.dependency_overrides[get_command_bus] = lambda: fake
    try:
        client = TestClient(app)
        response = client.post(
            "/brain/commands",
            json={
                "command_type": "noop",
                "target_type": "noop",
                "owner_scope": ["workspace:main"],
            },
        )
        assert response.status_code == 200
        assert response.json()["command"]["status"] == "pending"

        list_response = client.get("/brain/commands")
        assert list_response.status_code == 200
        assert list_response.json()[0]["command_id"] == "command-1"
    finally:
        app.dependency_overrides.clear()


def command() -> BrainCommand:
    return BrainCommand(
        command_id="command-1",
        command_type="noop",
        target_type="noop",
        mode="dry_run",
        status="pending",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
