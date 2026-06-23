"""aionctl model provider hardening commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Any, cast

import typer

from aion_sdk.client import AIONClient
from aion_sdk.types import JSONDict

model_providers_app = typer.Typer(
    no_args_is_help=True,
    help="Model provider hardening dry-run commands.",
)
profiles_app = typer.Typer(no_args_is_help=True, help="Provider profile commands.")


def install_model_provider_hardening_commands(
    app: typer.Typer,
    *,
    get_client: Any,
    get_scope: Any,
    render: Any,
) -> None:
    """Install model provider hardening commands."""

    app.add_typer(model_providers_app, name="model-providers")
    model_providers_app.add_typer(profiles_app, name="profiles")

    @profiles_app.command("seed")
    def seed_profiles(
        ctx: typer.Context,
        persist: Annotated[
            bool,
            typer.Option("--apply", help="Persist default profiles. Dry-run by default."),
        ] = False,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).model_provider_hardening.seed_profiles(
                {"scope": get_scope(ctx), "dry_run": not persist}
            ),
        )

    @profiles_app.command("create")
    def create_profile(
        ctx: typer.Context,
        provider_key: Annotated[str, typer.Argument()],
        name: Annotated[str, typer.Option("--name")] = "Generic Provider Profile",
        description: Annotated[str, typer.Option("--description")] = (
            "Metadata-only provider readiness profile."
        ),
        provider_type: Annotated[str, typer.Option("--provider-type")] = "metadata_only",
        payload_file: Annotated[Path | None, typer.Option("--payload-file")] = None,
    ) -> None:
        payload = _load_payload(payload_file)
        payload.setdefault("provider_key", provider_key)
        payload.setdefault("name", name)
        payload.setdefault("description", description)
        payload.setdefault("provider_type", provider_type)
        payload.setdefault("owner_scope", get_scope(ctx))
        render(ctx, _client(get_client(ctx)).model_provider_hardening.create_profile(payload))

    @profiles_app.command("list")
    def list_profiles(
        ctx: typer.Context,
        provider_key: Annotated[str | None, typer.Option("--provider-key")] = None,
        status: Annotated[str | None, typer.Option("--status")] = None,
        risk_level: Annotated[str | None, typer.Option("--risk-level")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).model_provider_hardening.list_profiles(
                get_scope(ctx),
                provider_key=provider_key,
                status=status,
                risk_level=risk_level,
                limit=limit,
            ),
        )

    @model_providers_app.command("egress-preview")
    def egress_preview(
        ctx: typer.Context,
        provider_key: Annotated[str, typer.Argument()],
        payload_file: Annotated[Path | None, typer.Option("--payload-file")] = None,
    ) -> None:
        payload = _load_payload(payload_file)
        payload.setdefault("provider_key", provider_key)
        payload.setdefault("owner_scope", get_scope(ctx))
        payload.setdefault("preview_type", "dry_run")
        render(ctx, _client(get_client(ctx)).model_provider_hardening.egress_preview(payload))

    @model_providers_app.command("simulate")
    def simulate(
        ctx: typer.Context,
        provider_key: Annotated[str, typer.Argument()],
        payload_file: Annotated[Path | None, typer.Option("--payload-file")] = None,
    ) -> None:
        payload = _load_payload(payload_file)
        payload.setdefault("provider_key", provider_key)
        payload.setdefault("owner_scope", get_scope(ctx))
        payload.setdefault("simulation_type", "dry_run")
        render(ctx, _client(get_client(ctx)).model_provider_hardening.simulate(payload))

    @model_providers_app.command("readiness")
    def readiness(
        ctx: typer.Context,
        provider_key: Annotated[str, typer.Argument()],
        payload_file: Annotated[Path | None, typer.Option("--payload-file")] = None,
    ) -> None:
        payload = _load_payload(payload_file)
        payload.setdefault("provider_key", provider_key)
        payload.setdefault("owner_scope", get_scope(ctx))
        render(ctx, _client(get_client(ctx)).model_provider_hardening.assess_readiness(payload))

    @model_providers_app.command("blockers")
    def blockers(
        ctx: typer.Context,
        provider_key: Annotated[str | None, typer.Option("--provider-key")] = None,
        status: Annotated[str | None, typer.Option("--status")] = "open",
        severity: Annotated[str | None, typer.Option("--severity")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).model_provider_hardening.blockers(
                get_scope(ctx),
                provider_key=provider_key,
                status=status,
                severity=severity,
                limit=limit,
            ),
        )

    @model_providers_app.command("query")
    def query(
        ctx: typer.Context,
        provider_key: Annotated[str | None, typer.Option("--provider-key")] = None,
        status: Annotated[str | None, typer.Option("--status")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 50,
    ) -> None:
        payload: JSONDict = {
            "scope": get_scope(ctx),
            "provider_key": provider_key,
            "status": status,
            "limit": limit,
        }
        render(ctx, _client(get_client(ctx)).model_provider_hardening.query(payload))


def _client(value: Any) -> AIONClient:
    return cast(AIONClient, value)


def _load_payload(path: Path | None) -> JSONDict:
    if path is None:
        return {}
    return cast(JSONDict, json.loads(path.read_text()))


__all__ = ["install_model_provider_hardening_commands"]
