"""aionctl Operator Console read-only commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Any, cast

import typer

from aion_sdk.client import AIONClient
from aion_sdk.types import JSONDict

operator_console_app = typer.Typer(
    no_args_is_help=True,
    help="Read-only Operator Console view-model commands.",
)


def install_operator_console_commands(
    app: typer.Typer,
    *,
    get_client: Any,
    get_scope: Any,
    render: Any,
) -> None:
    """Install read-only operator console commands."""

    app.add_typer(operator_console_app, name="operator-console")

    @operator_console_app.command("views")
    def views(ctx: typer.Context) -> None:
        render(ctx, _client(get_client(ctx)).operator_console.list_views(get_scope(ctx)))

    @operator_console_app.command("view-model")
    def view_model(
        ctx: typer.Context,
        view: Annotated[str, typer.Option("--view")] = "overview",
        payload_file: Annotated[Path | None, typer.Option("--payload-file")] = None,
    ) -> None:
        payload = _load_payload(payload_file)
        payload.setdefault("view", view)
        payload.setdefault("owner_scope", get_scope(ctx))
        render(ctx, _client(get_client(ctx)).operator_console.view_model(payload))

    @operator_console_app.command("audit")
    def audit(
        ctx: typer.Context,
        payload_file: Annotated[Path | None, typer.Option("--payload-file")] = None,
    ) -> None:
        payload = _load_payload(payload_file)
        payload.setdefault("owner_scope", get_scope(ctx))
        render(ctx, _client(get_client(ctx)).operator_console.audit(payload))

    @operator_console_app.command("workflows")
    def workflows(ctx: typer.Context) -> None:
        render(ctx, _client(get_client(ctx)).operator_console.workflows(get_scope(ctx)))

    @operator_console_app.command("demo-map")
    def demo_map(ctx: typer.Context) -> None:
        render(ctx, _client(get_client(ctx)).operator_console.demo_map(get_scope(ctx)))


def _client(value: Any) -> AIONClient:
    return cast(AIONClient, value)


def _load_payload(path: Path | None) -> JSONDict:
    if path is None:
        return {}
    return cast(JSONDict, json.loads(path.read_text()))


__all__ = ["install_operator_console_commands"]
