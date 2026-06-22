"""aionctl versioning and freeze gate commands."""

from __future__ import annotations

from typing import Annotated, Any, cast

import typer

from aion_sdk.client import AIONClient
from aion_sdk.types import JSONDict

versioning_app = typer.Typer(no_args_is_help=True, help="Version manifest helpers.")
manifest_app = typer.Typer(no_args_is_help=True, help="Version manifest commands.")
features_app = typer.Typer(no_args_is_help=True, help="Feature registry commands.")
compatibility_app = typer.Typer(no_args_is_help=True, help="Compatibility matrix commands.")
freeze_app = typer.Typer(no_args_is_help=True, help="Freeze gate commands.")


def install_versioning_commands(
    app: typer.Typer,
    *,
    get_client: Any,
    get_scope: Any,
    render: Any,
) -> None:
    """Install versioning and freeze gate commands onto the root CLI."""

    app.add_typer(versioning_app, name="versioning")
    app.add_typer(freeze_app, name="freeze")
    versioning_app.add_typer(manifest_app, name="manifests")
    versioning_app.add_typer(features_app, name="features")
    versioning_app.add_typer(compatibility_app, name="compatibility")

    @manifest_app.command("create")
    def create_manifest(
        ctx: typer.Context,
        version: Annotated[str, typer.Option("--version")],
        created_by: Annotated[str | None, typer.Option("--created-by")] = None,
    ) -> None:
        """Create a version manifest."""

        payload: JSONDict = {
            "version": version,
            "scope": get_scope(ctx),
            "created_by": created_by,
        }
        render(ctx, _client(get_client(ctx)).versioning.create_manifest(payload))

    @manifest_app.command("get")
    def get_manifest(
        ctx: typer.Context,
        version: Annotated[str, typer.Option("--version")],
    ) -> None:
        """Get the latest manifest for a version."""

        render(ctx, _client(get_client(ctx)).versioning.get_manifest(version))

    @manifest_app.command("list")
    def list_manifests(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        limit: Annotated[int, typer.Option("--limit", min=1, max=500)] = 50,
    ) -> None:
        """List manifests."""

        render(ctx, _client(get_client(ctx)).versioning.list_manifests(status=status, limit=limit))

    @manifest_app.command("freeze")
    def freeze_manifest(
        ctx: typer.Context,
        version: Annotated[str, typer.Option("--version")],
        reason: Annotated[str, typer.Option("--reason")] = "v0.1 freeze gate passed",
        frozen_by: Annotated[str | None, typer.Option("--frozen-by")] = None,
    ) -> None:
        """Freeze a manifest after a passing freeze gate."""

        payload: JSONDict = {
            "owner_scope": get_scope(ctx),
            "reason": reason,
            "actor_id": frozen_by,
        }
        render(ctx, _client(get_client(ctx)).versioning.freeze_manifest(version, payload))

    @features_app.command("seed-defaults")
    def seed_features(
        ctx: typer.Context,
        dry_run: Annotated[bool, typer.Option("--dry-run/--apply")] = True,
    ) -> None:
        """Seed the generic feature registry."""

        render(ctx, _client(get_client(ctx)).versioning.seed_features(get_scope(ctx), dry_run))

    @features_app.command("list")
    def list_features(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        category: Annotated[str | None, typer.Option("--category")] = None,
    ) -> None:
        """List feature registry entries."""

        render(
            ctx,
            _client(get_client(ctx)).versioning.list_features(
                scope=get_scope(ctx),
                status=status,
                category=category,
            ),
        )

    @features_app.command("deprecate")
    def deprecate_feature(
        ctx: typer.Context,
        feature_key: Annotated[str, typer.Option("--feature-key")],
        reason: Annotated[str, typer.Option("--reason")] = "replaced by later versioning policy",
    ) -> None:
        """Deprecate a feature registry entry."""

        render(
            ctx,
            _client(get_client(ctx)).versioning.deprecate_feature(
                feature_key,
                get_scope(ctx),
                reason,
            ),
        )

    @compatibility_app.command("generate")
    def generate_compatibility(
        ctx: typer.Context,
        version: Annotated[str, typer.Option("--version")],
    ) -> None:
        """Generate the local compatibility matrix."""

        render(
            ctx,
            _client(get_client(ctx)).versioning.generate_compatibility(version, get_scope(ctx)),
        )

    @compatibility_app.command("get")
    def get_compatibility(
        ctx: typer.Context,
        version: Annotated[str, typer.Option("--version")],
    ) -> None:
        """Get the compatibility matrix for a version."""

        render(ctx, _client(get_client(ctx)).versioning.get_compatibility(version))

    @versioning_app.command("migration-baseline")
    def generate_migration_baseline(
        ctx: typer.Context,
        version: Annotated[str, typer.Option("--version")],
    ) -> None:
        """Generate the migration baseline."""

        render(
            ctx,
            _client(get_client(ctx)).versioning.generate_migration_baseline(
                version,
                get_scope(ctx),
            ),
        )

    @versioning_app.command("release-artifacts")
    def generate_release_artifacts(
        ctx: typer.Context,
        version: Annotated[str, typer.Option("--version")],
        created_by: Annotated[str | None, typer.Option("--created-by")] = None,
    ) -> None:
        """Generate the release artifact manifest."""

        render(
            ctx,
            _client(get_client(ctx)).versioning.generate_release_artifacts(
                version,
                get_scope(ctx),
                created_by=created_by,
            ),
        )

    @versioning_app.command("sdk-compatibility")
    def sdk_compatibility(ctx: typer.Context) -> None:
        """Check SDK/API compatibility."""

        render(ctx, _client(get_client(ctx)).versioning.sdk_compatibility(get_scope(ctx)))

    @freeze_app.command("run")
    def run_freeze_gate(
        ctx: typer.Context,
        version: Annotated[str, typer.Option("--version")],
        dry_run: Annotated[bool, typer.Option("--dry-run/--apply")] = True,
    ) -> None:
        """Run the deterministic freeze gate."""

        payload: JSONDict = {
            "version": version,
            "owner_scope": get_scope(ctx),
            "dry_run": dry_run,
        }
        render(ctx, _client(get_client(ctx)).versioning.run_freeze_gate(payload))

    @freeze_app.command("get")
    def get_freeze_gate(
        ctx: typer.Context,
        freeze_gate_id: Annotated[str, typer.Option("--freeze-gate-id")],
    ) -> None:
        """Get a freeze gate run."""

        render(ctx, _client(get_client(ctx)).versioning.get_freeze_gate(freeze_gate_id))

    @freeze_app.command("list")
    def list_freeze_gates(
        ctx: typer.Context,
        version: Annotated[str | None, typer.Option("--version")] = None,
        status: Annotated[str | None, typer.Option("--status")] = None,
    ) -> None:
        """List freeze gate runs."""

        render(
            ctx,
            _client(get_client(ctx)).versioning.list_freeze_gates(
                scope=get_scope(ctx),
                version=version,
                status=status,
            ),
        )


def _client(value: object) -> AIONClient:
    return cast(AIONClient, value)
