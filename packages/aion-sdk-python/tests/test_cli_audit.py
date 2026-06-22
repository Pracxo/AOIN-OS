from __future__ import annotations

import json
from typing import Any

from typer.testing import CliRunner

from aion_sdk.cli import main as cli_main
from aion_sdk.config import AIONClientConfig

runner = CliRunner()


class FakeAudit:
    def status(self) -> dict[str, object]:
        return {"latest_sequence": 1}

    def verify(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"status": "passed", "metadata": payload.get("metadata")}

    def trace_provenance(self, trace_id: str, limit: int = 500) -> list[dict[str, object]]:
        return [{"trace_id": trace_id, "limit": limit}]


class FakeClient:
    def __init__(self, config: AIONClientConfig) -> None:
        self.config = config
        self.audit = FakeAudit()


def test_cli_audit_status_and_verify(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    status = runner.invoke(cli_main.app, ["--json", "audit", "status"])
    verify = runner.invoke(cli_main.app, ["--json", "audit", "verify"])

    assert status.exit_code == 0
    assert json.loads(status.stdout)["latest_sequence"] == 1
    assert verify.exit_code == 0
    assert json.loads(verify.stdout)["status"] == "passed"


def test_cli_provenance_trace(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    result = runner.invoke(
        cli_main.app,
        ["--json", "provenance", "trace", "--trace-id", "trace-1"],
    )

    assert result.exit_code == 0
    assert json.loads(result.stdout)[0]["trace_id"] == "trace-1"
