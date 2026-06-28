from __future__ import annotations

import json
from typing import Any

from typer.testing import CliRunner

from aion_sdk.cli import main as cli_main
from aion_sdk.config import AIONClientConfig

runner = CliRunner()


class FakeAuthRuntime:
    def status(self, scope: list[str]) -> dict[str, object]:
        return {"scope": scope, "auth_runtime_enabled": False}

    def mock_claims_preview(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"payload": payload, "production_identity": False}

    def audit(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"status": "passed", "payload": payload, "mock_only": True}


class FakeClient:
    def __init__(self, config: AIONClientConfig) -> None:
        self.config = config
        self.auth_runtime = FakeAuthRuntime()


def test_cli_auth_runtime_commands(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    status = runner.invoke(cli_main.app, ["--json", "auth-runtime", "status"])
    preview = runner.invoke(
        cli_main.app,
        [
            "--json",
            "auth-runtime",
            "mock-claims-preview",
            "--subject",
            "local.operator",
            "--role",
            "operator",
        ],
    )
    audit = runner.invoke(cli_main.app, ["--json", "auth-runtime", "audit"])
    login = runner.invoke(cli_main.app, ["auth-runtime", "login"])

    assert status.exit_code == 0
    assert json.loads(status.stdout)["auth_runtime_enabled"] is False
    assert preview.exit_code == 0
    assert json.loads(preview.stdout)["payload"]["mode"] == "preview"
    assert audit.exit_code == 0
    assert json.loads(audit.stdout)["mock_only"] is True
    assert login.exit_code != 0
