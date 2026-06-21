from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from typer.testing import CliRunner

from aion_sdk.cli import main as cli_main
from aion_sdk.config import AIONClientConfig

runner = CliRunner()


class FakeExtensions:
    def validate_manifest(self, manifest: dict[str, Any]) -> dict[str, object]:
        return {"validate": manifest}

    def intake(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"intake": payload}

    def query(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"query": payload}

    def get_package(self, extension_package_id: str, scope: list[str]) -> dict[str, object]:
        return {"package": {"extension_package_id": extension_package_id, "scope": scope}}

    def check_compatibility(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"compatibility": payload}

    def review_package(
        self,
        extension_package_id: str,
        payload: dict[str, Any],
        scope: list[str],
    ) -> dict[str, object]:
        return {
            "review": {
                "extension_package_id": extension_package_id,
                "payload": payload,
                "scope": scope,
            }
        }

    def create_install_plan(
        self,
        extension_package_id: str,
        payload: dict[str, Any],
    ) -> dict[str, object]:
        return {"install_plan": {"extension_package_id": extension_package_id, **payload}}

    def list_install_plans(self, scope: list[str], **kwargs: object) -> dict[str, object]:
        return {"install_plans": {"scope": scope, **kwargs}}


class FakeClient:
    def __init__(self, config: AIONClientConfig) -> None:
        self.config = config
        self.extensions = FakeExtensions()


def test_cli_extensions_intake_defaults_to_dry_run(monkeypatch, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))
    manifest_path = _write_manifest(tmp_path)

    result = runner.invoke(
        cli_main.app,
        ["--json", "extensions", "intake", "--manifest-file", str(manifest_path)],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)["intake"]
    assert payload["mode"] == "dry_run"
    assert payload["owner_scope"] == ["workspace:main"]
    assert payload["manifest"]["extension_key"] == "test.echo"


def test_cli_extensions_query_and_review(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    query = runner.invoke(
        cli_main.app,
        ["--json", "extensions", "query", "--query", "echo"],
    )
    review = runner.invoke(
        cli_main.app,
        [
            "--json",
            "extensions",
            "review",
            "package-1",
            "--decision",
            "approve",
            "--reason",
            "metadata reviewed",
        ],
    )

    assert query.exit_code == 0
    assert json.loads(query.stdout)["query"]["query"] == "echo"
    assert review.exit_code == 0
    assert json.loads(review.stdout)["review"]["payload"]["decision"] == "approve"


def test_cli_extensions_install_plan(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))

    result = runner.invoke(cli_main.app, ["--json", "extensions", "install-plan", "package-1"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)["install_plan"]
    assert payload["extension_package_id"] == "package-1"
    assert payload["scope"] == ["workspace:main"]


def _write_manifest(tmp_path: Path) -> Path:
    manifest = {
        "extension_key": "test.echo",
        "name": "Echo Extension",
        "description": "Generic metadata extension.",
        "version": "0.1.0",
        "package_type": "module",
    }
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest))
    return path
