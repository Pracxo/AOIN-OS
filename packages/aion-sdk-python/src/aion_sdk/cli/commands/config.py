"""aionctl runtime configuration commands."""

from __future__ import annotations

from typing import Annotated, Any, cast

import typer

from aion_sdk.client import AIONClient
from aion_sdk.types import JSONDict

config_app = typer.Typer(no_args_is_help=True, help="Runtime configuration commands.")
profile_app = typer.Typer(no_args_is_help=True, help="Config profile commands.")
feature_app = typer.Typer(no_args_is_help=True, help="Feature flag override commands.")


def install_config_commands(
    app: typer.Typer,
    *,
    get_client: Any,
    get_scope: Any,
    render: Any,
) -> None:
    """Install runtime configuration commands onto the root CLI."""

    app.add_typer(config_app, name="config")
    config_app.add_typer(profile_app, name="profile")
    config_app.add_typer(feature_app, name="feature")

    @config_app.command("status")
    def status(ctx: typer.Context) -> None:
        """Return runtime configuration status."""

        render(ctx, _client(get_client(ctx)).runtime_config.status(get_scope(ctx)))

    @config_app.command("validate")
    def validate(ctx: typer.Context) -> None:
        """Run runtime configuration validation."""

        payload: JSONDict = {"owner_scope": get_scope(ctx)}
        render(ctx, _client(get_client(ctx)).runtime_config.validate(payload))

    @config_app.command("snapshot")
    def snapshot(
        ctx: typer.Context,
        snapshot_type: Annotated[str, typer.Option("--type")] = "manual",
    ) -> None:
        """Create a runtime configuration snapshot."""

        payload: JSONDict = {"snapshot_type": snapshot_type, "owner_scope": get_scope(ctx)}
        render(ctx, _client(get_client(ctx)).runtime_config.create_snapshot(payload))

    @config_app.command("snapshots")
    def snapshots(
        ctx: typer.Context,
        snapshot_type: Annotated[str | None, typer.Option("--type")] = None,
    ) -> None:
        """List runtime configuration snapshots."""

        params: JSONDict = {}
        if snapshot_type is not None:
            params["snapshot_type"] = snapshot_type
        render(ctx, _client(get_client(ctx)).get("/brain/runtime-config/snapshots", params=params))

    @config_app.command("compare")
    def compare(
        ctx: typer.Context,
        snapshot_id_a: Annotated[str, typer.Option("--a")],
        snapshot_id_b: Annotated[str, typer.Option("--b")],
    ) -> None:
        """Compare two runtime configuration snapshots."""

        render(
            ctx,
            _client(get_client(ctx)).runtime_config.compare_snapshots(
                snapshot_id_a,
                snapshot_id_b,
            ),
        )

    @profile_app.command("create")
    def profile_create(
        ctx: typer.Context,
        name: Annotated[str, typer.Option("--name")],
        description: Annotated[str, typer.Option("--description")],
        profile_type: Annotated[str, typer.Option("--type")] = "custom",
    ) -> None:
        """Create a runtime configuration profile."""

        payload: JSONDict = {
            "name": name,
            "description": description,
            "profile_type": profile_type,
            "owner_scope": get_scope(ctx),
        }
        render(ctx, _client(get_client(ctx)).runtime_config.create_profile(payload))

    @profile_app.command("list")
    def profile_list(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        profile_type: Annotated[str | None, typer.Option("--type")] = None,
    ) -> None:
        """List runtime configuration profiles."""

        render(
            ctx,
            _client(get_client(ctx)).runtime_config.list_profiles(
                status=status,
                profile_type=profile_type,
            ),
        )

    @feature_app.command("override")
    def feature_override(
        ctx: typer.Context,
        feature_key: Annotated[str, typer.Option("--feature-key")],
        enabled: Annotated[bool, typer.Option("--enabled/--disabled")] = True,
        reason: Annotated[str, typer.Option("--reason")] = "aionctl runtime config override",
    ) -> None:
        """Create a feature flag override."""

        payload: JSONDict = {
            "feature_key": feature_key,
            "enabled": enabled,
            "owner_scope": get_scope(ctx),
            "reason": reason,
        }
        render(ctx, _client(get_client(ctx)).runtime_config.create_feature_override(payload))

    @feature_app.command("list")
    def feature_list(
        ctx: typer.Context,
        feature_key: Annotated[str | None, typer.Option("--feature-key")] = None,
        status: Annotated[str | None, typer.Option("--status")] = None,
    ) -> None:
        """List feature flag overrides."""

        render(
            ctx,
            _client(get_client(ctx)).runtime_config.list_feature_overrides(
                feature_key=feature_key,
                status=status,
            ),
        )


def _client(value: object) -> AIONClient:
    return cast(AIONClient, value)
