"""aionctl connector sandbox commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Any, cast

import typer

from aion_sdk.client import AIONClient
from aion_sdk.types import JSONDict

connector_sandbox_app = typer.Typer(
    no_args_is_help=True,
    help="Connector sandbox design and readiness preview commands.",
)


def install_connector_sandbox_commands(
    app: typer.Typer,
    *,
    get_client: Any,
    get_scope: Any,
    render: Any,
) -> None:
    """Install connector-sandbox commands."""

    app.add_typer(connector_sandbox_app, name="connector-sandbox")

    @connector_sandbox_app.command("boundary")
    def boundary(ctx: typer.Context) -> None:
        render(ctx, _client(get_client(ctx)).connector_sandbox.boundary())

    @connector_sandbox_app.command("capability-rules")
    def capability_rules(ctx: typer.Context) -> None:
        render(ctx, _client(get_client(ctx)).connector_sandbox.capability_rules())

    @connector_sandbox_app.command("readiness")
    def readiness(
        ctx: typer.Context,
        payload_file: Annotated[Path | None, typer.Option("--payload-file")] = None,
        connector_key: Annotated[str, typer.Option("--connector-key")] = "mock.local.preview",
    ) -> None:
        payload = _load_payload(payload_file)
        payload.setdefault("connector_key", connector_key)
        payload.setdefault("owner_scope", get_scope(ctx))
        payload.setdefault("requested_capabilities", ["connector.sandbox.readiness.preview"])
        payload.setdefault(
            "declared_policy_actions",
            ["connector_sandbox.readiness.preview"],
        )
        payload.setdefault("evidence_refs", ["docs/connectors/connector-sandbox-readiness-gate.md"])
        render(ctx, _client(get_client(ctx)).connector_sandbox.readiness(payload))

    @connector_sandbox_app.command("status")
    def status(ctx: typer.Context) -> None:
        render(ctx, _client(get_client(ctx)).connector_sandbox.status(get_scope(ctx)))


def _load_payload(path: Path | None) -> JSONDict:
    if path is None:
        return {}
    loaded = json.loads(path.read_text())
    if not isinstance(loaded, dict):
        raise typer.BadParameter("payload file must contain a JSON object")
    return cast(JSONDict, loaded)


def _client(value: object) -> AIONClient:
    return cast(AIONClient, value)


__all__ = ["install_connector_sandbox_commands"]
