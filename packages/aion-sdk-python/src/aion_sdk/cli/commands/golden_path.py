"""aionctl golden path commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Any, cast

import typer

from aion_sdk.client import AIONClient
from aion_sdk.types import JSONDict

golden_path_app = typer.Typer(no_args_is_help=True, help="Golden path harness commands.")
scenarios_app = typer.Typer(
    no_args_is_help=False,
    invoke_without_command=True,
    help="Golden path scenario commands.",
)
fixtures_app = typer.Typer(
    no_args_is_help=False,
    invoke_without_command=True,
    help="Golden path fixture commands.",
)


def install_golden_path_commands(
    app: typer.Typer,
    *,
    get_client: Any,
    get_scope: Any,
    render: Any,
) -> None:
    """Install golden path commands."""

    app.add_typer(golden_path_app, name="golden-path")
    golden_path_app.add_typer(scenarios_app, name="scenarios")
    golden_path_app.add_typer(fixtures_app, name="fixtures")

    @scenarios_app.callback()
    def scenarios(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        scenario_type: Annotated[str | None, typer.Option("--scenario-type")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        """List golden path scenarios."""

        if ctx.invoked_subcommand is None:
            render(
                ctx,
                _client(get_client(ctx)).golden_path.list_scenarios(
                    get_scope(ctx),
                    status=status,
                    scenario_type=scenario_type,
                    limit=limit,
                ),
            )

    @scenarios_app.command("seed")
    def seed_scenarios(
        ctx: typer.Context,
        dry_run: Annotated[
            bool,
            typer.Option("--dry-run/--apply", help="Preview by default; --apply persists."),
        ] = True,
    ) -> None:
        """Seed default golden path scenarios."""

        render(
            ctx,
            _client(get_client(ctx)).golden_path.seed_default_scenarios(
                get_scope(ctx),
                dry_run=dry_run,
            ),
        )

    @fixtures_app.callback()
    def fixtures(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 100,
    ) -> None:
        """List golden path fixture packs."""

        if ctx.invoked_subcommand is None:
            render(
                ctx,
                _client(get_client(ctx)).golden_path.list_fixtures(
                    get_scope(ctx),
                    status=status,
                    limit=limit,
                ),
            )

    @fixtures_app.command("seed")
    def seed_fixtures(
        ctx: typer.Context,
        dry_run: Annotated[
            bool,
            typer.Option("--dry-run/--apply", help="Preview by default; --apply persists."),
        ] = True,
    ) -> None:
        """Seed default synthetic fixture packs."""

        render(
            ctx,
            _client(get_client(ctx)).golden_path.seed_default_fixtures(
                get_scope(ctx),
                dry_run=dry_run,
            ),
        )

    @golden_path_app.command("run")
    def run_golden_path(
        ctx: typer.Context,
        payload_file: Annotated[Path | None, typer.Option("--payload-file")] = None,
        scenario_key: Annotated[
            list[str] | None,
            typer.Option("--scenario-key", help="Scenario key. Can be repeated."),
        ] = None,
        dry_run: Annotated[
            bool,
            typer.Option("--dry-run/--controlled", help="Run in dry-run mode by default."),
        ] = True,
    ) -> None:
        """Run deterministic golden path scenarios."""

        payload = _load_payload(payload_file)
        payload.setdefault("owner_scope", get_scope(ctx))
        payload.setdefault("mode", "dry_run" if dry_run else "controlled")
        if scenario_key:
            payload["scenario_keys"] = scenario_key
            payload["run_all_defaults"] = False
        render(ctx, _client(get_client(ctx)).golden_path.run(payload))

    @golden_path_app.command("runs")
    def runs(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        trace_id: Annotated[str | None, typer.Option("--trace-id")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 50,
    ) -> None:
        """List golden path runs."""

        render(
            ctx,
            _client(get_client(ctx)).golden_path.list_runs(
                get_scope(ctx),
                status=status,
                trace_id=trace_id,
                limit=limit,
            ),
        )

    @golden_path_app.command("reports")
    def reports(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 50,
    ) -> None:
        """List golden path reports."""

        render(
            ctx,
            _client(get_client(ctx)).golden_path.list_reports(
                get_scope(ctx),
                status=status,
                limit=limit,
            ),
        )

    @golden_path_app.command("release-smoke")
    def release_smoke(ctx: typer.Context) -> None:
        """Run local release smoke matrix."""

        render(ctx, _client(get_client(ctx)).golden_path.release_smoke(get_scope(ctx)))

    @golden_path_app.command("query")
    def query(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        scenario_type: Annotated[str | None, typer.Option("--scenario-type")] = None,
        trace_id: Annotated[str | None, typer.Option("--trace-id")] = None,
        limit: Annotated[int, typer.Option("--limit")] = 50,
    ) -> None:
        """Query golden path records."""

        payload: JSONDict = {
            "scope": get_scope(ctx),
            "status": status,
            "scenario_type": scenario_type,
            "trace_id": trace_id,
            "limit": limit,
        }
        render(ctx, _client(get_client(ctx)).golden_path.query(payload))


def _client(value: Any) -> AIONClient:
    return cast(AIONClient, value)


def _load_payload(path: Path | None) -> JSONDict:
    if path is None:
        return {}
    return cast(JSONDict, json.loads(path.read_text()))


__all__ = ["install_golden_path_commands"]
