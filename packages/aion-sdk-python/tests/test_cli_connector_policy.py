from __future__ import annotations

import json
from typing import Any

from typer.testing import CliRunner

from aion_sdk.cli import main as cli_main
from aion_sdk.config import AIONClientConfig

runner = CliRunner()


class FakeConnectorPolicy:
    def catalog(self) -> list[dict[str, object]]:
        return [{"action_key": "connector_policy.catalog.read", "allowed_in_runtime": False}]

    def matrix(self) -> list[dict[str, object]]:
        return [{"action_key": "connector_policy.dry_run", "runtime_allowed": False}]

    def dry_run(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"payload": payload, "dry_run_allowed": True, "runtime_allowed": False}

    def status(self, scope: list[str]) -> dict[str, object]:
        return {"scope": scope, "connector_policy_runtime_allow_enabled": False}


class FakeClient:
    def __init__(self, config: AIONClientConfig) -> None:
        self.config = config
        self.connector_policy = FakeConnectorPolicy()


def test_cli_connector_policy_commands(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    catalog = runner.invoke(cli_main.app, ["--json", "connector-policy", "catalog"])
    matrix = runner.invoke(cli_main.app, ["--json", "connector-policy", "matrix"])
    dry_run = runner.invoke(cli_main.app, ["--json", "connector-policy", "dry-run"])
    status = runner.invoke(cli_main.app, ["--json", "connector-policy", "status"])
    enable = runner.invoke(cli_main.app, ["connector-policy", "enable"])

    assert catalog.exit_code == 0
    assert json.loads(catalog.stdout)[0]["allowed_in_runtime"] is False
    assert matrix.exit_code == 0
    assert json.loads(matrix.stdout)[0]["runtime_allowed"] is False
    assert dry_run.exit_code == 0
    assert json.loads(dry_run.stdout)["runtime_allowed"] is False
    assert status.exit_code == 0
    assert json.loads(status.stdout)["connector_policy_runtime_allow_enabled"] is False
    assert enable.exit_code != 0

