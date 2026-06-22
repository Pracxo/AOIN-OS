"""aionctl first-run bootstrap commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Any, cast

import typer

from aion_sdk.client import AIONClient
from aion_sdk.types import JSONDict

profiles_app = typer.Typer(no_args_is_help=False, invoke_without_command=True)
seed_bundles_app = typer.Typer(no_args_is_help=False, invoke_without_command=True)


def install_bootstrap_commands(
    app: typer.Typer,
    *,
    get_client: Any,
    get_scope: Any,
    render: Any,
) -> None:
    """Install first-run bootstrap commands onto an existing bootstrap Typer."""

    app.add_typer(profiles_app, name="profiles", help="Bootstrap profile commands.")
    app.add_typer(seed_bundles_app, name="seed-bundles", help="Seed bundle commands.")

    @profiles_app.callback()
    def profiles(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        profile_type: Annotated[str | None, typer.Option("--profile-type")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        """List local bootstrap profiles."""

        if ctx.invoked_subcommand is None:
            render(
                ctx,
                _client(get_client(ctx)).bootstrap.list_profiles(
                    get_scope(ctx),
                    status=status,
                    profile_type=profile_type,
                    limit=limit,
                ),
            )

    @profiles_app.command("seed")
    def seed_profiles(
        ctx: typer.Context,
        dry_run: Annotated[
            bool,
            typer.Option("--dry-run/--apply", help="Preview by default; --apply persists."),
        ] = True,
    ) -> None:
        """Seed built-in local bootstrap profiles."""

        render(
            ctx,
            _client(get_client(ctx)).bootstrap.seed_profiles(get_scope(ctx), dry_run=dry_run),
        )

    @seed_bundles_app.callback()
    def seed_bundles(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        bundle_type: Annotated[str | None, typer.Option("--bundle-type")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        """List local seed bundles."""

        if ctx.invoked_subcommand is None:
            render(
                ctx,
                _client(get_client(ctx)).bootstrap.list_seed_bundles(
                    get_scope(ctx),
                    status=status,
                    bundle_type=bundle_type,
                    limit=limit,
                ),
            )

    @seed_bundles_app.command("seed")
    def seed_default_bundles(
        ctx: typer.Context,
        dry_run: Annotated[
            bool,
            typer.Option("--dry-run/--apply", help="Preview by default; --apply persists."),
        ] = True,
    ) -> None:
        """Seed built-in local seed bundles."""

        render(
            ctx,
            _client(get_client(ctx)).bootstrap.seed_bundles(get_scope(ctx), dry_run=dry_run),
        )

    @app.command("seed")
    def seed(
        ctx: typer.Context,
        seed_bundle_key: Annotated[str, typer.Option("--seed-bundle-key")],
        payload_file: Annotated[Path | None, typer.Option("--payload-file")] = None,
        dry_run: Annotated[
            bool,
            typer.Option("--dry-run/--controlled", help="Run in dry-run mode by default."),
        ] = True,
    ) -> None:
        """Execute one local seed bundle."""

        payload = _load_payload(payload_file)
        payload.setdefault("owner_scope", get_scope(ctx))
        payload.setdefault("seed_bundle_key", seed_bundle_key)
        payload.setdefault("mode", "dry_run" if dry_run else "controlled")
        render(ctx, _client(get_client(ctx)).bootstrap.seed(payload))

    @app.command("doctor")
    def doctor(
        ctx: typer.Context,
        payload_file: Annotated[Path | None, typer.Option("--payload-file")] = None,
        create_findings: Annotated[
            bool,
            typer.Option("--create-findings/--no-create-findings"),
        ] = True,
    ) -> None:
        """Run local setup doctor."""

        payload = _load_payload(payload_file)
        payload.setdefault("owner_scope", get_scope(ctx))
        payload.setdefault("create_findings", create_findings)
        render(ctx, _client(get_client(ctx)).bootstrap.doctor(payload))

    @app.command("run")
    def run(
        ctx: typer.Context,
        payload_file: Annotated[Path | None, typer.Option("--payload-file")] = None,
        profile_key: Annotated[str, typer.Option("--profile-key")] = "local.dev",
        dry_run: Annotated[
            bool,
            typer.Option("--dry-run/--controlled", help="Run in dry-run mode by default."),
        ] = True,
        seed_defaults: Annotated[bool, typer.Option("--seed-defaults/--no-seed-defaults")] = True,
        setup_doctor: Annotated[bool, typer.Option("--doctor/--no-doctor")] = True,
    ) -> None:
        """Run local first-run bootstrap."""

        payload = _load_payload(payload_file)
        payload.setdefault("owner_scope", get_scope(ctx))
        payload.setdefault("profile_key", profile_key)
        payload.setdefault("mode", "dry_run" if dry_run else "controlled")
        payload.setdefault("seed_defaults", seed_defaults)
        payload.setdefault("run_setup_doctor", setup_doctor)
        render(ctx, _client(get_client(ctx)).bootstrap.run(payload))

    @app.command("runs")
    def runs(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        profile_key: Annotated[str | None, typer.Option("--profile-key")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 50,
    ) -> None:
        """List bootstrap runs."""

        render(
            ctx,
            _client(get_client(ctx)).bootstrap.list_runs(
                get_scope(ctx),
                status=status,
                profile_key=profile_key,
                limit=limit,
            ),
        )

    @app.command("findings")
    def findings(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        severity: Annotated[str | None, typer.Option("--severity")] = None,
        category: Annotated[str | None, typer.Option("--category")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        """List local setup findings."""

        render(
            ctx,
            _client(get_client(ctx)).bootstrap.list_findings(
                get_scope(ctx),
                status=status,
                severity=severity,
                category=category,
                limit=limit,
            ),
        )

    @app.command("reports")
    def reports(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 50,
    ) -> None:
        """List setup reports."""

        render(
            ctx,
            _client(get_client(ctx)).bootstrap.list_reports(
                get_scope(ctx),
                status=status,
                limit=limit,
            ),
        )


def _client(value: Any) -> AIONClient:
    return cast(AIONClient, value)


def _load_payload(path: Path | None) -> JSONDict:
    if path is None:
        return {}
    return cast(JSONDict, json.loads(path.read_text()))


__all__ = ["install_bootstrap_commands"]
