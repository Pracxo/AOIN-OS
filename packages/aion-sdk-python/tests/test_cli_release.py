from __future__ import annotations

import json
from typing import Any

from typer.testing import CliRunner

from aion_sdk.cli import main as cli_main
from aion_sdk.config import AIONClientConfig

runner = CliRunner()


class FakeRelease:
    def create_package(self, payload: dict[str, Any]) -> dict[str, object]:
        return {
            "release_package_id": "package-1",
            "version": payload["version"],
            "dry_run": payload["dry_run"],
        }

    def validate_package(self, package_id: str, scope: list[str]) -> dict[str, object]:
        return {"status": "passed", "package_id": package_id, "scope": scope}

    def handoff(self, package_id: str, scope: list[str]) -> dict[str, object]:
        return {"status": "ready", "package_id": package_id, "scope": scope}


class FakeClient:
    def __init__(self, config: AIONClientConfig) -> None:
        self.config = config
        self.release = FakeRelease()


def _install_fake(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))


def _json(result) -> Any:  # type: ignore[no-untyped-def]
    return json.loads(result.stdout)


def test_cli_release_package_create_works(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    _install_fake(monkeypatch)

    result = runner.invoke(
        cli_main.app,
        [
            "--json",
            "release",
            "package",
            "--version",
            "0.1.0",
            "--output-dir",
            "artifacts/releases",
            "--dry-run",
        ],
    )

    assert result.exit_code == 0
    assert _json(result)["release_package_id"] == "package-1"
    assert _json(result)["dry_run"] is True


def test_cli_release_package_validate_works(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    _install_fake(monkeypatch)

    result = runner.invoke(
        cli_main.app,
        ["--json", "release", "package", "validate", "--id", "package-1"],
    )

    assert result.exit_code == 0
    assert _json(result)["status"] == "passed"


def test_cli_release_package_handoff_works(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    _install_fake(monkeypatch)

    result = runner.invoke(
        cli_main.app,
        ["--json", "release", "package", "handoff", "--id", "package-1"],
    )

    assert result.exit_code == 0
    assert _json(result)["status"] == "ready"
