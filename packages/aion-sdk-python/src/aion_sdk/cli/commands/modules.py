"""aionctl modules commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Any, cast

import typer

from aion_sdk.client import AIONClient
from aion_sdk.types import JSONDict, JSONValue

modules_app = typer.Typer(no_args_is_help=True, help="Module developer kit helpers.")


def install_modules_commands(
    app: typer.Typer,
    *,
    get_client: Any,
    get_scope: Any,
    render: Any,
) -> None:
    """Install module commands onto the root CLI."""

    app.add_typer(modules_app, name="modules")

    @modules_app.command("scaffold")
    def scaffold(
        ctx: typer.Context,
        module_id: Annotated[str, typer.Option("--module-id")],
        package_name: Annotated[str, typer.Option("--package-name")],
        output: Annotated[Path | None, typer.Option("--output")] = None,
        capability_count: Annotated[int, typer.Option("--capability-count", min=1, max=10)] = 1,
        output_format: Annotated[str, typer.Option("--output-format")] = "files",
    ) -> None:
        """Generate a generic non-executable module scaffold."""

        payload: JSONDict = {
            "module_id": module_id,
            "package_name": package_name,
            "capability_count": capability_count,
            "output_format": output_format,
            "owner_scope": get_scope(ctx),
            "metadata": {"source": "aionctl"},
        }
        result = _client(get_client(ctx)).modules.scaffold(payload)
        if output is not None and isinstance(result, dict):
            _write_scaffold(output, result)
        render(ctx, result)

    @modules_app.command("submit")
    def submit(
        ctx: typer.Context,
        manifest: Annotated[Path, typer.Option("--manifest")],
    ) -> None:
        """Submit a module package JSON manifest."""

        payload = _load_manifest(manifest)
        result = _client(get_client(ctx)).modules.submit_package(payload)
        render(ctx, result)

    @modules_app.command("certify")
    def certify(
        ctx: typer.Context,
        module_package_id: Annotated[str, typer.Option("--module-package-id")],
        dry_run: Annotated[bool, typer.Option("--dry-run/--apply")] = True,
    ) -> None:
        """Run deterministic package certification."""

        payload: JSONDict = {
            "module_package_id": module_package_id,
            "dry_run": dry_run,
            "owner_scope": get_scope(ctx),
        }
        result = _client(get_client(ctx)).modules.certify(module_package_id, payload)
        render(ctx, result)

    @modules_app.command("list")
    def list_packages(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        module_id: Annotated[str | None, typer.Option("--module-id")] = None,
    ) -> None:
        """List module packages."""

        result = _client(get_client(ctx)).modules.list_packages(
            status=status,
            module_id=module_id,
        )
        render(ctx, result)

    @modules_app.command("compatibility")
    def compatibility(
        ctx: typer.Context,
        module_package_id: Annotated[str, typer.Option("--module-package-id")],
    ) -> None:
        """Run compatibility checks."""

        result = _client(get_client(ctx)).modules.compatibility(module_package_id)
        render(ctx, result)

    @modules_app.command("test")
    def test(
        ctx: typer.Context,
        module_package_id: Annotated[str, typer.Option("--module-package-id")],
        dry_run: Annotated[bool, typer.Option("--dry-run/--apply")] = True,
    ) -> None:
        """Run static contract tests."""

        result = _client(get_client(ctx)).modules.run_contract_tests(
            module_package_id,
            dry_run=dry_run,
        )
        render(ctx, result)


def _client(value: object) -> AIONClient:
    return cast(AIONClient, value)


def _load_manifest(path: Path) -> JSONDict:
    if path.suffix.lower() not in {".json"}:
        raise typer.BadParameter("aionctl modules submit supports JSON manifests in v0.1")
    parsed = json.loads(path.read_text())
    if not isinstance(parsed, dict):
        raise typer.BadParameter("manifest must be a JSON object")
    manifest = cast(JSONDict, parsed)
    if {"package_name", "display_name", "description", "manifest"}.issubset(manifest):
        return manifest
    module_id = str(manifest.get("module_id") or "")
    package_name = module_id.replace(".", "-") or path.stem
    return {
        "module_id": module_id,
        "version": str(manifest.get("version") or "0.1.0"),
        "package_name": package_name,
        "display_name": package_name,
        "description": "Generic AION module package submitted from a manifest file.",
        "manifest": manifest,
        "compatibility": {},
        "metadata": {"source": "aionctl"},
        "submit": True,
    }


def _write_scaffold(output: Path, result: dict[str, JSONValue]) -> None:
    files = result.get("files")
    if not isinstance(files, dict):
        return
    output.mkdir(parents=True, exist_ok=True)
    for name, content in files.items():
        if isinstance(name, str) and isinstance(content, str):
            (output / name).write_text(content)
