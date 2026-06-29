from __future__ import annotations

import json
from typing import Any

from typer.testing import CliRunner

from aion_sdk.cli import main as cli_main
from aion_sdk.config import AIONClientConfig

runner = CliRunner()


class FakeConnectorSimulator:
    def simulate(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"payload": payload, "synthetic": True, "external_calls_made": False}

    def replay(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"payload": payload, "trusted": False}

    def policy_readiness(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"payload": payload, "external_calls_allowed": False}

    def status(self, scope: list[str]) -> dict[str, object]:
        return {"scope": scope, "connector_runtime_enabled": False}


class FakeClient:
    def __init__(self, config: AIONClientConfig) -> None:
        self.config = config
        self.connector_simulator = FakeConnectorSimulator()


def test_cli_connector_simulator_commands(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    simulate = runner.invoke(cli_main.app, ["--json", "connector-simulator", "simulate"])
    replay = runner.invoke(cli_main.app, ["--json", "connector-simulator", "replay"])
    readiness = runner.invoke(
        cli_main.app,
        ["--json", "connector-simulator", "policy-readiness"],
    )
    status = runner.invoke(cli_main.app, ["--json", "connector-simulator", "status"])
    activate = runner.invoke(cli_main.app, ["connector-simulator", "activate"])

    assert simulate.exit_code == 0
    assert json.loads(simulate.stdout)["synthetic"] is True
    assert replay.exit_code == 0
    assert json.loads(replay.stdout)["trusted"] is False
    assert readiness.exit_code == 0
    assert json.loads(readiness.stdout)["external_calls_allowed"] is False
    assert status.exit_code == 0
    assert json.loads(status.stdout)["connector_runtime_enabled"] is False
    assert activate.exit_code != 0
