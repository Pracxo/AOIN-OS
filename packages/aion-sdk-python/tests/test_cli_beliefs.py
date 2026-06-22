from __future__ import annotations

import json
from typing import Any

from typer.testing import CliRunner

from aion_sdk.cli import main as cli_main
from aion_sdk.config import AIONClientConfig

runner = CliRunner()


class FakeBeliefs:
    def create_claim(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"claim_id": "claim-1", "payload": payload}

    def query(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"claims": [], "payload": payload}

    def extract(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"extracted_claims": [{"claim_text": payload["text"]}]}

    def list_contradictions(
        self,
        scope: list[str],
        *,
        status: str | None = None,
        severity: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, object]]:
        return [{"scope": scope, "status": status, "severity": severity, "limit": limit}]

    def run_truth_maintenance(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"truth_run_id": "truth-1", "payload": payload}

    def get_truth_maintenance(self, truth_run_id: str) -> dict[str, object]:
        return {"truth_run_id": truth_run_id}


class FakeClient:
    def __init__(self, config: AIONClientConfig) -> None:
        self.config = config
        self.beliefs = FakeBeliefs()


def test_cli_beliefs_create_and_query(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    created = runner.invoke(
        cli_main.app,
        ["--json", "beliefs", "create", "--claim", "A generic claim exists."],
    )
    queried = runner.invoke(cli_main.app, ["--json", "beliefs", "query", "--query", "generic"])

    assert created.exit_code == 0
    assert json.loads(created.stdout)["claim_id"] == "claim-1"
    assert queried.exit_code == 0
    assert json.loads(queried.stdout)["payload"]["query"] == "generic"


def test_cli_beliefs_extract_contradictions_and_truth(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    extracted = runner.invoke(
        cli_main.app,
        ["--json", "beliefs", "extract", "--text", "A generic claim can be extracted."],
    )
    contradictions = runner.invoke(cli_main.app, ["--json", "beliefs", "contradictions"])
    truth = runner.invoke(cli_main.app, ["--json", "beliefs", "truth-maintenance", "run"])

    assert extracted.exit_code == 0
    assert json.loads(extracted.stdout)["extracted_claims"][0]["claim_text"]
    assert contradictions.exit_code == 0
    assert json.loads(contradictions.stdout)[0]["status"] == "open"
    assert truth.exit_code == 0
    assert json.loads(truth.stdout)["truth_run_id"] == "truth-1"
