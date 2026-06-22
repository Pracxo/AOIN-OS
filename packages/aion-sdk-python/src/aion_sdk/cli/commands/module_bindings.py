"""aionctl module binding registry commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Any, cast

import typer

from aion_sdk.client import AIONClient
from aion_sdk.types import JSONDict

module_slots_app = typer.Typer(no_args_is_help=True, help="Module slot commands.")
capability_bindings_app = typer.Typer(
    no_args_is_help=True,
    help="Capability binding commands.",
)
module_bindings_app = typer.Typer(
    no_args_is_help=True,
    help="Module binding registry commands.",
)


def install_module_binding_commands(
    app: typer.Typer,
    *,
    get_client: Any,
    get_scope: Any,
    render: Any,
) -> None:
    """Install module binding commands."""

    app.add_typer(module_slots_app, name="module-slots")
    app.add_typer(capability_bindings_app, name="capability-bindings")
    app.add_typer(module_bindings_app, name="module-bindings")

    @module_slots_app.command("create")
    def create_module_slot(
        ctx: typer.Context,
        payload_file: Annotated[Path, typer.Option("--payload-file")],
    ) -> None:
        payload = _load_payload(payload_file)
        payload.setdefault("owner_scope", get_scope(ctx))
        render(ctx, _client(get_client(ctx)).module_bindings.create_module_slot(payload))

    @module_slots_app.command("list")
    def list_module_slots(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        slot_type: Annotated[str | None, typer.Option("--slot-type")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).module_bindings.list_module_slots(
                get_scope(ctx),
                status=status,
                slot_type=slot_type,
                limit=limit,
            ),
        )

    @capability_bindings_app.command("create")
    def create_capability_binding(
        ctx: typer.Context,
        payload_file: Annotated[Path, typer.Option("--payload-file")],
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).module_bindings.create_capability_binding(
                _load_payload(payload_file)
            ),
        )

    @capability_bindings_app.command("list")
    def list_capability_bindings(
        ctx: typer.Context,
        module_slot_id: Annotated[str | None, typer.Option("--module-slot-id")] = None,
        status: Annotated[str | None, typer.Option("--status")] = None,
        capability_type: Annotated[str | None, typer.Option("--capability-type")] = None,
        risk_level: Annotated[str | None, typer.Option("--risk-level")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).module_bindings.list_capability_bindings(
                get_scope(ctx),
                module_slot_id=module_slot_id,
                status=status,
                capability_type=capability_type,
                risk_level=risk_level,
                limit=limit,
            ),
        )

    @module_bindings_app.command("validate")
    def validate(
        ctx: typer.Context,
        payload_file: Annotated[Path | None, typer.Option("--payload-file")] = None,
        dry_run: Annotated[
            bool,
            typer.Option("--dry-run/--controlled", help="Validate without persisted conflicts."),
        ] = True,
    ) -> None:
        payload = _load_payload(payload_file)
        payload.setdefault("owner_scope", get_scope(ctx))
        payload.setdefault("mode", "dry_run" if dry_run else "controlled")
        render(ctx, _client(get_client(ctx)).module_bindings.validate(payload))

    @module_bindings_app.command("conflicts")
    def conflicts(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        severity: Annotated[str | None, typer.Option("--severity")] = None,
        module_slot_id: Annotated[str | None, typer.Option("--module-slot-id")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).module_bindings.list_conflicts(
                get_scope(ctx),
                status=status,
                severity=severity,
                module_slot_id=module_slot_id,
                limit=limit,
            ),
        )

    @module_bindings_app.command("mount-plan")
    def mount_plan(
        ctx: typer.Context,
        module_slot_id: Annotated[str, typer.Argument()],
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).module_bindings.create_mount_plan(
                {"module_slot_id": module_slot_id, "scope": get_scope(ctx)}
            ),
        )

    @module_bindings_app.command("route-preview")
    def route_preview(
        ctx: typer.Context,
        capability_binding_id: Annotated[str, typer.Argument()],
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).module_bindings.create_route_preview(
                {"capability_binding_id": capability_binding_id, "scope": get_scope(ctx)}
            ),
        )

    @module_bindings_app.command("query")
    def query(
        ctx: typer.Context,
        query_text: Annotated[str | None, typer.Option("--query")] = None,
        module_slot_id: Annotated[str | None, typer.Option("--module-slot-id")] = None,
        status: Annotated[str | None, typer.Option("--status")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 50,
    ) -> None:
        payload: JSONDict = {
            "scope": get_scope(ctx),
            "query": query_text,
            "module_slot_id": module_slot_id,
            "status": status,
            "limit": limit,
        }
        render(ctx, _client(get_client(ctx)).module_bindings.query(payload))


def _client(value: Any) -> AIONClient:
    return cast(AIONClient, value)


def _load_payload(path: Path | None) -> JSONDict:
    if path is None:
        return {}
    return cast(JSONDict, json.loads(path.read_text()))


__all__ = ["install_module_binding_commands"]
