"""aionctl release package commands."""

from __future__ import annotations

from typing import Annotated, Any, cast

import typer

from aion_sdk.client import AIONClient
from aion_sdk.types import JSONDict

release_app = typer.Typer(no_args_is_help=True, help="Release handoff helpers.")
package_app = typer.Typer(
    invoke_without_command=True,
    no_args_is_help=False,
    help="Local release package commands.",
)


def install_release_commands(
    app: typer.Typer,
    *,
    get_client: Any,
    get_scope: Any,
    render: Any,
) -> None:
    """Install release package commands onto the root CLI."""

    app.add_typer(release_app, name="release")
    release_app.add_typer(package_app, name="package")

    @package_app.callback()
    def create_package(
        ctx: typer.Context,
        version: Annotated[str | None, typer.Option("--version")] = None,
        output_dir: Annotated[str, typer.Option("--output-dir")] = "artifacts/releases",
        dry_run: Annotated[bool, typer.Option("--dry-run/--write")] = True,
    ) -> None:
        """Create or dry-run a local release package."""

        if ctx.invoked_subcommand is not None:
            return
        if version is None:
            raise typer.BadParameter("--version is required")
        payload: JSONDict = {
            "version": version,
            "owner_scope": get_scope(ctx),
            "output_dir": output_dir,
            "dry_run": dry_run,
        }
        render(ctx, _client(get_client(ctx)).release.create_package(payload))

    @package_app.command("get")
    def get_package(
        ctx: typer.Context,
        package_id: Annotated[str, typer.Option("--id", help="Release package id.")],
    ) -> None:
        """Get one release package."""

        render(ctx, _client(get_client(ctx)).release.get_package(package_id, get_scope(ctx)))

    @package_app.command("list")
    def list_packages(
        ctx: typer.Context,
        version: Annotated[str | None, typer.Option("--version")] = None,
        status: Annotated[str | None, typer.Option("--status")] = None,
    ) -> None:
        """List release packages."""

        render(
            ctx,
            _client(get_client(ctx)).release.list_packages(
                scope=get_scope(ctx),
                version=version,
                status=status,
            ),
        )

    @package_app.command("validate")
    def validate_package(
        ctx: typer.Context,
        package_id: Annotated[str, typer.Option("--id", help="Release package id.")],
    ) -> None:
        """Return package validation."""

        render(ctx, _client(get_client(ctx)).release.validate_package(package_id, get_scope(ctx)))

    @package_app.command("handoff")
    def handoff(
        ctx: typer.Context,
        package_id: Annotated[str, typer.Option("--id", help="Release package id.")],
    ) -> None:
        """Return final handoff report."""

        render(ctx, _client(get_client(ctx)).release.handoff(package_id, get_scope(ctx)))


def _client(value: object) -> AIONClient:
    return cast(AIONClient, value)
