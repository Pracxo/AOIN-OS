from __future__ import annotations

import json
from typing import Any

from typer.testing import CliRunner

from aion_sdk.cli import main as cli_main
from aion_sdk.config import AIONClientConfig

runner = CliRunner()


class FakeConcepts:
    def create(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"concept_id": "concept-1", "payload": payload}

    def list_concepts(self, scope: list[str], **kwargs: object) -> dict[str, object]:
        return {"concepts": [], "scope": scope, "kwargs": kwargs}


class FakeEntities:
    def create(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"entity_id": "entity-1", "payload": payload}

    def query(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"entities": [], "payload": payload}

    def extract_mentions(self, payload: dict[str, Any]) -> list[dict[str, object]]:
        return [{"mention_text": payload["text"]}]

    def resolve(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"status": "dry_run", "payload": payload}

    def propose_merge(
        self,
        payload: dict[str, Any],
        scope: list[str],
    ) -> dict[str, object]:
        return {"merge_proposal_id": "merge-1", "payload": payload, "scope": scope}

    def approve_merge(
        self,
        proposal_id: str,
        reason: str,
        scope: list[str],
        *,
        approval_present: bool = True,
    ) -> dict[str, object]:
        return {
            "merge_proposal_id": proposal_id,
            "reason": reason,
            "scope": scope,
            "approval_present": approval_present,
        }

    def list_references(self, scope: list[str], **kwargs: object) -> dict[str, object]:
        return {"references": [], "scope": scope, "kwargs": kwargs}

    def propose_split(
        self,
        payload: dict[str, Any],
        scope: list[str],
    ) -> dict[str, object]:
        return {"split_proposal_id": "split-1", "payload": payload, "scope": scope}


class FakeClient:
    def __init__(self, config: AIONClientConfig) -> None:
        self.config = config
        self.concepts = FakeConcepts()
        self.entities = FakeEntities()


def test_cli_concepts_create_and_list(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    created = runner.invoke(
        cli_main.app,
        [
            "--json",
            "concepts",
            "create",
            "--name",
            "Generic Concept",
            "--description",
            "A concept.",
        ],
    )
    listed = runner.invoke(cli_main.app, ["--json", "concepts", "list", "--query", "generic"])

    assert created.exit_code == 0
    assert json.loads(created.stdout)["concept_id"] == "concept-1"
    assert listed.exit_code == 0
    assert json.loads(listed.stdout)["kwargs"]["query"] == "generic"


def test_cli_entities_create_query_extract_resolve_and_merge(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    created = runner.invoke(cli_main.app, ["--json", "entities", "create", "--name", "Entity"])
    queried = runner.invoke(cli_main.app, ["--json", "entities", "query", "--query", "Entity"])
    extracted = runner.invoke(
        cli_main.app,
        ["--json", "entities", "extract-mentions", "--text", "Entity"],
    )
    resolved = runner.invoke(
        cli_main.app,
        ["--json", "entities", "resolve", "--text", "Entity"],
    )
    proposed = runner.invoke(
        cli_main.app,
        [
            "--json",
            "entities",
            "propose-merge",
            "--primary",
            "entity-1",
            "--duplicate",
            "entity-2",
            "--reason",
            "same",
        ],
    )
    nested_merge = runner.invoke(
        cli_main.app,
        [
            "--json",
            "entities",
            "merge",
            "approve",
            "merge-1",
            "--reason",
            "approved",
            "--approved",
        ],
    )
    references = runner.invoke(cli_main.app, ["--json", "entities", "references"])
    split = runner.invoke(
        cli_main.app,
        [
            "--json",
            "entities",
            "split",
            "propose",
            "--entity-id",
            "entity-1",
            "--reason",
            "too broad",
        ],
    )

    assert created.exit_code == 0
    assert json.loads(created.stdout)["entity_id"] == "entity-1"
    assert queried.exit_code == 0
    assert extracted.exit_code == 0
    assert resolved.exit_code == 0
    assert proposed.exit_code == 0
    assert nested_merge.exit_code == 0
    assert json.loads(nested_merge.stdout)["approval_present"] is True
    assert references.exit_code == 0
    assert split.exit_code == 0
