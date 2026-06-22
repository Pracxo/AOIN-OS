"""aionctl Contract Registry commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Any, cast

import typer

from aion_sdk.client import AIONClient
from aion_sdk.types import JSONDict


def install_contract_commands(
    contracts_app: typer.Typer,
    *,
    get_client: Any,
    get_scope: Any,
    render: Any,
) -> None:
    """Install Contract Registry commands into the existing contracts group."""

    rules_app = typer.Typer(no_args_is_help=False, invoke_without_command=True)
    contracts_app.add_typer(rules_app, name="rules")

    @contracts_app.command("list")
    def list_contracts(
        ctx: typer.Context,
        contract_type: Annotated[str | None, typer.Option("--contract-type")] = None,
        status: Annotated[str | None, typer.Option("--status")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).contracts.list_contracts(
                get_scope(ctx),
                contract_type=contract_type,
                status=status,
                limit=limit,
            ),
        )

    @contracts_app.command("interfaces")
    def interfaces(
        ctx: typer.Context,
        interface_type: Annotated[str | None, typer.Option("--interface-type")] = None,
        source_system: Annotated[str | None, typer.Option("--source-system")] = None,
        status: Annotated[str | None, typer.Option("--status")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).contracts.list_interfaces(
                get_scope(ctx),
                interface_type=interface_type,
                source_system=source_system,
                status=status,
                limit=limit,
            ),
        )

    @contracts_app.command("snapshot")
    def snapshot(
        ctx: typer.Context,
        snapshot_type: Annotated[str, typer.Option("--snapshot-type")] = "manual",
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).contracts.create_snapshot(
                get_scope(ctx),
                snapshot_type=snapshot_type,
            ),
        )

    @contracts_app.command("snapshots")
    def snapshots(
        ctx: typer.Context,
        snapshot_type: Annotated[str | None, typer.Option("--snapshot-type")] = None,
        status: Annotated[str | None, typer.Option("--status")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 50,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).contracts.list_snapshots(
                get_scope(ctx),
                snapshot_type=snapshot_type,
                status=status,
                limit=limit,
            ),
        )

    @rules_app.callback()
    def rules(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        rule_type: Annotated[str | None, typer.Option("--rule-type")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        if ctx.invoked_subcommand is not None:
            return
        render(
            ctx,
            _client(get_client(ctx)).contracts.list_rules(
                get_scope(ctx),
                status=status,
                rule_type=rule_type,
                limit=limit,
            ),
        )

    @rules_app.command("seed")
    def rules_seed(
        ctx: typer.Context,
        apply: Annotated[bool, typer.Option("--apply")] = False,
    ) -> None:
        render(
            ctx, _client(get_client(ctx)).contracts.seed_rules(get_scope(ctx), dry_run=not apply)
        )

    @contracts_app.command("scan")
    def scan(
        ctx: typer.Context,
        payload_file: Annotated[Path | None, typer.Option("--payload-file")] = None,
        controlled: Annotated[bool, typer.Option("--controlled")] = False,
        create_notifications: Annotated[bool, typer.Option("--create-notifications")] = False,
    ) -> None:
        payload = _load_payload(payload_file)
        payload.setdefault("owner_scope", get_scope(ctx))
        payload.setdefault("mode", "controlled" if controlled else "dry_run")
        payload.setdefault("create_notifications", create_notifications)
        render(ctx, _client(get_client(ctx)).contracts.scan_compatibility(payload))

    @contracts_app.command("findings")
    def findings(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        severity: Annotated[str | None, typer.Option("--severity")] = None,
        breaking: Annotated[bool | None, typer.Option("--breaking/--non-breaking")] = None,
        interface_type: Annotated[str | None, typer.Option("--interface-type")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).contracts.findings(
                status=status,
                severity=severity,
                breaking=breaking,
                interface_type=interface_type,
                limit=limit,
            ),
        )

    @contracts_app.command("migration-notes")
    def migration_notes(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        note_type: Annotated[str | None, typer.Option("--note-type")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).contracts.migration_notes(
                get_scope(ctx),
                status=status,
                note_type=note_type,
                limit=limit,
            ),
        )

    @contracts_app.command("report")
    def report(ctx: typer.Context) -> None:
        render(ctx, _client(get_client(ctx)).contracts.report(get_scope(ctx)))


def _load_payload(path: Path | None) -> JSONDict:
    if path is None:
        return {}
    return cast(JSONDict, json.loads(path.read_text()))


def _client(value: object) -> AIONClient:
    return cast(AIONClient, value)


__all__ = ["install_contract_commands"]
