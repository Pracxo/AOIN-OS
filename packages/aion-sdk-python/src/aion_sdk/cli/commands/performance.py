"""aionctl performance commands."""

from __future__ import annotations

from typing import Annotated, Any, cast

import typer

from aion_sdk.client import AIONClient
from aion_sdk.types import JSONDict

performance_app = typer.Typer(no_args_is_help=True, help="Performance benchmark commands.")
benchmarks_app = typer.Typer(no_args_is_help=True, help="Benchmark definition commands.")
baselines_app = typer.Typer(no_args_is_help=True, help="Capacity baseline commands.")
regression_app = typer.Typer(no_args_is_help=True, help="Regression comparison commands.")


def install_performance_commands(
    app: typer.Typer,
    *,
    get_client: Any,
    get_scope: Any,
    render: Any,
) -> None:
    """Install performance commands onto the root CLI."""

    app.add_typer(performance_app, name="performance")
    performance_app.add_typer(benchmarks_app, name="benchmarks")
    performance_app.add_typer(baselines_app, name="baselines")
    performance_app.add_typer(regression_app, name="regression")

    @benchmarks_app.command("list")
    def list_benchmarks(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        benchmark_type: Annotated[str | None, typer.Option("--type")] = None,
    ) -> None:
        """List benchmark definitions."""

        render(
            ctx,
            _client(get_client(ctx)).performance.list_benchmarks(
                status=status,
                benchmark_type=benchmark_type,
            ),
        )

    @benchmarks_app.command("seed-defaults")
    def seed_defaults(
        ctx: typer.Context,
        apply: Annotated[
            bool,
            typer.Option("--apply", help="Persist defaults instead of dry-run."),
        ] = False,
    ) -> None:
        """Seed or preview default benchmark definitions."""

        render(
            ctx,
            _client(get_client(ctx)).performance.seed_defaults(
                get_scope(ctx),
                dry_run=not apply,
            ),
        )

    @performance_app.command("run")
    def run_benchmark(
        ctx: typer.Context,
        benchmark_id: Annotated[str | None, typer.Option("--benchmark-id")] = None,
        benchmark_type: Annotated[str, typer.Option("--type")] = "smoke",
        repeat: Annotated[int, typer.Option("--repeat")] = 1,
    ) -> None:
        """Run a deterministic local benchmark."""

        payload: JSONDict
        if benchmark_id:
            payload = {
                "benchmark_id": benchmark_id,
                "owner_scope": get_scope(ctx),
                "mode": "dry_run",
                "repeat": repeat,
            }
        else:
            payload = {
                "benchmark": _inline_benchmark(benchmark_type, get_scope(ctx)),
                "owner_scope": get_scope(ctx),
                "mode": "dry_run",
                "repeat": repeat,
            }
        render(ctx, _client(get_client(ctx)).performance.run_benchmark(payload))

    @performance_app.command("summary")
    def summary(
        ctx: typer.Context,
        operation_type: Annotated[str | None, typer.Option("--operation-type")] = None,
        window: Annotated[str | None, typer.Option("--window")] = None,
    ) -> None:
        """Show local performance summary."""

        render(
            ctx,
            _client(get_client(ctx)).performance.summary(
                get_scope(ctx),
                operation_type=operation_type,
                window=window,
            ),
        )

    @baselines_app.command("create")
    def create_baseline(
        ctx: typer.Context,
        benchmark_run_id: Annotated[
            list[str] | None,
            typer.Option("--run-id", help="Benchmark run id. Repeatable."),
        ] = None,
        version: Annotated[str, typer.Option("--version")] = "0.1.0",
        name: Annotated[str, typer.Option("--name")] = "local-baseline",
    ) -> None:
        """Create a capacity baseline from benchmark runs."""

        payload: JSONDict = {
            "version": version,
            "baseline_name": name,
            "benchmark_run_ids": benchmark_run_id or [],
        }
        render(ctx, _client(get_client(ctx)).performance.create_baseline(payload))

    @baselines_app.command("list")
    def list_baselines(
        ctx: typer.Context,
        version: Annotated[str | None, typer.Option("--version")] = None,
        status: Annotated[str | None, typer.Option("--status")] = None,
    ) -> None:
        """List capacity baselines."""

        render(
            ctx,
            _client(get_client(ctx)).performance.list_baselines(
                version=version,
                status=status,
            ),
        )

    @regression_app.command("compare")
    def compare_regression(
        ctx: typer.Context,
        benchmark_run_id: Annotated[str, typer.Option("--run-id")],
        baseline_id: Annotated[str, typer.Option("--baseline-id")],
    ) -> None:
        """Compare benchmark run to baseline."""

        render(
            ctx,
            _client(get_client(ctx)).performance.compare_regression(
                benchmark_run_id,
                baseline_id,
            ),
        )


def _inline_benchmark(benchmark_type: str, scope: list[str]) -> JSONDict:
    operation = "noop" if benchmark_type == "smoke" else "health"
    return {
        "benchmark_id": f"cli-{benchmark_type}",
        "name": f"CLI {benchmark_type} benchmark",
        "description": "Local deterministic benchmark generated by aionctl.",
        "status": "active",
        "benchmark_type": benchmark_type,
        "owner_scope": scope,
        "steps": [
            {
                "step_id": operation,
                "operation_type": operation,
                "description": "Local deterministic operation.",
                "repeat": 1,
                "expected_status": "passed",
                "required": True,
            }
        ],
        "thresholds": {"default_threshold_ms": 1000},
        "metadata": {"local_only": True, "external_calls": False},
    }


def _client(value: object) -> AIONClient:
    return cast(AIONClient, value)
