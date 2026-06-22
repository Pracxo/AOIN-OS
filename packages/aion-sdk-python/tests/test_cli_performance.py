from __future__ import annotations

import json
from typing import Any

from typer.testing import CliRunner

from aion_sdk.cli import main as cli_main
from aion_sdk.config import AIONClientConfig

runner = CliRunner()


class FakePerformance:
    def seed_defaults(self, scope: list[str], dry_run: bool = True) -> dict[str, object]:
        return {"scope": scope, "dry_run": dry_run}

    def run_benchmark(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"benchmark_run_id": "run-1", "mode": payload["mode"]}

    def create_baseline(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"capacity_baseline_id": "baseline-1", "runs": payload["benchmark_run_ids"]}

    def summary(
        self,
        scope: list[str],
        *,
        operation_type: str | None = None,
        window: str | None = None,
    ) -> dict[str, object]:
        return {"scope": scope, "operation_type": operation_type, "window": window}


class FakeClient:
    def __init__(self, config: AIONClientConfig) -> None:
        self.config = config
        self.performance = FakePerformance()


def _install_fake(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))


def _json(result) -> Any:  # type: ignore[no-untyped-def]
    return json.loads(result.stdout)


def test_cli_performance_run_works_with_mocked_sdk(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    _install_fake(monkeypatch)

    result = runner.invoke(cli_main.app, ["--json", "performance", "run"])

    assert result.exit_code == 0
    assert _json(result)["benchmark_run_id"] == "run-1"


def test_cli_performance_summary_works_with_mocked_sdk(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    _install_fake(monkeypatch)

    result = runner.invoke(cli_main.app, ["--json", "performance", "summary"])

    assert result.exit_code == 0
    assert _json(result)["scope"] == ["workspace:main"]
