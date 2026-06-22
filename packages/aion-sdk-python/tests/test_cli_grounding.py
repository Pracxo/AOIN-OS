from __future__ import annotations

import json
from typing import Any

from typer.testing import CliRunner

from aion_sdk.cli import main as cli_main
from aion_sdk.config import AIONClientConfig

runner = CliRunner()


class FakeGrounding:
    def verify(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"grounding_verification_id": "grounding-verification-1", "payload": payload}

    def unsupported(self, **kwargs: object) -> dict[str, object]:
        return {"unsupported": [], "kwargs": kwargs}

    def map_response(
        self,
        response_id: str,
        owner_scope: list[str],
        required_source_types: list[str] | None = None,
    ) -> dict[str, object]:
        return {"response_id": response_id, "owner_scope": owner_scope}

    def coverage(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"source_coverage_id": "coverage-1", "payload": payload}


class FakeClient:
    def __init__(self, config: AIONClientConfig) -> None:
        self.config = config
        self.grounding = FakeGrounding()


def test_cli_grounding_verify_and_unsupported(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    verify = runner.invoke(
        cli_main.app,
        ["--json", "grounding", "verify", "--response-id", "response-1"],
    )
    unsupported = runner.invoke(
        cli_main.app,
        ["--json", "grounding", "unsupported", "--response-id", "response-1"],
    )

    assert verify.exit_code == 0
    assert json.loads(verify.stdout)["grounding_verification_id"] == "grounding-verification-1"
    assert unsupported.exit_code == 0
    assert json.loads(unsupported.stdout)["unsupported"] == []


def test_cli_grounding_map_response(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    result = runner.invoke(
        cli_main.app,
        ["--json", "grounding", "map-response", "--response-id", "response-1"],
    )

    assert result.exit_code == 0
    assert json.loads(result.stdout)["response_id"] == "response-1"
