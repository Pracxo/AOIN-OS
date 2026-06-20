from __future__ import annotations

import json
from typing import Any

from typer.testing import CliRunner

from aion_sdk.cli import main as cli_main
from aion_sdk.config import AIONClientConfig

runner = CliRunner()


class FakeExplanations:
    def explain(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"explanation_id": "explanation-1", "payload": payload}

    def why_not(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"why_not_id": "why-not-1", "payload": payload}

    def trace_narrative(self, trace_id: str, payload: dict[str, Any]) -> dict[str, object]:
        return {"trace_id": trace_id, "payload": payload}

    def verify(self, explanation_id: str) -> dict[str, object]:
        return {"explanation_id": explanation_id, "status": "passed"}

    def feedback(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"feedback": payload}


class FakeClient:
    def __init__(self, config: AIONClientConfig) -> None:
        self.config = config
        self.explanations = FakeExplanations()


def test_cli_explain_target_and_why_not(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    target = runner.invoke(
        cli_main.app,
        ["--json", "explain", "target", "--target-type", "trace", "--target-id", "trace-1"],
    )
    why_not = runner.invoke(
        cli_main.app,
        ["--json", "explain", "why-not", "--target-type", "trace", "--question", "Why not?"],
    )

    assert target.exit_code == 0
    assert json.loads(target.stdout)["explanation_id"] == "explanation-1"
    assert why_not.exit_code == 0
    assert json.loads(why_not.stdout)["why_not_id"] == "why-not-1"


def test_cli_explain_trace_verify_and_feedback(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    trace = runner.invoke(cli_main.app, ["--json", "explain", "trace", "--trace-id", "trace-1"])
    verify = runner.invoke(
        cli_main.app,
        ["--json", "explain", "verify", "--explanation-id", "explanation-1"],
    )
    feedback = runner.invoke(
        cli_main.app,
        [
            "--json",
            "explain",
            "feedback",
            "--explanation-id",
            "explanation-1",
            "--type",
            "helpful",
            "--rating",
            "5",
        ],
    )

    assert trace.exit_code == 0
    assert json.loads(trace.stdout)["trace_id"] == "trace-1"
    assert verify.exit_code == 0
    assert json.loads(verify.stdout)["status"] == "passed"
    assert feedback.exit_code == 0
    assert json.loads(feedback.stdout)["feedback"]["rating"] == 5
