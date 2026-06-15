"""aionctl audit and provenance commands."""

from __future__ import annotations

from typing import Annotated, Any, cast

import typer

from aion_sdk.client import AIONClient
from aion_sdk.types import JSONDict

audit_app = typer.Typer(no_args_is_help=True, help="Audit integrity commands.")
provenance_app = typer.Typer(no_args_is_help=True, help="Provenance commands.")


def install_audit_commands(
    app: typer.Typer,
    *,
    get_client: Any,
    get_scope: Any,
    render: Any,
) -> None:
    """Install audit and provenance commands onto the root CLI."""

    app.add_typer(audit_app, name="audit")
    app.add_typer(provenance_app, name="provenance")

    @audit_app.command("status")
    def status(ctx: typer.Context) -> None:
        """Show audit integrity status."""

        render(ctx, _client(get_client(ctx)).audit.status())

    @audit_app.command("entries")
    def entries(
        ctx: typer.Context,
        trace_id: Annotated[str | None, typer.Option("--trace-id")] = None,
        resource_type: Annotated[str | None, typer.Option("--resource-type")] = None,
        action_type: Annotated[str | None, typer.Option("--action-type")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        """List audit entries."""

        render(
            ctx,
            _client(get_client(ctx)).audit.list_entries(
                trace_id=trace_id,
                resource_type=resource_type,
                action_type=action_type,
                limit=limit,
            ),
        )

    @audit_app.command("verify")
    def verify(
        ctx: typer.Context,
        trace_id: Annotated[str | None, typer.Option("--trace-id")] = None,
        from_sequence: Annotated[int | None, typer.Option("--from-sequence")] = None,
        to_sequence: Annotated[int | None, typer.Option("--to-sequence")] = None,
    ) -> None:
        """Verify audit hash-chain integrity."""

        payload: JSONDict = {"metadata": {"source": "aionctl"}}
        if trace_id is not None:
            payload["trace_id"] = trace_id
        if from_sequence is not None:
            payload["from_sequence"] = from_sequence
        if to_sequence is not None:
            payload["to_sequence"] = to_sequence
        render(ctx, _client(get_client(ctx)).audit.verify(payload))

    @audit_app.command("checkpoint")
    def checkpoint(
        ctx: typer.Context,
        from_sequence: Annotated[int | None, typer.Option("--from-sequence")] = None,
        to_sequence: Annotated[int | None, typer.Option("--to-sequence")] = None,
    ) -> None:
        """Create an audit integrity checkpoint."""

        payload: JSONDict = {}
        if from_sequence is not None:
            payload["from_sequence"] = from_sequence
        if to_sequence is not None:
            payload["to_sequence"] = to_sequence
        render(ctx, _client(get_client(ctx)).audit.create_checkpoint(payload))

    @audit_app.command("export")
    def export(
        ctx: typer.Context,
        dry_run: Annotated[
            bool,
            typer.Option("--dry-run/--write", help="Dry-run by default; --write writes files."),
        ] = True,
        export_type: Annotated[str, typer.Option("--type")] = "jsonl",
        output_dir: Annotated[str, typer.Option("--output-dir")] = "artifacts/audit",
    ) -> None:
        """Export audit entries locally."""

        payload: JSONDict = {
            "owner_scope": get_scope(ctx),
            "export_type": export_type,
            "output_dir": output_dir,
            "dry_run": dry_run,
            "metadata": {"source": "aionctl"},
        }
        render(ctx, _client(get_client(ctx)).audit.export(payload))

    @provenance_app.command("trace")
    def provenance_trace(
        ctx: typer.Context,
        trace_id: Annotated[str, typer.Option("--trace-id")],
        limit: Annotated[int, typer.Option("--limit")] = 500,
    ) -> None:
        """Show provenance links for a trace."""

        render(ctx, _client(get_client(ctx)).audit.trace_provenance(trace_id, limit))

    @provenance_app.command("links")
    def provenance_links(
        ctx: typer.Context,
        trace_id: Annotated[str | None, typer.Option("--trace-id")] = None,
        source_type: Annotated[str | None, typer.Option("--source-type")] = None,
        source_id: Annotated[str | None, typer.Option("--source-id")] = None,
        target_type: Annotated[str | None, typer.Option("--target-type")] = None,
        target_id: Annotated[str | None, typer.Option("--target-id")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        """List provenance links."""

        render(
            ctx,
            _client(get_client(ctx)).audit.list_provenance_links(
                trace_id=trace_id,
                source_type=source_type,
                source_id=source_id,
                target_type=target_type,
                target_id=target_id,
                limit=limit,
            ),
        )


def _client(value: object) -> AIONClient:
    return cast(AIONClient, value)
