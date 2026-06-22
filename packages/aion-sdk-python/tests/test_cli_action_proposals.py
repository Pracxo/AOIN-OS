from __future__ import annotations

import json
from typing import Any

from typer.testing import CliRunner

from aion_sdk.cli import main as cli_main
from aion_sdk.config import AIONClientConfig

runner = CliRunner()


class FakeActionProposals:
    def create(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"created": True, "payload": payload}

    def query(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"query": payload}

    def review(self, action_proposal_id: str, payload: dict[str, Any]) -> dict[str, object]:
        return {"reviewed": action_proposal_id, "payload": payload}

    def handoff(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"handoff": payload}

    def list_blockers(self, **kwargs: object) -> dict[str, object]:
        return {"blockers": [], "kwargs": kwargs}

    def list_handoffs(self, **kwargs: object) -> dict[str, object]:
        return {"handoffs": [], "kwargs": kwargs}

    def review_tool_intent(self, tool_intent_id: str, payload: dict[str, Any]) -> dict[str, object]:
        return {"tool_intent_id": tool_intent_id, "payload": payload}


class FakeClient:
    def __init__(self, config: AIONClientConfig) -> None:
        self.config = config
        self.action_proposals = FakeActionProposals()


def test_cli_action_proposals_handoff_defaults_to_dry_run(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    result = runner.invoke(
        cli_main.app,
        ["--json", "action-proposals", "handoff", "--action-proposal-id", "proposal-1"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)["handoff"]
    assert payload["mode"] == "dry_run"


def test_cli_action_proposals_query_blockers_and_tool_intent_review(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    query = runner.invoke(cli_main.app, ["--json", "action-proposals", "query"])
    blockers = runner.invoke(cli_main.app, ["--json", "action-proposals", "blockers"])
    review = runner.invoke(
        cli_main.app,
        [
            "--json",
            "action-proposals",
            "tool-intent",
            "review",
            "--tool-intent-id",
            "tool-1",
        ],
    )

    assert query.exit_code == 0
    assert blockers.exit_code == 0
    assert json.loads(blockers.stdout)["blockers"] == []
    assert review.exit_code == 0
    assert json.loads(review.stdout)["tool_intent_id"] == "tool-1"
