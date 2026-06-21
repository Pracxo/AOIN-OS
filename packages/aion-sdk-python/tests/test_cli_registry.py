from __future__ import annotations

import json
from typing import Any

from typer.testing import CliRunner

from aion_sdk.cli import main as cli_main
from aion_sdk.config import AIONClientConfig

runner = CliRunner()


class FakeRegistry:
    def query(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"query": payload}

    def validate(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"validate": payload}

    def rebuild(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"rebuild": payload}

    def create_snapshot(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"snapshot": payload}


class FakeClient:
    def __init__(self, config: AIONClientConfig) -> None:
        self.config = config
        self.registry = FakeRegistry()


def test_cli_registry_query(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    result = runner.invoke(cli_main.app, ["--json", "registry", "query", "--query", "thing"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)["query"]
    assert payload["query"] == "thing"
    assert payload["scope"] == ["workspace:main"]


def test_cli_registry_validate_defaults_to_dry_run(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    result = runner.invoke(cli_main.app, ["--json", "registry", "validate"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)["validate"]
    assert payload["mode"] == "dry_run"


def test_cli_registry_rebuild_can_run_controlled(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    result = runner.invoke(cli_main.app, ["--json", "registry", "rebuild", "--controlled"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)["rebuild"]
    assert payload["mode"] == "controlled"


def test_cli_registry_snapshot(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    result = runner.invoke(cli_main.app, ["--json", "registry", "snapshot"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)["snapshot"]
    assert payload["snapshot_type"] == "manual"
