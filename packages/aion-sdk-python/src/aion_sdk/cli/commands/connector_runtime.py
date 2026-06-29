"""aionctl disabled connector runtime commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Any, cast

import typer

from aion_sdk.client import AIONClient
from aion_sdk.types import JSONDict

connector_runtime_app = typer.Typer(
    no_args_is_help=True,
    help="Disabled external connector runtime commands.",
)


def install_connector_runtime_commands(
    app: typer.Typer,
    *,
    get_client: Any,
    get_scope: Any,
    render: Any,
) -> None:
    """Install connector-runtime commands."""

    app.add_typer(connector_runtime_app, name="connector-runtime")

    @connector_runtime_app.command("status")
    def status(ctx: typer.Context) -> None:
        render(ctx, _client(get_client(ctx)).connector_runtime.status(get_scope(ctx)))

    @connector_runtime_app.command("validate-manifest")
    def validate_manifest(
        ctx: typer.Context,
        payload_file: Annotated[Path | None, typer.Option("--payload-file")] = None,
        connector_key: Annotated[str, typer.Option("--connector-key")] = "mock.local.preview",
        name: Annotated[str, typer.Option("--name")] = "Mock Local Preview",
    ) -> None:
        payload = _load_payload(payload_file)
        payload.setdefault("connector_key", connector_key)
        payload.setdefault("name", name)
        payload.setdefault("description", "Mock-only connector preview manifest.")
        payload.setdefault("version", "0.0.0-preview")
        payload.setdefault("owner_scope", get_scope(ctx))
        payload.setdefault("connector_type", "mock")
        payload.setdefault("supported_modes", ["dry_run"])
        payload.setdefault("declared_capabilities", [])
        payload.setdefault("required_policy_actions", [])
        payload.setdefault("required_scopes", [])
        payload.setdefault("sandbox_required", True)
        payload.setdefault("dry_run_supported", True)
        payload.setdefault("external_calls_required", False)
        payload.setdefault("credentials_required", False)
        payload.setdefault("routes_declared", [])
        render(ctx, _client(get_client(ctx)).connector_runtime.validate_manifest(payload))

    @connector_runtime_app.command("egress-preview")
    def egress_preview(
        ctx: typer.Context,
        payload_file: Annotated[Path | None, typer.Option("--payload-file")] = None,
        connector_key: Annotated[str, typer.Option("--connector-key")] = "mock.local.preview",
    ) -> None:
        payload = _load_payload(payload_file)
        payload.setdefault("connector_key", connector_key)
        payload.setdefault("owner_scope", get_scope(ctx))
        payload.setdefault("preview_type", "dry_run")
        payload.setdefault("payload_summary", {"fields": [], "external_call_allowed": False})
        render(ctx, _client(get_client(ctx)).connector_runtime.egress_preview(payload))

    @connector_runtime_app.command("ingress-preview")
    def ingress_preview(
        ctx: typer.Context,
        payload_file: Annotated[Path | None, typer.Option("--payload-file")] = None,
        connector_key: Annotated[str, typer.Option("--connector-key")] = "mock.local.preview",
    ) -> None:
        payload = _load_payload(payload_file)
        payload.setdefault("connector_key", connector_key)
        payload.setdefault("owner_scope", get_scope(ctx))
        payload.setdefault("preview_type", "dry_run")
        payload.setdefault("response_summary", {"fields": [], "trusted": False})
        render(ctx, _client(get_client(ctx)).connector_runtime.ingress_preview(payload))

    @connector_runtime_app.command("audit")
    def audit(
        ctx: typer.Context,
        include_examples: Annotated[
            bool,
            typer.Option("--include-examples/--skip-examples"),
        ] = True,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).connector_runtime.audit(
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


__all__ = ["install_connector_runtime_commands"]
