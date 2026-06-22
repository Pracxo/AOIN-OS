"""aionctl model output governance commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Any, cast

import typer

from aion_sdk.client import AIONClient
from aion_sdk.types import JSONDict

model_outputs_app = typer.Typer(no_args_is_help=True, help="Model output governance commands.")
candidates_app = typer.Typer(no_args_is_help=True, help="Response candidate commands.")
tool_intents_app = typer.Typer(no_args_is_help=True, help="Tool intent commands.")


def install_model_output_commands(
    app: typer.Typer,
    *,
    get_client: Any,
    get_scope: Any,
    render: Any,
) -> None:
    """Install model output governance commands."""

    app.add_typer(model_outputs_app, name="model-outputs")
    model_outputs_app.add_typer(candidates_app, name="candidates")
    model_outputs_app.add_typer(tool_intents_app, name="tool-intents")

    @model_outputs_app.command("create")
    def create(
        ctx: typer.Context,
        raw_output: Annotated[str | None, typer.Option("--raw-output")] = None,
        payload_file: Annotated[Path | None, typer.Option("--payload-file")] = None,
        output_type: Annotated[str, typer.Option("--output-type")] = "text",
    ) -> None:
        payload = _load_payload(payload_file)
        if raw_output is not None:
            payload["raw_output"] = raw_output
        payload.setdefault("output_type", output_type)
        payload.setdefault("owner_scope", get_scope(ctx))
        render(ctx, _client(get_client(ctx)).model_outputs.create(payload))

    @model_outputs_app.command("get")
    def get(
        ctx: typer.Context,
        model_output_id: Annotated[str, typer.Option("--model-output-id")],
    ) -> None:
        render(ctx, _client(get_client(ctx)).model_outputs.get(model_output_id, get_scope(ctx)))

    @model_outputs_app.command("query")
    def query(
        ctx: typer.Context,
        payload_file: Annotated[Path | None, typer.Option("--payload-file")] = None,
        trace_id: Annotated[str | None, typer.Option("--trace-id")] = None,
        status: Annotated[str | None, typer.Option("--status")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 50,
    ) -> None:
        payload = _load_payload(payload_file)
        payload.setdefault("scope", get_scope(ctx))
        payload.setdefault("limit", limit)
        if trace_id is not None:
            payload["trace_id"] = trace_id
        if status is not None:
            payload["status"] = status
        render(ctx, _client(get_client(ctx)).model_outputs.query(payload))

    @model_outputs_app.command("delete")
    def delete(
        ctx: typer.Context,
        model_output_id: Annotated[str, typer.Option("--model-output-id")],
        reason: Annotated[str, typer.Option("--reason")] = "operator_requested",
    ) -> None:
        render(ctx, _client(get_client(ctx)).model_outputs.delete(model_output_id, reason))

    @model_outputs_app.command("govern")
    def govern(
        ctx: typer.Context,
        model_output_id: Annotated[str, typer.Option("--model-output-id")],
        payload_file: Annotated[Path | None, typer.Option("--payload-file")] = None,
    ) -> None:
        payload = _load_payload(payload_file)
        payload.setdefault("model_output_id", model_output_id)
        payload.setdefault("owner_scope", get_scope(ctx))
        render(ctx, _client(get_client(ctx)).model_outputs.govern(model_output_id, payload))

    @model_outputs_app.command("segments")
    def segments(
        ctx: typer.Context,
        model_output_id: Annotated[str, typer.Option("--model-output-id")],
    ) -> None:
        render(
            ctx, _client(get_client(ctx)).model_outputs.segments(model_output_id, get_scope(ctx))
        )

    @model_outputs_app.command("validate-structured")
    def validate_structured(
        ctx: typer.Context,
        model_output_id: Annotated[str, typer.Option("--model-output-id")],
        schema_name: Annotated[str | None, typer.Option("--schema-name")] = None,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).model_outputs.validate_structured(
                model_output_id,
                get_scope(ctx),
                schema_name=schema_name,
            ),
        )

    @candidates_app.command("list")
    def candidates(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        trace_id: Annotated[str | None, typer.Option("--trace-id")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).model_outputs.response_candidates(
                get_scope(ctx),
                status=status,
                trace_id=trace_id,
                limit=limit,
            ),
        )

    @candidates_app.command("promote")
    def promote_candidate(
        ctx: typer.Context,
        response_candidate_id: Annotated[str, typer.Option("--response-candidate-id")],
        reason: Annotated[str, typer.Option("--reason")] = "operator_requested",
        approval_present: Annotated[bool, typer.Option("--approval-present")] = False,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).model_outputs.promote_candidate(
                response_candidate_id,
                approval_present=approval_present,
                reason=reason,
            ),
        )

    @tool_intents_app.command("list")
    def tool_intents(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        trace_id: Annotated[str | None, typer.Option("--trace-id")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).model_outputs.tool_intents(
                get_scope(ctx),
                status=status,
                trace_id=trace_id,
                limit=limit,
            ),
        )

    @tool_intents_app.command("reject")
    def reject_tool_intent(
        ctx: typer.Context,
        tool_intent_id: Annotated[str, typer.Option("--tool-intent-id")],
        reason: Annotated[str, typer.Option("--reason")] = "operator_rejected",
    ) -> None:
        render(
            ctx, _client(get_client(ctx)).model_outputs.reject_tool_intent(tool_intent_id, reason)
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


__all__ = ["install_model_output_commands"]
