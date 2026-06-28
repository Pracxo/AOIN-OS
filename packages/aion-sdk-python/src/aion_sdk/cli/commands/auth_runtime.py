"""aionctl disabled auth runtime commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Any, cast

import typer

from aion_sdk.client import AIONClient
from aion_sdk.types import JSONDict

auth_runtime_app = typer.Typer(
    no_args_is_help=True,
    help="Disabled production auth runtime commands.",
)


def install_auth_runtime_commands(
    app: typer.Typer,
    *,
    get_client: Any,
    get_scope: Any,
    render: Any,
) -> None:
    """Install auth-runtime commands."""

    app.add_typer(auth_runtime_app, name="auth-runtime")

    @auth_runtime_app.command("status")
    def status(ctx: typer.Context) -> None:
        render(ctx, _client(get_client(ctx)).auth_runtime.status(get_scope(ctx)))

    @auth_runtime_app.command("mock-claims-preview")
    def mock_claims_preview(
        ctx: typer.Context,
        payload_file: Annotated[Path | None, typer.Option("--payload-file")] = None,
        subject: Annotated[str, typer.Option("--subject")] = "local.operator",
        role: Annotated[list[str] | None, typer.Option("--role")] = None,
    ) -> None:
        payload = _load_payload(payload_file)
        payload.setdefault("issuer", "mock.local")
        payload.setdefault("subject", subject)
        payload.setdefault("audience", "aion.local")
        payload.setdefault("roles", role or ["operator"])
        payload.setdefault("workspace_id", "local")
        payload.setdefault("owner_scope", get_scope(ctx))
        payload.setdefault("mode", "preview")
        render(ctx, _client(get_client(ctx)).auth_runtime.mock_claims_preview(payload))

    @auth_runtime_app.command("audit")
    def audit(
        ctx: typer.Context,
        include_examples: Annotated[
            bool,
            typer.Option("--include-examples/--skip-examples"),
        ] = True,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).auth_runtime.audit(
                {"owner_scope": get_scope(ctx), "include_examples": include_examples}
            ),
        )


def _load_payload(path: Path | None) -> JSONDict:
    if path is None:
        return {}
    loaded = json.loads(path.read_text())
    if not isinstance(loaded, dict):
        raise typer.BadParameter("payload file must contain a JSON object")
    return cast(JSONDict, loaded)


def _client(value: object) -> AIONClient:
    return cast(AIONClient, value)


__all__ = ["install_auth_runtime_commands"]
