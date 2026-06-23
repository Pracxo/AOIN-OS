"""aionctl governed operator action commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Any, cast

import typer

from aion_sdk.client import AIONClient
from aion_sdk.types import JSONDict

operator_actions_app = typer.Typer(
    no_args_is_help=True,
    help="Dry-run operator action request commands.",
)


def install_operator_action_commands(
    app: typer.Typer,
    *,
    get_client: Any,
    get_scope: Any,
    render: Any,
) -> None:
    """Install operator action commands."""

    app.add_typer(operator_actions_app, name="operator-actions")

    @operator_actions_app.command("request")
    def request(
        ctx: typer.Context,
        payload_file: Annotated[Path | None, typer.Option("--payload-file")] = None,
        action_key: Annotated[str, typer.Option("--action-key")] = "operator.review",
        action_type: Annotated[str, typer.Option("--action-type")] = "generic",
        target_type: Annotated[str, typer.Option("--target-type")] = "generic",
        risk_level: Annotated[str, typer.Option("--risk-level")] = "medium",
    ) -> None:
        payload = _load_payload(payload_file)
        payload.setdefault("action_key", action_key)
        payload.setdefault("action_type", action_type)
        payload.setdefault("target_type", target_type)
        payload.setdefault("risk_level", risk_level)
        payload.setdefault("owner_scope", get_scope(ctx))
        payload.setdefault("mode", "dry_run")
        render(ctx, _client(get_client(ctx)).operator_actions.create_request(payload))

    @operator_actions_app.command("requests")
    def requests(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        action_type: Annotated[str | None, typer.Option("--action-type")] = None,
        target_type: Annotated[str | None, typer.Option("--target-type")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).operator_actions.list_requests(
                get_scope(ctx),
                status=status,
                action_type=action_type,
                target_type=target_type,
                limit=limit,
            ),
        )

    @operator_actions_app.command("preview")
    def preview(
        ctx: typer.Context,
        operator_action_request_id: Annotated[str, typer.Option("--request-id")],
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).operator_actions.create_preview(
                operator_action_request_id,
                get_scope(ctx),
            ),
        )

    @operator_actions_app.command("blockers")
    def blockers(
        ctx: typer.Context,
        operator_action_request_id: Annotated[str | None, typer.Option("--request-id")] = None,
        status: Annotated[str | None, typer.Option("--status")] = None,
        severity: Annotated[str | None, typer.Option("--severity")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).operator_actions.blockers(
                get_scope(ctx),
                operator_action_request_id=operator_action_request_id,
                status=status,
                severity=severity,
                limit=limit,
            ),
        )

    @operator_actions_app.command("review")
    def review(
        ctx: typer.Context,
        operator_action_request_id: Annotated[str, typer.Option("--request-id")],
        decision: Annotated[str, typer.Option("--decision")] = "approve_preview_only",
        reason: Annotated[str, typer.Option("--reason")] = "operator_review",
        approval_present: Annotated[bool, typer.Option("--approval-present")] = False,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).operator_actions.review(
                operator_action_request_id,
                {
                    "operator_action_request_id": operator_action_request_id,
                    "decision": decision,
                    "reason": reason,
                    "approval_present": approval_present,
                },
            ),
        )

    @operator_actions_app.command("query")
    def query(
        ctx: typer.Context,
        payload_file: Annotated[Path | None, typer.Option("--payload-file")] = None,
        status: Annotated[str | None, typer.Option("--status")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 50,
    ) -> None:
        payload = _load_payload(payload_file)
        payload.setdefault("scope", get_scope(ctx))
        payload.setdefault("limit", limit)
        if status is not None:
            payload["status"] = status
        render(ctx, _client(get_client(ctx)).operator_actions.query(payload))


def _load_payload(path: Path | None) -> JSONDict:
    if path is None:
        return {}
    loaded = json.loads(path.read_text())
    if not isinstance(loaded, dict):
        raise typer.BadParameter("payload file must contain a JSON object")
    return cast(JSONDict, loaded)


def _client(value: object) -> AIONClient:
    return cast(AIONClient, value)


__all__ = ["install_operator_action_commands"]
