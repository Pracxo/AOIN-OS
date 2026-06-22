"""aionctl module mock runtime commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Any, cast

import typer

from aion_sdk.client import AIONClient
from aion_sdk.types import JSONDict

module_mock_runtime_app = typer.Typer(
    no_args_is_help=True,
    help="Deterministic module mock runtime dry-run commands.",
)


def install_module_mock_runtime_commands(
    app: typer.Typer,
    *,
    get_client: Any,
    get_scope: Any,
    render: Any,
) -> None:
    """Install module mock runtime commands."""

    app.add_typer(module_mock_runtime_app, name="module-mock")
    app.add_typer(module_mock_runtime_app, name="module-mock-runtime")

    @module_mock_runtime_app.command("seed-profiles")
    def seed_profiles(
        ctx: typer.Context,
        persist: Annotated[
            bool,
            typer.Option("--apply", help="Persist default profiles. Dry-run by default."),
        ] = False,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).module_mock_runtime.seed_profiles(
                {"scope": get_scope(ctx), "dry_run": not persist}
            ),
        )

    @module_mock_runtime_app.command("create-profile")
    def create_profile(
        ctx: typer.Context,
        profile_key: Annotated[str, typer.Argument()],
        name: Annotated[str, typer.Option("--name")] = "Generic Mock Profile",
        description: Annotated[str, typer.Option("--description")] = (
            "Deterministic synthetic module mock profile."
        ),
        profile_type: Annotated[str, typer.Option("--profile-type")] = "generic",
        payload_file: Annotated[Path | None, typer.Option("--payload-file")] = None,
    ) -> None:
        payload = _load_payload(payload_file)
        payload.setdefault("profile_key", profile_key)
        payload.setdefault("name", name)
        payload.setdefault("description", description)
        payload.setdefault("profile_type", profile_type)
        payload.setdefault("owner_scope", get_scope(ctx))
        render(ctx, _client(get_client(ctx)).module_mock_runtime.create_profile(payload))

    @module_mock_runtime_app.command("profiles")
    def list_profiles(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        profile_type: Annotated[str | None, typer.Option("--profile-type")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).module_mock_runtime.list_profiles(
                get_scope(ctx),
                status=status,
                profile_type=profile_type,
                limit=limit,
            ),
        )

    @module_mock_runtime_app.command("invoke")
    def invoke(
        ctx: typer.Context,
        capability_binding_id: Annotated[str, typer.Argument()],
        capability_key: Annotated[str, typer.Option("--capability-key")],
        payload_file: Annotated[Path | None, typer.Option("--payload-file")] = None,
        invocation_type: Annotated[str, typer.Option("--invocation-type")] = "schema_simulation",
    ) -> None:
        payload = _load_payload(payload_file)
        payload.setdefault("capability_binding_id", capability_binding_id)
        payload.setdefault("capability_key", capability_key)
        payload.setdefault("invocation_type", invocation_type)
        payload.setdefault("mode", "dry_run")
        payload.setdefault("owner_scope", get_scope(ctx))
        render(ctx, _client(get_client(ctx)).module_mock_runtime.invoke(payload))

    @module_mock_runtime_app.command("runs")
    def list_runs(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        capability_binding_id: Annotated[
            str | None,
            typer.Option("--capability-binding-id"),
        ] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).module_mock_runtime.list_runs(
                get_scope(ctx),
                status=status,
                capability_binding_id=capability_binding_id,
                limit=limit,
            ),
        )

    @module_mock_runtime_app.command("outputs")
    def list_outputs(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        module_mock_run_id: Annotated[
            str | None,
            typer.Option("--module-mock-run-id"),
        ] = None,
        capability_binding_id: Annotated[
            str | None,
            typer.Option("--capability-binding-id"),
        ] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).module_mock_runtime.outputs(
                get_scope(ctx),
                status=status,
                module_mock_run_id=module_mock_run_id,
                capability_binding_id=capability_binding_id,
                limit=limit,
            ),
        )

    @module_mock_runtime_app.command("findings")
    def list_findings(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = "open",
        severity: Annotated[str | None, typer.Option("--severity")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        render(
            ctx,
            _client(get_client(ctx)).module_mock_runtime.list_findings(
                get_scope(ctx),
                status=status,
                severity=severity,
                limit=limit,
            ),
        )

    @module_mock_runtime_app.command("query")
    def query(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        capability_binding_id: Annotated[
            str | None,
            typer.Option("--capability-binding-id"),
        ] = None,
        limit: Annotated[int, typer.Option("--limit")] = 50,
    ) -> None:
        payload: JSONDict = {
            "scope": get_scope(ctx),
            "status": status,
            "capability_binding_id": capability_binding_id,
            "limit": limit,
        }
        render(ctx, _client(get_client(ctx)).module_mock_runtime.query(payload))


def _client(value: Any) -> AIONClient:
    return cast(AIONClient, value)


def _load_payload(path: Path | None) -> JSONDict:
    if path is None:
        return {}
    return cast(JSONDict, json.loads(path.read_text()))


__all__ = ["install_module_mock_runtime_commands"]
