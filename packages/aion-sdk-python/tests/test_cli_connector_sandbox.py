from __future__ import annotations

import json
from typing import Any

from typer.testing import CliRunner

from aion_sdk.cli import main as cli_main
from aion_sdk.config import AIONClientConfig

runner = CliRunner()


class FakeConnectorSandbox:
    def boundary(self) -> dict[str, object]:
        return {"runtime_execution_allowed": False, "filesystem_access_allowed": False}

    def capability_rules(self) -> list[dict[str, object]]:
        return [{"rule_key": "connector.sandbox.readiness.preview", "runtime_allowed": False}]

    def readiness(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"payload": payload, "runtime_execution_allowed": False}

    def status(self, scope: list[str]) -> dict[str, object]:
        return {"scope": scope, "connector_sandbox_runtime_execution_enabled": False}


class FakeClient:
    def __init__(self, config: AIONClientConfig) -> None:
        self.config = config
        self.connector_sandbox = FakeConnectorSandbox()


def test_cli_connector_sandbox_commands(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    boundary = runner.invoke(cli_main.app, ["--json", "connector-sandbox", "boundary"])
    rules = runner.invoke(cli_main.app, ["--json", "connector-sandbox", "capability-rules"])
    readiness = runner.invoke(cli_main.app, ["--json", "connector-sandbox", "readiness"])
    status = runner.invoke(cli_main.app, ["--json", "connector-sandbox", "status"])
    execute = runner.invoke(cli_main.app, ["connector-sandbox", "execute"])
    enable = runner.invoke(cli_main.app, ["connector-sandbox", "enable"])

    assert boundary.exit_code == 0
    assert json.loads(boundary.stdout)["runtime_execution_allowed"] is False
    assert rules.exit_code == 0
    assert json.loads(rules.stdout)[0]["runtime_allowed"] is False
    assert readiness.exit_code == 0
    assert json.loads(readiness.stdout)["runtime_execution_allowed"] is False
    assert status.exit_code == 0
    assert json.loads(status.stdout)["connector_sandbox_runtime_execution_enabled"] is False
    assert execute.exit_code != 0
    assert enable.exit_code != 0
