"""aionctl conformance and readiness commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Any, cast

import typer

from aion_sdk.client import AIONClient
from aion_sdk.types import JSONDict

conformance_app = typer.Typer(no_args_is_help=True, help="Conformance harness commands.")
profiles_app = typer.Typer(
    no_args_is_help=False,
    invoke_without_command=True,
    help="Conformance profile commands.",
)
test_vectors_app = typer.Typer(
    no_args_is_help=False,
    invoke_without_command=True,
    help="Capability test vector commands.",
)
readiness_app = typer.Typer(no_args_is_help=True, help="Extension readiness commands.")


def install_conformance_commands(
    app: typer.Typer,
    *,
    get_client: Any,
    get_scope: Any,
    render: Any,
) -> None:
    """Install conformance and readiness commands."""

    app.add_typer(conformance_app, name="conformance")
    app.add_typer(readiness_app, name="readiness")
    conformance_app.add_typer(profiles_app, name="profiles")
    conformance_app.add_typer(test_vectors_app, name="test-vectors")

    @profiles_app.callback()
    def profiles(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        profile_type: Annotated[str | None, typer.Option("--profile-type")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        """List conformance profiles."""

        if ctx.invoked_subcommand is None:
            render(
                ctx,
                _client(get_client(ctx)).conformance.list_profiles(
                    get_scope(ctx),
                    status=status,
                    profile_type=profile_type,
                    limit=limit,
                ),
            )

    @profiles_app.command("seed")
    def seed_profiles(
        ctx: typer.Context,
        dry_run: Annotated[
            bool,
            typer.Option("--dry-run/--apply", help="Preview by default; --apply persists."),
        ] = True,
    ) -> None:
        """Seed default generic conformance profiles."""

        render(
            ctx,
            _client(get_client(ctx)).conformance.seed_default_profiles(
                get_scope(ctx),
                dry_run=dry_run,
            ),
        )

    @test_vectors_app.callback()
    def test_vectors(
        ctx: typer.Context,
        capability_binding_id: Annotated[
            str | None,
            typer.Option("--capability-binding-id"),
        ] = None,
        status: Annotated[str | None, typer.Option("--status")] = None,
        vector_type: Annotated[str | None, typer.Option("--vector-type")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        """List capability test vectors."""

        if ctx.invoked_subcommand is None:
            render(
                ctx,
                _client(get_client(ctx)).conformance.list_test_vectors(
                    get_scope(ctx),
                    capability_binding_id=capability_binding_id,
                    status=status,
                    vector_type=vector_type,
                    limit=limit,
                ),
            )

    @test_vectors_app.command("generate")
    def generate_test_vectors(
        ctx: typer.Context,
        capability_binding_id: Annotated[str, typer.Argument()],
    ) -> None:
        """Generate schema vectors for a capability binding."""

        render(
            ctx,
            _client(get_client(ctx)).conformance.generate_test_vectors(
                capability_binding_id,
                get_scope(ctx),
            ),
        )

    @conformance_app.command("run")
    def run_conformance(
        ctx: typer.Context,
        payload_file: Annotated[Path | None, typer.Option("--payload-file")] = None,
        capability_binding_id: Annotated[
            str | None,
            typer.Option("--capability-binding-id"),
        ] = None,
        module_slot_id: Annotated[str | None, typer.Option("--module-slot-id")] = None,
        extension_package_id: Annotated[str | None, typer.Option("--extension-package-id")] = None,
        dry_run: Annotated[
            bool,
            typer.Option("--dry-run/--controlled", help="Run in dry-run mode by default."),
        ] = True,
    ) -> None:
        """Run deterministic conformance checks."""

        payload = _load_payload(payload_file)
        payload.setdefault("owner_scope", get_scope(ctx))
        payload.setdefault("mode", "dry_run" if dry_run else "controlled")
        _set(payload, "capability_binding_id", capability_binding_id)
        _set(payload, "module_slot_id", module_slot_id)
        _set(payload, "extension_package_id", extension_package_id)
        render(ctx, _client(get_client(ctx)).conformance.run(payload))

    @conformance_app.command("findings")
    def findings(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        severity: Annotated[str | None, typer.Option("--severity")] = None,
        finding_type: Annotated[str | None, typer.Option("--finding-type")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        """List conformance findings."""

        render(
            ctx,
            _client(get_client(ctx)).conformance.list_findings(
                get_scope(ctx),
                status=status,
                severity=severity,
                finding_type=finding_type,
                limit=limit,
            ),
        )

    @conformance_app.command("query")
    def query(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        capability_binding_id: Annotated[
            str | None,
            typer.Option("--capability-binding-id"),
        ] = None,
        module_slot_id: Annotated[str | None, typer.Option("--module-slot-id")] = None,
        extension_package_id: Annotated[str | None, typer.Option("--extension-package-id")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 50,
    ) -> None:
        """Query conformance records."""

        payload: JSONDict = {
            "scope": get_scope(ctx),
            "status": status,
            "capability_binding_id": capability_binding_id,
            "module_slot_id": module_slot_id,
            "extension_package_id": extension_package_id,
            "limit": limit,
        }
        render(ctx, _client(get_client(ctx)).conformance.query(payload))

    @readiness_app.command("assess")
    def assess_readiness(
        ctx: typer.Context,
        payload_file: Annotated[Path | None, typer.Option("--payload-file")] = None,
        capability_binding_id: Annotated[
            str | None,
            typer.Option("--capability-binding-id"),
        ] = None,
        module_slot_id: Annotated[str | None, typer.Option("--module-slot-id")] = None,
        extension_package_id: Annotated[str | None, typer.Option("--extension-package-id")] = None,
    ) -> None:
        """Assess extension readiness without activation."""

        payload = _load_payload(payload_file)
        payload.setdefault("owner_scope", get_scope(ctx))
        _set(payload, "capability_binding_id", capability_binding_id)
        _set(payload, "module_slot_id", module_slot_id)
        _set(payload, "extension_package_id", extension_package_id)
        render(ctx, _client(get_client(ctx)).conformance.assess_readiness(payload))

    @readiness_app.command("list")
    def readiness_list(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        readiness_level: Annotated[str | None, typer.Option("--readiness-level")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        """List readiness assessments."""

        render(
            ctx,
            _client(get_client(ctx)).conformance.list_readiness_assessments(
                get_scope(ctx),
                status=status,
                readiness_level=readiness_level,
                limit=limit,
            ),
        )


def _client(value: Any) -> AIONClient:
    return cast(AIONClient, value)


def _load_payload(path: Path | None) -> JSONDict:
    if path is None:
        return {}
    return cast(JSONDict, json.loads(path.read_text()))


def _set(payload: JSONDict, key: str, value: object | None) -> None:
    if value is not None:
        payload[key] = value


__all__ = ["install_conformance_commands"]
