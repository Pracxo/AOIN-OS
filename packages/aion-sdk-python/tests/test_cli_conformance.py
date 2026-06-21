from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from typer.testing import CliRunner

from aion_sdk.cli import main as cli_main
from aion_sdk.config import AIONClientConfig

runner = CliRunner()


class FakeConformance:
    def list_profiles(self, scope: list[str], **kwargs: object) -> dict[str, object]:
        return {"profiles": {"scope": scope, **kwargs}}

    def seed_default_profiles(self, scope: list[str], *, dry_run: bool) -> dict[str, object]:
        return {"seed": {"scope": scope, "dry_run": dry_run}}

    def list_test_vectors(self, scope: list[str], **kwargs: object) -> dict[str, object]:
        return {"test_vectors": {"scope": scope, **kwargs}}

    def generate_test_vectors(
        self,
        capability_binding_id: str,
        scope: list[str],
    ) -> dict[str, object]:
        return {"generated": {"capability_binding_id": capability_binding_id, "scope": scope}}

    def run(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"run": payload}

    def list_findings(self, scope: list[str], **kwargs: object) -> dict[str, object]:
        return {"findings": {"scope": scope, **kwargs}}

    def assess_readiness(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"readiness": payload}

    def list_readiness_assessments(
        self,
        scope: list[str],
        **kwargs: object,
    ) -> dict[str, object]:
        return {"readiness_list": {"scope": scope, **kwargs}}

    def query(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"query": payload}


class FakeClient:
    def __init__(self, config: AIONClientConfig) -> None:
        self.config = config
        self.conformance = FakeConformance()


def test_cli_conformance_profiles_and_seed(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    profiles = runner.invoke(cli_main.app, ["--json", "conformance", "profiles"])
    seed = runner.invoke(cli_main.app, ["--json", "conformance", "profiles", "seed"])

    assert profiles.exit_code == 0
    assert json.loads(profiles.stdout)["profiles"]["scope"] == ["workspace:main"]
    assert seed.exit_code == 0
    assert json.loads(seed.stdout)["seed"]["dry_run"] is True


def test_cli_conformance_run_and_query(monkeypatch, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))
    payload_path = _write_payload(tmp_path, {"capability_binding_id": "binding-1"})

    run = runner.invoke(
        cli_main.app,
        ["--json", "conformance", "run", "--payload-file", str(payload_path)],
    )
    query = runner.invoke(
        cli_main.app,
        ["--json", "conformance", "query", "--capability-binding-id", "binding-1"],
    )

    assert run.exit_code == 0
    assert json.loads(run.stdout)["run"]["mode"] == "dry_run"
    assert query.exit_code == 0
    assert json.loads(query.stdout)["query"]["capability_binding_id"] == "binding-1"


def test_cli_conformance_test_vectors_and_findings(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    vectors = runner.invoke(cli_main.app, ["--json", "conformance", "test-vectors"])
    generated = runner.invoke(
        cli_main.app,
        ["--json", "conformance", "test-vectors", "generate", "binding-1"],
    )
    findings = runner.invoke(cli_main.app, ["--json", "conformance", "findings"])

    assert vectors.exit_code == 0
    assert json.loads(vectors.stdout)["test_vectors"]["scope"] == ["workspace:main"]
    assert generated.exit_code == 0
    assert json.loads(generated.stdout)["generated"]["capability_binding_id"] == "binding-1"
    assert findings.exit_code == 0


def test_cli_readiness_assess_and_list(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    assess = runner.invoke(
        cli_main.app,
        ["--json", "readiness", "assess", "--capability-binding-id", "binding-1"],
    )
    list_result = runner.invoke(cli_main.app, ["--json", "readiness", "list"])

    assert assess.exit_code == 0
    assert json.loads(assess.stdout)["readiness"]["capability_binding_id"] == "binding-1"
    assert list_result.exit_code == 0
    assert json.loads(list_result.stdout)["readiness_list"]["scope"] == ["workspace:main"]


def _write_payload(tmp_path: Path, payload: dict[str, Any]) -> Path:
    path = tmp_path / "payload.json"
    path.write_text(json.dumps(payload))
    return path
