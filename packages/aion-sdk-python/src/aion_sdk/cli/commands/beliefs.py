"""aionctl belief commands."""

from __future__ import annotations

from typing import Annotated, Any, cast

import typer

from aion_sdk.client import AIONClient
from aion_sdk.types import JSONDict

beliefs_app = typer.Typer(no_args_is_help=True, help="Belief State Manager commands.")
truth_app = typer.Typer(no_args_is_help=True, help="Truth maintenance commands.")


def install_belief_commands(
    app: typer.Typer,
    *,
    get_client: Any,
    get_scope: Any,
    render: Any,
) -> None:
    """Install belief commands."""

    app.add_typer(beliefs_app, name="beliefs")
    beliefs_app.add_typer(truth_app, name="truth-maintenance")

    @beliefs_app.command("create")
    def create(
        ctx: typer.Context,
        claim: Annotated[str, typer.Option("--claim")],
        source_type: Annotated[str, typer.Option("--source-type")] = "generic",
        source_id: Annotated[str | None, typer.Option("--source-id")] = None,
        confidence: Annotated[float, typer.Option("--confidence")] = 0.5,
    ) -> None:
        """Create one belief claim."""
        payload: JSONDict = {
            "claim_text": claim,
            "claim_type": "generic",
            "source_type": source_type,
            "source_id": source_id,
            "owner_scope": get_scope(ctx),
            "confidence": confidence,
            "metadata": {"source": "aionctl"},
        }
        render(ctx, _client(get_client(ctx)).beliefs.create_claim(payload))

    @beliefs_app.command("query")
    def query(
        ctx: typer.Context,
        query_text: Annotated[str | None, typer.Option("--query")] = None,
        status: Annotated[list[str] | None, typer.Option("--status")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 50,
    ) -> None:
        """Query belief claims."""
        payload: JSONDict = {
            "query": query_text,
            "scope": get_scope(ctx),
            "statuses": status or [],
            "limit": limit,
        }
        render(ctx, _client(get_client(ctx)).beliefs.query(payload))

    @beliefs_app.command("extract")
    def extract(
        ctx: typer.Context,
        text: Annotated[str, typer.Option("--text")],
        source_type: Annotated[str, typer.Option("--source-type")] = "generic",
        source_id: Annotated[str, typer.Option("--source-id")] = "cli-input",
    ) -> None:
        """Extract claims deterministically from text."""
        payload: JSONDict = {
            "source_type": source_type,
            "source_id": source_id,
            "text": text,
            "owner_scope": get_scope(ctx),
            "metadata": {"source": "aionctl"},
        }
        render(ctx, _client(get_client(ctx)).beliefs.extract(payload))

    @beliefs_app.command("contradictions")
    def contradictions(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = "open",
        severity: Annotated[str | None, typer.Option("--severity")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        """List belief contradictions."""
        render(
            ctx,
            _client(get_client(ctx)).beliefs.list_contradictions(
                get_scope(ctx),
                status=status,
                severity=severity,
                limit=limit,
            ),
        )

    @truth_app.command("run")
    def truth_run(
        ctx: typer.Context,
        dry_run: Annotated[bool, typer.Option("--dry-run/--write")] = True,
    ) -> None:
        """Run truth maintenance; dry-run is the default."""
        payload: JSONDict = {
            "owner_scope": get_scope(ctx),
            "dry_run": dry_run,
            "metadata": {"source": "aionctl"},
        }
        render(ctx, _client(get_client(ctx)).beliefs.run_truth_maintenance(payload))

    @truth_app.command("get")
    def truth_get(
        ctx: typer.Context,
        truth_run_id: Annotated[str, typer.Option("--truth-run-id")],
    ) -> None:
        """Get one truth maintenance run."""
        render(ctx, _client(get_client(ctx)).beliefs.get_truth_maintenance(truth_run_id))


def _client(value: object) -> AIONClient:
    return cast(AIONClient, value)
