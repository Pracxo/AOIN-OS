"""aionctl operator commands."""

from __future__ import annotations

from typing import Annotated, Any, cast

import typer

from aion_sdk.client import AIONClient
from aion_sdk.types import JSONDict

operator_app = typer.Typer(no_args_is_help=True, help="Operator Control Tower commands.")


def install_operator_commands(
    app: typer.Typer,
    *,
    get_client: Any,
    get_scope: Any,
    render: Any,
) -> None:
    """Install operator commands onto the root CLI."""

    app.add_typer(operator_app, name="operator")

    @operator_app.command("overview")
    def overview(ctx: typer.Context) -> None:
        """Show local operator overview."""

        payload: JSONDict = {"owner_scope": get_scope(ctx), "metadata": {"source": "aionctl"}}
        render(ctx, _client(get_client(ctx)).operator.overview(payload))

    @operator_app.command("readiness")
    def readiness(ctx: typer.Context) -> None:
        """Show local operator readiness."""

        render(ctx, _client(get_client(ctx)).operator.readiness(get_scope(ctx)))

    @operator_app.command("cards")
    def cards(ctx: typer.Context) -> None:
        """Show operator status cards."""

        render(ctx, _client(get_client(ctx)).operator.status_cards(get_scope(ctx)))

    @operator_app.command("queues")
    def queues(ctx: typer.Context) -> None:
        """Show operator queue summaries."""

        render(ctx, _client(get_client(ctx)).operator.queues(get_scope(ctx)))

    @operator_app.command("actions")
    def actions(
        ctx: typer.Context,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        """Show action-center recommendations."""

        render(ctx, _client(get_client(ctx)).operator.actions(get_scope(ctx), limit))

    @operator_app.command("acknowledge")
    def acknowledge(
        ctx: typer.Context,
        source_type: Annotated[str, typer.Option("--source-type")],
        source_id: Annotated[str, typer.Option("--source-id")],
        reason: Annotated[str, typer.Option("--reason")],
        action_item_id: Annotated[str | None, typer.Option("--action-item-id")] = None,
    ) -> None:
        """Record acknowledgement only; does not resolve the source issue."""

        payload: JSONDict = {
            "source_type": source_type,
            "source_id": source_id,
            "reason": reason,
            "metadata": {"source": "aionctl"},
        }
        if action_item_id is not None:
            payload["action_item_id"] = action_item_id
        render(ctx, _client(get_client(ctx)).operator.acknowledge(payload))

    @operator_app.command("snapshot")
    def snapshot(
        ctx: typer.Context,
        snapshot_type: Annotated[str, typer.Option("--type")] = "manual",
    ) -> None:
        """Create a local operator snapshot."""

        payload: JSONDict = {
            "snapshot_type": snapshot_type,
            "owner_scope": get_scope(ctx),
            "metadata": {"source": "aionctl"},
            "generated_by": "aionctl",
        }
        render(ctx, _client(get_client(ctx)).operator.create_snapshot(payload))

    @operator_app.command("runbooks")
    def runbooks(
        ctx: typer.Context,
        category: Annotated[str | None, typer.Option("--category")] = None,
    ) -> None:
        """List local operator runbook links."""

        render(ctx, _client(get_client(ctx)).operator.runbooks(category))


def _client(value: object) -> AIONClient:
    return cast(AIONClient, value)
