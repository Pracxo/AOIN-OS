"""aionctl Extension Registry commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Any, cast

import typer

from aion_sdk.client import AIONClient
from aion_sdk.types import JSONDict

extensions_app = typer.Typer(no_args_is_help=True, help="Extension registry commands.")


def install_extension_commands(
    app: typer.Typer,
    *,
    get_client: Any,
    get_scope: Any,
    render: Any,
) -> None:
    """Install Extension Registry commands."""

    app.add_typer(extensions_app, name="extensions")

    @extensions_app.command("validate")
    def validate_manifest(
        ctx: typer.Context,
        manifest_file: Annotated[Path, typer.Option("--manifest-file")],
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).extensions.validate_manifest(_load_payload(manifest_file)),
        )

    @extensions_app.command("intake")
    def intake(
        ctx: typer.Context,
        manifest_file: Annotated[Path, typer.Option("--manifest-file")],
        controlled: Annotated[bool, typer.Option("--controlled")] = False,
        run_compatibility: Annotated[
            bool,
            typer.Option("--compatibility/--no-compatibility"),
        ] = True,
        create_install_plan: Annotated[
            bool,
            typer.Option("--install-plan/--no-install-plan"),
        ] = True,
        create_notifications: Annotated[
            bool,
            typer.Option("--notify/--no-notify"),
        ] = False,
    ) -> None:
        payload: JSONDict = {
            "mode": "controlled" if controlled else "dry_run",
            "owner_scope": get_scope(ctx),
            "manifest": _load_payload(manifest_file),
            "source_type": "local_manifest",
            "source_ref": str(manifest_file),
            "run_compatibility": run_compatibility,
            "create_install_plan": create_install_plan,
            "create_notifications": create_notifications,
            "metadata": {"source": "aionctl"},
        }
        render(ctx, _client(get_client(ctx)).extensions.intake(payload))

    @extensions_app.command("query")
    def query(
        ctx: typer.Context,
        text: Annotated[str | None, typer.Option("--query")] = None,
        status: Annotated[str | None, typer.Option("--status")] = None,
        package_type: Annotated[str | None, typer.Option("--package-type")] = None,
        compatibility_status: Annotated[
            str | None,
            typer.Option("--compatibility-status"),
        ] = None,
        review_status: Annotated[str | None, typer.Option("--review-status")] = None,
        include_deleted: Annotated[bool, typer.Option("--include-deleted")] = False,
        limit: Annotated[int, typer.Option("--limit")] = 50,
    ) -> None:
        payload: JSONDict = {
            "scope": get_scope(ctx),
            "include_deleted": include_deleted,
            "limit": limit,
        }
        if text is not None:
            payload["query"] = text
        if status is not None:
            payload["status"] = status
        if package_type is not None:
            payload["package_type"] = package_type
        if compatibility_status is not None:
            payload["compatibility_status"] = compatibility_status
        if review_status is not None:
            payload["review_status"] = review_status
        render(ctx, _client(get_client(ctx)).extensions.query(payload))

    @extensions_app.command("package")
    def package(
        ctx: typer.Context,
        extension_package_id: Annotated[str, typer.Argument()],
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).extensions.get_package(extension_package_id, get_scope(ctx)),
        )

    @extensions_app.command("capabilities")
    def capabilities(
        ctx: typer.Context,
        extension_package_id: Annotated[str, typer.Argument()],
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).extensions.list_capabilities(
                extension_package_id,
                get_scope(ctx),
            ),
        )

    @extensions_app.command("dependencies")
    def dependencies(
        ctx: typer.Context,
        extension_package_id: Annotated[str, typer.Argument()],
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).extensions.list_dependencies(
                extension_package_id,
                get_scope(ctx),
            ),
        )

    @extensions_app.command("compatibility-check")
    def compatibility_check(
        ctx: typer.Context,
        extension_package_id: Annotated[str, typer.Argument()],
        controlled: Annotated[bool, typer.Option("--controlled")] = False,
    ) -> None:
        payload: JSONDict = {
            "extension_package_id": extension_package_id,
            "mode": "controlled" if controlled else "dry_run",
            "owner_scope": get_scope(ctx),
            "metadata": {"source": "aionctl"},
        }
        render(ctx, _client(get_client(ctx)).extensions.check_compatibility(payload))

    @extensions_app.command("review")
    def review(
        ctx: typer.Context,
        extension_package_id: Annotated[str, typer.Argument()],
        decision: Annotated[str, typer.Option("--decision")],
        reason: Annotated[str, typer.Option("--reason")],
        reviewer_id: Annotated[str | None, typer.Option("--reviewer-id")] = None,
    ) -> None:
        payload: JSONDict = {
            "extension_package_id": extension_package_id,
            "decision": decision,
            "reason": reason,
            "metadata": {"source": "aionctl"},
        }
        if reviewer_id is not None:
            payload["reviewer_id"] = reviewer_id
        render(
            ctx,
            _client(get_client(ctx)).extensions.review_package(
                extension_package_id,
                payload,
                get_scope(ctx),
            ),
        )

    @extensions_app.command("reviews")
    def reviews(
        ctx: typer.Context,
        extension_package_id: Annotated[
            str | None,
            typer.Option("--extension-package-id"),
        ] = None,
        decision: Annotated[str | None, typer.Option("--decision")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).extensions.list_reviews(
                get_scope(ctx),
                extension_package_id=extension_package_id,
                decision=decision,
                limit=limit,
            ),
        )

    @extensions_app.command("install-plan")
    def install_plan(
        ctx: typer.Context,
        extension_package_id: Annotated[str, typer.Argument()],
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).extensions.create_install_plan(
                extension_package_id,
                {"scope": get_scope(ctx)},
            ),
        )

    @extensions_app.command("install-plans")
    def install_plans(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        extension_package_id: Annotated[
            str | None,
            typer.Option("--extension-package-id"),
        ] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).extensions.list_install_plans(
                get_scope(ctx),
                status=status,
                extension_package_id=extension_package_id,
                limit=limit,
            ),
        )


def _load_payload(path: Path) -> JSONDict:
    return cast(JSONDict, json.loads(path.read_text()))


def _client(client: object) -> AIONClient:
    return cast(AIONClient, client)


__all__ = ["install_extension_commands"]
