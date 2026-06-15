"""aionctl backup and restore commands."""

from __future__ import annotations

from typing import Annotated, Any, cast

import typer

from aion_sdk.client import AIONClient
from aion_sdk.types import JSONDict

backups_app = typer.Typer(no_args_is_help=True, help="Local backup commands.")
restore_app = typer.Typer(no_args_is_help=True, help="Restore preview commands.")


def install_backup_commands(
    app: typer.Typer,
    *,
    get_client: Any,
    get_scope: Any,
    render: Any,
) -> None:
    """Install backup and restore commands onto the root CLI."""

    app.add_typer(backups_app, name="backups")
    app.add_typer(restore_app, name="restore")

    @backups_app.command("export")
    def export_backup(
        ctx: typer.Context,
        resource_type: Annotated[
            list[str] | None,
            typer.Option("--resource-type", help="Resource type. Repeatable."),
        ] = None,
        output_dir: Annotated[str, typer.Option("--output-dir")] = "artifacts/backups",
        redaction_mode: Annotated[str, typer.Option("--redaction-mode")] = "redact_sensitive",
        write: Annotated[
            bool,
            typer.Option("--write", help="Write files instead of dry-run."),
        ] = False,
    ) -> None:
        """Create a local backup job."""

        payload: JSONDict = {
            "owner_scope": get_scope(ctx),
            "resource_types": resource_type or ["events", "memory", "traces"],
            "output_dir": output_dir,
            "redaction_mode": redaction_mode,
            "dry_run": not write,
        }
        render(ctx, _client(get_client(ctx)).backups.export(payload))

    @backups_app.command("list")
    def list_backups(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
    ) -> None:
        """List local backup jobs."""

        render(ctx, _client(get_client(ctx)).backups.list(scope=get_scope(ctx), status=status))

    @backups_app.command("get")
    def get_backup(
        ctx: typer.Context,
        backup_job_id: Annotated[str, typer.Option("--id", help="Backup job id.")],
    ) -> None:
        """Get one local backup job."""

        render(ctx, _client(get_client(ctx)).backups.get(backup_job_id, get_scope(ctx)))

    @backups_app.command("validate")
    def validate_backup(
        ctx: typer.Context,
        backup_job_id: Annotated[str | None, typer.Option("--id")] = None,
        backup_path: Annotated[str | None, typer.Option("--path")] = None,
    ) -> None:
        """Validate a backup job or backup path."""

        if backup_job_id and backup_path:
            raise typer.BadParameter("pass either --id or --path, not both")
        if backup_path:
            render(ctx, _client(get_client(ctx)).backups.validate_path(backup_path, get_scope(ctx)))
            return
        if not backup_job_id:
            raise typer.BadParameter("--id or --path is required")
        render(ctx, _client(get_client(ctx)).backups.validate(backup_job_id, get_scope(ctx)))

    @restore_app.command("preview")
    def restore_preview(
        ctx: typer.Context,
        backup_job_id: Annotated[str | None, typer.Option("--backup-job-id")] = None,
        backup_path: Annotated[str | None, typer.Option("--backup-path")] = None,
    ) -> None:
        """Preview a local backup restore."""

        if backup_job_id and backup_path:
            raise typer.BadParameter("pass either --backup-job-id or --backup-path, not both")
        if not backup_job_id and not backup_path:
            raise typer.BadParameter("--backup-job-id or --backup-path is required")
        payload: JSONDict = {
            "backup_job_id": backup_job_id,
            "backup_path": backup_path,
            "owner_scope": get_scope(ctx),
        }
        render(ctx, _client(get_client(ctx)).backups.restore_preview(payload))

    @restore_app.command("apply")
    def restore_apply(
        ctx: typer.Context,
        restore_preview_id: Annotated[str, typer.Option("--preview-id")],
        apply: Annotated[bool, typer.Option("--apply", help="Request apply mode.")] = False,
        approval_present: Annotated[bool, typer.Option("--approval-present")] = False,
    ) -> None:
        """Create a dry-run or guarded restore job."""

        payload: JSONDict = {
            "restore_preview_id": restore_preview_id,
            "mode": "apply" if apply else "dry_run",
            "approval_present": approval_present,
            "owner_scope": get_scope(ctx),
        }
        render(ctx, _client(get_client(ctx)).backups.restore_apply(payload))


def _client(value: object) -> AIONClient:
    return cast(AIONClient, value)
