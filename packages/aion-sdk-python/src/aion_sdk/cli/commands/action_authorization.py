"""aionctl dry-run action authorization commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Any, cast

import typer

from aion_sdk.client import AIONClient
from aion_sdk.types import JSONDict

action_authorization_app = typer.Typer(
    no_args_is_help=True,
    help="Dry-run action authorization commands.",
)


def install_action_authorization_commands(
    app: typer.Typer,
    *,
    get_client: Any,
    get_scope: Any,
    render: Any,
) -> None:
    """Install action authorization commands."""

    app.add_typer(action_authorization_app, name="action-authorization")

    @action_authorization_app.command("authorize")
    def authorize(
        ctx: typer.Context,
        payload_file: Annotated[Path | None, typer.Option("--payload-file")] = None,
        action_key: Annotated[str, typer.Option("--action-key")] = "operator.review",
        action_type: Annotated[str, typer.Option("--action-type")] = "generic",
        target_type: Annotated[str, typer.Option("--target-type")] = "generic",
        role: Annotated[list[str] | None, typer.Option("--role")] = None,
        requested_operation: Annotated[str, typer.Option("--operation")] = "preview",
    ) -> None:
        payload = _load_payload(payload_file)
        payload.setdefault("actor_id", "local.operator")
        payload.setdefault("workspace_id", "local")
        payload.setdefault("roles", role or ["operator"])
        payload.setdefault("owner_scope", get_scope(ctx))
        payload.setdefault("action_key", action_key)
        payload.setdefault("action_type", action_type)
        payload.setdefault("target_type", target_type)
        payload.setdefault("mode", "dry_run")
        payload.setdefault("requested_operation", requested_operation)
        render(ctx, _client(get_client(ctx)).action_authorization.authorize(payload))

    @action_authorization_app.command("audit")
    def audit(
        ctx: typer.Context,
        include_examples: Annotated[
            bool,
            typer.Option("--include-examples/--skip-examples"),
        ] = True,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).action_authorization.audit(
                {"owner_scope": get_scope(ctx), "include_examples": include_examples}
            ),
        )

    @action_authorization_app.command("status")
    def status(ctx: typer.Context) -> None:
        render(ctx, _client(get_client(ctx)).action_authorization.status(get_scope(ctx)))


def _load_payload(path: Path | None) -> JSONDict:
    if path is None:
        return {}
    loaded = json.loads(path.read_text())
    if not isinstance(loaded, dict):
        raise typer.BadParameter("payload file must contain a JSON object")
    return cast(JSONDict, loaded)


def _client(value: object) -> AIONClient:
    return cast(AIONClient, value)


__all__ = ["install_action_authorization_commands"]
