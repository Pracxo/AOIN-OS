"""aionctl situation model commands."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Annotated, Any, cast

import typer

from aion_sdk.client import AIONClient
from aion_sdk.types import JSONDict

situations_app = typer.Typer(no_args_is_help=True, help="Situation model commands.")


def install_situation_commands(
    app: typer.Typer,
    *,
    get_client: Any,
    get_scope: Any,
    render: Any,
) -> None:
    """Install situation commands."""

    app.add_typer(situations_app, name="situations")

    @situations_app.command("create")
    def create(
        ctx: typer.Context,
        title: Annotated[str, typer.Option("--title")],
        summary: Annotated[str, typer.Option("--summary")],
        situation_type: Annotated[str, typer.Option("--type")] = "general",
    ) -> None:
        """Create one situation."""
        payload: JSONDict = {
            "title": title,
            "summary": summary,
            "situation_type": situation_type,
            "owner_scope": get_scope(ctx),
            "metadata": {"source": "aionctl"},
        }
        render(ctx, _client(get_client(ctx)).situations.create(payload))

    @situations_app.command("query")
    def query(
        ctx: typer.Context,
        text: Annotated[str | None, typer.Option("--text")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        """Query situations."""
        payload: JSONDict = {"scope": get_scope(ctx), "text": text, "limit": limit}
        render(ctx, _client(get_client(ctx)).situations.query(payload))

    @situations_app.command("project")
    def project(
        ctx: typer.Context,
        mode: Annotated[str, typer.Option("--mode")] = "dry_run",
    ) -> None:
        """Run a situation projection. Defaults to dry_run."""
        payload: JSONDict = {"mode": mode, "owner_scope": get_scope(ctx), "source_refs": []}
        render(ctx, _client(get_client(ctx)).situations.project(payload))

    @situations_app.command("atoms")
    def atoms(
        ctx: typer.Context,
        situation_id: Annotated[str | None, typer.Option("--situation-id")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        """List state atoms."""
        render(
            ctx,
            _client(get_client(ctx)).situations.list_atoms(
                get_scope(ctx),
                situation_id=situation_id,
                limit=limit,
            ),
        )

    @situations_app.command("transitions")
    def transitions(
        ctx: typer.Context,
        trace_id: Annotated[str | None, typer.Option("--trace-id")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        """List state transitions."""
        render(
            ctx,
            _client(get_client(ctx)).situations.list_transitions(
                trace_id=trace_id,
                limit=limit,
            ),
        )

    @situations_app.command("temporal-window")
    def temporal_window(
        ctx: typer.Context,
        window_type: Annotated[str, typer.Option("--type")] = "recent",
    ) -> None:
        """Create a temporal state window for the last hour."""
        end_at = datetime.now(UTC)
        start_at = end_at - timedelta(hours=1)
        payload: JSONDict = {
            "window_type": window_type,
            "owner_scope": get_scope(ctx),
            "start_at": start_at.isoformat(),
            "end_at": end_at.isoformat(),
            "metadata": {"source": "aionctl"},
        }
        render(ctx, _client(get_client(ctx)).situations.create_temporal_window(payload))

    @situations_app.command("continuity")
    def continuity(
        ctx: typer.Context,
        ref: Annotated[list[str] | None, typer.Option("--ref")] = None,
    ) -> None:
        """Record context continuity refs."""
        payload: JSONDict = {
            "owner_scope": get_scope(ctx),
            "refs": ref or [],
            "continuity_type": "generic",
            "reason": "Continuity recorded from aionctl.",
        }
        render(ctx, _client(get_client(ctx)).situations.record_continuity(payload))


def _client(value: object) -> AIONClient:
    return cast(AIONClient, value)
