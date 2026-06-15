"""aionctl scenario harness commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Any, cast

import typer

from aion_sdk.client import AIONClient
from aion_sdk.types import JSONDict

scenarios_app = typer.Typer(no_args_is_help=True, help="Scenario harness helpers.")
fixtures_app = typer.Typer(no_args_is_help=True, help="Demo fixture helpers.")
release_app = typer.Typer(no_args_is_help=True, help="Release baseline helpers.")


def install_scenarios_commands(
    app: typer.Typer,
    *,
    get_client: Any,
    get_scope: Any,
    render: Any,
) -> None:
    """Install scenario harness commands onto the root CLI."""

    app.add_typer(scenarios_app, name="scenarios")
    app.add_typer(fixtures_app, name="demo-fixtures")
    app.add_typer(release_app, name="release-baseline")

    @scenarios_app.command("list")
    def list_scenarios(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        scenario_type: Annotated[str | None, typer.Option("--scenario-type")] = None,
        tag: Annotated[list[str] | None, typer.Option("--tag")] = None,
    ) -> None:
        """List scenario definitions."""

        result = _client(get_client(ctx)).scenarios.list(
            status=status,
            scenario_type=scenario_type,
            tags=tag,
        )
        render(ctx, result)

    @scenarios_app.command("seed-defaults")
    def seed_defaults(
        ctx: typer.Context,
        dry_run: Annotated[bool, typer.Option("--dry-run/--apply")] = True,
    ) -> None:
        """Seed default generic scenarios."""

        result = _client(get_client(ctx)).scenarios.seed_defaults(
            get_scope(ctx),
            dry_run=dry_run,
        )
        render(ctx, result)

    @scenarios_app.command("run")
    def run_scenario(
        ctx: typer.Context,
        scenario_id: Annotated[str | None, typer.Option("--scenario-id")] = None,
        scenario_file: Annotated[Path | None, typer.Option("--scenario-file")] = None,
        dry_run: Annotated[bool, typer.Option("--dry-run/--controlled")] = True,
        fail_fast: Annotated[bool, typer.Option("--fail-fast")] = False,
    ) -> None:
        """Run a scenario in dry-run mode by default."""

        payload: JSONDict = {
            "mode": "dry_run" if dry_run else "controlled",
            "owner_scope": get_scope(ctx),
            "fail_fast": fail_fast,
            "metadata": {"source": "aionctl"},
        }
        if scenario_file is not None:
            payload["scenario"] = _load_json_object(scenario_file)
        elif scenario_id is not None:
            payload["scenario_id"] = scenario_id
        else:
            raise typer.BadParameter("--scenario-id or --scenario-file is required")
        result = _client(get_client(ctx)).scenarios.run(payload)
        render(ctx, result)

    @scenarios_app.command("runs")
    def list_runs(
        ctx: typer.Context,
        status: Annotated[str | None, typer.Option("--status")] = None,
        scenario_type: Annotated[str | None, typer.Option("--scenario-type")] = None,
        limit: Annotated[int, typer.Option("--limit", min=1, max=500)] = 50,
    ) -> None:
        """List scenario runs."""

        result = _client(get_client(ctx)).scenarios.runs(
            scope=get_scope(ctx),
            status=status,
            scenario_type=scenario_type,
            limit=limit,
        )
        render(ctx, result)

    @fixtures_app.command("list")
    def list_fixtures(
        ctx: typer.Context,
        fixture_type: Annotated[str | None, typer.Option("--fixture-type")] = None,
    ) -> None:
        """List generic demo fixtures."""

        result = _client(get_client(ctx)).scenarios.list_fixtures(
            get_scope(ctx),
            fixture_type=fixture_type,
        )
        render(ctx, result)

    @fixtures_app.command("load")
    def load_fixture(
        ctx: typer.Context,
        fixture_id: Annotated[str | None, typer.Option("--fixture-id")] = None,
        fixture_name: Annotated[str | None, typer.Option("--fixture-name")] = None,
        fixture_file: Annotated[Path | None, typer.Option("--fixture-file")] = None,
        dry_run: Annotated[bool, typer.Option("--dry-run/--apply")] = True,
    ) -> None:
        """Load a generic demo fixture."""

        payload: JSONDict = {"owner_scope": get_scope(ctx), "dry_run": dry_run}
        if fixture_file is not None:
            payload["fixture"] = _load_json_object(fixture_file)
        elif fixture_id is not None:
            payload["fixture_id"] = fixture_id
        elif fixture_name is not None:
            payload["fixture_name"] = fixture_name
        else:
            raise typer.BadParameter("--fixture-id, --fixture-name, or --fixture-file is required")
        result = _client(get_client(ctx)).scenarios.load_fixture(payload)
        render(ctx, result)

    @release_app.command("run")
    def run_release_baseline(
        ctx: typer.Context,
        version: Annotated[str, typer.Option("--version")],
        scenario_id: Annotated[list[str] | None, typer.Option("--scenario-id")] = None,
        fail_fast: Annotated[bool, typer.Option("--fail-fast")] = False,
    ) -> None:
        """Run deterministic release baseline checks."""

        payload: JSONDict = {
            "version": version,
            "owner_scope": get_scope(ctx),
            "scenario_ids": scenario_id or [],
            "fail_fast": fail_fast,
            "metadata": {"source": "aionctl"},
        }
        result = _client(get_client(ctx)).scenarios.run_release_baseline(payload)
        render(ctx, result)

    @release_app.command("get")
    def get_release_baseline(
        ctx: typer.Context,
        release_baseline_id: Annotated[str, typer.Option("--release-baseline-id")],
    ) -> None:
        """Return a release baseline report."""

        result = _client(get_client(ctx)).scenarios.get_release_baseline(release_baseline_id)
        render(ctx, result)


def _client(value: object) -> AIONClient:
    return cast(AIONClient, value)


def _load_json_object(path: Path) -> JSONDict:
    parsed = json.loads(path.read_text())
    if not isinstance(parsed, dict):
        raise typer.BadParameter("JSON file must contain an object")
    return cast(JSONDict, parsed)
