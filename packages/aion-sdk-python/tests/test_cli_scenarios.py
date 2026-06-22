from __future__ import annotations

import json
from typing import Any

from typer.testing import CliRunner

from aion_sdk.cli import main as cli_main
from aion_sdk.config import AIONClientConfig

runner = CliRunner()


class FakeScenarios:
    def list(
        self,
        *,
        status: str | None = None,
        scenario_type: str | None = None,
        tags: list[str] | None = None,
    ) -> list[dict[str, object]]:
        return [{"scenario_id": "golden_path_brain", "status": status or "active"}]

    def run(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"status": "passed", "scenario_id": payload.get("scenario_id")}

    def runs(
        self,
        *,
        scope: list[str],
        status: str | None = None,
        scenario_type: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, object]]:
        return [{"scenario_run_id": "run-1", "scope": scope, "limit": limit}]

    def seed_defaults(self, scope: list[str], dry_run: bool = True) -> dict[str, object]:
        return {"dry_run": dry_run, "scope": scope}

    def list_fixtures(
        self,
        scope: list[str],
        fixture_type: str | None = None,
    ) -> list[dict[str, object]]:
        return [{"fixture_id": "generic_event", "fixture_type": fixture_type or "event"}]

    def load_fixture(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"fixture_id": payload.get("fixture_id"), "loaded": False}

    def run_release_baseline(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"version": payload["version"], "status": "passed"}

    def get_release_baseline(self, release_baseline_id: str) -> dict[str, object]:
        return {"release_baseline_id": release_baseline_id, "status": "passed"}


class FakeClient:
    def __init__(self, config: AIONClientConfig) -> None:
        self.config = config
        self.scenarios = FakeScenarios()


def _install_fake(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))


def _json(result) -> Any:  # type: ignore[no-untyped-def]
    return json.loads(result.stdout)


def test_cli_scenarios_list_works(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    _install_fake(monkeypatch)

    result = runner.invoke(cli_main.app, ["--json", "scenarios", "list"])

    assert result.exit_code == 0
    assert _json(result)[0]["scenario_id"] == "golden_path_brain"


def test_cli_scenarios_run_works(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    _install_fake(monkeypatch)

    result = runner.invoke(
        cli_main.app,
        ["--json", "scenarios", "run", "--scenario-id", "golden_path_brain"],
    )

    assert result.exit_code == 0
    assert _json(result)["status"] == "passed"


def test_cli_release_baseline_run_works(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    _install_fake(monkeypatch)

    result = runner.invoke(
        cli_main.app,
        ["--json", "release-baseline", "run", "--version", "0.1.0"],
    )

    assert result.exit_code == 0
    assert _json(result)["version"] == "0.1.0"
