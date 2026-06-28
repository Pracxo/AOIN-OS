from __future__ import annotations

import json
from typing import Any

from typer.testing import CliRunner

from aion_sdk.cli import main as cli_main
from aion_sdk.config import AIONClientConfig

runner = CliRunner()


class FakeActionAuthorization:
    def authorize(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"decision": "allow_dry_run_preview", "payload": payload}

    def audit(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"status": "passed", "payload": payload, "execution_blocked": True}

    def status(self, scope: list[str]) -> dict[str, object]:
        return {"scope": scope, "execution_allowed": False}


class FakeClient:
    def __init__(self, config: AIONClientConfig) -> None:
        self.config = config
        self.action_authorization = FakeActionAuthorization()


def test_cli_action_authorization_commands(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    authorize = runner.invoke(
        cli_main.app,
        [
            "--json",
            "action-authorization",
            "authorize",
            "--action-key",
            "operator.review",
            "--role",
            "operator",
        ],
    )
    audit = runner.invoke(cli_main.app, ["--json", "action-authorization", "audit"])
    status = runner.invoke(cli_main.app, ["--json", "action-authorization", "status"])
    execute = runner.invoke(cli_main.app, ["action-authorization", "execute"])

    assert authorize.exit_code == 0
    assert json.loads(authorize.stdout)["payload"]["mode"] == "dry_run"
    assert audit.exit_code == 0
    assert json.loads(audit.stdout)["execution_blocked"] is True
    assert status.exit_code == 0
    assert json.loads(status.stdout)["execution_allowed"] is False
    assert execute.exit_code != 0
