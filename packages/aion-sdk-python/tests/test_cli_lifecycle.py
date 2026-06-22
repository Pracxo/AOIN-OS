from __future__ import annotations

import json
from typing import Any

from typer.testing import CliRunner

from aion_sdk.cli import main as cli_main
from aion_sdk.config import AIONClientConfig

runner = CliRunner()


class FakeLifecycle:
    def seed_default_policies(self, scope: list[str], *, dry_run: bool = True) -> dict[str, object]:
        return {"seed": {"scope": scope, "dry_run": dry_run}}

    def evaluate(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"evaluate": payload}

    def create_purge_preview(
        self,
        resource_uris: list[str],
        scope: list[str],
    ) -> dict[str, object]:
        return {"purge": {"resource_uris": resource_uris, "scope": scope}}

    def report(self, scope: list[str]) -> dict[str, object]:
        return {"report": {"scope": scope}}


class FakeClient:
    def __init__(self, config: AIONClientConfig) -> None:
        self.config = config
        self.lifecycle = FakeLifecycle()


def test_cli_lifecycle_seed_defaults_is_dry_run(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    result = runner.invoke(cli_main.app, ["--json", "lifecycle", "seed-defaults"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)["seed"]
    assert payload["scope"] == ["workspace:main"]
    assert payload["dry_run"] is True


def test_cli_lifecycle_evaluate_defaults_to_dry_run(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    result = runner.invoke(cli_main.app, ["--json", "lifecycle", "evaluate"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)["evaluate"]
    assert payload["owner_scope"] == ["workspace:main"]
    assert payload["mode"] == "dry_run"


def test_cli_lifecycle_purge_preview(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    result = runner.invoke(
        cli_main.app,
        [
            "--json",
            "lifecycle",
            "purge-preview",
            "--resource-uri",
            "aion://generic/res-1",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)["purge"]
    assert payload["resource_uris"] == ["aion://generic/res-1"]


def test_cli_lifecycle_report(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    result = runner.invoke(cli_main.app, ["--json", "lifecycle", "report"])

    assert result.exit_code == 0
    assert json.loads(result.stdout)["report"]["scope"] == ["workspace:main"]
