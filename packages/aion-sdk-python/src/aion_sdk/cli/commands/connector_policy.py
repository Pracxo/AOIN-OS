"""aionctl connector policy commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Any, cast

import typer

from aion_sdk.client import AIONClient
from aion_sdk.types import JSONDict

connector_policy_app = typer.Typer(
    no_args_is_help=True,
    help="Connector policy catalog and dry-run preview commands.",
)


def install_connector_policy_commands(
    app: typer.Typer,
    *,
    get_client: Any,
    get_scope: Any,
    render: Any,
) -> None:
    """Install connector-policy commands."""

    app.add_typer(connector_policy_app, name="connector-policy")

    @connector_policy_app.command("catalog")
    def catalog(ctx: typer.Context) -> None:
        render(ctx, _client(get_client(ctx)).connector_policy.catalog())

    @connector_policy_app.command("matrix")
    def matrix(ctx: typer.Context) -> None:
        render(ctx, _client(get_client(ctx)).connector_policy.matrix())

    @connector_policy_app.command("dry-run")
    def dry_run(
        ctx: typer.Context,
        payload_file: Annotated[Path | None, typer.Option("--payload-file")] = None,
        connector_key: Annotated[str, typer.Option("--connector-key")] = "mock.local.preview",
        action_key: Annotated[
            str,
            typer.Option("--action-key"),
        ] = "connector_policy.dry_run",
        role: Annotated[str, typer.Option("--role")] = "operator",
    ) -> None:
        payload = _load_payload(payload_file)
        payload.setdefault("connector_key", connector_key)
        payload.setdefault("requested_action_key", action_key)
        payload.setdefault("role", role)
        payload.setdefault("owner_scope", get_scope(ctx))
        payload.setdefault("declared_scopes", get_scope(ctx))
        payload.setdefault("evidence_refs", ["docs/connectors/connector-policy-dry-run-gate.md"])
        render(ctx, _client(get_client(ctx)).connector_policy.dry_run(payload))

    @connector_policy_app.command("status")
    def status(ctx: typer.Context) -> None:
        render(ctx, _client(get_client(ctx)).connector_policy.status(get_scope(ctx)))


def _load_payload(path: Path | None) -> JSONDict:
    if path is None:
        return {}
    loaded = json.loads(path.read_text())
    if not isinstance(loaded, dict):
        raise typer.BadParameter("payload file must contain a JSON object")
    return cast(JSONDict, loaded)


def _client(value: object) -> AIONClient:
    return cast(AIONClient, value)


__all__ = ["install_connector_policy_commands"]
