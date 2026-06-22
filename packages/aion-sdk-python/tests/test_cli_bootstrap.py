from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from typer.testing import CliRunner

from aion_sdk.cli import main as cli_main
from aion_sdk.config import AIONClientConfig

runner = CliRunner()


class FakeBootstrap:
    def list_profiles(self, scope: list[str], **kwargs: object) -> dict[str, object]:
        return {"profiles": {"scope": scope, **kwargs}}

    def seed_profiles(self, scope: list[str], *, dry_run: bool) -> dict[str, object]:
        return {"profile_seed": {"scope": scope, "dry_run": dry_run}}

    def list_seed_bundles(self, scope: list[str], **kwargs: object) -> dict[str, object]:
        return {"seed_bundles": {"scope": scope, **kwargs}}

    def seed_bundles(self, scope: list[str], *, dry_run: bool) -> dict[str, object]:
        return {"bundle_seed": {"scope": scope, "dry_run": dry_run}}

    def seed(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"seed": payload}

    def doctor(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"doctor": payload}

    def run(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"run": payload}

    def list_runs(self, scope: list[str], **kwargs: object) -> dict[str, object]:
        return {"runs": {"scope": scope, **kwargs}}

    def list_findings(self, scope: list[str], **kwargs: object) -> dict[str, object]:
        return {"findings": {"scope": scope, **kwargs}}

    def list_reports(self, scope: list[str], **kwargs: object) -> dict[str, object]:
        return {"reports": {"scope": scope, **kwargs}}


class FakeClient:
    def __init__(self, config: AIONClientConfig) -> None:
        self.config = config
        self.bootstrap = FakeBootstrap()


def test_cli_bootstrap_profiles_and_seed_bundles(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    profiles = runner.invoke(cli_main.app, ["--json", "bootstrap", "profiles"])
    profile_seed = runner.invoke(cli_main.app, ["--json", "bootstrap", "profiles", "seed"])
    bundles = runner.invoke(cli_main.app, ["--json", "bootstrap", "seed-bundles"])
    bundle_seed = runner.invoke(cli_main.app, ["--json", "bootstrap", "seed-bundles", "seed"])

    assert profiles.exit_code == 0
    assert json.loads(profiles.stdout)["profiles"]["scope"] == ["workspace:main"]
    assert profile_seed.exit_code == 0
    assert json.loads(profile_seed.stdout)["profile_seed"]["dry_run"] is True
    assert bundles.exit_code == 0
    assert bundle_seed.exit_code == 0


def test_cli_bootstrap_seed_doctor_and_run(monkeypatch, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))
    payload_path = _write_payload(tmp_path, {"metadata": {"source": "test"}})

    seed = runner.invoke(
        cli_main.app,
        ["--json", "bootstrap", "seed", "--seed-bundle-key", "core.defaults"],
    )
    doctor = runner.invoke(cli_main.app, ["--json", "bootstrap", "doctor"])
    run = runner.invoke(
        cli_main.app,
        ["--json", "bootstrap", "run", "--payload-file", str(payload_path)],
    )

    assert seed.exit_code == 0
    assert json.loads(seed.stdout)["seed"]["mode"] == "dry_run"
    assert doctor.exit_code == 0
    assert json.loads(doctor.stdout)["doctor"]["create_findings"] is True
    assert run.exit_code == 0
    assert json.loads(run.stdout)["run"]["profile_key"] == "local.dev"


def test_cli_bootstrap_runs_findings_reports(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    runs = runner.invoke(cli_main.app, ["--json", "bootstrap", "runs"])
    findings = runner.invoke(cli_main.app, ["--json", "bootstrap", "findings"])
    reports = runner.invoke(cli_main.app, ["--json", "bootstrap", "reports"])

    assert runs.exit_code == 0
    assert findings.exit_code == 0
    assert reports.exit_code == 0
    assert json.loads(reports.stdout)["reports"]["scope"] == ["workspace:main"]


def _write_payload(tmp_path: Path, payload: dict[str, Any]) -> Path:
    path = tmp_path / "payload.json"
    path.write_text(json.dumps(payload))
    return path
