from __future__ import annotations

import json
from typing import Any

from typer.testing import CliRunner

from aion_sdk.cli import main as cli_main
from aion_sdk.config import AIONClientConfig

runner = CliRunner()


class FakeConnectorCredentials:
    def boundary(self) -> dict[str, object]:
        return {"credential_storage_enabled": False, "token_storage_enabled": False}

    def lifecycle(self) -> list[dict[str, object]]:
        return [{"state_key": "provisioned_future", "allowed_today": False}]

    def authorization(self) -> list[dict[str, object]]:
        return [{"action_key": "connector_credentials.readiness.preview", "storage_allowed": False}]

    def readiness(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"payload": payload, "credential_storage_allowed": False}

    def redaction_preview(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"payload": payload, "redaction_applied": False}

    def status(self, scope: list[str]) -> dict[str, object]:
        return {"scope": scope, "connector_credentials_storage_enabled": False}


class FakeClient:
    def __init__(self, config: AIONClientConfig) -> None:
        self.config = config
        self.connector_credentials = FakeConnectorCredentials()


def test_cli_connector_credentials_commands(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    boundary = runner.invoke(cli_main.app, ["--json", "connector-credentials", "boundary"])
    lifecycle = runner.invoke(cli_main.app, ["--json", "connector-credentials", "lifecycle"])
    authorization = runner.invoke(
        cli_main.app,
        ["--json", "connector-credentials", "authorization"],
    )
    readiness = runner.invoke(cli_main.app, ["--json", "connector-credentials", "readiness"])
    redaction = runner.invoke(
        cli_main.app,
        ["--json", "connector-credentials", "redaction-preview"],
    )
    status = runner.invoke(cli_main.app, ["--json", "connector-credentials", "status"])
    store = runner.invoke(cli_main.app, ["connector-credentials", "store"])
    read = runner.invoke(cli_main.app, ["connector-credentials", "read"])
    rotate = runner.invoke(cli_main.app, ["connector-credentials", "rotate"])
    revoke = runner.invoke(cli_main.app, ["connector-credentials", "revoke"])
    login = runner.invoke(cli_main.app, ["connector-credentials", "login"])

    assert boundary.exit_code == 0
    assert json.loads(boundary.stdout)["credential_storage_enabled"] is False
    assert lifecycle.exit_code == 0
    assert json.loads(lifecycle.stdout)[0]["allowed_today"] is False
    assert authorization.exit_code == 0
    assert json.loads(authorization.stdout)[0]["storage_allowed"] is False
    assert readiness.exit_code == 0
    assert json.loads(readiness.stdout)["credential_storage_allowed"] is False
    assert redaction.exit_code == 0
    assert json.loads(redaction.stdout)["redaction_applied"] is False
    assert status.exit_code == 0
    assert json.loads(status.stdout)["connector_credentials_storage_enabled"] is False
    assert store.exit_code != 0
    assert read.exit_code != 0
    assert rotate.exit_code != 0
    assert revoke.exit_code != 0
    assert login.exit_code != 0
