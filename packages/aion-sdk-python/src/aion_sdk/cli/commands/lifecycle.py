"""aionctl data lifecycle commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Any, cast

import typer

from aion_sdk.client import AIONClient
from aion_sdk.types import JSONDict

lifecycle_app = typer.Typer(no_args_is_help=True, help="Data lifecycle commands.")


def install_lifecycle_commands(
    app: typer.Typer,
    *,
    get_client: Any,
    get_scope: Any,
    render: Any,
) -> None:
    """Install lifecycle commands."""

    app.add_typer(lifecycle_app, name="lifecycle")

    @lifecycle_app.command("seed-defaults")
    def seed_defaults(
        ctx: typer.Context,
        apply: Annotated[
            bool,
            typer.Option("--apply", help="Persist defaults instead of previewing them."),
        ] = False,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).lifecycle.seed_default_policies(
                get_scope(ctx),
                dry_run=not apply,
            ),
        )

    @lifecycle_app.command("policies")
    def policies(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        policy_type: Annotated[str | None, typer.Option("--policy-type")] = None,
        retention_class: Annotated[str | None, typer.Option("--retention-class")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).lifecycle.list_policies(
                get_scope(ctx),
                status=status,
                policy_type=policy_type,
                retention_class=retention_class,
                limit=limit,
            ),
        )

    @lifecycle_app.command("create-policy")
    def create_policy(
        ctx: typer.Context,
        payload_file: Annotated[Path, typer.Option("--payload-file")],
    ) -> None:
        render(ctx, _client(get_client(ctx)).lifecycle.create_policy(_load_payload(payload_file)))

    @lifecycle_app.command("evaluate")
    def evaluate(
        ctx: typer.Context,
        payload_file: Annotated[Path | None, typer.Option("--payload-file")] = None,
        controlled: Annotated[bool, typer.Option("--controlled")] = False,
    ) -> None:
        payload = _load_payload(payload_file)
        payload.setdefault("owner_scope", get_scope(ctx))
        payload.setdefault("mode", "controlled" if controlled else "dry_run")
        render(ctx, _client(get_client(ctx)).lifecycle.evaluate(payload))

    @lifecycle_app.command("classifications")
    def classifications(
        ctx: typer.Context,
        retention_class: Annotated[str | None, typer.Option("--retention-class")] = None,
        lifecycle_state: Annotated[str | None, typer.Option("--lifecycle-state")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).lifecycle.list_classifications(
                get_scope(ctx),
                retention_class=retention_class,
                lifecycle_state=lifecycle_state,
                limit=limit,
            ),
        )

    @lifecycle_app.command("archive-candidates")
    def archive_candidates(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        severity: Annotated[str | None, typer.Option("--severity")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).lifecycle.list_archive_candidates(
                get_scope(ctx),
                status=status,
                severity=severity,
                limit=limit,
            ),
        )

    @lifecycle_app.command("redaction-candidates")
    def redaction_candidates(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        severity: Annotated[str | None, typer.Option("--severity")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).lifecycle.list_redaction_candidates(
                get_scope(ctx),
                status=status,
                severity=severity,
                limit=limit,
            ),
        )

    @lifecycle_app.command("purge-preview")
    def purge_preview(
        ctx: typer.Context,
        resource_uri: Annotated[
            list[str] | None,
            typer.Option("--resource-uri", help="Resource URI. Can be repeated."),
        ] = None,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).lifecycle.create_purge_preview(
                resource_uri or [],
                get_scope(ctx),
            ),
        )

    @lifecycle_app.command("reviews")
    def reviews(
        ctx: typer.Context,
        candidate_type: Annotated[str | None, typer.Option("--candidate-type")] = None,
        decision: Annotated[str | None, typer.Option("--decision")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).lifecycle.list_reviews(
                get_scope(ctx),
                candidate_type=candidate_type,
                decision=decision,
                limit=limit,
            ),
        )

    @lifecycle_app.command("report")
    def report(ctx: typer.Context) -> None:
        render(ctx, _client(get_client(ctx)).lifecycle.report(get_scope(ctx)))


def _load_payload(path: Path | None) -> JSONDict:
    if path is None:
        return {}
    return cast(JSONDict, json.loads(path.read_text()))


def _client(client: object) -> AIONClient:
    return cast(AIONClient, client)


__all__ = ["install_lifecycle_commands"]
