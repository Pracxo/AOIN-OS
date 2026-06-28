"""aionctl local session commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Any, cast

import typer

from aion_sdk.client import AIONClient
from aion_sdk.types import JSONDict

local_session_app = typer.Typer(
    no_args_is_help=True,
    help="Read-only local session prototype commands.",
)


def install_local_session_commands(
    app: typer.Typer,
    *,
    get_client: Any,
    get_scope: Any,
    render: Any,
) -> None:
    """Install local session commands."""

    app.add_typer(local_session_app, name="local-session")

    @local_session_app.command("preview")
    def preview(
        ctx: typer.Context,
        payload_file: Annotated[Path | None, typer.Option("--payload-file")] = None,
        role: Annotated[list[str] | None, typer.Option("--role")] = None,
    ) -> None:
        payload = _load_payload(payload_file)
        payload.setdefault("roles", role or ["operator"])
        payload.setdefault("owner_scope", get_scope(ctx))
        render(ctx, _client(get_client(ctx)).local_session.preview(payload))

    @local_session_app.command("context")
    def context(
        ctx: typer.Context,
        payload_file: Annotated[Path | None, typer.Option("--payload-file")] = None,
        role: Annotated[list[str] | None, typer.Option("--role")] = None,
    ) -> None:
        payload = _load_payload(payload_file)
        payload.setdefault("roles", role or ["operator"])
        payload.setdefault("owner_scope", get_scope(ctx))
        render(ctx, _client(get_client(ctx)).local_session.context(payload))

    @local_session_app.command("status")
    def status(ctx: typer.Context) -> None:
        render(ctx, _client(get_client(ctx)).local_session.status(get_scope(ctx)))

    @local_session_app.command("boundary-check")
    def boundary_check(ctx: typer.Context) -> None:
        render(ctx, _client(get_client(ctx)).local_session.boundary_check(get_scope(ctx)))

    @local_session_app.command("audit")
    def audit(
        ctx: typer.Context,
        include_examples: Annotated[
            bool,
            typer.Option("--include-examples/--skip-examples"),
        ] = True,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).local_session.audit(
                {"owner_scope": get_scope(ctx), "include_examples": include_examples}
            ),
        )


def _client(value: Any) -> AIONClient:
    return cast(AIONClient, value)


def _load_payload(path: Path | None) -> JSONDict:
    if path is None:
        return {}
    return cast(JSONDict, json.loads(path.read_text()))


__all__ = ["install_local_session_commands"]
