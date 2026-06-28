from __future__ import annotations

import json
from typing import Any

import pytest
from typer.testing import CliRunner

from aion_sdk.cli import main as cli_main
from aion_sdk.config import AIONClientConfig

runner = CliRunner()


class FakeLocalSession:
    def preview(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"preview": payload, "read_only": True}

    def context(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"context": payload, "write_allowed": False}

    def status(self, scope: list[str]) -> dict[str, object]:
        return {"scope": scope, "production_session": False}

    def boundary_check(self, scope: list[str]) -> dict[str, object]:
        return {"scope": scope, "status": "passed"}

    def audit(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"status": "passed", "payload": payload}


class FakeClient:
    def __init__(self, config: AIONClientConfig) -> None:
        self.config = config
        self.local_session = FakeLocalSession()


def test_cli_local_session_read_only_commands(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    preview = runner.invoke(cli_main.app, ["--json", "local-session", "preview"])
    context = runner.invoke(cli_main.app, ["--json", "local-session", "context"])
    status = runner.invoke(cli_main.app, ["--json", "local-session", "status"])
    boundary = runner.invoke(cli_main.app, ["--json", "local-session", "boundary-check"])
    audit = runner.invoke(cli_main.app, ["--json", "local-session", "audit"])

    assert preview.exit_code == 0
    assert json.loads(preview.stdout)["read_only"] is True
    assert context.exit_code == 0
    assert json.loads(context.stdout)["write_allowed"] is False
    assert status.exit_code == 0
    assert json.loads(status.stdout)["production_session"] is False
    assert boundary.exit_code == 0
    assert json.loads(boundary.stdout)["status"] == "passed"
    assert audit.exit_code == 0
    assert json.loads(audit.stdout)["status"] == "passed"


def test_cli_local_session_has_no_login_logout_or_token_command(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    for command in ["login", "logout", "token", "cookie", "credential"]:
        result = runner.invoke(cli_main.app, ["local-session", command])
        assert result.exit_code != 0
