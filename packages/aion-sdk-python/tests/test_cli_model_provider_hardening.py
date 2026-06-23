from __future__ import annotations

import json
from typing import Any

from typer.testing import CliRunner

from aion_sdk.cli import main as cli_main
from aion_sdk.config import AIONClientConfig

runner = CliRunner()


class FakeModelProviderHardening:
    def create_profile(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"created": payload}

    def list_profiles(self, scope: list[str], **kwargs: object) -> dict[str, object]:
        return {"profiles": {"scope": scope, **kwargs}}

    def seed_profiles(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"seed": payload}

    def egress_preview(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"preview": payload}

    def simulate(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"simulation": payload}

    def assess_readiness(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"readiness": payload}

    def blockers(self, scope: list[str], **kwargs: object) -> dict[str, object]:
        return {"blockers": {"scope": scope, **kwargs}}

    def query(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"query": payload}


class FakeClient:
    def __init__(self, config: AIONClientConfig) -> None:
        self.config = config
        self.model_provider_hardening = FakeModelProviderHardening()


def test_cli_model_provider_profiles_seed_and_create(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    seed = runner.invoke(cli_main.app, ["--json", "model-providers", "profiles", "seed"])
    create = runner.invoke(
        cli_main.app,
        ["--json", "model-providers", "profiles", "create", "generic.metadata_only"],
    )

    assert seed.exit_code == 0
    assert json.loads(seed.stdout)["seed"]["dry_run"] is True
    assert create.exit_code == 0
    assert json.loads(create.stdout)["created"]["provider_key"] == "generic.metadata_only"


def test_cli_model_provider_dry_run_commands(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    preview = runner.invoke(
        cli_main.app,
        ["--json", "model-providers", "egress-preview", "generic.metadata_only"],
    )
    simulation = runner.invoke(
        cli_main.app,
        ["--json", "model-providers", "simulate", "generic.metadata_only"],
    )
    readiness = runner.invoke(
        cli_main.app,
        ["--json", "model-providers", "readiness", "generic.metadata_only"],
    )
    blockers = runner.invoke(cli_main.app, ["--json", "model-providers", "blockers"])
    query = runner.invoke(cli_main.app, ["--json", "model-providers", "query"])

    assert preview.exit_code == 0
    assert json.loads(preview.stdout)["preview"]["preview_type"] == "dry_run"
    assert simulation.exit_code == 0
    assert json.loads(simulation.stdout)["simulation"]["simulation_type"] == "dry_run"
    assert readiness.exit_code == 0
    assert json.loads(readiness.stdout)["readiness"]["provider_key"] == "generic.metadata_only"
    assert blockers.exit_code == 0
    assert query.exit_code == 0
