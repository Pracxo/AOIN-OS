"""aionctl dialogue and response commands."""

from __future__ import annotations

from typing import Annotated, Any, cast

import typer

from aion_sdk.client import AIONClient
from aion_sdk.types import JSONDict

dialogue_app = typer.Typer(no_args_is_help=True, help="Dialogue backend commands.")
responses_app = typer.Typer(no_args_is_help=True, help="Response draft commands.")


def install_dialogue_commands(
    app: typer.Typer,
    *,
    get_client: Any,
    get_scope: Any,
    render: Any,
) -> None:
    """Install dialogue and response commands."""

    app.add_typer(dialogue_app, name="dialogue")
    app.add_typer(responses_app, name="responses")

    @dialogue_app.command("start")
    def start(
        ctx: typer.Context,
        title: Annotated[str, typer.Option("--title")] = "Dialogue Session",
        session_type: Annotated[str, typer.Option("--type")] = "general",
    ) -> None:
        """Create a dialogue session."""

        payload: JSONDict = {
            "title": title,
            "session_type": session_type,
            "owner_scope": get_scope(ctx),
            "metadata": {"source": "aionctl"},
        }
        render(ctx, _client(get_client(ctx)).dialogue.create_session(payload))

    @dialogue_app.command("send")
    def send(
        ctx: typer.Context,
        message: Annotated[str, typer.Option("--message")],
        dialogue_session_id: Annotated[str | None, typer.Option("--session-id")] = None,
        mode: Annotated[str, typer.Option("--mode")] = "assist",
        require_grounding: Annotated[bool, typer.Option("--require-grounding")] = False,
        remember: Annotated[bool, typer.Option("--remember")] = False,
    ) -> None:
        """Send one dialogue turn through the backend dialogue API."""

        payload: JSONDict = {
            "dialogue_session_id": dialogue_session_id,
            "message": message,
            "owner_scope": get_scope(ctx),
            "create_session": dialogue_session_id is None,
            "use_brain_loop": True,
            "require_grounding": require_grounding,
            "mode": mode,
            "metadata": {"source": "aionctl", "remember": remember},
        }
        render(ctx, _client(get_client(ctx)).dialogue.turn(payload))

    @dialogue_app.command("messages")
    def messages(
        ctx: typer.Context,
        dialogue_session_id: Annotated[str, typer.Option("--session-id")],
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        """List messages for one dialogue session."""

        render(
            ctx,
            _client(get_client(ctx)).dialogue.list_messages(
                dialogue_session_id,
                get_scope(ctx),
                limit,
            ),
        )

    @dialogue_app.command("sessions")
    def sessions(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        session_type: Annotated[str | None, typer.Option("--type")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 50,
    ) -> None:
        """List dialogue sessions."""

        render(
            ctx,
            _client(get_client(ctx)).dialogue.list_sessions(
                get_scope(ctx),
                status=status,
                session_type=session_type,
                limit=limit,
            ),
        )

    @dialogue_app.command("clarifications")
    def clarifications(
        ctx: typer.Context,
        dialogue_session_id: Annotated[str | None, typer.Option("--session-id")] = None,
    ) -> None:
        """List pending dialogue clarifications."""

        render(
            ctx,
            _client(get_client(ctx)).dialogue.pending_clarifications(
                get_scope(ctx),
                dialogue_session_id,
            ),
        )

    @dialogue_app.command("answer")
    def answer(
        ctx: typer.Context,
        clarification_id: Annotated[str, typer.Option("--clarification-id")],
        answer_text: Annotated[str, typer.Option("--answer")],
    ) -> None:
        """Answer a clarification request."""

        render(
            ctx,
            _client(get_client(ctx)).dialogue.answer_clarification(
                clarification_id,
                answer_text,
            ),
        )

    @responses_app.command("get")
    def get_response(
        ctx: typer.Context,
        response_id: Annotated[str, typer.Option("--response-id")],
    ) -> None:
        """Get a response draft."""

        render(ctx, _client(get_client(ctx)).responses.get(response_id))

    @responses_app.command("verify")
    def verify_response(
        ctx: typer.Context,
        response_id: Annotated[str, typer.Option("--response-id")],
    ) -> None:
        """Verify a response draft."""

        render(ctx, _client(get_client(ctx)).responses.verify(response_id))


def _client(value: object) -> AIONClient:
    return cast(AIONClient, value)
