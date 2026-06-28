from __future__ import annotations

import json
from typing import Any

import pytest
from typer.testing import CliRunner

from aion_sdk.cli import main as cli_main
from aion_sdk.config import AIONClientConfig

runner = CliRunner()


class FakeLocalAuth:
    def roles(self, scope: list[str]) -> list[dict[str, object]]:
        return [{"role": "viewer", "scope": scope}]

    def simulate(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"context": payload, "production_auth": False}

    def audit(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"status": "passed", "payload": payload}

    def role_matrix(self, scope: list[str]) -> dict[str, object]:
        return {"scope": scope, "roles": {"viewer": {}}}

    def role_access_audit(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"status": "passed", "payload": payload, "forbidden_actions_visible": True}

    def status(self, scope: list[str]) -> dict[str, object]:
        return {"scope": scope, "production_auth_enabled": False}


class FakeClient:
    def __init__(self, config: AIONClientConfig) -> None:
        self.config = config
        self.local_auth = FakeLocalAuth()


def test_cli_local_auth_read_only_commands(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    roles = runner.invoke(cli_main.app, ["--json", "local-auth", "roles"])
    simulate = runner.invoke(
        cli_main.app,
        ["--json", "local-auth", "simulate", "--role", "viewer"],
    )
    audit = runner.invoke(cli_main.app, ["--json", "local-auth", "audit"])
    role_matrix = runner.invoke(cli_main.app, ["--json", "local-auth", "role-matrix"])
    role_access_audit = runner.invoke(
        cli_main.app,
        ["--json", "local-auth", "role-access-audit"],
    )
    status = runner.invoke(cli_main.app, ["--json", "local-auth", "status"])

    assert roles.exit_code == 0
    assert json.loads(roles.stdout)[0]["role"] == "viewer"
    assert simulate.exit_code == 0
    assert json.loads(simulate.stdout)["context"]["roles"] == ["viewer"]
    assert audit.exit_code == 0
    assert json.loads(audit.stdout)["status"] == "passed"
    assert role_matrix.exit_code == 0
    assert "viewer" in json.loads(role_matrix.stdout)["roles"]
    assert role_access_audit.exit_code == 0
    assert json.loads(role_access_audit.stdout)["forbidden_actions_visible"] is True
    assert status.exit_code == 0
    assert json.loads(status.stdout)["production_auth_enabled"] is False


def test_cli_local_auth_has_no_login_or_token_command(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    login = runner.invoke(cli_main.app, ["local-auth", "login"])
    token = runner.invoke(cli_main.app, ["local-auth", "token"])

    assert login.exit_code != 0
    assert token.exit_code != 0
