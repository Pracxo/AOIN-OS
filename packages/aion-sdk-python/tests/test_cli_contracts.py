from __future__ import annotations

import json
from typing import Any

from typer.testing import CliRunner

from aion_sdk.cli import main as cli_main
from aion_sdk.config import AIONClientConfig

runner = CliRunner()


class FakeContracts:
    def list_contracts(self, scope: list[str], **kwargs: object) -> dict[str, object]:
        return {"contracts": {"scope": scope, **kwargs}}

    def list_interfaces(self, scope: list[str], **kwargs: object) -> dict[str, object]:
        return {"interfaces": {"scope": scope, **kwargs}}

    def create_snapshot(self, scope: list[str], snapshot_type: str = "manual") -> dict[str, object]:
        return {"snapshot": {"scope": scope, "snapshot_type": snapshot_type}}

    def list_snapshots(self, scope: list[str], **kwargs: object) -> dict[str, object]:
        return {"snapshots": {"scope": scope, **kwargs}}

    def list_rules(self, scope: list[str], **kwargs: object) -> dict[str, object]:
        return {"rules": {"scope": scope, **kwargs}}

    def seed_rules(self, scope: list[str], dry_run: bool = True) -> dict[str, object]:
        return {"seed": {"scope": scope, "dry_run": dry_run}}

    def scan_compatibility(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"scan": payload}

    def findings(self, **kwargs: object) -> dict[str, object]:
        return {"findings": kwargs}

    def migration_notes(self, scope: list[str], **kwargs: object) -> dict[str, object]:
        return {"migration_notes": {"scope": scope, **kwargs}}

    def report(self, scope: list[str]) -> dict[str, object]:
        return {"report": {"scope": scope}}


class FakeClient:
    def __init__(self, config: AIONClientConfig) -> None:
        self.config = config
        self.contracts = FakeContracts()


def test_cli_contracts_scan_defaults_to_dry_run(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    result = runner.invoke(cli_main.app, ["--json", "contracts", "scan"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)["scan"]
    assert payload["mode"] == "dry_run"
    assert payload["owner_scope"] == ["workspace:main"]


def test_cli_contracts_findings(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    result = runner.invoke(cli_main.app, ["--json", "contracts", "findings", "--status", "open"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)["findings"]
    assert payload["status"] == "open"


def test_cli_contracts_snapshot_and_report(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    snapshot = runner.invoke(cli_main.app, ["--json", "contracts", "snapshot"])
    report = runner.invoke(cli_main.app, ["--json", "contracts", "report"])

    assert snapshot.exit_code == 0
    assert json.loads(snapshot.stdout)["snapshot"]["snapshot_type"] == "manual"
    assert report.exit_code == 0
    assert json.loads(report.stdout)["report"]["scope"] == ["workspace:main"]
