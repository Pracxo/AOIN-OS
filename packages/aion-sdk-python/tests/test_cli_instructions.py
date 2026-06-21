from __future__ import annotations

import json
from typing import Any

from typer.testing import CliRunner

from aion_sdk.cli import main as cli_main
from aion_sdk.config import AIONClientConfig

runner = CliRunner()


class FakeInstructions:
    def create_instruction(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"instruction_id": "instruction-1", "payload": payload}

    def list_instructions(self, scope: list[str], **kwargs: object) -> dict[str, object]:
        return {"scope": scope, "kwargs": kwargs}

    def resolve(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"resolution_run_id": "resolution-1", "payload": payload}

    def list_conflicts(self, scope: list[str], **kwargs: object) -> dict[str, object]:
        return {"conflicts": [], "scope": scope, "kwargs": kwargs}

    def create_preference(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"preference_id": "preference-1", "payload": payload}

    def list_preferences(self, scope: list[str], **kwargs: object) -> dict[str, object]:
        return {"preferences": [], "scope": scope, "kwargs": kwargs}

    def confirm_preference(self, preference_id: str, reason: str) -> dict[str, object]:
        return {"preference_id": preference_id, "reason": reason, "status": "confirmed"}

    def list_candidates(self, scope: list[str], **kwargs: object) -> dict[str, object]:
        return {"candidates": [], "scope": scope, "kwargs": kwargs}

    def create_style_profile(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"style_profile_id": "style-1", "payload": payload}

    def list_style_profiles(self, scope: list[str], **kwargs: object) -> dict[str, object]:
        return {"styles": [], "scope": scope, "kwargs": kwargs}

    def effective_style(self, scope: list[str]) -> dict[str, object]:
        return {"name": "Direct", "scope": scope}


class FakeClient:
    def __init__(self, config: AIONClientConfig) -> None:
        self.config = config
        self.instructions = FakeInstructions()


def test_cli_instructions_resolve_and_preferences_list(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    resolve = runner.invoke(cli_main.app, ["--json", "instructions", "resolve"])
    preferences = runner.invoke(cli_main.app, ["--json", "preferences", "list"])

    assert resolve.exit_code == 0
    assert json.loads(resolve.stdout)["resolution_run_id"] == "resolution-1"
    assert preferences.exit_code == 0
    assert json.loads(preferences.stdout)["preferences"] == []


def test_cli_style_profiles_effective(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    result = runner.invoke(cli_main.app, ["--json", "style-profiles", "effective"])

    assert result.exit_code == 0
    assert json.loads(result.stdout)["name"] == "Direct"
