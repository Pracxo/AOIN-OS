from __future__ import annotations

import json
from typing import Any

import pytest
from typer.testing import CliRunner

from aion_sdk.cli import main as cli_main
from aion_sdk.config import AIONClientConfig

runner = CliRunner()


class FakeOperatorConsole:
    def list_views(self, scope: list[str]) -> list[dict[str, Any]]:
        return [{"view": "overview", "scope": scope, "read_only": True}]

    def view_model(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"view": payload["view"], "read_only": True, "payload": payload}

    def audit(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"status": "passed", "payload": payload}

    def workflows(self, scope: list[str]) -> list[dict[str, Any]]:
        return [{"workflow_key": "operator.first_run_readiness", "scope": scope}]

    def demo_map(self, scope: list[str]) -> dict[str, Any]:
        return {"demo_key": "operator.console.local_read_only", "scope": scope}


class FakeClient:
    def __init__(self, config: AIONClientConfig) -> None:
        self.config = config
        self.operator_console = FakeOperatorConsole()


def test_cli_operator_console_read_only_commands(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    views = runner.invoke(cli_main.app, ["--json", "operator-console", "views"])
    view_model = runner.invoke(
        cli_main.app,
        ["--json", "operator-console", "view-model", "--view", "overview"],
    )
    audit = runner.invoke(cli_main.app, ["--json", "operator-console", "audit"])
    workflows = runner.invoke(cli_main.app, ["--json", "operator-console", "workflows"])
    demo = runner.invoke(cli_main.app, ["--json", "operator-console", "demo-map"])

    assert views.exit_code == 0
    assert json.loads(views.stdout)[0]["read_only"] is True
    assert view_model.exit_code == 0
    assert json.loads(view_model.stdout)["read_only"] is True
    assert audit.exit_code == 0
    assert json.loads(audit.stdout)["status"] == "passed"
    assert workflows.exit_code == 0
    assert demo.exit_code == 0


def test_cli_operator_console_has_no_activate_or_execute_command(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    activate = runner.invoke(cli_main.app, ["operator-console", "activate"])
    execute = runner.invoke(cli_main.app, ["operator-console", "execute"])

    assert activate.exit_code != 0
    assert execute.exit_code != 0
