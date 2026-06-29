from __future__ import annotations

import json
from typing import Any

from typer.testing import CliRunner

from aion_sdk.cli import main as cli_main
from aion_sdk.config import AIONClientConfig

runner = CliRunner()


class FakeConnectorRuntime:
    def status(self, scope: list[str]) -> dict[str, object]:
        return {"scope": scope, "connector_runtime_enabled": False}

    def validate_manifest(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"payload": payload, "valid": True, "status": "preview"}

    def egress_preview(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"payload": payload, "egress_allowed": False}

    def ingress_preview(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"payload": payload, "trusted": False}

    def audit(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"status": "passed", "payload": payload, "runtime_disabled": True}


class FakeClient:
    def __init__(self, config: AIONClientConfig) -> None:
        self.config = config
        self.connector_runtime = FakeConnectorRuntime()


def test_cli_connector_runtime_commands(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    status = runner.invoke(cli_main.app, ["--json", "connector-runtime", "status"])
    manifest = runner.invoke(
        cli_main.app,
        [
            "--json",
            "connector-runtime",
            "validate-manifest",
            "--connector-key",
            "mock.local.preview",
        ],
    )
    egress = runner.invoke(
        cli_main.app,
        ["--json", "connector-runtime", "egress-preview"],
    )
    ingress = runner.invoke(
        cli_main.app,
        ["--json", "connector-runtime", "ingress-preview"],
    )
    audit = runner.invoke(cli_main.app, ["--json", "connector-runtime", "audit"])
    activate = runner.invoke(cli_main.app, ["connector-runtime", "activate"])

    assert status.exit_code == 0
    assert json.loads(status.stdout)["connector_runtime_enabled"] is False
    assert manifest.exit_code == 0
    assert json.loads(manifest.stdout)["payload"]["external_calls_required"] is False
    assert egress.exit_code == 0
    assert json.loads(egress.stdout)["egress_allowed"] is False
    assert ingress.exit_code == 0
    assert json.loads(ingress.stdout)["trusted"] is False
    assert audit.exit_code == 0
    assert json.loads(audit.stdout)["runtime_disabled"] is True
    assert activate.exit_code != 0
