"""aionctl security baseline commands."""

from __future__ import annotations

from typing import Annotated, Any, cast

import typer

from aion_sdk.client import AIONClient
from aion_sdk.types import JSONDict

security_app = typer.Typer(no_args_is_help=True, help="Security baseline commands.")
threat_model_app = typer.Typer(no_args_is_help=True, help="Threat model commands.")
controls_app = typer.Typer(no_args_is_help=True, help="Security control commands.")
hardening_app = typer.Typer(no_args_is_help=True, help="Hardening gate commands.")


def install_security_commands(
    app: typer.Typer,
    *,
    get_client: Any,
    get_scope: Any,
    render: Any,
) -> None:
    """Install security commands onto the root CLI."""

    app.add_typer(security_app, name="security")
    security_app.add_typer(threat_model_app, name="threat-model")
    security_app.add_typer(controls_app, name="controls")
    security_app.add_typer(hardening_app, name="hardening-gate")

    @security_app.command("scan")
    def run_scan(
        ctx: typer.Context,
        scan_type: Annotated[str, typer.Option("--scan-type")] = "full",
    ) -> None:
        """Run a deterministic local security scan."""

        payload: JSONDict = {"scan_type": scan_type, "owner_scope": get_scope(ctx)}
        render(ctx, _client(get_client(ctx)).security.run_scan(payload))

    @security_app.command("scans")
    def list_scans(
        ctx: typer.Context,
        scan_type: Annotated[str | None, typer.Option("--scan-type")] = None,
        status: Annotated[str | None, typer.Option("--status")] = None,
    ) -> None:
        """List local security scan runs."""

        render(
            ctx,
            _client(get_client(ctx)).security.list_scans(
                scan_type=scan_type,
                status=status,
            ),
        )

    @threat_model_app.command("seed")
    def seed_threat_models(
        ctx: typer.Context,
        apply: Annotated[bool, typer.Option("--apply", help="Persist defaults.")] = False,
    ) -> None:
        """Seed or preview default threat models."""

        render(
            ctx,
            _client(get_client(ctx)).security.seed_threat_models(
                get_scope(ctx),
                dry_run=not apply,
            ),
        )

    @threat_model_app.command("list")
    def list_threat_models(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        category: Annotated[str | None, typer.Option("--category")] = None,
    ) -> None:
        """List threat models."""

        render(
            ctx,
            _client(get_client(ctx)).security.list_threat_models(
                status=status,
                category=category,
            ),
        )

    @controls_app.command("seed")
    def seed_controls(
        ctx: typer.Context,
        apply: Annotated[bool, typer.Option("--apply", help="Persist defaults.")] = False,
    ) -> None:
        """Seed or preview default controls."""

        render(ctx, _client(get_client(ctx)).security.seed_controls(dry_run=not apply))

    @controls_app.command("list")
    def list_controls(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        category: Annotated[str | None, typer.Option("--category")] = None,
    ) -> None:
        """List controls."""

        render(
            ctx,
            _client(get_client(ctx)).security.list_controls(status=status, category=category),
        )

    @hardening_app.command("run")
    def run_hardening_gate(
        ctx: typer.Context,
        version: Annotated[str | None, typer.Option("--version")] = "0.1.0",
    ) -> None:
        """Run the deterministic local hardening gate."""

        payload: JSONDict = {"version": version, "owner_scope": get_scope(ctx)}
        render(ctx, _client(get_client(ctx)).security.run_hardening_gate(payload))

    @hardening_app.command("get")
    def get_hardening_gate(
        ctx: typer.Context,
        hardening_gate_id: Annotated[str, typer.Option("--id", help="Hardening gate id.")],
    ) -> None:
        """Return one hardening gate run."""

        render(ctx, _client(get_client(ctx)).security.get_hardening_gate(hardening_gate_id))


def _client(value: object) -> AIONClient:
    return cast(AIONClient, value)
