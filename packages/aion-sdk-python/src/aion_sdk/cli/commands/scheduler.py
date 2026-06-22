"""aionctl temporal scheduler commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Any, cast

import typer

from aion_sdk.client import AIONClient
from aion_sdk.types import JSONDict

scheduler_app = typer.Typer(no_args_is_help=True, help="Local scheduler commands.")
schedules_app = typer.Typer(no_args_is_help=True, help="Schedule commands.")
reminders_app = typer.Typer(no_args_is_help=True, help="Reminder commands.")


def install_scheduler_commands(
    app: typer.Typer,
    *,
    get_client: Any,
    get_scope: Any,
    render: Any,
) -> None:
    """Install local scheduler commands."""

    app.add_typer(scheduler_app, name="scheduler")
    scheduler_app.add_typer(schedules_app, name="schedules")
    scheduler_app.add_typer(reminders_app, name="reminders")

    @schedules_app.command("create")
    def create_schedule(
        ctx: typer.Context,
        payload_file: Annotated[Path, typer.Option("--payload-file")],
    ) -> None:
        payload = _load_payload(payload_file)
        payload.setdefault("owner_scope", get_scope(ctx))
        render(ctx, _client(get_client(ctx)).scheduler.create_schedule(payload))

    @schedules_app.command("list")
    def list_schedules(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        schedule_type: Annotated[str | None, typer.Option("--schedule-type")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).scheduler.list_schedules(
                get_scope(ctx),
                status=status,
                schedule_type=schedule_type,
                limit=limit,
            ),
        )

    @schedules_app.command("pause")
    def pause_schedule(
        ctx: typer.Context,
        schedule_id: Annotated[str, typer.Option("--schedule-id")],
    ) -> None:
        render(ctx, _client(get_client(ctx)).scheduler.pause_schedule(schedule_id, get_scope(ctx)))

    @schedules_app.command("resume")
    def resume_schedule(
        ctx: typer.Context,
        schedule_id: Annotated[str, typer.Option("--schedule-id")],
    ) -> None:
        render(ctx, _client(get_client(ctx)).scheduler.resume_schedule(schedule_id, get_scope(ctx)))

    @scheduler_app.command("due-items")
    def due_items(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        schedule_id: Annotated[str | None, typer.Option("--schedule-id")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).scheduler.list_due_items(
                get_scope(ctx),
                status=status,
                schedule_id=schedule_id,
                limit=limit,
            ),
        )

    @reminders_app.command("create")
    def create_reminder(
        ctx: typer.Context,
        payload_file: Annotated[Path, typer.Option("--payload-file")],
    ) -> None:
        payload = _load_payload(payload_file)
        payload.setdefault("owner_scope", get_scope(ctx))
        render(ctx, _client(get_client(ctx)).scheduler.create_reminder(payload))

    @reminders_app.command("list")
    def list_reminders(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).scheduler.list_reminders(
                get_scope(ctx),
                status=status,
                limit=limit,
            ),
        )

    @reminders_app.command("acknowledge")
    def acknowledge_reminder(
        ctx: typer.Context,
        reminder_id: Annotated[str, typer.Option("--reminder-id")],
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).scheduler.acknowledge_reminder(reminder_id, get_scope(ctx)),
        )

    @scheduler_app.command("tick")
    def tick(
        ctx: typer.Context,
        payload_file: Annotated[Path | None, typer.Option("--payload-file")] = None,
        mode: Annotated[str, typer.Option("--mode")] = "dry_run",
        dry_run: Annotated[bool, typer.Option("--dry-run")] = False,
    ) -> None:
        payload = _load_payload(payload_file)
        payload.setdefault("scope", get_scope(ctx))
        payload.setdefault("mode", "dry_run" if dry_run else mode)
        render(ctx, _client(get_client(ctx)).scheduler.run_tick(payload))

    @scheduler_app.command("report")
    def report(ctx: typer.Context) -> None:
        render(ctx, _client(get_client(ctx)).scheduler.create_report(get_scope(ctx)))


def _load_payload(path: Path | None) -> JSONDict:
    if path is None:
        return {}
    return cast(JSONDict, json.loads(path.read_text()))


def _client(client: object) -> AIONClient:
    return cast(AIONClient, client)
