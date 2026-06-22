"""aionctl explain commands."""

from __future__ import annotations

from typing import Annotated, Any, cast

import typer

from aion_sdk.client import AIONClient
from aion_sdk.types import JSONDict

explain_app = typer.Typer(no_args_is_help=True, help="Explanation Engine commands.")


def install_explanation_commands(
    app: typer.Typer,
    *,
    get_client: Any,
    get_scope: Any,
    render: Any,
) -> None:
    """Install explanation commands."""

    app.add_typer(explain_app, name="explain")

    @explain_app.command("target")
    def explain_target(
        ctx: typer.Context,
        target_type: Annotated[str, typer.Option("--target-type")],
        target_id: Annotated[str | None, typer.Option("--target-id")] = None,
        trace_id: Annotated[str | None, typer.Option("--trace-id")] = None,
        explanation_type: Annotated[str, typer.Option("--type")] = "generic",
    ) -> None:
        payload: JSONDict = {
            "trace_id": trace_id,
            "explanation_type": explanation_type,
            "target_type": target_type,
            "target_id": target_id,
            "owner_scope": get_scope(ctx),
            "metadata": {"source": "aionctl"},
        }
        render(ctx, _client(get_client(ctx)).explanations.explain(payload))

    @explain_app.command("why-not")
    def explain_why_not(
        ctx: typer.Context,
        target_type: Annotated[str, typer.Option("--target-type")],
        question: Annotated[str, typer.Option("--question")] = "Why did this not continue?",
        target_id: Annotated[str | None, typer.Option("--target-id")] = None,
        requested_action: Annotated[str | None, typer.Option("--requested-action")] = None,
        trace_id: Annotated[str | None, typer.Option("--trace-id")] = None,
    ) -> None:
        payload: JSONDict = {
            "trace_id": trace_id,
            "question": question,
            "target_type": target_type,
            "target_id": target_id,
            "requested_action": requested_action,
            "owner_scope": get_scope(ctx),
            "metadata": {"source": "aionctl"},
        }
        render(ctx, _client(get_client(ctx)).explanations.why_not(payload))

    @explain_app.command("trace")
    def explain_trace(
        ctx: typer.Context,
        trace_id: Annotated[str, typer.Option("--trace-id")],
        max_timeline_items: Annotated[int, typer.Option("--max-items")] = 100,
    ) -> None:
        payload: JSONDict = {
            "trace_id": trace_id,
            "owner_scope": get_scope(ctx),
            "max_timeline_items": max_timeline_items,
            "metadata": {"source": "aionctl"},
        }
        render(ctx, _client(get_client(ctx)).explanations.trace_narrative(trace_id, payload))

    @explain_app.command("verify")
    def verify(
        ctx: typer.Context,
        explanation_id: Annotated[str, typer.Option("--explanation-id")],
    ) -> None:
        render(ctx, _client(get_client(ctx)).explanations.verify(explanation_id))

    @explain_app.command("feedback")
    def feedback(
        ctx: typer.Context,
        explanation_id: Annotated[str | None, typer.Option("--explanation-id")] = None,
        trace_narrative_id: Annotated[str | None, typer.Option("--trace-narrative-id")] = None,
        why_not_id: Annotated[str | None, typer.Option("--why-not-id")] = None,
        feedback_type: Annotated[str, typer.Option("--type")] = "generic",
        rating: Annotated[int | None, typer.Option("--rating")] = None,
        comment: Annotated[str | None, typer.Option("--comment")] = None,
    ) -> None:
        payload: JSONDict = {
            "explanation_feedback_id": "feedback-cli",
            "explanation_id": explanation_id,
            "trace_narrative_id": trace_narrative_id,
            "why_not_id": why_not_id,
            "feedback_type": feedback_type,
            "rating": rating,
            "comment": comment,
            "metadata": {"owner_scope": get_scope(ctx), "source": "aionctl"},
        }
        render(ctx, _client(get_client(ctx)).explanations.feedback(payload))


def _client(value: object) -> AIONClient:
    return cast(AIONClient, value)


__all__ = ["install_explanation_commands"]
