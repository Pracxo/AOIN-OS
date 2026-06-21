"""aionctl resource registry commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Any, cast

import typer

from aion_sdk.client import AIONClient
from aion_sdk.types import JSONDict

registry_app = typer.Typer(no_args_is_help=True, help="Resource registry commands.")


def install_registry_commands(
    app: typer.Typer,
    *,
    get_client: Any,
    get_scope: Any,
    render: Any,
) -> None:
    """Install registry commands."""

    app.add_typer(registry_app, name="registry")

    @registry_app.command("query")
    def query(
        ctx: typer.Context,
        text: Annotated[str | None, typer.Option("--query")] = None,
        resource_type: Annotated[str | None, typer.Option("--resource-type")] = None,
        source_system: Annotated[str | None, typer.Option("--source-system")] = None,
        status: Annotated[str | None, typer.Option("--status")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 50,
    ) -> None:
        payload: JSONDict = {"scope": get_scope(ctx), "limit": limit}
        if text is not None:
            payload["query"] = text
        if resource_type is not None:
            payload["resource_type"] = resource_type
        if source_system is not None:
            payload["source_system"] = source_system
        if status is not None:
            payload["status"] = status
        render(ctx, _client(get_client(ctx)).registry.query(payload))

    @registry_app.command("get")
    def get_resource(
        ctx: typer.Context,
        resource_uri: Annotated[str | None, typer.Option("--uri")] = None,
        resource_type: Annotated[str | None, typer.Option("--resource-type")] = None,
        resource_id: Annotated[str | None, typer.Option("--resource-id")] = None,
    ) -> None:
        client = _client(get_client(ctx)).registry
        if resource_uri:
            render(ctx, client.get_by_uri(resource_uri, get_scope(ctx)))
            return
        if not resource_type or not resource_id:
            raise typer.BadParameter("--resource-type and --resource-id are required without --uri")
        render(ctx, client.get_resource(resource_type, resource_id, get_scope(ctx)))

    @registry_app.command("upsert")
    def upsert(
        ctx: typer.Context,
        payload_file: Annotated[Path, typer.Option("--payload-file")],
    ) -> None:
        render(ctx, _client(get_client(ctx)).registry.upsert_resource(_load_payload(payload_file)))

    @registry_app.command("links")
    def links(
        ctx: typer.Context,
        source_uri: Annotated[str | None, typer.Option("--source-uri")] = None,
        target_uri: Annotated[str | None, typer.Option("--target-uri")] = None,
        relation_type: Annotated[str | None, typer.Option("--relation-type")] = None,
        status: Annotated[str | None, typer.Option("--status")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).registry.list_links(
                get_scope(ctx),
                source_uri=source_uri,
                target_uri=target_uri,
                relation_type=relation_type,
                status=status,
                limit=limit,
            ),
        )

    @registry_app.command("link")
    def link(
        ctx: typer.Context,
        payload_file: Annotated[Path, typer.Option("--payload-file")],
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).registry.create_link(
                _load_payload(payload_file), get_scope(ctx)
            ),
        )

    @registry_app.command("backlinks")
    def backlinks(
        ctx: typer.Context,
        resource_uri: Annotated[str, typer.Option("--uri")],
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).registry.list_backlinks(
                resource_uri,
                get_scope(ctx),
                limit=limit,
            ),
        )

    @registry_app.command("validate")
    def validate(
        ctx: typer.Context,
        payload_file: Annotated[Path | None, typer.Option("--payload-file")] = None,
        controlled: Annotated[bool, typer.Option("--controlled")] = False,
    ) -> None:
        payload = _load_payload(payload_file)
        payload.setdefault("owner_scope", get_scope(ctx))
        payload.setdefault("mode", "controlled" if controlled else "dry_run")
        render(ctx, _client(get_client(ctx)).registry.validate(payload))

    @registry_app.command("broken")
    def broken(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        severity: Annotated[str | None, typer.Option("--severity")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).registry.list_broken_references(
                get_scope(ctx),
                status=status,
                severity=severity,
                limit=limit,
            ),
        )

    @registry_app.command("orphaned")
    def orphaned(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        severity: Annotated[str | None, typer.Option("--severity")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).registry.list_orphaned_resources(
                get_scope(ctx),
                status=status,
                severity=severity,
                limit=limit,
            ),
        )

    @registry_app.command("rebuild")
    def rebuild(
        ctx: typer.Context,
        payload_file: Annotated[Path | None, typer.Option("--payload-file")] = None,
        controlled: Annotated[bool, typer.Option("--controlled")] = False,
    ) -> None:
        payload = _load_payload(payload_file)
        payload.setdefault("owner_scope", get_scope(ctx))
        payload.setdefault("mode", "controlled" if controlled else "dry_run")
        render(ctx, _client(get_client(ctx)).registry.rebuild(payload))

    @registry_app.command("snapshot")
    def snapshot(
        ctx: typer.Context,
        snapshot_type: Annotated[str, typer.Option("--snapshot-type")] = "manual",
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).registry.create_snapshot(
                {"scope": get_scope(ctx), "snapshot_type": snapshot_type}
            ),
        )

    @registry_app.command("snapshots")
    def snapshots(
        ctx: typer.Context,
        snapshot_type: Annotated[str | None, typer.Option("--snapshot-type")] = None,
        status: Annotated[str | None, typer.Option("--status")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 50,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).registry.list_snapshots(
                get_scope(ctx),
                snapshot_type=snapshot_type,
                status=status,
                limit=limit,
            ),
        )


def _load_payload(path: Path | None) -> JSONDict:
    if path is None:
        return {}
    return cast(JSONDict, json.loads(path.read_text()))


def _client(client: object) -> AIONClient:
    return cast(AIONClient, client)


__all__ = ["install_registry_commands"]
