from __future__ import annotations

import json
from typing import Any

from typer.testing import CliRunner

from aion_sdk.cli import main as cli_main
from aion_sdk.config import AIONClientConfig

runner = CliRunner()


class FakeSelfModel:
    def describe(self, scope: list[str], **kwargs: object) -> dict[str, object]:
        return {"scope": scope, "kind": "description", "kwargs": kwargs}

    def capabilities(
        self,
        scope: list[str],
        *,
        status: str | None = None,
        capability_type: str | None = None,
    ) -> list[dict[str, object]]:
        return [{"scope": scope, "status": status, "capability_type": capability_type}]

    def refresh_capabilities(self, scope: list[str], dry_run: bool = True) -> dict[str, object]:
        return {"scope": scope, "dry_run": dry_run}

    def list_limitations(
        self,
        scope: list[str],
        *,
        status: str | None = None,
        severity: str | None = None,
    ) -> list[dict[str, object]]:
        return [{"scope": scope, "status": status, "severity": severity}]

    def seed_limitations(self, scope: list[str], dry_run: bool = True) -> dict[str, object]:
        return {"scope": scope, "dry_run": dry_run}

    def calibrate_confidence(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"calibration_id": "confidence-1", "payload": payload}

    def run_assessment(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"self_assessment_id": "assessment-1", "payload": payload}

    def create_introspection(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"introspection_snapshot_id": "snapshot-1", "payload": payload}

    def list_introspection(
        self,
        scope: list[str],
        *,
        snapshot_type: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, object]]:
        return [{"scope": scope, "snapshot_type": snapshot_type, "limit": limit}]


class FakeClient:
    def __init__(self, config: AIONClientConfig) -> None:
        self.config = config
        self.self_model = FakeSelfModel()


def test_cli_self_describe(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    result = runner.invoke(cli_main.app, ["--json", "self", "describe"])

    assert result.exit_code == 0
    assert json.loads(result.stdout)["kind"] == "description"


def test_cli_self_capabilities_default_and_refresh(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    listed = runner.invoke(cli_main.app, ["--json", "self", "capabilities"])
    refreshed = runner.invoke(cli_main.app, ["--json", "self", "capabilities", "refresh"])

    assert listed.exit_code == 0
    assert json.loads(listed.stdout)[0]["scope"] == ["workspace:main"]
    assert refreshed.exit_code == 0
    assert json.loads(refreshed.stdout)["dry_run"] is True


def test_cli_self_assessment_and_introspection(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    assessment = runner.invoke(cli_main.app, ["--json", "self", "assessment", "run"])
    introspection = runner.invoke(cli_main.app, ["--json", "self", "introspection", "create"])

    assert assessment.exit_code == 0
    assert json.loads(assessment.stdout)["self_assessment_id"] == "assessment-1"
    assert introspection.exit_code == 0
    assert json.loads(introspection.stdout)["introspection_snapshot_id"] == "snapshot-1"
