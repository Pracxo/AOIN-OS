from __future__ import annotations

import json
from typing import Any

from typer.testing import CliRunner

from aion_sdk.cli import main as cli_main
from aion_sdk.config import AIONClientConfig

runner = CliRunner()


class FakeVersioning:
    def create_manifest(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"version": payload["version"], "status": "active"}

    def seed_features(self, scope: list[str], dry_run: bool = True) -> dict[str, object]:
        return {"feature_count": 1, "scope": scope, "dry_run": dry_run}

    def generate_compatibility(self, version: str, scope: list[str]) -> dict[str, object]:
        return {"version": version, "status": "warning", "scope": scope}

    def run_freeze_gate(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"version": payload["version"], "status": "passed"}


class FakeClient:
    def __init__(self, config: AIONClientConfig) -> None:
        self.config = config
        self.versioning = FakeVersioning()


def _install_fake(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))


def _json(result) -> Any:  # type: ignore[no-untyped-def]
    return json.loads(result.stdout)


def test_cli_versioning_manifest_create_works(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    _install_fake(monkeypatch)

    result = runner.invoke(
        cli_main.app,
        ["--json", "versioning", "manifests", "create", "--version", "0.1.0"],
    )

    assert result.exit_code == 0
    assert _json(result)["status"] == "active"


def test_cli_versioning_features_seed_defaults_works(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    _install_fake(monkeypatch)

    result = runner.invoke(
        cli_main.app,
        ["--json", "versioning", "features", "seed-defaults"],
    )

    assert result.exit_code == 0
    assert _json(result)["feature_count"] == 1


def test_cli_freeze_run_works(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    _install_fake(monkeypatch)

    result = runner.invoke(cli_main.app, ["--json", "freeze", "run", "--version", "0.1.0"])

    assert result.exit_code == 0
    assert _json(result)["status"] == "passed"
