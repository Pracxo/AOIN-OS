"""aionctl connector credential commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Any, cast

import typer

from aion_sdk.client import AIONClient
from aion_sdk.types import JSONDict

connector_credentials_app = typer.Typer(
    no_args_is_help=True,
    help="Connector credential architecture and readiness preview commands.",
)


def install_connector_credentials_commands(
    app: typer.Typer,
    *,
    get_client: Any,
    get_scope: Any,
    render: Any,
) -> None:
    """Install connector-credentials commands."""

    app.add_typer(connector_credentials_app, name="connector-credentials")

    @connector_credentials_app.command("boundary")
    def boundary(ctx: typer.Context) -> None:
        render(ctx, _client(get_client(ctx)).connector_credentials.boundary())

    @connector_credentials_app.command("lifecycle")
    def lifecycle(ctx: typer.Context) -> None:
        render(ctx, _client(get_client(ctx)).connector_credentials.lifecycle())

    @connector_credentials_app.command("authorization")
    def authorization(ctx: typer.Context) -> None:
        render(ctx, _client(get_client(ctx)).connector_credentials.authorization())

    @connector_credentials_app.command("readiness")
    def readiness(
        ctx: typer.Context,
        payload_file: Annotated[Path | None, typer.Option("--payload-file")] = None,
        connector_key: Annotated[str, typer.Option("--connector-key")] = "mock.local.preview",
    ) -> None:
        payload = _load_payload(payload_file)
        payload.setdefault("connector_key", connector_key)
        payload.setdefault("owner_scope", get_scope(ctx))
        payload.setdefault("requested_scopes", ["connector_credentials.readiness.preview"])
        payload.setdefault(
            "evidence_refs",
            ["docs/connectors/connector-credential-readiness-gate.md"],
        )
        render(ctx, _client(get_client(ctx)).connector_credentials.readiness(payload))

    @connector_credentials_app.command("redaction-preview")
    def redaction_preview(
        ctx: typer.Context,
        payload_file: Annotated[Path | None, typer.Option("--payload-file")] = None,
    ) -> None:
        payload = _load_payload(payload_file)
        payload.setdefault("sample", "safe-placeholder")
        render(ctx, _client(get_client(ctx)).connector_credentials.redaction_preview(payload))

    @connector_credentials_app.command("status")
    def status(ctx: typer.Context) -> None:
        render(ctx, _client(get_client(ctx)).connector_credentials.status(get_scope(ctx)))


def _load_payload(path: Path | None) -> JSONDict:
    if path is None:
        return {}
    loaded = json.loads(path.read_text())
    if not isinstance(loaded, dict):
        raise typer.BadParameter("payload file must contain a JSON object")
    return cast(JSONDict, loaded)


def _client(value: object) -> AIONClient:
    return cast(AIONClient, value)


__all__ = ["install_connector_credentials_commands"]
