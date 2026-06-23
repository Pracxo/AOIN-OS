from __future__ import annotations

import json
from typing import Any

from typer.testing import CliRunner

from aion_sdk.cli import main as cli_main
from aion_sdk.config import AIONClientConfig

runner = CliRunner()


class FakeOperatorActions:
    def create_request(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"request": payload}

    def list_requests(self, scope: list[str], **kwargs: object) -> dict[str, object]:
        return {"scope": scope, "kwargs": kwargs, "requests": []}

    def create_preview(
        self,
        operator_action_request_id: str,
        scope: list[str],
    ) -> dict[str, object]:
        return {"preview": operator_action_request_id, "scope": scope, "would_execute": False}

    def blockers(self, scope: list[str], **kwargs: object) -> dict[str, object]:
        return {"blockers": [], "scope": scope, "kwargs": kwargs}

    def review(self, operator_action_request_id: str, payload: dict[str, Any]) -> dict[str, object]:
        return {"review": operator_action_request_id, "payload": payload}

    def query(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"query": payload}


class FakeClient:
    def __init__(self, config: AIONClientConfig) -> None:
        self.config = config
        self.operator_actions = FakeOperatorActions()


def test_cli_operator_actions_request_defaults_to_dry_run(
    monkeypatch,
) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    result = runner.invoke(
        cli_main.app,
        ["--json", "operator-actions", "request", "--action-key", "operator.review"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)["request"]
    assert payload["mode"] == "dry_run"
    assert payload["action_key"] == "operator.review"


def test_cli_operator_actions_preview_blockers_review_query(
    monkeypatch,
) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    preview = runner.invoke(
        cli_main.app,
        ["--json", "operator-actions", "preview", "--request-id", "request-1"],
    )
    blockers = runner.invoke(cli_main.app, ["--json", "operator-actions", "blockers"])
    review = runner.invoke(
        cli_main.app,
        ["--json", "operator-actions", "review", "--request-id", "request-1"],
    )
    query = runner.invoke(cli_main.app, ["--json", "operator-actions", "query"])

    assert preview.exit_code == 0
    assert json.loads(preview.stdout)["would_execute"] is False
    assert blockers.exit_code == 0
    assert json.loads(blockers.stdout)["blockers"] == []
    assert review.exit_code == 0
    assert json.loads(review.stdout)["payload"]["decision"] == "approve_preview_only"
    assert query.exit_code == 0
