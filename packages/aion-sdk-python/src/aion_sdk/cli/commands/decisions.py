"""aionctl decision intelligence commands."""

from __future__ import annotations

from typing import Annotated, Any, cast

import typer

from aion_sdk.client import AIONClient
from aion_sdk.types import JSONDict

decisions_app = typer.Typer(no_args_is_help=True, help="Decision intelligence commands.")
frame_app = typer.Typer(no_args_is_help=True, help="Decision frame commands.")
option_app = typer.Typer(no_args_is_help=True, help="Decision option commands.")
counterfactual_app = typer.Typer(no_args_is_help=True, help="Counterfactual commands.")
journal_app = typer.Typer(no_args_is_help=True, help="Decision journal commands.")


def install_decision_commands(
    app: typer.Typer,
    *,
    get_client: Any,
    get_scope: Any,
    render: Any,
) -> None:
    """Install decision commands."""

    app.add_typer(decisions_app, name="decisions")
    decisions_app.add_typer(frame_app, name="frame")
    decisions_app.add_typer(option_app, name="option")
    decisions_app.add_typer(counterfactual_app, name="counterfactual")
    decisions_app.add_typer(journal_app, name="journal")

    @frame_app.command("create")
    def create_frame(
        ctx: typer.Context,
        title: Annotated[str, typer.Option("--title")],
        question: Annotated[str, typer.Option("--question")],
        frame_type: Annotated[str, typer.Option("--type")] = "generic",
    ) -> None:
        """Create a decision frame."""
        payload: JSONDict = {
            "title": title,
            "question": question,
            "frame_type": frame_type,
            "owner_scope": get_scope(ctx),
            "metadata": {"source": "aionctl"},
        }
        render(ctx, _client(get_client(ctx)).decisions.create_frame(payload))

    @decisions_app.command("frames")
    def frames(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 50,
    ) -> None:
        """List decision frames."""
        render(
            ctx,
            _client(get_client(ctx)).decisions.list_frames(
                get_scope(ctx),
                status=status,
                limit=limit,
            ),
        )

    @option_app.command("add")
    def add_option(
        ctx: typer.Context,
        frame_id: Annotated[str, typer.Option("--frame-id")],
        title: Annotated[str, typer.Option("--title")],
        description: Annotated[str, typer.Option("--description")],
        option_type: Annotated[str, typer.Option("--type")] = "generic",
        risk_level: Annotated[str, typer.Option("--risk")] = "medium",
    ) -> None:
        """Add an option to a decision frame."""
        payload: JSONDict = {
            "decision_frame_id": frame_id,
            "title": title,
            "description": description,
            "option_type": option_type,
            "risk_level": risk_level,
            "metadata": {"source": "aionctl"},
        }
        render(ctx, _client(get_client(ctx)).decisions.create_option(payload))

    @decisions_app.command("evaluate")
    def evaluate(
        ctx: typer.Context,
        frame_id: Annotated[str, typer.Option("--frame-id")],
        dry_run: Annotated[bool, typer.Option("--dry-run/--controlled")] = True,
    ) -> None:
        """Evaluate options. Defaults to dry_run."""
        payload: JSONDict = {"decision_frame_id": frame_id, "dry_run": dry_run}
        render(ctx, _client(get_client(ctx)).decisions.evaluate(payload))

    @decisions_app.command("recommend")
    def recommend(
        ctx: typer.Context,
        frame_id: Annotated[str, typer.Option("--frame-id")],
        dry_run: Annotated[bool, typer.Option("--dry-run/--controlled")] = True,
    ) -> None:
        """Create a recommendation without executing it."""
        render(
            ctx,
            _client(get_client(ctx)).decisions.recommend(frame_id, {"dry_run": dry_run}),
        )

    @counterfactual_app.command("run")
    def run_counterfactual(
        ctx: typer.Context,
        frame_id: Annotated[str, typer.Option("--frame-id")],
        option_id: Annotated[str | None, typer.Option("--option-id")] = None,
    ) -> None:
        """Run a dry-run counterfactual projection."""
        payload: JSONDict = {
            "decision_frame_id": frame_id,
            "decision_option_id": option_id,
            "mode": "dry_run",
            "owner_scope": get_scope(ctx),
            "metadata": {"source": "aionctl"},
        }
        render(ctx, _client(get_client(ctx)).decisions.run_counterfactual(payload))

    @journal_app.command("record")
    def record(
        ctx: typer.Context,
        frame_id: Annotated[str, typer.Option("--frame-id")],
        rationale: Annotated[str, typer.Option("--rationale")],
        option_id: Annotated[str | None, typer.Option("--option-id")] = None,
    ) -> None:
        """Record a decision without execution."""
        payload: JSONDict = {
            "decision_frame_id": frame_id,
            "selected_option_id": option_id,
            "rationale": rationale,
            "metadata": {"source": "aionctl", "no_execution": True},
        }
        render(ctx, _client(get_client(ctx)).decisions.record_decision(payload))

    @journal_app.command("list")
    def list_records(
        ctx: typer.Context,
        frame_id: Annotated[str | None, typer.Option("--frame-id")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 50,
    ) -> None:
        """List decision journal records."""
        render(
            ctx,
            _client(get_client(ctx)).decisions.list_decision_records(
                get_scope(ctx),
                decision_frame_id=frame_id,
                limit=limit,
            ),
        )


def _client(value: object) -> AIONClient:
    return cast(AIONClient, value)
