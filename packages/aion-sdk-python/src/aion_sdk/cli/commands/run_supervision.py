"""aionctl run supervision commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Any, cast

import typer

from aion_sdk.client import AIONClient
from aion_sdk.types import JSONDict

run_supervision_app = typer.Typer(no_args_is_help=True, help="Run supervision commands.")
control_app = typer.Typer(no_args_is_help=True, help="Run control commands.")
compensation_app = typer.Typer(no_args_is_help=True, help="Compensation plan commands.")


def install_run_supervision_commands(
    app: typer.Typer,
    *,
    get_client: Any,
    get_scope: Any,
    render: Any,
) -> None:
    """Install run supervision commands."""

    app.add_typer(run_supervision_app, name="run-supervision")
    run_supervision_app.add_typer(control_app, name="control")
    run_supervision_app.add_typer(compensation_app, name="compensation")

    @run_supervision_app.command("runs")
    def runs(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        target_system: Annotated[str | None, typer.Option("--target-system")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).run_supervision.list_runs(
                get_scope(ctx),
                status=status,
                target_system=target_system,
                limit=limit,
            ),
        )

    @run_supervision_app.command("sample")
    def sample(
        ctx: typer.Context,
        run_supervision_id: Annotated[str, typer.Option("--run-supervision-id")],
    ) -> None:
        render(
            ctx, _client(get_client(ctx)).run_supervision.sample(run_supervision_id, get_scope(ctx))
        )

    @run_supervision_app.command("sample-many")
    def sample_many(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = "active",
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        render(
            ctx, _client(get_client(ctx)).run_supervision.sample_many(get_scope(ctx), status, limit)
        )

    @run_supervision_app.command("timeout-policies")
    def timeout_policies(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        target_system: Annotated[str | None, typer.Option("--target-system")] = None,
        run_type: Annotated[str | None, typer.Option("--run-type")] = None,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).run_supervision.list_timeout_policies(
                get_scope(ctx),
                status=status,
                target_system=target_system,
                run_type=run_type,
            ),
        )

    @run_supervision_app.command("report")
    def report(
        ctx: typer.Context,
        payload_file: Annotated[Path | None, typer.Option("--payload-file")] = None,
    ) -> None:
        payload = _load_payload(payload_file)
        payload.setdefault("owner_scope", get_scope(ctx))
        render(ctx, _client(get_client(ctx)).run_supervision.create_report(payload))

    @control_app.command("request")
    def control_request(
        ctx: typer.Context,
        run_supervision_id: Annotated[str, typer.Option("--run-supervision-id")],
        control_type: Annotated[str, typer.Option("--control-type")] = "request_status",
        reason: Annotated[str, typer.Option("--reason")] = "operator_request",
        requested_mode: Annotated[str, typer.Option("--requested-mode")] = "dry_run",
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).run_supervision.create_control_request(
                {
                    "run_supervision_id": run_supervision_id,
                    "control_type": control_type,
                    "reason": reason,
                    "requested_mode": requested_mode,
                }
            ),
        )

    @control_app.command("handoff")
    def control_handoff(
        ctx: typer.Context,
        run_control_request_id: Annotated[str, typer.Option("--run-control-request-id")],
        approval_present: Annotated[bool, typer.Option("--approval-present")] = False,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).run_supervision.handoff_control(
                run_control_request_id,
                approval_present=approval_present,
            ),
        )

    @compensation_app.command("propose")
    def compensation_propose(
        ctx: typer.Context,
        run_supervision_id: Annotated[str, typer.Option("--run-supervision-id")],
        trigger_reason: Annotated[str, typer.Option("--trigger-reason")] = "operator_review",
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).run_supervision.propose_compensation(
                run_supervision_id,
                trigger_reason,
            ),
        )

    @compensation_app.command("list")
    def compensation_list(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        run_supervision_id: Annotated[str | None, typer.Option("--run-supervision-id")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).run_supervision.list_compensation_plans(
                get_scope(ctx),
                status=status,
                run_supervision_id=run_supervision_id,
                limit=limit,
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


__all__ = ["install_run_supervision_commands"]
