"""aionctl local auth commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Any, cast

import typer

from aion_sdk.client import AIONClient
from aion_sdk.types import JSONDict

local_auth_app = typer.Typer(
    no_args_is_help=True,
    help="Dev-only local auth contract and simulation commands.",
)


def install_local_auth_commands(
    app: typer.Typer,
    *,
    get_client: Any,
    get_scope: Any,
    render: Any,
) -> None:
    """Install local auth commands."""

    app.add_typer(local_auth_app, name="local-auth")

    @local_auth_app.command("roles")
    def roles(ctx: typer.Context) -> None:
        render(ctx, _client(get_client(ctx)).local_auth.roles(get_scope(ctx)))

    @local_auth_app.command("simulate")
    def simulate(
        ctx: typer.Context,
        payload_file: Annotated[Path | None, typer.Option("--payload-file")] = None,
        role: Annotated[list[str] | None, typer.Option("--role")] = None,
    ) -> None:
        payload = _load_payload(payload_file)
        payload.setdefault("roles", role or ["operator"])
        payload.setdefault("owner_scope", get_scope(ctx))
        render(ctx, _client(get_client(ctx)).local_auth.simulate(payload))

    @local_auth_app.command("audit")
    def audit(
        ctx: typer.Context,
        include_examples: Annotated[
            bool,
            typer.Option("--include-examples/--skip-examples"),
        ] = True,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).local_auth.audit(
                {"owner_scope": get_scope(ctx), "include_examples": include_examples}
            ),
        )

    @local_auth_app.command("status")
    def status(ctx: typer.Context) -> None:
        render(ctx, _client(get_client(ctx)).local_auth.status(get_scope(ctx)))


def _client(value: Any) -> AIONClient:
    return cast(AIONClient, value)


def _load_payload(path: Path | None) -> JSONDict:
    if path is None:
        return {}
    return cast(JSONDict, json.loads(path.read_text()))


__all__ = ["install_local_auth_commands"]
