"""aionctl instruction and preference commands."""

from __future__ import annotations

import json
from typing import Annotated, Any, cast

import typer

from aion_sdk.client import AIONClient
from aion_sdk.types import JSONDict

instructions_app = typer.Typer(no_args_is_help=True, help="Instruction hierarchy commands.")
preferences_app = typer.Typer(no_args_is_help=True, help="Preference ledger commands.")
style_profiles_app = typer.Typer(no_args_is_help=True, help="Style profile commands.")


def install_instruction_commands(
    app: typer.Typer,
    *,
    get_client: Any,
    get_scope: Any,
    render: Any,
) -> None:
    """Install instruction, preference, and style profile commands."""

    app.add_typer(instructions_app, name="instructions")
    app.add_typer(preferences_app, name="preferences")
    app.add_typer(style_profiles_app, name="style-profiles")

    @instructions_app.command("create")
    def create_instruction(
        ctx: typer.Context,
        text: Annotated[str, typer.Option("--text")],
        instruction_type: Annotated[str, typer.Option("--type")] = "generic",
        source_type: Annotated[str, typer.Option("--source-type")] = "user",
        scope_type: Annotated[str, typer.Option("--scope-type")] = "actor",
        priority: Annotated[int, typer.Option("--priority")] = 500,
    ) -> None:
        payload: JSONDict = {
            "instruction_text": text,
            "instruction_type": instruction_type,
            "source_type": source_type,
            "scope_type": scope_type,
            "owner_scope": get_scope(ctx),
            "priority": priority,
            "metadata": {"source": "aionctl"},
        }
        render(ctx, _client(get_client(ctx)).instructions.create_instruction(payload))

    @instructions_app.command("list")
    def list_instructions(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        instruction_type: Annotated[str | None, typer.Option("--type")] = None,
        scope_type: Annotated[str | None, typer.Option("--scope-type")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).instructions.list_instructions(
                get_scope(ctx),
                status=status,
                instruction_type=instruction_type,
                scope_type=scope_type,
                limit=limit,
            ),
        )

    @instructions_app.command("resolve")
    def resolve_instructions(
        ctx: typer.Context,
        request_text: Annotated[str | None, typer.Option("--request-text")] = None,
    ) -> None:
        payload: JSONDict = {
            "owner_scope": get_scope(ctx),
            "request_text": request_text,
            "metadata": {"source": "aionctl"},
        }
        render(ctx, _client(get_client(ctx)).instructions.resolve(payload))

    @instructions_app.command("conflicts")
    def list_conflicts(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        severity: Annotated[str | None, typer.Option("--severity")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).instructions.list_conflicts(
                get_scope(ctx),
                status=status,
                severity=severity,
                limit=limit,
            ),
        )

    @preferences_app.command("create")
    def create_preference(
        ctx: typer.Context,
        key: Annotated[str, typer.Option("--key")],
        value: Annotated[str, typer.Option("--value")],
        preference_type: Annotated[str, typer.Option("--type")] = "generic",
        status: Annotated[str, typer.Option("--status")] = "candidate",
        confidence: Annotated[float, typer.Option("--confidence")] = 0.5,
    ) -> None:
        payload: JSONDict = {
            "preference_key": key,
            "preference_type": preference_type,
            "preference_value": _json_value(value),
            "status": status,
            "confidence": confidence,
            "owner_scope": get_scope(ctx),
            "metadata": {"source": "aionctl"},
        }
        render(ctx, _client(get_client(ctx)).instructions.create_preference(payload))

    @preferences_app.command("list")
    def list_preferences(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        preference_type: Annotated[str | None, typer.Option("--type")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).instructions.list_preferences(
                get_scope(ctx),
                status=status,
                preference_type=preference_type,
                limit=limit,
            ),
        )

    @preferences_app.command("confirm")
    def confirm_preference(
        ctx: typer.Context,
        preference_id: Annotated[str, typer.Option("--id")],
        reason: Annotated[str, typer.Option("--reason")],
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).instructions.confirm_preference(preference_id, reason),
        )

    @preferences_app.command("candidates")
    def list_candidates(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        preference_type: Annotated[str | None, typer.Option("--type")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).instructions.list_candidates(
                get_scope(ctx),
                status=status,
                preference_type=preference_type,
                limit=limit,
            ),
        )

    @style_profiles_app.command("create")
    def create_style_profile(
        ctx: typer.Context,
        name: Annotated[str, typer.Option("--name")],
        description: Annotated[str, typer.Option("--description")] = "AION style profile",
    ) -> None:
        payload: JSONDict = {
            "name": name,
            "description": description,
            "owner_scope": get_scope(ctx),
            "style_rules": {"style": "generic"},
            "metadata": {"source": "aionctl"},
        }
        render(ctx, _client(get_client(ctx)).instructions.create_style_profile(payload))

    @style_profiles_app.command("list")
    def list_style_profiles(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).instructions.list_style_profiles(
                get_scope(ctx),
                status=status,
                limit=limit,
            ),
        )

    @style_profiles_app.command("effective")
    def effective_style_profile(ctx: typer.Context) -> None:
        render(ctx, _client(get_client(ctx)).instructions.effective_style(get_scope(ctx)))


def _json_value(value: str) -> JSONDict:
    try:
        loaded = json.loads(value)
    except json.JSONDecodeError:
        return {"value": value}
    return loaded if isinstance(loaded, dict) else {"value": loaded}


def _client(value: object) -> AIONClient:
    return cast(AIONClient, value)


__all__ = ["install_instruction_commands"]
