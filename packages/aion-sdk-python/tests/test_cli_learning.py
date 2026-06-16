from __future__ import annotations

import json
from typing import Any

from typer.testing import CliRunner

from aion_sdk.cli import main as cli_main
from aion_sdk.config import AIONClientConfig

runner = CliRunner()


class FakeLearning:
    def create_experience(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"experience_id": "experience-1", "payload": payload}

    def query(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"experiences": [], "payload": payload}

    def mine_patterns(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"pattern_mining_run_id": "mine-1", "payload": payload}

    def synthesize(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"synthesis_run_id": "synthesis-1", "payload": payload}

    def list_skill_suggestions(
        self,
        *,
        scope: list[str],
        status: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, object]]:
        return [{"scope": scope, "status": status, "limit": limit}]

    def accept_regression_suggestion(
        self,
        regression_suggestion_id: str,
        reason: str,
    ) -> dict[str, object]:
        return {"regression_suggestion_id": regression_suggestion_id, "reason": reason}


class FakeClient:
    def __init__(self, config: AIONClientConfig) -> None:
        self.config = config
        self.learning = FakeLearning()


def test_cli_learning_experience_create(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    result = runner.invoke(
        cli_main.app,
        [
            "--json",
            "learning",
            "experiences",
            "create",
            "--source-type",
            "generic",
            "--source-id",
            "source-1",
            "--title",
            "Experience",
            "--summary",
            "Generic experience",
        ],
    )

    assert result.exit_code == 0
    assert json.loads(result.stdout)["experience_id"] == "experience-1"


def test_cli_learning_synthesize(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    result = runner.invoke(
        cli_main.app,
        [
            "--json",
            "learning",
            "synthesize",
            "--experience-id",
            "experience-1",
        ],
    )

    assert result.exit_code == 0
    assert json.loads(result.stdout)["synthesis_run_id"] == "synthesis-1"


def test_cli_learning_suggestion_commands(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    skills = runner.invoke(
        cli_main.app,
        ["--json", "learning", "skill-suggestions", "list", "--status", "suggested"],
    )
    regression = runner.invoke(
        cli_main.app,
        [
            "--json",
            "learning",
            "regression-suggestions",
            "accept",
            "--id",
            "regression-1",
            "--reason",
            "reviewed",
        ],
    )

    assert skills.exit_code == 0
    assert json.loads(skills.stdout)[0]["status"] == "suggested"
    assert regression.exit_code == 0
    assert json.loads(regression.stdout)["regression_suggestion_id"] == "regression-1"
