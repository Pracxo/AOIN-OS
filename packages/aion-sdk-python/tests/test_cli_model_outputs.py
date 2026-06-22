from __future__ import annotations

import json
from typing import Any

from typer.testing import CliRunner

from aion_sdk.cli import main as cli_main
from aion_sdk.config import AIONClientConfig

runner = CliRunner()


class FakeModelOutputs:
    def create(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"created": True, "payload": payload}

    def get(self, model_output_id: str, scope: list[str]) -> dict[str, object]:
        return {"model_output_id": model_output_id, "scope": scope}

    def query(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"query": payload}

    def govern(self, model_output_id: str, payload: dict[str, Any]) -> dict[str, object]:
        return {"governed": model_output_id, "payload": payload}

    def segments(self, model_output_id: str, scope: list[str]) -> dict[str, object]:
        return {"segments": [], "model_output_id": model_output_id, "scope": scope}

    def validate_structured(
        self,
        model_output_id: str,
        scope: list[str],
        *,
        schema_name: str | None = None,
    ) -> dict[str, object]:
        return {"validated": model_output_id, "scope": scope, "schema_name": schema_name}

    def response_candidates(self, scope: list[str], **kwargs: object) -> dict[str, object]:
        return {"candidates": [], "scope": scope, "kwargs": kwargs}

    def promote_candidate(
        self,
        response_candidate_id: str,
        **kwargs: object,
    ) -> dict[str, object]:
        return {"promoted": response_candidate_id, "kwargs": kwargs}

    def tool_intents(self, scope: list[str], **kwargs: object) -> dict[str, object]:
        return {"tool_intents": [], "scope": scope, "kwargs": kwargs}

    def reject_tool_intent(self, tool_intent_id: str, reason: str) -> dict[str, object]:
        return {"rejected": tool_intent_id, "reason": reason}


class FakeClient:
    def __init__(self, config: AIONClientConfig) -> None:
        self.config = config
        self.model_outputs = FakeModelOutputs()


def test_cli_model_outputs_create_and_govern(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    created = runner.invoke(
        cli_main.app,
        ["--json", "model-outputs", "create", "--raw-output", "ok"],
    )
    governed = runner.invoke(
        cli_main.app,
        ["--json", "model-outputs", "govern", "--model-output-id", "output-1"],
    )

    assert created.exit_code == 0
    assert json.loads(created.stdout)["created"] is True
    assert governed.exit_code == 0
    assert json.loads(governed.stdout)["governed"] == "output-1"


def test_cli_model_outputs_lists(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    query = runner.invoke(cli_main.app, ["--json", "model-outputs", "query"])
    candidates = runner.invoke(cli_main.app, ["--json", "model-outputs", "candidates", "list"])
    tools = runner.invoke(cli_main.app, ["--json", "model-outputs", "tool-intents", "list"])
    rejected = runner.invoke(
        cli_main.app,
        [
            "--json",
            "model-outputs",
            "tool-intents",
            "reject",
            "--tool-intent-id",
            "tool-1",
        ],
    )

    assert query.exit_code == 0
    assert candidates.exit_code == 0
    assert tools.exit_code == 0
    assert rejected.exit_code == 0
