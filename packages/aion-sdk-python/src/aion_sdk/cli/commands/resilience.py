"""aionctl resilience commands."""

from __future__ import annotations

from typing import Annotated, Any, cast

import typer

from aion_sdk.client import AIONClient
from aion_sdk.types import JSONDict

resilience_app = typer.Typer(no_args_is_help=True, help="Resilience control-plane commands.")
dependencies_app = typer.Typer(no_args_is_help=True, help="Dependency health commands.")
retry_policies_app = typer.Typer(no_args_is_help=True, help="Retry policy commands.")
circuit_breakers_app = typer.Typer(no_args_is_help=True, help="Circuit breaker commands.")
degraded_app = typer.Typer(no_args_is_help=True, help="Degraded mode commands.")
fault_rules_app = typer.Typer(no_args_is_help=True, help="Fault injection rule commands.")
test_app = typer.Typer(no_args_is_help=True, help="Resilience test commands.")


def install_resilience_commands(
    app: typer.Typer,
    *,
    get_client: Any,
    get_scope: Any,
    render: Any,
) -> None:
    """Install resilience commands onto the root CLI."""

    app.add_typer(resilience_app, name="resilience")
    resilience_app.add_typer(dependencies_app, name="dependencies")
    resilience_app.add_typer(retry_policies_app, name="retry-policies")
    resilience_app.add_typer(circuit_breakers_app, name="circuit-breakers")
    resilience_app.add_typer(degraded_app, name="degraded")
    resilience_app.add_typer(fault_rules_app, name="fault-rules")
    resilience_app.add_typer(test_app, name="test")

    @resilience_app.command("status")
    def status(ctx: typer.Context) -> None:
        """Show local resilience status."""

        render(ctx, _client(get_client(ctx)).resilience.status(get_scope(ctx)))

    @dependencies_app.command("check")
    def check_dependencies(ctx: typer.Context) -> None:
        """Run bounded dependency health checks."""

        render(ctx, _client(get_client(ctx)).resilience.check_dependencies(get_scope(ctx)))

    @dependencies_app.command("list")
    def list_dependencies(
        ctx: typer.Context,
        dependency_type: Annotated[str | None, typer.Option("--type")] = None,
        component: Annotated[str | None, typer.Option("--component")] = None,
    ) -> None:
        """List latest dependency health records."""

        render(
            ctx,
            _client(get_client(ctx)).resilience.list_dependencies(
                dependency_type=dependency_type,
                component=component,
            ),
        )

    @retry_policies_app.command("seed")
    def seed_retry_policies(
        ctx: typer.Context,
        apply: Annotated[
            bool,
            typer.Option("--apply", help="Persist defaults instead of dry-run."),
        ] = False,
    ) -> None:
        """Seed or preview default retry policies."""

        render(
            ctx,
            _client(get_client(ctx)).resilience.seed_retry_policies(
                dry_run=not apply,
            ),
        )

    @retry_policies_app.command("list")
    def list_retry_policies(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        target_type: Annotated[str | None, typer.Option("--target-type")] = None,
    ) -> None:
        """List retry policies."""

        render(
            ctx,
            _client(get_client(ctx)).resilience.list_retry_policies(
                status=status,
                target_type=target_type,
            ),
        )

    @circuit_breakers_app.command("list")
    def list_circuit_breakers(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        target_type: Annotated[str | None, typer.Option("--target-type")] = None,
    ) -> None:
        """List circuit breakers."""

        render(
            ctx,
            _client(get_client(ctx)).resilience.list_circuit_breakers(
                status=status,
                target_type=target_type,
            ),
        )

    @degraded_app.command("list")
    def list_degraded(
        ctx: typer.Context,
        component: Annotated[str | None, typer.Option("--component")] = None,
    ) -> None:
        """List active degraded mode events."""

        render(ctx, _client(get_client(ctx)).resilience.list_degraded(component))

    @fault_rules_app.command("list")
    def list_fault_rules(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        target_type: Annotated[str | None, typer.Option("--target-type")] = None,
    ) -> None:
        """List fault injection rules."""

        render(
            ctx,
            _client(get_client(ctx)).resilience.list_fault_rules(
                status=status,
                target_type=target_type,
            ),
        )

    @test_app.command("run")
    def run_test(
        ctx: typer.Context,
        mode: Annotated[str, typer.Option("--mode")] = "dry_run",
    ) -> None:
        """Run deterministic resilience readiness test."""

        payload: JSONDict = {
            "owner_scope": get_scope(ctx),
            "mode": mode,
            "include_fault_injection": False,
        }
        render(ctx, _client(get_client(ctx)).resilience.run_test(payload))


def _client(value: object) -> AIONClient:
    return cast(AIONClient, value)
