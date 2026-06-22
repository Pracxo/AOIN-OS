from __future__ import annotations

import json
from typing import Any

from typer.testing import CliRunner

from aion_sdk.cli import main as cli_main
from aion_sdk.config import AIONClientConfig

runner = CliRunner()


class FakeModuleMockRuntime:
    def seed_profiles(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"seed": payload}

    def create_profile(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"profile": payload}

    def list_profiles(self, scope: list[str], **kwargs: object) -> dict[str, object]:
        return {"profiles": {"scope": scope, **kwargs}}

    def invoke(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"run": payload}

    def list_runs(self, scope: list[str], **kwargs: object) -> dict[str, object]:
        return {"runs": {"scope": scope, **kwargs}}

    def outputs(self, scope: list[str], **kwargs: object) -> dict[str, object]:
        return {"outputs": {"scope": scope, **kwargs}}

    def list_findings(self, scope: list[str], **kwargs: object) -> dict[str, object]:
        return {"findings": {"scope": scope, **kwargs}}

    def query(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"query": payload}


class FakeClient:
    def __init__(self, config: AIONClientConfig) -> None:
        self.config = config
        self.module_mock_runtime = FakeModuleMockRuntime()


def test_cli_module_mock_runtime_seed_and_invoke(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    seed = runner.invoke(cli_main.app, ["--json", "module-mock", "seed-profiles"])
    invoke = runner.invoke(
        cli_main.app,
        [
            "--json",
            "module-mock",
            "invoke",
            "binding-1",
            "--capability-key",
            "generic.mock",
        ],
    )

    assert seed.exit_code == 0
    assert json.loads(seed.stdout)["seed"]["dry_run"] is True
    assert invoke.exit_code == 0
    assert json.loads(invoke.stdout)["run"]["mode"] == "dry_run"
    assert json.loads(invoke.stdout)["run"]["capability_binding_id"] == "binding-1"


def test_cli_module_mock_runtime_profiles_runs_findings_query(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    profile = runner.invoke(
        cli_main.app,
        ["--json", "module-mock", "create-profile", "generic.mock"],
    )
    profiles = runner.invoke(cli_main.app, ["--json", "module-mock", "profiles"])
    runs = runner.invoke(cli_main.app, ["--json", "module-mock", "runs"])
    outputs = runner.invoke(cli_main.app, ["--json", "module-mock", "outputs"])
    findings = runner.invoke(cli_main.app, ["--json", "module-mock", "findings"])
    query = runner.invoke(cli_main.app, ["--json", "module-mock", "query"])

    assert profile.exit_code == 0
    assert json.loads(profile.stdout)["profile"]["profile_key"] == "generic.mock"
    assert profiles.exit_code == 0
    assert json.loads(profiles.stdout)["profiles"]["scope"] == ["workspace:main"]
    assert runs.exit_code == 0
    assert outputs.exit_code == 0
    assert findings.exit_code == 0
    assert query.exit_code == 0
