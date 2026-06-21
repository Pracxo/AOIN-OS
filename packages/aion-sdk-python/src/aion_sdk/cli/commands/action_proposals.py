"""aionctl action proposal commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Any, cast

import typer

from aion_sdk.client import AIONClient
from aion_sdk.types import JSONDict

action_proposals_app = typer.Typer(no_args_is_help=True, help="Action proposal commands.")
tool_intents_app = typer.Typer(no_args_is_help=True, help="Tool intent review commands.")


def install_action_proposal_commands(
    app: typer.Typer,
    *,
    get_client: Any,
    get_scope: Any,
    render: Any,
) -> None:
    """Install action proposal commands."""

    app.add_typer(action_proposals_app, name="action-proposals")
    action_proposals_app.add_typer(tool_intents_app, name="tool-intent")

    @action_proposals_app.command("create")
    def create(
        ctx: typer.Context,
        payload_file: Annotated[Path | None, typer.Option("--payload-file")] = None,
    ) -> None:
        payload = _load_payload(payload_file)
        payload.setdefault("owner_scope", get_scope(ctx))
        render(ctx, _client(get_client(ctx)).action_proposals.create(payload))

    @action_proposals_app.command("query")
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
        render(ctx, _client(get_client(ctx)).action_proposals.query(payload))

    @action_proposals_app.command("review")
    def review(
        ctx: typer.Context,
        action_proposal_id: Annotated[str, typer.Option("--action-proposal-id")],
        decision: Annotated[str, typer.Option("--decision")] = "approve_for_handoff",
        reason: Annotated[str, typer.Option("--reason")] = "operator_review",
        approval_present: Annotated[bool, typer.Option("--approval-present")] = False,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).action_proposals.review(
                action_proposal_id,
                {
                    "action_proposal_id": action_proposal_id,
                    "decision": decision,
                    "reason": reason,
                    "approval_present": approval_present,
                },
            ),
        )

    @action_proposals_app.command("handoff")
    def handoff(
        ctx: typer.Context,
        action_proposal_id: Annotated[str, typer.Option("--action-proposal-id")],
        target_system: Annotated[str, typer.Option("--target-system")] = "noop",
        handoff_type: Annotated[str, typer.Option("--handoff-type")] = "dry_run",
        mode: Annotated[str, typer.Option("--mode")] = "dry_run",
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).action_proposals.handoff(
                {
                    "action_proposal_id": action_proposal_id,
                    "target_system": target_system,
                    "handoff_type": handoff_type,
                    "mode": mode,
                }
            ),
        )

    @action_proposals_app.command("blockers")
    def blockers(
        ctx: typer.Context,
        action_proposal_id: Annotated[str | None, typer.Option("--action-proposal-id")] = None,
        status: Annotated[str | None, typer.Option("--status")] = None,
        severity: Annotated[str | None, typer.Option("--severity")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).action_proposals.list_blockers(
                action_proposal_id=action_proposal_id,
                status=status,
                severity=severity,
                limit=limit,
            ),
        )

    @action_proposals_app.command("handoffs")
    def handoffs(
        ctx: typer.Context,
        action_proposal_id: Annotated[str | None, typer.Option("--action-proposal-id")] = None,
        status: Annotated[str | None, typer.Option("--status")] = None,
        target_system: Annotated[str | None, typer.Option("--target-system")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).action_proposals.list_handoffs(
                action_proposal_id=action_proposal_id,
                status=status,
                target_system=target_system,
                limit=limit,
            ),
        )

    @tool_intents_app.command("review")
    def review_tool_intent(
        ctx: typer.Context,
        tool_intent_id: Annotated[str, typer.Option("--tool-intent-id")],
        decision: Annotated[str, typer.Option("--decision")] = "create_proposal",
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).action_proposals.review_tool_intent(
                tool_intent_id,
                {
                    "tool_intent_id": tool_intent_id,
                    "decision": decision,
                    "owner_scope": get_scope(ctx),
                },
            ),
        )


def _load_payload(path: Path | None) -> JSONDict:
    if path is None:
        return {}
    loaded = json.loads(path.read_text())
    if not isinstance(loaded, dict):
        raise typer.BadParameter("payload file must contain a JSON object")
    return cast(JSONDict, loaded)


def _client(value: object) -> AIONClient:
    return cast(AIONClient, value)


__all__ = ["install_action_proposal_commands"]
