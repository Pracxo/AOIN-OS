from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from typer.testing import CliRunner

from aion_sdk.cli import main as cli_main
from aion_sdk.config import AIONClientConfig

runner = CliRunner()


class FakeModules:
    def scaffold(self, payload: dict[str, Any]) -> dict[str, object]:
        return {
            "module_id": payload["module_id"],
            "package_name": payload["package_name"],
            "files": {"README.md": "# Generic\n", "aion.module.json": "{}\n"},
        }

    def certify(self, module_package_id: str, payload: dict[str, Any]) -> dict[str, object]:
        return {"module_package_id": module_package_id, "payload": payload, "status": "passed"}

    def list_packages(
        self,
        *,
        status: str | None = None,
        module_id: str | None = None,
    ) -> list[dict[str, object]]:
        return [{"module_package_id": "pkg-1", "status": status, "module_id": module_id}]

    def submit_package(self, payload: dict[str, Any]) -> dict[str, object]:
        return {"submitted": True, "module_id": payload["module_id"]}

    def compatibility(self, module_package_id: str) -> dict[str, object]:
        return {"module_package_id": module_package_id, "compatible": True}

    def run_contract_tests(
        self,
        module_package_id: str,
        *,
        dry_run: bool = True,
    ) -> dict[str, object]:
        return {"module_package_id": module_package_id, "dry_run": dry_run}


class FakeClient:
    def __init__(self, config: AIONClientConfig) -> None:
        self.config = config
        self.modules = FakeModules()


def _install_fake(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli_main, "make_client", lambda config: FakeClient(config))


def _json(result) -> Any:  # type: ignore[no-untyped-def]
    return json.loads(result.stdout)


def test_cli_modules_scaffold_works(monkeypatch, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    _install_fake(monkeypatch)
    output = tmp_path / "generic-module"

    result = runner.invoke(
        cli_main.app,
        [
            "--json",
            "--scope",
            "workspace:main",
            "modules",
            "scaffold",
            "--module-id",
            "generic.example",
            "--package-name",
            "generic-example",
            "--output",
            str(output),
        ],
    )

    assert result.exit_code == 0
    assert _json(result)["module_id"] == "generic.example"
    assert (output / "README.md").exists()


def test_cli_modules_certify_works(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    _install_fake(monkeypatch)

    result = runner.invoke(
        cli_main.app,
        ["--json", "modules", "certify", "--module-package-id", "pkg-1"],
    )

    assert result.exit_code == 0
    assert _json(result)["status"] == "passed"


def test_cli_modules_list_works(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    _install_fake(monkeypatch)

    result = runner.invoke(cli_main.app, ["--json", "modules", "list", "--status", "submitted"])

    assert result.exit_code == 0
    assert _json(result)[0]["status"] == "submitted"
