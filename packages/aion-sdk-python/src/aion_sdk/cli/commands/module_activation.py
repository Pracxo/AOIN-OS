"""aionctl module activation gate commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Any, cast

import typer

from aion_sdk.client import AIONClient
from aion_sdk.types import JSONDict

module_activation_app = typer.Typer(
    no_args_is_help=True,
    help="Metadata-only module activation request gate commands.",
)


def install_module_activation_commands(
    app: typer.Typer,
    *,
    get_client: Any,
    get_scope: Any,
    render: Any,
) -> None:
    """Install module activation commands."""

    app.add_typer(module_activation_app, name="module-activation")

    @module_activation_app.command("request")
    def create_request(
        ctx: typer.Context,
        module_slot_id: Annotated[str, typer.Argument()],
        payload_file: Annotated[Path | None, typer.Option("--payload-file")] = None,
    ) -> None:
        payload = _load_payload(payload_file)
        payload.setdefault("module_slot_id", module_slot_id)
        payload.setdefault("owner_scope", get_scope(ctx))
        render(ctx, _client(get_client(ctx)).module_activation.create_request(payload))

    @module_activation_app.command("list")
    def list_requests(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        module_slot_id: Annotated[str | None, typer.Option("--module-slot-id")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).module_activation.list_requests(
                get_scope(ctx),
                status=status,
                module_slot_id=module_slot_id,
                limit=limit,
            ),
        )

    @module_activation_app.command("gate")
    def run_gate(
        ctx: typer.Context,
        activation_request_id: Annotated[str, typer.Argument()],
        mode: Annotated[str, typer.Option("--mode")] = "dry_run",
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).module_activation.run_gate(
                activation_request_id,
                {"scope": get_scope(ctx), "mode": mode},
            ),
        )

    @module_activation_app.command("blockers")
    def blockers(
        ctx: typer.Context,
        activation_request_id: Annotated[
            str | None,
            typer.Option("--activation-request-id"),
        ] = None,
        status: Annotated[str | None, typer.Option("--status")] = "open",
        severity: Annotated[str | None, typer.Option("--severity")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).module_activation.list_blockers(
                get_scope(ctx),
                activation_request_id=activation_request_id,
                status=status,
                severity=severity,
                limit=limit,
            ),
        )

    @module_activation_app.command("review")
    def review(
        ctx: typer.Context,
        activation_request_id: Annotated[str, typer.Argument()],
        decision: Annotated[str, typer.Option("--decision")] = "no_action",
        reason: Annotated[str, typer.Option("--reason")] = "Recorded metadata-only review.",
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).module_activation.create_review(
                {
                    "activation_request_id": activation_request_id,
                    "decision": decision,
                    "reason": reason,
                },
                get_scope(ctx),
            ),
        )

    @module_activation_app.command("plan")
    def plan(
        ctx: typer.Context,
        activation_request_id: Annotated[str, typer.Argument()],
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).module_activation.create_plan(
                activation_request_id,
                {"scope": get_scope(ctx)},
            ),
        )

    @module_activation_app.command("runtime-preview")
    def runtime_preview(
        ctx: typer.Context,
        activation_request_id: Annotated[str, typer.Argument()],
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).module_activation.create_runtime_registration_preview(
                activation_request_id,
                {"scope": get_scope(ctx)},
            ),
        )

    @module_activation_app.command("query")
    def query(
        ctx: typer.Context,
        activation_request_id: Annotated[
            str | None,
            typer.Option("--activation-request-id"),
        ] = None,
        module_slot_id: Annotated[str | None, typer.Option("--module-slot-id")] = None,
        status: Annotated[str | None, typer.Option("--status")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 50,
    ) -> None:
        payload: JSONDict = {
            "scope": get_scope(ctx),
            "activation_request_id": activation_request_id,
            "module_slot_id": module_slot_id,
            "status": status,
            "limit": limit,
        }
        render(ctx, _client(get_client(ctx)).module_activation.query(payload))


def _client(value: Any) -> AIONClient:
    return cast(AIONClient, value)


def _load_payload(path: Path | None) -> JSONDict:
    if path is None:
        return {}
    return cast(JSONDict, json.loads(path.read_text()))


__all__ = ["install_module_activation_commands"]
