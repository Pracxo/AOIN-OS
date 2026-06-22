"""aionctl self-model commands."""

from __future__ import annotations

from typing import Annotated, Any, cast

import typer

from aion_sdk.client import AIONClient
from aion_sdk.types import JSONDict

self_app = typer.Typer(no_args_is_help=True, help="Self-model commands.")
capabilities_app = typer.Typer(
    invoke_without_command=True,
    help="Capability awareness commands.",
)
limitations_app = typer.Typer(
    invoke_without_command=True,
    help="Limitation ledger commands.",
)
confidence_app = typer.Typer(no_args_is_help=True, help="Confidence calibration commands.")
assessment_app = typer.Typer(no_args_is_help=True, help="Self-assessment commands.")
introspection_app = typer.Typer(no_args_is_help=True, help="Introspection commands.")


def install_self_model_commands(
    app: typer.Typer,
    *,
    get_client: Any,
    get_scope: Any,
    render: Any,
) -> None:
    """Install self-model commands."""
    app.add_typer(self_app, name="self")
    self_app.add_typer(capabilities_app, name="capabilities")
    self_app.add_typer(limitations_app, name="limitations")
    self_app.add_typer(confidence_app, name="confidence")
    self_app.add_typer(assessment_app, name="assessment")
    self_app.add_typer(introspection_app, name="introspection")

    @self_app.command("describe")
    def describe(
        ctx: typer.Context,
        format: Annotated[str, typer.Option("--format")] = "structured",
        include_limitations: Annotated[
            bool,
            typer.Option("--limitations/--no-limitations"),
        ] = True,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).self_model.describe(
                get_scope(ctx),
                include_limitations=include_limitations,
                format=format,
            ),
        )

    @capabilities_app.callback()
    def capabilities_callback(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        capability_type: Annotated[str | None, typer.Option("--type")] = None,
    ) -> None:
        if ctx.invoked_subcommand is None:
            _render_capabilities(ctx, get_client, get_scope, render, status, capability_type)

    @capabilities_app.command("list")
    def list_capabilities(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        capability_type: Annotated[str | None, typer.Option("--type")] = None,
    ) -> None:
        _render_capabilities(ctx, get_client, get_scope, render, status, capability_type)

    @capabilities_app.command("refresh")
    def refresh_capabilities(
        ctx: typer.Context,
        dry_run: Annotated[bool, typer.Option("--dry-run/--write")] = True,
    ) -> None:
        render(
            ctx, _client(get_client(ctx)).self_model.refresh_capabilities(get_scope(ctx), dry_run)
        )

    @limitations_app.callback()
    def limitations_callback(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        severity: Annotated[str | None, typer.Option("--severity")] = None,
    ) -> None:
        if ctx.invoked_subcommand is None:
            _render_limitations(ctx, get_client, get_scope, render, status, severity)

    @limitations_app.command("list")
    def list_limitations(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        severity: Annotated[str | None, typer.Option("--severity")] = None,
    ) -> None:
        _render_limitations(ctx, get_client, get_scope, render, status, severity)

    @limitations_app.command("seed")
    def seed_limitations(
        ctx: typer.Context,
        dry_run: Annotated[bool, typer.Option("--dry-run/--write")] = True,
    ) -> None:
        render(ctx, _client(get_client(ctx)).self_model.seed_limitations(get_scope(ctx), dry_run))

    @confidence_app.command("calibrate")
    def calibrate_confidence(
        ctx: typer.Context,
        source_type: Annotated[str, typer.Option("--source-type")] = "generic",
        source_id: Annotated[str | None, typer.Option("--source-id")] = None,
        require_grounding: Annotated[bool, typer.Option("--require-grounding")] = False,
    ) -> None:
        payload: JSONDict = {
            "source_type": source_type,
            "source_id": source_id,
            "require_grounding": require_grounding,
            "metadata": {"owner_scope": get_scope(ctx), "source": "aionctl"},
        }
        render(ctx, _client(get_client(ctx)).self_model.calibrate_confidence(payload))

    @assessment_app.command("run")
    def run_assessment(
        ctx: typer.Context,
        assessment_type: Annotated[str, typer.Option("--type")] = "full",
        dry_run: Annotated[bool, typer.Option("--dry-run/--controlled")] = True,
    ) -> None:
        payload: JSONDict = {
            "owner_scope": get_scope(ctx),
            "assessment_type": assessment_type,
            "dry_run": dry_run,
            "metadata": {"source": "aionctl"},
        }
        render(ctx, _client(get_client(ctx)).self_model.run_assessment(payload))

    @introspection_app.command("create")
    def create_introspection(
        ctx: typer.Context,
        snapshot_type: Annotated[str, typer.Option("--type")] = "manual",
    ) -> None:
        payload: JSONDict = {
            "owner_scope": get_scope(ctx),
            "snapshot_type": snapshot_type,
            "metadata": {"source": "aionctl"},
        }
        render(ctx, _client(get_client(ctx)).self_model.create_introspection(payload))

    @introspection_app.command("list")
    def list_introspection(
        ctx: typer.Context,
        snapshot_type: Annotated[str | None, typer.Option("--type")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 50,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).self_model.list_introspection(
                get_scope(ctx),
                snapshot_type=snapshot_type,
                limit=limit,
            ),
        )


def _client(value: object) -> AIONClient:
    return cast(AIONClient, value)


def _render_capabilities(
    ctx: typer.Context,
    get_client: Any,
    get_scope: Any,
    render: Any,
    status: str | None,
    capability_type: str | None,
) -> None:
    render(
        ctx,
        _client(get_client(ctx)).self_model.capabilities(
            get_scope(ctx),
            status=status,
            capability_type=capability_type,
        ),
    )


def _render_limitations(
    ctx: typer.Context,
    get_client: Any,
    get_scope: Any,
    render: Any,
    status: str | None,
    severity: str | None,
) -> None:
    render(
        ctx,
        _client(get_client(ctx)).self_model.list_limitations(
            get_scope(ctx),
            status=status,
            severity=severity,
        ),
    )


__all__ = ["install_self_model_commands"]
