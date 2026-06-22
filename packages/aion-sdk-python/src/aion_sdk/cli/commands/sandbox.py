"""aionctl sandbox, secrets, and connectors commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Any, cast

import typer

from aion_sdk.client import AIONClient
from aion_sdk.types import JSONDict

sandbox_app = typer.Typer(no_args_is_help=True, help="Sandbox Control Plane helpers.")
profile_app = typer.Typer(no_args_is_help=True, help="Sandbox profile commands.")
secrets_app = typer.Typer(no_args_is_help=True, help="Secret reference commands.")
connectors_app = typer.Typer(no_args_is_help=True, help="Connector registry commands.")

sandbox_app.add_typer(profile_app, name="profile")


def install_sandbox_commands(
    app: typer.Typer,
    *,
    get_client: Any,
    get_scope: Any,
    render: Any,
) -> None:
    """Install sandbox, secrets, and connectors commands."""

    app.add_typer(sandbox_app, name="sandbox")
    app.add_typer(secrets_app, name="secrets")
    app.add_typer(connectors_app, name="connectors")

    @profile_app.command("create")
    def profile_create(
        ctx: typer.Context,
        name: Annotated[str, typer.Option("--name")],
        description: Annotated[str, typer.Option("--description")],
        sandbox_type: Annotated[str, typer.Option("--sandbox-type")] = "local_noop",
    ) -> None:
        """Create a conservative sandbox profile."""
        payload: JSONDict = {
            "name": name,
            "description": description,
            "sandbox_type": sandbox_type,
            "owner_scope": get_scope(ctx),
            "resource_limits": _default_limits(),
            "metadata": {"source": "aionctl"},
        }
        render(ctx, _client(get_client(ctx)).sandbox.create_profile(payload))

    @profile_app.command("list")
    def profile_list(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
    ) -> None:
        """List sandbox profiles."""
        render(ctx, _client(get_client(ctx)).sandbox.list_profiles(get_scope(ctx), status=status))

    @profile_app.command("validate")
    def profile_validate(
        ctx: typer.Context,
        sandbox_profile_id: Annotated[str, typer.Option("--sandbox-profile-id")],
    ) -> None:
        """Validate one sandbox profile."""
        result = _client(get_client(ctx)).sandbox.validate_profile(
            sandbox_profile_id,
            get_scope(ctx),
        )
        render(ctx, result)

    @sandbox_app.command("run")
    def sandbox_run(
        ctx: typer.Context,
        sandbox_profile_id: Annotated[str, typer.Option("--sandbox-profile-id")],
        target_type: Annotated[str, typer.Option("--target-type")] = "test",
        target_id: Annotated[str | None, typer.Option("--target-id")] = None,
        payload: Annotated[Path | None, typer.Option("--payload")] = None,
    ) -> None:
        """Run sandbox validation in dry-run mode."""
        request: JSONDict = {
            "sandbox_profile_id": sandbox_profile_id,
            "target_type": target_type,
            "target_id": target_id,
            "mode": "dry_run",
            "input": _load_json(payload) if payload else {},
            "metadata": {"source": "aionctl"},
        }
        render(ctx, _client(get_client(ctx)).sandbox.run(request))

    @secrets_app.command("create-ref")
    def secret_create_ref(
        ctx: typer.Context,
        name: Annotated[str, typer.Option("--name")],
        description: Annotated[str, typer.Option("--description")],
        secret_type: Annotated[str, typer.Option("--secret-type")] = "generic_ref",
        external_ref: Annotated[str | None, typer.Option("--external-ref")] = None,
        raw_value: Annotated[str | None, typer.Option("--raw-value")] = None,
    ) -> None:
        """Create a metadata-only secret reference."""
        if raw_value is not None:
            raise typer.BadParameter("raw secret values are not accepted; use --external-ref")
        payload: JSONDict = {
            "name": name,
            "description": description,
            "owner_scope": get_scope(ctx),
            "secret_type": secret_type,
            "external_ref": external_ref,
            "metadata": {"source": "aionctl"},
        }
        render(ctx, _client(get_client(ctx)).sandbox.create_secret_ref(payload))

    @secrets_app.command("list")
    def secret_list(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
    ) -> None:
        """List secret references."""
        render(
            ctx,
            _client(get_client(ctx)).sandbox.list_secret_refs(get_scope(ctx), status=status),
        )

    @connectors_app.command("create")
    def connector_create(
        ctx: typer.Context,
        name: Annotated[str, typer.Option("--name")],
        description: Annotated[str, typer.Option("--description")],
        connector_type: Annotated[str, typer.Option("--connector-type")] = "generic_placeholder",
    ) -> None:
        """Create connector metadata."""
        payload: JSONDict = {
            "name": name,
            "description": description,
            "connector_type": connector_type,
            "owner_scope": get_scope(ctx),
            "metadata": {"source": "aionctl"},
        }
        render(ctx, _client(get_client(ctx)).sandbox.create_connector(payload))

    @connectors_app.command("list")
    def connector_list(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        connector_type: Annotated[str | None, typer.Option("--connector-type")] = None,
    ) -> None:
        """List connectors."""
        result = _client(get_client(ctx)).sandbox.list_connectors(
            get_scope(ctx),
            status=status,
            connector_type=connector_type,
        )
        render(ctx, result)

    @connectors_app.command("validate")
    def connector_validate(
        ctx: typer.Context,
        connector_id: Annotated[str, typer.Option("--connector-id")],
    ) -> None:
        """Validate connector metadata."""
        result = _client(get_client(ctx)).sandbox.validate_connector(connector_id, get_scope(ctx))
        render(ctx, result)


def _client(value: object) -> AIONClient:
    return cast(AIONClient, value)


def _default_limits() -> JSONDict:
    return {
        "cpu_millis": 500,
        "memory_mb": 128,
        "timeout_seconds": 30,
        "max_output_bytes": 65536,
        "max_files": 0,
        "max_file_bytes": 0,
    }


def _load_json(path: Path) -> JSONDict:
    parsed = json.loads(path.read_text())
    if not isinstance(parsed, dict):
        raise typer.BadParameter("payload must be a JSON object")
    return cast(JSONDict, parsed)
