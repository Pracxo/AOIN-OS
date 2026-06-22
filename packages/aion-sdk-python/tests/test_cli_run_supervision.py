from __future__ import annotations

import json
from typing import Any

from typer.testing import CliRunner

from aion_sdk.cli import main as cli_main
from aion_sdk.config import AIONClientConfig

runner = CliRunner()


class FakeRunSupervision:
    def list_runs(self, scope: list[str], **kwargs: object) -> dict[str, object]:
        return {"runs": [], "scope": scope, "kwargs": kwargs}

    def sample(self, run_supervision_id: str, scope: list[str]) -> dict[str, object]:
        return {"sample": run_supervision_id, "scope": scope}

    def sample_many(
        self, scope: list[str], status: str | None = "active", limit: int = 100
    ) -> dict[str, object]:
        return {"scope": scope, "status": status, "limit": limit}

    def list_timeout_policies(self, scope: list[str], **kwargs: object) -> dict[str, object]:
        return {"policies": [], "scope": scope, "kwargs": kwargs}

    def create_report(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"report": payload}

    def create_control_request(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"control": payload}

    def handoff_control(
        self, run_control_request_id: str, approval_present: bool = False
    ) -> dict[str, object]:
        return {"handoff": run_control_request_id, "approval_present": approval_present}

    def propose_compensation(
        self, run_supervision_id: str, trigger_reason: str
    ) -> dict[str, object]:
        return {"run_supervision_id": run_supervision_id, "trigger_reason": trigger_reason}

    def list_compensation_plans(self, scope: list[str], **kwargs: object) -> dict[str, object]:
        return {"plans": [], "scope": scope, "kwargs": kwargs}


class FakeClient:
    def __init__(self, config: AIONClientConfig) -> None:
        self.config = config
        self.run_supervision = FakeRunSupervision()


def test_cli_run_supervision_sample(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    result = runner.invoke(
        cli_main.app,
        ["--json", "run-supervision", "sample", "--run-supervision-id", "run-1"],
    )

    assert result.exit_code == 0
    assert json.loads(result.stdout)["sample"] == "run-1"


def test_cli_run_supervision_compensation_propose(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    result = runner.invoke(
        cli_main.app,
        [
            "--json",
            "run-supervision",
            "compensation",
            "propose",
            "--run-supervision-id",
            "run-1",
            "--trigger-reason",
            "failed",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["run_supervision_id"] == "run-1"
    assert payload["trigger_reason"] == "failed"
