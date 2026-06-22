from __future__ import annotations

import json
from typing import Any

from typer.testing import CliRunner

from aion_sdk.cli import main as cli_main
from aion_sdk.config import AIONClientConfig

runner = CliRunner()


class FakeScheduler:
    def list_schedules(self, scope: list[str], **kwargs: Any) -> dict[str, object]:
        return {"scope": scope, "kwargs": kwargs}

    def run_tick(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"tick": payload}

    def create_report(self, scope: list[str]) -> dict[str, object]:
        return {"report_scope": scope}


class FakeClient:
    def __init__(self, config: AIONClientConfig) -> None:
        self.config = config
        self.scheduler = FakeScheduler()


def test_cli_scheduler_list(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    result = runner.invoke(cli_main.app, ["--json", "scheduler", "schedules", "list"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["scope"] == ["workspace:main"]


def test_cli_scheduler_tick(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    result = runner.invoke(cli_main.app, ["--json", "scheduler", "tick", "--mode", "dry_run"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)["tick"]
    assert payload["mode"] == "dry_run"
    assert payload["scope"] == ["workspace:main"]


def test_cli_scheduler_report(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    result = runner.invoke(cli_main.app, ["--json", "scheduler", "report"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["report_scope"] == ["workspace:main"]
