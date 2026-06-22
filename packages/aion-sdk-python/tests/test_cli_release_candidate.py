from __future__ import annotations

import json
from typing import Any

from typer.testing import CliRunner

from aion_sdk.cli import main as cli_main
from aion_sdk.config import AIONClientConfig

runner = CliRunner()


class FakeReleaseCandidate:
    def create_candidate(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"release_candidate_id": "rc-1", "rc_key": payload["rc_key"]}

    def list_candidates(self, scope: list[str], **kwargs: object) -> list[dict[str, object]]:
        return [{"release_candidate_id": "rc-1", "scope": scope}]

    def list_matrices(self, scope: list[str], **kwargs: object) -> list[dict[str, object]]:
        return [{"verification_matrix_id": "matrix-1", "scope": scope}]

    def seed_default_matrices(self, scope: list[str], dry_run: bool = True) -> dict[str, object]:
        return {"dry_run": dry_run, "scope": scope}

    def run_gate(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"rc_run_id": "run-1", "mode": payload["mode"]}

    def get_run(self, rc_run_id: str, scope: list[str]) -> dict[str, object]:
        return {"rc_run_id": rc_run_id, "scope": scope}

    def list_findings(self, scope: list[str], **kwargs: object) -> list[dict[str, object]]:
        return [{"rc_finding_id": "finding-1", "scope": scope}]

    def dismiss_finding(
        self, rc_finding_id: str, scope: list[str], *, reason: str
    ) -> dict[str, object]:
        return {"rc_finding_id": rc_finding_id, "status": "dismissed", "reason": reason}

    def list_reports(self, scope: list[str], **kwargs: object) -> list[dict[str, object]]:
        return [{"rc_report_id": "report-1", "scope": scope}]

    def list_evidence_packs(self, scope: list[str], **kwargs: object) -> list[dict[str, object]]:
        return [{"evidence_pack_id": "pack-1", "scope": scope}]

    def query(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"status": "ok", "scope": payload["scope"]}


class FakeClient:
    def __init__(self, config: AIONClientConfig) -> None:
        self.config = config
        self.release_candidate = FakeReleaseCandidate()


def _install_fake(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))


def _json(result) -> Any:  # type: ignore[no-untyped-def]
    return json.loads(result.stdout)


def test_cli_rc_create_and_run_work(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    _install_fake(monkeypatch)

    created = runner.invoke(
        cli_main.app,
        ["--json", "rc", "create", "--rc-key", "rc.test", "--version", "0.1.0"],
    )
    run = runner.invoke(cli_main.app, ["--json", "rc", "run", "--no-service-checks"])

    assert created.exit_code == 0
    assert run.exit_code == 0
    assert _json(created)["release_candidate_id"] == "rc-1"
    assert _json(run)["mode"] == "dry_run"


def test_cli_rc_query_surfaces_work(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    _install_fake(monkeypatch)

    commands = [
        ["--json", "rc", "candidates"],
        ["--json", "rc", "matrices"],
        ["--json", "rc", "matrices", "seed"],
        ["--json", "rc", "run-get", "--id", "run-1"],
        ["--json", "rc", "findings"],
        ["--json", "rc", "dismiss-finding", "--id", "finding-1"],
        ["--json", "rc", "reports"],
        ["--json", "rc", "evidence"],
        ["--json", "rc", "query"],
    ]

    results = [runner.invoke(cli_main.app, command) for command in commands]

    assert [result.exit_code for result in results] == [0] * len(results)
