from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from typer.testing import CliRunner

from aion_sdk.cli import main as cli_main
from aion_sdk.config import AIONClientConfig

runner = CliRunner()


class FakeGoldenPath:
    def list_scenarios(self, scope: list[str], **kwargs: object) -> dict[str, object]:
        return {"scenarios": {"scope": scope, **kwargs}}

    def seed_default_scenarios(self, scope: list[str], *, dry_run: bool) -> dict[str, object]:
        return {"scenario_seed": {"scope": scope, "dry_run": dry_run}}

    def list_fixtures(self, scope: list[str], **kwargs: object) -> dict[str, object]:
        return {"fixtures": {"scope": scope, **kwargs}}

    def seed_default_fixtures(self, scope: list[str], *, dry_run: bool) -> dict[str, object]:
        return {"fixture_seed": {"scope": scope, "dry_run": dry_run}}

    def run(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"run": payload}

    def list_runs(self, scope: list[str], **kwargs: object) -> dict[str, object]:
        return {"runs": {"scope": scope, **kwargs}}

    def list_reports(self, scope: list[str], **kwargs: object) -> dict[str, object]:
        return {"reports": {"scope": scope, **kwargs}}

    def release_smoke(self, scope: list[str]) -> dict[str, object]:
        return {"release_smoke": {"scope": scope}}

    def query(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"query": payload}


class FakeClient:
    def __init__(self, config: AIONClientConfig) -> None:
        self.config = config
        self.golden_path = FakeGoldenPath()


def test_cli_golden_path_scenarios_and_fixtures(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    scenarios = runner.invoke(cli_main.app, ["--json", "golden-path", "scenarios"])
    scenario_seed = runner.invoke(
        cli_main.app,
        ["--json", "golden-path", "scenarios", "seed"],
    )
    fixtures = runner.invoke(cli_main.app, ["--json", "golden-path", "fixtures"])
    fixture_seed = runner.invoke(
        cli_main.app,
        ["--json", "golden-path", "fixtures", "seed"],
    )

    assert scenarios.exit_code == 0
    assert json.loads(scenarios.stdout)["scenarios"]["scope"] == ["workspace:main"]
    assert scenario_seed.exit_code == 0
    assert json.loads(scenario_seed.stdout)["scenario_seed"]["dry_run"] is True
    assert fixtures.exit_code == 0
    assert fixture_seed.exit_code == 0


def test_cli_golden_path_run_and_query(monkeypatch, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))
    payload_path = _write_payload(tmp_path, {"scenario_keys": ["golden.boot.readiness"]})

    run = runner.invoke(
        cli_main.app,
        ["--json", "golden-path", "run", "--payload-file", str(payload_path)],
    )
    query = runner.invoke(
        cli_main.app,
        ["--json", "golden-path", "query", "--status", "failed"],
    )

    assert run.exit_code == 0
    assert json.loads(run.stdout)["run"]["mode"] == "dry_run"
    assert query.exit_code == 0
    assert json.loads(query.stdout)["query"]["status"] == "failed"


def test_cli_golden_path_runs_reports_release_smoke(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    runs = runner.invoke(cli_main.app, ["--json", "golden-path", "runs"])
    reports = runner.invoke(cli_main.app, ["--json", "golden-path", "reports"])
    smoke = runner.invoke(cli_main.app, ["--json", "golden-path", "release-smoke"])

    assert runs.exit_code == 0
    assert reports.exit_code == 0
    assert smoke.exit_code == 0
    assert json.loads(smoke.stdout)["release_smoke"]["scope"] == ["workspace:main"]


def _write_payload(tmp_path: Path, payload: dict[str, Any]) -> Path:
    path = tmp_path / "payload.json"
    path.write_text(json.dumps(payload))
    return path
