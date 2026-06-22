from __future__ import annotations

import json
from typing import Any

from typer.testing import CliRunner

from aion_sdk.cli import main as cli_main
from aion_sdk.config import AIONClientConfig

runner = CliRunner()


class FakeDialogue:
    def turn(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"response": {"response_id": "response-1"}, "payload": payload}

    def create_session(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"dialogue_session_id": "session-1", "payload": payload}

    def pending_clarifications(
        self,
        scope: list[str],
        dialogue_session_id: str | None = None,
    ) -> list[dict[str, object]]:
        return [{"scope": scope, "dialogue_session_id": dialogue_session_id}]

    def answer_clarification(self, clarification_id: str, answer: str) -> dict[str, object]:
        return {"clarification_id": clarification_id, "answer": answer}

    def list_messages(
        self,
        dialogue_session_id: str,
        scope: list[str],
        limit: int = 100,
    ) -> list[dict[str, object]]:
        return [{"dialogue_session_id": dialogue_session_id, "scope": scope, "limit": limit}]

    def list_sessions(
        self,
        scope: list[str],
        *,
        status: str | None = None,
        session_type: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, object]]:
        return [{"scope": scope, "status": status, "session_type": session_type, "limit": limit}]


class FakeResponses:
    def get(self, response_id: str) -> dict[str, object]:
        return {"response_id": response_id}

    def verify(self, response_id: str) -> dict[str, object]:
        return {"response_id": response_id, "status": "passed"}


class FakeClient:
    def __init__(self, config: AIONClientConfig) -> None:
        self.config = config
        self.dialogue = FakeDialogue()
        self.responses = FakeResponses()


def test_cli_dialogue_send_and_clarifications(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    send = runner.invoke(
        cli_main.app,
        ["--json", "dialogue", "send", "--message", "hello"],
    )
    clarifications = runner.invoke(cli_main.app, ["--json", "dialogue", "clarifications"])

    assert send.exit_code == 0
    assert json.loads(send.stdout)["response"]["response_id"] == "response-1"
    assert clarifications.exit_code == 0
    assert json.loads(clarifications.stdout)[0]["scope"]


def test_cli_dialogue_answer_and_responses_verify(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    answer = runner.invoke(
        cli_main.app,
        [
            "--json",
            "dialogue",
            "answer",
            "--clarification-id",
            "clarification-1",
            "--answer",
            "continue",
        ],
    )
    verify = runner.invoke(
        cli_main.app,
        ["--json", "responses", "verify", "--response-id", "response-1"],
    )

    assert answer.exit_code == 0
    assert json.loads(answer.stdout)["clarification_id"] == "clarification-1"
    assert verify.exit_code == 0
    assert json.loads(verify.stdout)["status"] == "passed"
