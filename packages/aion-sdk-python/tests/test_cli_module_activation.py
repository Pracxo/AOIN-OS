from __future__ import annotations

import json
from typing import Any

from typer.testing import CliRunner

from aion_sdk.cli import main as cli_main
from aion_sdk.config import AIONClientConfig

runner = CliRunner()


class FakeModuleActivation:
    def create_request(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"request": payload}

    def list_requests(self, scope: list[str], **kwargs: object) -> dict[str, object]:
        return {"requests": {"scope": scope, **kwargs}}

    def run_gate(self, activation_request_id: str, payload: dict[str, Any]) -> dict[str, object]:
        return {"gate": {"activation_request_id": activation_request_id, **payload}}

    def list_blockers(self, scope: list[str], **kwargs: object) -> dict[str, object]:
        return {"blockers": {"scope": scope, **kwargs}}

    def create_review(
        self,
        payload: dict[str, Any],
        scope: list[str],
    ) -> dict[str, object]:
        return {"review": {"payload": payload, "scope": scope}}

    def create_plan(self, activation_request_id: str, payload: dict[str, Any]) -> dict[str, object]:
        return {"plan": {"activation_request_id": activation_request_id, **payload}}

    def create_runtime_registration_preview(
        self,
        activation_request_id: str,
        payload: dict[str, Any],
    ) -> dict[str, object]:
        return {"preview": {"activation_request_id": activation_request_id, **payload}}

    def query(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"query": payload}


class FakeClient:
    def __init__(self, config: AIONClientConfig) -> None:
        self.config = config
        self.module_activation = FakeModuleActivation()


def test_cli_module_activation_request_and_gate(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    request = runner.invoke(cli_main.app, ["--json", "module-activation", "request", "slot-1"])
    gate = runner.invoke(cli_main.app, ["--json", "module-activation", "gate", "request-1"])

    assert request.exit_code == 0
    assert json.loads(request.stdout)["request"]["module_slot_id"] == "slot-1"
    assert json.loads(request.stdout)["request"]["owner_scope"] == ["workspace:main"]
    assert gate.exit_code == 0
    assert json.loads(gate.stdout)["gate"]["activation_request_id"] == "request-1"


def test_cli_module_activation_plan_preview_and_query(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    plan = runner.invoke(cli_main.app, ["--json", "module-activation", "plan", "request-1"])
    preview = runner.invoke(
        cli_main.app,
        ["--json", "module-activation", "runtime-preview", "request-1"],
    )
    query = runner.invoke(
        cli_main.app,
        ["--json", "module-activation", "query", "--activation-request-id", "request-1"],
    )

    assert plan.exit_code == 0
    assert json.loads(plan.stdout)["plan"]["scope"] == ["workspace:main"]
    assert preview.exit_code == 0
    assert json.loads(preview.stdout)["preview"]["activation_request_id"] == "request-1"
    assert query.exit_code == 0
    assert json.loads(query.stdout)["query"]["activation_request_id"] == "request-1"
