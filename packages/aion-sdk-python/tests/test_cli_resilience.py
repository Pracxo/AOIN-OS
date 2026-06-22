from __future__ import annotations

import json
from typing import Any

from typer.testing import CliRunner

from aion_sdk.cli import main as cli_main
from aion_sdk.config import AIONClientConfig

runner = CliRunner()


class FakeResilience:
    def status(self, scope: list[str]) -> dict[str, object]:
        return {"overall_status": "healthy", "scope": scope}

    def check_dependencies(self, scope: list[str]) -> list[dict[str, object]]:
        return [{"dependency_name": "postgres", "scope": scope}]

    def seed_retry_policies(self, dry_run: bool = True) -> dict[str, object]:
        return {"dry_run": dry_run, "policy_count": 7}

    def list_retry_policies(
        self,
        *,
        status: str | None = None,
        target_type: str | None = None,
    ) -> list[dict[str, object]]:
        return [{"status": status, "target_type": target_type}]

    def list_circuit_breakers(
        self,
        *,
        status: str | None = None,
        target_type: str | None = None,
    ) -> list[dict[str, object]]:
        return [{"status": status, "target_type": target_type}]

    def list_degraded(self, component: str | None = None) -> list[dict[str, object]]:
        return [{"component": component}]

    def list_fault_rules(
        self,
        *,
        status: str | None = None,
        target_type: str | None = None,
    ) -> list[dict[str, object]]:
        return [{"status": status, "target_type": target_type}]

    def run_test(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"status": "passed", "mode": payload["mode"]}


class FakeClient:
    def __init__(self, config: AIONClientConfig) -> None:
        self.config = config
        self.resilience = FakeResilience()


def _install_fake(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))


def _json(result) -> Any:  # type: ignore[no-untyped-def]
    return json.loads(result.stdout)


def test_cli_resilience_status_and_dependency_check(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    _install_fake(monkeypatch)

    status = runner.invoke(cli_main.app, ["--json", "resilience", "status"])
    dependencies = runner.invoke(cli_main.app, ["--json", "resilience", "dependencies", "check"])

    assert status.exit_code == 0
    assert _json(status)["overall_status"] == "healthy"
    assert dependencies.exit_code == 0
    assert _json(dependencies)[0]["dependency_name"] == "postgres"


def test_cli_resilience_seed_list_and_run(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    _install_fake(monkeypatch)

    seeded = runner.invoke(cli_main.app, ["--json", "resilience", "retry-policies", "seed"])
    breakers = runner.invoke(cli_main.app, ["--json", "resilience", "circuit-breakers", "list"])
    degraded = runner.invoke(cli_main.app, ["--json", "resilience", "degraded", "list"])
    faults = runner.invoke(cli_main.app, ["--json", "resilience", "fault-rules", "list"])
    run = runner.invoke(cli_main.app, ["--json", "resilience", "test", "run"])

    assert seeded.exit_code == 0
    assert _json(seeded)["dry_run"] is True
    assert breakers.exit_code == 0
    assert degraded.exit_code == 0
    assert faults.exit_code == 0
    assert run.exit_code == 0
    assert _json(run)["status"] == "passed"
