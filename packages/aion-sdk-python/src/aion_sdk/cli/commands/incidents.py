"""aionctl incident correlation commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Any, cast

import typer

from aion_sdk.client import AIONClient
from aion_sdk.types import JSONDict

incidents_app = typer.Typer(no_args_is_help=True, help="Incident correlation commands.")
signals_app = typer.Typer(no_args_is_help=True, help="Incident signal commands.")
rules_app = typer.Typer(no_args_is_help=True, help="Incident correlation rule commands.")
root_causes_app = typer.Typer(no_args_is_help=True, help="Root cause candidate commands.")


def install_incident_commands(
    app: typer.Typer,
    *,
    get_client: Any,
    get_scope: Any,
    render: Any,
) -> None:
    """Install incident commands."""

    app.add_typer(incidents_app, name="incidents")
    incidents_app.add_typer(signals_app, name="signals")
    incidents_app.add_typer(rules_app, name="rules")
    incidents_app.add_typer(root_causes_app, name="root-causes")

    @signals_app.command("create")
    def create_signal(
        ctx: typer.Context,
        payload_file: Annotated[Path, typer.Option("--payload-file")],
    ) -> None:
        payload = _load_payload(payload_file)
        payload.setdefault("owner_scope", get_scope(ctx))
        render(ctx, _client(get_client(ctx)).incidents.create_signal(payload))

    @signals_app.command("list")
    def list_signals(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        source_type: Annotated[str | None, typer.Option("--source-type")] = None,
        signal_type: Annotated[str | None, typer.Option("--signal-type")] = None,
        severity: Annotated[str | None, typer.Option("--severity")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).incidents.list_signals(
                get_scope(ctx),
                status=status,
                source_type=source_type,
                signal_type=signal_type,
                severity=severity,
                limit=limit,
            ),
        )

    @incidents_app.command("create")
    def create_incident(
        ctx: typer.Context,
        payload_file: Annotated[Path, typer.Option("--payload-file")],
    ) -> None:
        payload = _load_payload(payload_file)
        payload.setdefault("owner_scope", get_scope(ctx))
        render(ctx, _client(get_client(ctx)).incidents.create_incident(payload))

    @incidents_app.command("query")
    def query_incidents(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        severity: Annotated[str | None, typer.Option("--severity")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 50,
    ) -> None:
        payload: JSONDict = {"scope": get_scope(ctx), "limit": limit}
        if status is not None:
            payload["status"] = status
        if severity is not None:
            payload["severity"] = severity
        render(ctx, _client(get_client(ctx)).incidents.query(payload))

    @incidents_app.command("acknowledge")
    def acknowledge(
        ctx: typer.Context,
        incident_id: Annotated[str, typer.Option("--incident-id")],
        reason: Annotated[str, typer.Option("--reason")] = "acknowledged by operator",
    ) -> None:
        render(ctx, _client(get_client(ctx)).incidents.acknowledge(incident_id, reason))

    @incidents_app.command("resolve")
    def resolve(
        ctx: typer.Context,
        incident_id: Annotated[str, typer.Option("--incident-id")],
        reason: Annotated[str, typer.Option("--reason")] = "resolved by operator",
    ) -> None:
        render(ctx, _client(get_client(ctx)).incidents.resolve(incident_id, reason))

    @rules_app.command("list")
    def list_rules(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        rule_type: Annotated[str | None, typer.Option("--rule-type")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).incidents.list_rules(
                get_scope(ctx), status=status, rule_type=rule_type, limit=limit
            ),
        )

    @rules_app.command("seed")
    def seed_rules(
        ctx: typer.Context,
        dry_run: Annotated[bool, typer.Option("--dry-run/--apply")] = True,
    ) -> None:
        render(ctx, _client(get_client(ctx)).incidents.seed_rules(get_scope(ctx), dry_run=dry_run))

    @incidents_app.command("correlate")
    def correlate(
        ctx: typer.Context,
        payload_file: Annotated[Path | None, typer.Option("--payload-file")] = None,
        dry_run: Annotated[bool, typer.Option("--dry-run/--controlled")] = True,
    ) -> None:
        payload = _load_payload(payload_file)
        payload.setdefault("owner_scope", get_scope(ctx))
        payload.setdefault("mode", "dry_run" if dry_run else "controlled")
        render(ctx, _client(get_client(ctx)).incidents.correlate(payload))

    @root_causes_app.command("generate")
    def generate_root_causes(
        ctx: typer.Context,
        incident_id: Annotated[str, typer.Option("--incident-id")],
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).incidents.generate_root_causes(incident_id, get_scope(ctx)),
        )

    @incidents_app.command("recovery-review")
    def recovery_review(
        ctx: typer.Context,
        incident_id: Annotated[str, typer.Option("--incident-id")],
        create_actions: Annotated[bool, typer.Option("--create-actions")] = False,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).incidents.create_recovery_review(
                {
                    "incident_id": incident_id,
                    "owner_scope": get_scope(ctx),
                    "create_action_proposals": create_actions,
                }
            ),
        )


def _load_payload(path: Path | None) -> JSONDict:
    if path is None:
        return {}
    return cast(JSONDict, json.loads(path.read_text()))


def _client(client: object) -> AIONClient:
    return cast(AIONClient, client)


__all__ = ["install_incident_commands"]
