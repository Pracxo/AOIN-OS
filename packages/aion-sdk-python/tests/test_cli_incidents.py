from __future__ import annotations

import json
from typing import Any

from typer.testing import CliRunner

from aion_sdk.cli import main as cli_main
from aion_sdk.config import AIONClientConfig

runner = CliRunner()


class FakeIncidents:
    def query(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"query": payload}

    def correlate(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"correlate": payload}

    def generate_root_causes(self, incident_id: str, scope: list[str]) -> dict[str, object]:
        return {"incident_id": incident_id, "scope": scope}

    def create_recovery_review(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"review": payload}


class FakeClient:
    def __init__(self, config: AIONClientConfig) -> None:
        self.config = config
        self.incidents = FakeIncidents()


def test_cli_incidents_query(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    result = runner.invoke(cli_main.app, ["--json", "incidents", "query"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["query"]["scope"] == ["workspace:main"]


def test_cli_incidents_correlate_defaults_to_dry_run(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    result = runner.invoke(cli_main.app, ["--json", "incidents", "correlate"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)["correlate"]
    assert payload["owner_scope"] == ["workspace:main"]
    assert payload["mode"] == "dry_run"


def test_cli_incidents_root_causes_generate(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    result = runner.invoke(
        cli_main.app,
        ["--json", "incidents", "root-causes", "generate", "--incident-id", "incident-1"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["incident_id"] == "incident-1"


def test_cli_incidents_recovery_review(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    result = runner.invoke(
        cli_main.app,
        ["--json", "incidents", "recovery-review", "--incident-id", "incident-1"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)["review"]
    assert payload["create_action_proposals"] is False
