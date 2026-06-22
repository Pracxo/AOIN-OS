from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from typer.testing import CliRunner

from aion_sdk.cli import main as cli_main
from aion_sdk.config import AIONClientConfig

runner = CliRunner()


class FakeModuleBindings:
    def create_module_slot(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"module_slot": payload}

    def list_module_slots(self, scope: list[str], **kwargs: object) -> dict[str, object]:
        return {"module_slots": {"scope": scope, **kwargs}}

    def create_capability_binding(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"capability_binding": payload}

    def list_capability_bindings(self, scope: list[str], **kwargs: object) -> dict[str, object]:
        return {"capability_bindings": {"scope": scope, **kwargs}}

    def validate(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"validation": payload}

    def list_conflicts(self, scope: list[str], **kwargs: object) -> dict[str, object]:
        return {"conflicts": {"scope": scope, **kwargs}}

    def create_mount_plan(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"mount_plan": payload}

    def create_route_preview(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"route_preview": payload}

    def query(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"query": payload}


class FakeClient:
    def __init__(self, config: AIONClientConfig) -> None:
        self.config = config
        self.module_bindings = FakeModuleBindings()


def test_cli_module_slots_create_defaults_scope(monkeypatch, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))
    payload_path = _write_payload(tmp_path, {"slot_key": "test.echo"})

    result = runner.invoke(
        cli_main.app,
        ["--json", "module-slots", "create", "--payload-file", str(payload_path)],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)["module_slot"]
    assert payload["slot_key"] == "test.echo"
    assert payload["owner_scope"] == ["workspace:main"]


def test_cli_capability_bindings_list(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    result = runner.invoke(
        cli_main.app,
        [
            "--json",
            "capability-bindings",
            "list",
            "--module-slot-id",
            "slot-1",
            "--status",
            "proposed",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)["capability_bindings"]
    assert payload["scope"] == ["workspace:main"]
    assert payload["module_slot_id"] == "slot-1"
    assert payload["status"] == "proposed"


def test_cli_module_bindings_validate_and_query(monkeypatch, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))
    payload_path = _write_payload(tmp_path, {"module_slot_id": "slot-1"})

    validation = runner.invoke(
        cli_main.app,
        [
            "--json",
            "module-bindings",
            "validate",
            "--payload-file",
            str(payload_path),
            "--dry-run",
        ],
    )
    query = runner.invoke(
        cli_main.app,
        ["--json", "module-bindings", "query", "--query", "echo", "--status", "blocked"],
    )

    assert validation.exit_code == 0
    assert json.loads(validation.stdout)["validation"]["mode"] == "dry_run"
    assert query.exit_code == 0
    assert json.loads(query.stdout)["query"]["query"] == "echo"


def test_cli_module_bindings_mount_plan_and_route_preview(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    mount_plan = runner.invoke(
        cli_main.app,
        ["--json", "module-bindings", "mount-plan", "slot-1"],
    )
    route_preview = runner.invoke(
        cli_main.app,
        ["--json", "module-bindings", "route-preview", "binding-1"],
    )

    assert mount_plan.exit_code == 0
    assert json.loads(mount_plan.stdout)["mount_plan"]["module_slot_id"] == "slot-1"
    assert route_preview.exit_code == 0
    assert json.loads(route_preview.stdout)["route_preview"]["capability_binding_id"] == "binding-1"


def _write_payload(tmp_path: Path, payload: dict[str, Any]) -> Path:
    path = tmp_path / "payload.json"
    path.write_text(json.dumps(payload))
    return path
