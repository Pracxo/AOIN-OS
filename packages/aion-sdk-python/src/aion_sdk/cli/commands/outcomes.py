"""aionctl outcome ledger commands."""

from __future__ import annotations

from typing import Annotated, Any, cast

import typer

from aion_sdk.client import AIONClient
from aion_sdk.types import JSONDict

outcomes_app = typer.Typer(no_args_is_help=True, help="Outcome ledger commands.")
expected_app = typer.Typer(no_args_is_help=True, help="Expected effect commands.")
observed_app = typer.Typer(no_args_is_help=True, help="Observed effect commands.")
feedback_app = typer.Typer(no_args_is_help=True, help="Outcome feedback commands.")


def install_outcome_commands(
    app: typer.Typer,
    *,
    get_client: Any,
    get_scope: Any,
    render: Any,
) -> None:
    """Install outcome commands."""

    app.add_typer(outcomes_app, name="outcomes")
    outcomes_app.add_typer(expected_app, name="expected")
    outcomes_app.add_typer(observed_app, name="observed")
    outcomes_app.add_typer(feedback_app, name="feedback")

    @outcomes_app.command("create")
    def create(
        ctx: typer.Context,
        source_type: Annotated[str, typer.Option("--source-type")],
        source_id: Annotated[str, typer.Option("--source-id")],
        title: Annotated[str, typer.Option("--title")],
        summary: Annotated[str, typer.Option("--summary")],
        outcome_type: Annotated[str, typer.Option("--type")] = "generic",
    ) -> None:
        """Create an outcome record."""
        payload: JSONDict = {
            "source_type": source_type,
            "source_id": source_id,
            "outcome_type": outcome_type,
            "title": title,
            "summary": summary,
            "owner_scope": get_scope(ctx),
            "metadata": {"source": "aionctl"},
        }
        render(ctx, _client(get_client(ctx)).outcomes.create(payload))

    @outcomes_app.command("query")
    def query(
        ctx: typer.Context,
        text: Annotated[str | None, typer.Option("--query")] = None,
        status: Annotated[str | None, typer.Option("--status")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 50,
    ) -> None:
        """Query outcomes."""
        payload: JSONDict = {"scope": get_scope(ctx), "limit": limit}
        if text:
            payload["query"] = text
        if status:
            payload["statuses"] = [status]
        render(ctx, _client(get_client(ctx)).outcomes.query(payload))

    @expected_app.command("add")
    def add_expected(
        ctx: typer.Context,
        source_type: Annotated[str, typer.Option("--source-type")],
        source_id: Annotated[str, typer.Option("--source-id")],
        predicate: Annotated[str, typer.Option("--predicate")],
        effect_type: Annotated[str, typer.Option("--effect-type")] = "generic",
    ) -> None:
        """Add an expected effect."""
        payload: JSONDict = {
            "source_type": source_type,
            "source_id": source_id,
            "effect_type": effect_type,
            "predicate": predicate,
            "owner_scope": get_scope(ctx),
            "success_criteria": {"exists": True},
            "metadata": {"source": "aionctl"},
        }
        render(ctx, _client(get_client(ctx)).outcomes.create_expected_effect(payload))

    @observed_app.command("add")
    def add_observed(
        ctx: typer.Context,
        source_type: Annotated[str, typer.Option("--source-type")],
        source_id: Annotated[str, typer.Option("--source-id")],
        predicate: Annotated[str, typer.Option("--predicate")],
        observation_source_type: Annotated[
            str,
            typer.Option("--observation-source-type"),
        ] = "generic",
        effect_type: Annotated[str, typer.Option("--effect-type")] = "generic",
    ) -> None:
        """Add an observed effect."""
        payload: JSONDict = {
            "source_type": source_type,
            "source_id": source_id,
            "effect_type": effect_type,
            "predicate": predicate,
            "observation_source_type": observation_source_type,
            "observation_source_id": source_id,
            "owner_scope": get_scope(ctx),
            "observed_value": {"status": "observed"},
            "metadata": {"source": "aionctl"},
        }
        render(ctx, _client(get_client(ctx)).outcomes.create_observed_effect(payload))

    @outcomes_app.command("verify")
    def verify(
        ctx: typer.Context,
        source_id: Annotated[str | None, typer.Option("--source-id")] = None,
        outcome_id: Annotated[str | None, typer.Option("--outcome-id")] = None,
        source_type: Annotated[str | None, typer.Option("--source-type")] = None,
    ) -> None:
        """Run deterministic dry-run effect verification."""
        payload: JSONDict = {
            "owner_scope": get_scope(ctx),
            "mode": "dry_run",
            "collect_observed_effects": True,
        }
        if outcome_id:
            payload["outcome_id"] = outcome_id
        if source_type:
            payload["source_type"] = source_type
        if source_id:
            payload["source_id"] = source_id
        render(ctx, _client(get_client(ctx)).outcomes.verify(payload))

    @feedback_app.command("list")
    def list_feedback(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        severity: Annotated[str | None, typer.Option("--severity")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        """List outcome feedback."""
        render(
            ctx,
            _client(get_client(ctx)).outcomes.list_feedback(
                status=status,
                severity=severity,
                limit=limit,
            ),
        )

    @feedback_app.command("resolve")
    def resolve_feedback(
        ctx: typer.Context,
        feedback_id: Annotated[str, typer.Option("--feedback-id")],
        reason: Annotated[str, typer.Option("--reason")],
    ) -> None:
        """Resolve outcome feedback."""
        render(ctx, _client(get_client(ctx)).outcomes.resolve_feedback(feedback_id, reason))

    @outcomes_app.command("learning-bridge")
    def learning_bridge(
        ctx: typer.Context,
        outcome_id: Annotated[str, typer.Option("--outcome-id")],
        dry_run: Annotated[bool, typer.Option("--dry-run/--write")] = True,
    ) -> None:
        """Bridge outcome feedback to learning. Defaults to dry-run."""
        render(ctx, _client(get_client(ctx)).outcomes.learning_bridge(outcome_id, dry_run))


def _client(value: object) -> AIONClient:
    return cast(AIONClient, value)


__all__ = ["install_outcome_commands"]
