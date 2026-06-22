from __future__ import annotations

import json
from typing import Any

from typer.testing import CliRunner

from aion_sdk.cli import main as cli_main
from aion_sdk.config import AIONClientConfig

runner = CliRunner()


class FakeSecurity:
    def run_scan(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"security_scan_id": "scan-1", "scan_type": payload["scan_type"]}

    def run_hardening_gate(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"hardening_gate_id": "gate-1", "version": payload["version"]}

    def seed_threat_models(self, owner_scope: list[str], dry_run: bool = True) -> dict[str, object]:
        return {"owner_scope": owner_scope, "dry_run": dry_run}

    def list_threat_models(
        self,
        *,
        status: str | None = None,
        category: str | None = None,
    ) -> dict[str, object]:
        return {"status": status, "category": category}

    def seed_controls(self, dry_run: bool = True) -> dict[str, object]:
        return {"dry_run": dry_run}

    def list_controls(
        self,
        *,
        status: str | None = None,
        category: str | None = None,
    ) -> dict[str, object]:
        return {"status": status, "category": category}

    def list_scans(
        self,
        *,
        scan_type: str | None = None,
        status: str | None = None,
    ) -> dict[str, object]:
        return {"scan_type": scan_type, "status": status}

    def get_hardening_gate(self, hardening_gate_id: str) -> dict[str, object]:
        return {"hardening_gate_id": hardening_gate_id}


class FakeClient:
    def __init__(self, config: AIONClientConfig) -> None:
        self.config = config
        self.security = FakeSecurity()


def _install_fake(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))


def _json(result) -> Any:  # type: ignore[no-untyped-def]
    return json.loads(result.stdout)


def test_cli_security_scan_works_with_mocked_sdk(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    _install_fake(monkeypatch)

    result = runner.invoke(cli_main.app, ["--json", "security", "scan"])

    assert result.exit_code == 0
    assert _json(result)["security_scan_id"] == "scan-1"


def test_cli_security_hardening_gate_run_works_with_mocked_sdk(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    _install_fake(monkeypatch)

    result = runner.invoke(cli_main.app, ["--json", "security", "hardening-gate", "run"])

    assert result.exit_code == 0
    assert _json(result)["hardening_gate_id"] == "gate-1"
