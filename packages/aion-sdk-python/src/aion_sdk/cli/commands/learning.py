"""aionctl learning synthesis commands."""

from __future__ import annotations

from typing import Annotated, Any, cast

import typer

from aion_sdk.client import AIONClient
from aion_sdk.types import JSONDict

learning_app = typer.Typer(no_args_is_help=True, help="Learning synthesis commands.")
experience_app = typer.Typer(no_args_is_help=True, help="Experience ledger commands.")
patterns_app = typer.Typer(no_args_is_help=True, help="Learning pattern commands.")
lessons_app = typer.Typer(no_args_is_help=True, help="Lesson record commands.")
skill_app = typer.Typer(no_args_is_help=True, help="Skill suggestion commands.")
regression_app = typer.Typer(no_args_is_help=True, help="Regression suggestion commands.")


def install_learning_commands(
    app: typer.Typer,
    *,
    get_client: Any,
    get_scope: Any,
    render: Any,
) -> None:
    """Install learning commands."""

    app.add_typer(learning_app, name="learning")
    learning_app.add_typer(experience_app, name="experiences")
    learning_app.add_typer(patterns_app, name="patterns")
    learning_app.add_typer(lessons_app, name="lessons")
    learning_app.add_typer(skill_app, name="skill-suggestions")
    learning_app.add_typer(regression_app, name="regression-suggestions")

    @experience_app.command("create")
    def create_experience(
        ctx: typer.Context,
        source_type: Annotated[str, typer.Option("--source-type")],
        source_id: Annotated[str, typer.Option("--source-id")],
        title: Annotated[str, typer.Option("--title")],
        summary: Annotated[str, typer.Option("--summary")],
        experience_type: Annotated[str, typer.Option("--type")] = "signal",
        score: Annotated[float, typer.Option("--score")] = 0.5,
        confidence: Annotated[float, typer.Option("--confidence")] = 0.6,
    ) -> None:
        """Record a generic experience."""
        payload: JSONDict = {
            "source_type": source_type,
            "source_id": source_id,
            "experience_type": experience_type,
            "title": title,
            "summary": summary,
            "owner_scope": get_scope(ctx),
            "score": score,
            "confidence": confidence,
            "metadata": {"source": "aionctl"},
        }
        render(ctx, _client(get_client(ctx)).learning.create_experience(payload))

    @experience_app.command("get")
    def get_experience(
        ctx: typer.Context,
        experience_id: Annotated[str, typer.Option("--id")],
    ) -> None:
        """Get one experience."""
        render(
            ctx,
            _client(get_client(ctx)).learning.get_experience(
                experience_id,
                get_scope(ctx),
            ),
        )

    @experience_app.command("query")
    def query_experiences(
        ctx: typer.Context,
        text: Annotated[str | None, typer.Option("--query")] = None,
        experience_type: Annotated[str | None, typer.Option("--type")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 50,
    ) -> None:
        """Query experiences and synthesized learning records."""
        payload: JSONDict = {"scope": get_scope(ctx), "limit": limit}
        if text:
            payload["query"] = text
        if experience_type:
            payload["experience_types"] = [experience_type]
        render(ctx, _client(get_client(ctx)).learning.query(payload))

    @patterns_app.command("mine")
    def mine_patterns(
        ctx: typer.Context,
        min_frequency: Annotated[int, typer.Option("--min-frequency")] = 2,
        min_confidence: Annotated[float, typer.Option("--min-confidence")] = 0.6,
        dry_run: Annotated[bool, typer.Option("--dry-run/--write")] = True,
    ) -> None:
        """Mine deterministic learning patterns."""
        payload: JSONDict = {
            "owner_scope": get_scope(ctx),
            "min_frequency": min_frequency,
            "min_confidence": min_confidence,
            "dry_run": dry_run,
        }
        render(ctx, _client(get_client(ctx)).learning.mine_patterns(payload))

    @patterns_app.command("list")
    def list_patterns(
        ctx: typer.Context,
        pattern_type: Annotated[str | None, typer.Option("--type")] = None,
        status: Annotated[str | None, typer.Option("--status")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        """List learning patterns."""
        render(
            ctx,
            _client(get_client(ctx)).learning.list_patterns(
                scope=get_scope(ctx),
                pattern_type=pattern_type,
                status=status,
                limit=limit,
            ),
        )

    @lessons_app.command("list")
    def list_lessons(
        ctx: typer.Context,
        lesson_type: Annotated[str | None, typer.Option("--type")] = None,
        status: Annotated[str | None, typer.Option("--status")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        """List lessons."""
        render(
            ctx,
            _client(get_client(ctx)).learning.list_lessons(
                scope=get_scope(ctx),
                lesson_type=lesson_type,
                status=status,
                limit=limit,
            ),
        )

    @learning_app.command("synthesize")
    def synthesize(
        ctx: typer.Context,
        outcome_id: Annotated[list[str] | None, typer.Option("--outcome-id")] = None,
        experience_id: Annotated[list[str] | None, typer.Option("--experience-id")] = None,
        mode: Annotated[str, typer.Option("--mode")] = "dry_run",
        create_lessons: Annotated[bool, typer.Option("--lessons/--no-lessons")] = True,
    ) -> None:
        """Run deterministic learning synthesis."""
        payload: JSONDict = {
            "owner_scope": get_scope(ctx),
            "mode": mode,
            "outcome_ids": outcome_id or [],
            "experience_ids": experience_id or [],
            "create_lessons": create_lessons,
        }
        render(ctx, _client(get_client(ctx)).learning.synthesize(payload))

    @skill_app.command("list")
    def list_skill_suggestions(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        """List passive skill suggestions."""
        render(
            ctx,
            _client(get_client(ctx)).learning.list_skill_suggestions(
                scope=get_scope(ctx),
                status=status,
                limit=limit,
            ),
        )

    @skill_app.command("accept")
    def accept_skill_suggestion(
        ctx: typer.Context,
        suggestion_id: Annotated[str, typer.Option("--id")],
        reason: Annotated[str, typer.Option("--reason")],
    ) -> None:
        """Accept a skill suggestion without promotion."""
        render(
            ctx,
            _client(get_client(ctx)).learning.accept_skill_suggestion(
                suggestion_id,
                reason,
            ),
        )

    @skill_app.command("reject")
    def reject_skill_suggestion(
        ctx: typer.Context,
        suggestion_id: Annotated[str, typer.Option("--id")],
        reason: Annotated[str, typer.Option("--reason")],
    ) -> None:
        """Reject a skill suggestion."""
        render(
            ctx,
            _client(get_client(ctx)).learning.reject_skill_suggestion(
                suggestion_id,
                reason,
            ),
        )

    @skill_app.command("convert")
    def convert_skill_suggestion(
        ctx: typer.Context,
        suggestion_id: Annotated[str, typer.Option("--id")],
        reason: Annotated[str, typer.Option("--reason")],
        approval_present: Annotated[bool, typer.Option("--approved")] = False,
    ) -> None:
        """Convert a suggestion to a passive skill candidate reference."""
        render(
            ctx,
            _client(get_client(ctx)).learning.convert_skill_suggestion(
                suggestion_id,
                reason=reason,
                approval_present=approval_present,
            ),
        )

    @regression_app.command("list")
    def list_regression_suggestions(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        severity: Annotated[str | None, typer.Option("--severity")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        """List passive regression suggestions."""
        render(
            ctx,
            _client(get_client(ctx)).learning.list_regression_suggestions(
                scope=get_scope(ctx),
                status=status,
                severity=severity,
                limit=limit,
            ),
        )

    @regression_app.command("accept")
    def accept_regression_suggestion(
        ctx: typer.Context,
        suggestion_id: Annotated[str, typer.Option("--id")],
        reason: Annotated[str, typer.Option("--reason")],
    ) -> None:
        """Accept a regression suggestion without creating a case."""
        render(
            ctx,
            _client(get_client(ctx)).learning.accept_regression_suggestion(
                suggestion_id,
                reason,
            ),
        )

    @regression_app.command("reject")
    def reject_regression_suggestion(
        ctx: typer.Context,
        suggestion_id: Annotated[str, typer.Option("--id")],
        reason: Annotated[str, typer.Option("--reason")],
    ) -> None:
        """Reject a regression suggestion."""
        render(
            ctx,
            _client(get_client(ctx)).learning.reject_regression_suggestion(
                suggestion_id,
                reason,
            ),
        )


def _client(value: object) -> AIONClient:
    return cast(AIONClient, value)


__all__ = ["install_learning_commands"]
