from __future__ import annotations

import json
from typing import Any

from typer.testing import CliRunner

from aion_sdk.cli import main as cli_main
from aion_sdk.config import AIONClientConfig

runner = CliRunner()


class FakeDecisions:
    def create_frame(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"decision_frame_id": "frame-1", "payload": payload}

    def list_frames(
        self,
        scope: list[str],
        *,
        status: str | None = None,
        frame_type: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, object]]:
        return [{"scope": scope, "status": status, "frame_type": frame_type, "limit": limit}]

    def create_option(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"decision_option_id": "option-1", "payload": payload}

    def evaluate(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"recommended_option_id": "option-1", "payload": payload}

    def recommend(self, decision_frame_id: str, payload: dict[str, Any]) -> dict[str, object]:
        return {"decision_frame_id": decision_frame_id, "payload": payload}

    def run_counterfactual(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"counterfactual_run_id": "counterfactual-1", "payload": payload}

    def record_decision(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"decision_record_id": "record-1", "payload": payload}

    def list_decision_records(
        self,
        scope: list[str],
        *,
        decision_frame_id: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, object]]:
        return [{"scope": scope, "decision_frame_id": decision_frame_id, "limit": limit}]


class FakeClient:
    def __init__(self, config: AIONClientConfig) -> None:
        self.config = config
        self.decisions = FakeDecisions()


def test_cli_decisions_evaluate_and_counterfactual(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    evaluated = runner.invoke(
        cli_main.app,
        ["--json", "decisions", "evaluate", "--frame-id", "frame-1"],
    )
    counterfactual = runner.invoke(
        cli_main.app,
        ["--json", "decisions", "counterfactual", "run", "--frame-id", "frame-1"],
    )

    assert evaluated.exit_code == 0
    assert json.loads(evaluated.stdout)["recommended_option_id"] == "option-1"
    assert counterfactual.exit_code == 0
    assert json.loads(counterfactual.stdout)["counterfactual_run_id"] == "counterfactual-1"


def test_cli_decisions_record_and_help(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    help_result = runner.invoke(cli_main.app, ["decisions", "--help"])
    recorded = runner.invoke(
        cli_main.app,
        [
            "--json",
            "decisions",
            "journal",
            "record",
            "--frame-id",
            "frame-1",
            "--rationale",
            "Record only.",
        ],
    )

    assert help_result.exit_code == 0
    assert "Decision intelligence commands" in help_result.stdout
    assert recorded.exit_code == 0
    assert json.loads(recorded.stdout)["decision_record_id"] == "record-1"
