"""aionctl prompt governance commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Any, cast

import typer

from aion_sdk.client import AIONClient
from aion_sdk.types import JSONDict

prompts_app = typer.Typer(no_args_is_help=True, help="Prompt packet governance commands.")
templates_app = typer.Typer(no_args_is_help=True, help="Prompt template commands.")
fragments_app = typer.Typer(no_args_is_help=True, help="Prompt fragment commands.")


def install_prompt_commands(
    app: typer.Typer,
    *,
    get_client: Any,
    get_scope: Any,
    render: Any,
) -> None:
    """Install prompt governance commands."""

    app.add_typer(prompts_app, name="prompts")
    prompts_app.add_typer(templates_app, name="templates")
    prompts_app.add_typer(fragments_app, name="fragments")

    @prompts_app.command("compile")
    def compile_prompt(
        ctx: typer.Context,
        user_message: Annotated[str | None, typer.Option("--user-message")] = None,
        payload_file: Annotated[Path | None, typer.Option("--payload-file")] = None,
        packet_type: Annotated[str, typer.Option("--packet-type")] = "generic",
        target_model_route: Annotated[str | None, typer.Option("--target-model-route")] = None,
    ) -> None:
        payload = _load_payload(payload_file)
        if user_message is not None:
            payload["user_message"] = user_message
        payload.setdefault("packet_type", packet_type)
        payload.setdefault("target_model_route", target_model_route)
        payload.setdefault("owner_scope", get_scope(ctx))
        render(ctx, _client(get_client(ctx)).prompts.compile(payload))

    @prompts_app.command("preview")
    def preview(
        ctx: typer.Context,
        prompt_packet_id: Annotated[str | None, typer.Option("--prompt-packet-id")] = None,
        payload_file: Annotated[Path | None, typer.Option("--payload-file")] = None,
        redaction_level: Annotated[str, typer.Option("--redaction-level")] = "safe",
    ) -> None:
        payload = _load_payload(payload_file)
        if prompt_packet_id is not None:
            payload["prompt_packet_id"] = prompt_packet_id
        payload.setdefault("owner_scope", get_scope(ctx))
        payload.setdefault("redaction_level", redaction_level)
        render(ctx, _client(get_client(ctx)).prompts.preview(payload))

    @prompts_app.command("packets")
    def packets(
        ctx: typer.Context,
        trace_id: Annotated[str | None, typer.Option("--trace-id")] = None,
        status: Annotated[str | None, typer.Option("--status")] = None,
        packet_type: Annotated[str | None, typer.Option("--packet-type")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 50,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).prompts.list_packets(
                get_scope(ctx),
                trace_id=trace_id,
                status=status,
                packet_type=packet_type,
                limit=limit,
            ),
        )

    @prompts_app.command("packet")
    def packet(
        ctx: typer.Context,
        prompt_packet_id: Annotated[str, typer.Option("--prompt-packet-id")],
    ) -> None:
        render(ctx, _client(get_client(ctx)).prompts.get_packet(prompt_packet_id, get_scope(ctx)))

    @templates_app.command("seed")
    @prompts_app.command("seed-templates")
    def seed_templates(
        ctx: typer.Context,
        dry_run: Annotated[bool, typer.Option("--dry-run/--apply")] = True,
    ) -> None:
        render(
            ctx, _client(get_client(ctx)).prompts.seed_templates(get_scope(ctx), dry_run=dry_run)
        )

    @templates_app.command("list")
    def templates(
        ctx: typer.Context,
        template_type: Annotated[str | None, typer.Option("--template-type")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).prompts.list_templates(
                get_scope(ctx),
                template_type=template_type,
                limit=limit,
            ),
        )

    @fragments_app.command("list")
    def fragments(
        ctx: typer.Context,
        fragment_type: Annotated[str | None, typer.Option("--fragment-type")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).prompts.list_fragments(
                get_scope(ctx),
                fragment_type=fragment_type,
                limit=limit,
            ),
        )

    @prompts_app.command("boundary-check")
    def boundary_check(
        ctx: typer.Context,
        prompt_packet_id: Annotated[str, typer.Option("--prompt-packet-id")],
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).prompts.boundary_check(prompt_packet_id, get_scope(ctx)),
        )

    @prompts_app.command("injection-findings")
    @prompts_app.command("injections")
    def injection_findings(
        ctx: typer.Context,
        trace_id: Annotated[str | None, typer.Option("--trace-id")] = None,
        prompt_packet_id: Annotated[str | None, typer.Option("--prompt-packet-id")] = None,
        severity: Annotated[str | None, typer.Option("--severity")] = None,
        status: Annotated[str | None, typer.Option("--status")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).prompts.injection_findings(
                trace_id=trace_id,
                prompt_packet_id=prompt_packet_id,
                severity=severity,
                status=status,
                limit=limit,
            ),
        )

    @prompts_app.command("manifests")
    def manifests(
        ctx: typer.Context,
        trace_id: Annotated[str | None, typer.Option("--trace-id")] = None,
        prompt_packet_id: Annotated[str | None, typer.Option("--prompt-packet-id")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 50,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).prompts.list_manifests(
                get_scope(ctx),
                trace_id=trace_id,
                prompt_packet_id=prompt_packet_id,
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


__all__ = ["install_prompt_commands"]
