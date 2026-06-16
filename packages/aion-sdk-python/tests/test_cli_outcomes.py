from __future__ import annotations

import json
from typing import Any

from typer.testing import CliRunner

from aion_sdk.cli import main as cli_main
from aion_sdk.config import AIONClientConfig

runner = CliRunner()


class FakeOutcomes:
    def create(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"outcome_id": "outcome-1", "payload": payload}

    def query(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"outcomes": [], "payload": payload}

    def create_expected_effect(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"expected_effect_id": "expected-1", "payload": payload}

    def create_observed_effect(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"observed_effect_id": "observed-1", "payload": payload}

    def verify(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"verification_run_id": "verification-1", "payload": payload}

    def list_feedback(
        self,
        *,
        outcome_id: str | None = None,
        status: str | None = None,
        severity: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, object]]:
        return [{"outcome_id": outcome_id, "status": status, "severity": severity, "limit": limit}]

    def resolve_feedback(self, outcome_feedback_id: str, reason: str) -> dict[str, object]:
        return {"outcome_feedback_id": outcome_feedback_id, "reason": reason}

    def learning_bridge(self, outcome_id: str, dry_run: bool = True) -> dict[str, object]:
        return {"outcome_id": outcome_id, "dry_run": dry_run}


class FakeClient:
    def __init__(self, config: AIONClientConfig) -> None:
        self.config = config
        self.outcomes = FakeOutcomes()


def test_cli_outcomes_verify_and_feedback_list(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    verified = runner.invoke(
        cli_main.app,
        ["--json", "outcomes", "verify", "--source-type", "command", "--source-id", "command-1"],
    )
    feedback = runner.invoke(
        cli_main.app,
        ["--json", "outcomes", "feedback", "list", "--status", "open"],
    )

    assert verified.exit_code == 0
    assert json.loads(verified.stdout)["verification_run_id"] == "verification-1"
    assert feedback.exit_code == 0
    assert json.loads(feedback.stdout)[0]["status"] == "open"


def test_cli_outcomes_learning_bridge_defaults_to_dry_run(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    result = runner.invoke(
        cli_main.app,
        ["--json", "outcomes", "learning-bridge", "--outcome-id", "outcome-1"],
    )

    assert result.exit_code == 0
    assert json.loads(result.stdout)["dry_run"] is True
