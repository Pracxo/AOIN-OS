from __future__ import annotations

import json
from typing import Any

from typer.testing import CliRunner

from aion_sdk.cli import main as cli_main
from aion_sdk.config import AIONClientConfig

runner = CliRunner()


class FakeRuntimeConfig:
    def status(self, scope: list[str]) -> dict[str, object]:
        return {"scope": scope, "validation_status": "passed"}

    def validate(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"config_validation_id": "validation-1", "owner_scope": payload["owner_scope"]}

    def create_snapshot(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"config_snapshot_id": "snapshot-1", "snapshot_type": payload["snapshot_type"]}


class FakeClient:
    def __init__(self, config: AIONClientConfig) -> None:
        self.config = config
        self.runtime_config = FakeRuntimeConfig()


def _install_fake(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))


def _json(result) -> Any:  # type: ignore[no-untyped-def]
    return json.loads(result.stdout)


def test_cli_config_status_works_with_mocked_sdk(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    _install_fake(monkeypatch)

    result = runner.invoke(cli_main.app, ["--json", "config", "status"])

    assert result.exit_code == 0
    assert _json(result)["validation_status"] == "passed"


def test_cli_config_validate_works_with_mocked_sdk(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    _install_fake(monkeypatch)

    result = runner.invoke(cli_main.app, ["--json", "config", "validate"])

    assert result.exit_code == 0
    assert _json(result)["config_validation_id"] == "validation-1"


def test_cli_config_snapshot_works_with_mocked_sdk(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    _install_fake(monkeypatch)

    result = runner.invoke(cli_main.app, ["--json", "config", "snapshot"])

    assert result.exit_code == 0
    assert _json(result)["config_snapshot_id"] == "snapshot-1"
