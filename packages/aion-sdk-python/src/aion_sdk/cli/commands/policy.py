"""aionctl policy catalog and policy test commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Any, cast

import typer

from aion_sdk.client import AIONClient
from aion_sdk.types import JSONDict

policy_app = typer.Typer(no_args_is_help=True, help="Policy catalog helpers.")
tests_app = typer.Typer(no_args_is_help=True, help="Policy test harness commands.")
bundle_app = typer.Typer(no_args_is_help=True, help="Policy bundle commands.")

policy_app.add_typer(tests_app, name="tests")
policy_app.add_typer(bundle_app, name="bundle")


def install_policy_commands(
    app: typer.Typer,
    *,
    get_client: Any,
    get_scope: Any,
    render: Any,
) -> None:
    """Install policy catalog commands."""

    app.add_typer(policy_app, name="policy")

    @policy_app.command("actions")
    def actions(
        ctx: typer.Context,
        category: Annotated[str | None, typer.Option("--category")] = None,
        status: Annotated[str | None, typer.Option("--status")] = None,
    ) -> None:
        """List policy action catalog entries."""
        render(ctx, _client(get_client(ctx)).policy.list_actions(category=category, status=status))

    @policy_app.command("permissions")
    def permissions(
        ctx: typer.Context,
        category: Annotated[str | None, typer.Option("--category")] = None,
        status: Annotated[str | None, typer.Option("--status")] = None,
    ) -> None:
        """List permission catalog entries."""
        result = _client(get_client(ctx)).policy.list_permissions(
            category=category,
            status=status,
        )
        render(ctx, result)

    @policy_app.command("roles")
    def roles(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
    ) -> None:
        """List role templates."""
        render(ctx, _client(get_client(ctx)).policy.list_roles(status=status))

    @policy_app.command("seed-defaults")
    def seed_defaults(
        ctx: typer.Context,
        dry_run: Annotated[
            bool,
            typer.Option("--dry-run/--apply", help="Preview by default; --apply persists."),
        ] = True,
    ) -> None:
        """Seed default action, permission, and role catalogs."""
        client = _client(get_client(ctx))
        render(
            ctx,
            {
                "actions": client.policy.seed_actions(dry_run=dry_run),
                "roles": client.policy.seed_roles(dry_run=dry_run),
            },
        )

    @policy_app.command("simulate")
    def simulate(
        ctx: typer.Context,
        request_file: Annotated[Path | None, typer.Option("--request-file")] = None,
        action_type: Annotated[str, typer.Option("--action-type")] = "memory.retrieve",
        resource_type: Annotated[str, typer.Option("--resource-type")] = "memory_record",
        risk_level: Annotated[str, typer.Option("--risk-level")] = "low",
    ) -> None:
        """Simulate a policy decision without executing an action."""
        payload = (
            _load_json(request_file)
            if request_file
            else _simulation_payload(
                action_type,
                resource_type,
                risk_level,
                get_scope(ctx),
            )
        )
        render(ctx, _client(get_client(ctx)).policy.simulate(payload))

    @tests_app.command("run")
    def tests_run(
        ctx: typer.Context,
        request_file: Annotated[Path | None, typer.Option("--request-file")] = None,
        dry_run: Annotated[bool, typer.Option("--dry-run/--apply")] = True,
    ) -> None:
        """Run stored policy test cases."""
        payload = _load_json(request_file) if request_file else {"dry_run": dry_run}
        render(ctx, _client(get_client(ctx)).policy.run_tests(payload))

    @policy_app.command("coverage")
    def coverage(ctx: typer.Context) -> None:
        """Return policy coverage."""
        render(ctx, _client(get_client(ctx)).policy.coverage())

    @bundle_app.command("export")
    def bundle_export(
        ctx: typer.Context,
        bundle_type: Annotated[str, typer.Option("--bundle-type")] = "full",
        include_rego: Annotated[bool, typer.Option("--include-rego/--no-rego")] = True,
        include_tests: Annotated[bool, typer.Option("--include-tests/--no-tests")] = True,
    ) -> None:
        """Export a policy governance bundle."""
        payload: JSONDict = {
            "bundle_type": bundle_type,
            "include_catalog": True,
            "include_permissions": True,
            "include_role_templates": True,
            "include_tests": include_tests,
            "include_rego": include_rego,
            "created_by": None,
        }
        render(ctx, _client(get_client(ctx)).policy.export_bundle(payload))

    @policy_app.command("opa-status")
    def opa_status(ctx: typer.Context) -> None:
        """Return OPA adapter status."""
        render(ctx, _client(get_client(ctx)).policy.opa_status())


def _client(value: object) -> AIONClient:
    return cast(AIONClient, value)


def _load_json(path: Path | None) -> JSONDict:
    if path is None:
        return {}
    parsed = json.loads(path.read_text())
    if not isinstance(parsed, dict):
        raise typer.BadParameter("request file must contain a JSON object")
    return cast(JSONDict, parsed)


def _simulation_payload(
    action_type: str,
    resource_type: str,
    risk_level: str,
    scope: list[str],
) -> JSONDict:
    return {
        "action_type": action_type,
        "resource_type": resource_type,
        "resource_id": None,
        "risk_level": risk_level,
        "approval_present": False,
        "requested_permissions": [action_type],
        "security_scope": scope,
        "context": {},
        "metadata": {"source": "aionctl"},
    }
