from __future__ import annotations

import json
from typing import Any

from typer.testing import CliRunner

from aion_sdk.cli import main as cli_main
from aion_sdk.config import AIONClientConfig

runner = CliRunner()


class FakeOperator:
    def overview(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"overall_status": "ready", "payload": payload}

    def readiness(self, scope: list[str]) -> dict[str, object]:
        return {"release_ready": True, "scope": scope}

    def actions(self, scope: list[str], limit: int = 100) -> list[dict[str, object]]:
        return [{"scope": scope, "limit": limit}]

    def acknowledge(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"acknowledgement_id": "ack-1", "payload": payload}

    def status_cards(self, scope: list[str]) -> list[dict[str, object]]:
        return [{"scope": scope}]

    def queues(self, scope: list[str]) -> list[dict[str, object]]:
        return [{"scope": scope}]

    def create_snapshot(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"operator_snapshot_id": "snapshot-1", "payload": payload}

    def runbooks(self, category: str | None = None) -> list[dict[str, object]]:
        return [{"category": category or "operator"}]


class FakeClient:
    def __init__(self, config: AIONClientConfig) -> None:
        self.config = config
        self.operator = FakeOperator()


def test_cli_operator_overview_and_readiness(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    overview = runner.invoke(cli_main.app, ["--json", "operator", "overview"])
    readiness = runner.invoke(cli_main.app, ["--json", "operator", "readiness"])

    assert overview.exit_code == 0
    assert json.loads(overview.stdout)["overall_status"] == "ready"
    assert readiness.exit_code == 0
    assert json.loads(readiness.stdout)["release_ready"] is True


def test_cli_operator_actions_and_acknowledge(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    actions = runner.invoke(cli_main.app, ["--json", "operator", "actions", "--limit", "5"])
    acknowledge = runner.invoke(
        cli_main.app,
        [
            "--json",
            "operator",
            "acknowledge",
            "--source-type",
            "generic",
            "--source-id",
            "item-1",
            "--reason",
            "seen",
        ],
    )

    assert actions.exit_code == 0
    assert json.loads(actions.stdout)[0]["limit"] == 5
    assert acknowledge.exit_code == 0
    assert json.loads(acknowledge.stdout)["acknowledgement_id"] == "ack-1"
