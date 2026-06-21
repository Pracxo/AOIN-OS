"""aionctl grounding commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Any, cast

import typer

from aion_sdk.client import AIONClient
from aion_sdk.types import JSONDict

grounding_app = typer.Typer(no_args_is_help=True, help="Grounding and citation commands.")


def install_grounding_commands(
    app: typer.Typer,
    *,
    get_client: Any,
    get_scope: Any,
    render: Any,
) -> None:
    """Install grounding commands."""

    app.add_typer(grounding_app, name="grounding")

    @grounding_app.command("verify")
    def verify(
        ctx: typer.Context,
        response_id: Annotated[str | None, typer.Option("--response-id")] = None,
        explanation_id: Annotated[str | None, typer.Option("--explanation-id")] = None,
        text: Annotated[str | None, typer.Option("--text")] = None,
        require_evidence: Annotated[bool, typer.Option("--require-evidence")] = False,
    ) -> None:
        payload: JSONDict = {
            "response_id": response_id,
            "explanation_id": explanation_id,
            "target_type": "response" if response_id else "generic",
            "owner_scope": get_scope(ctx),
            "text": text,
            "require_evidence": require_evidence,
            "metadata": {"source": "aionctl"},
        }
        render(ctx, _client(get_client(ctx)).grounding.verify(payload))

    @grounding_app.command("map-response")
    def map_response(
        ctx: typer.Context,
        response_id: Annotated[str, typer.Option("--response-id")],
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).grounding.map_response(response_id, get_scope(ctx)),
        )

    @grounding_app.command("map-text")
    def map_text(
        ctx: typer.Context,
        text: Annotated[str | None, typer.Option("--text")] = None,
        payload_file: Annotated[Path | None, typer.Option("--payload-file")] = None,
    ) -> None:
        payload = _load_payload(payload_file)
        if text is not None:
            payload["text"] = text
        payload.setdefault("owner_scope", get_scope(ctx))
        payload.setdefault("sources", [])
        payload.setdefault("target_type", "generic")
        render(ctx, _client(get_client(ctx)).grounding.map_text(payload))

    @grounding_app.command("citations")
    def citations(
        ctx: typer.Context,
        response_id: Annotated[str | None, typer.Option("--response-id")] = None,
        explanation_id: Annotated[str | None, typer.Option("--explanation-id")] = None,
        source_id: Annotated[str | None, typer.Option("--source-id")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).grounding.list_citations(
                response_id=response_id,
                explanation_id=explanation_id,
                source_id=source_id,
                limit=limit,
            ),
        )

    @grounding_app.command("unsupported")
    def unsupported(
        ctx: typer.Context,
        response_id: Annotated[str | None, typer.Option("--response-id")] = None,
        explanation_id: Annotated[str | None, typer.Option("--explanation-id")] = None,
        trace_id: Annotated[str | None, typer.Option("--trace-id")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).grounding.unsupported(
                response_id=response_id,
                explanation_id=explanation_id,
                trace_id=trace_id,
                limit=limit,
            ),
        )

    @grounding_app.command("coverage")
    def coverage(
        ctx: typer.Context,
        response_id: Annotated[str | None, typer.Option("--response-id")] = None,
        explanation_id: Annotated[str | None, typer.Option("--explanation-id")] = None,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).grounding.coverage(
                {
                    "response_id": response_id,
                    "explanation_id": explanation_id,
                    "owner_scope": get_scope(ctx),
                    "required_source_types": [],
                }
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


__all__ = ["install_grounding_commands"]
