"""Contract scanner tests."""

from __future__ import annotations

from pathlib import Path

from fastapi.routing import APIRoute

from aion_brain.config import Settings
from aion_brain.contract_registry.scanners import ContractScanner
from tests.contract_registry_helpers import SCOPE


def test_contract_scanner_scans_pydantic_contracts_without_external_calls(tmp_path: Path) -> None:
    scanner = _scanner(tmp_path)

    records = scanner.scan_pydantic_contracts(SCOPE)

    assert records
    assert all(record.metadata["source_mutated"] is False for record in records)


def test_contract_scanner_scans_fastapi_routes(tmp_path: Path) -> None:
    route = APIRoute("/brain/example", lambda: {"ok": True}, methods=["GET"], name="example")
    scanner = _scanner(tmp_path, app_routes=[route])

    records = scanner.scan_api_routes(SCOPE)

    assert records[0].interface_key == "GET /brain/example"
    assert records[0].interface_type == "api_route"


def test_contract_scanner_scans_policy_actions_and_env_settings(tmp_path: Path) -> None:
    scanner = _scanner(tmp_path)

    policy_actions = scanner.scan_policy_actions(SCOPE)
    settings = scanner.scan_env_settings(SCOPE)

    assert {item.action for item in policy_actions} == {"contract_registry.resource.read"}
    assert any(item.setting_key == "database_url" for item in settings)


def test_contract_scanner_scans_sdk_cli_and_registry_vocab(tmp_path: Path) -> None:
    scanner = _scanner(tmp_path)

    sdk_records = scanner.scan_sdk_resources(SCOPE)
    cli_records = scanner.scan_cli_commands(SCOPE)
    registry_records = scanner.scan_registry_resource_types(SCOPE)

    assert any(item.interface_key == "sdk.echo.ping" for item in sdk_records)
    assert any(item.interface_key == "cli.echo.ping" for item in cli_records)
    assert {item.resource_type for item in registry_records} >= {
        "contract_snapshot",
        "compatibility_scan",
        "interface_drift",
    }


def _scanner(tmp_path: Path, app_routes: list[APIRoute] | None = None) -> ContractScanner:
    sdk_root = tmp_path / "packages/aion-sdk-python/src/aion_sdk"
    resources = sdk_root / "resources"
    commands = sdk_root / "cli/commands"
    resources.mkdir(parents=True)
    commands.mkdir(parents=True)
    (resources / "echo.py").write_text(
        "class EchoResource:\n    def ping(self):\n        return {'ok': True}\n",
        encoding="utf-8",
    )
    (commands / "echo.py").write_text(
        "import typer\n\napp = typer.Typer()\n\n@app.command('ping')\ndef ping():\n    pass\n",
        encoding="utf-8",
    )
    policy_file = tmp_path / "brain.rego"
    policy_file.write_text('"contract_registry.resource.read"\n', encoding="utf-8")
    return ContractScanner(
        settings=Settings(_env_file=None),
        sdk_root=sdk_root,
        policy_file=policy_file,
        app_routes=app_routes or [],
    )
