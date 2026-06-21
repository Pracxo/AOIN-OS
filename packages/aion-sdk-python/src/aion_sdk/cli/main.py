"""Command line interface for AION Brain."""

from __future__ import annotations

import json as json_module
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Any, cast
from uuid import uuid4

import typer
from rich.console import Console

from aion_sdk.cli.commands.action_proposals import install_action_proposal_commands
from aion_sdk.cli.commands.audit import install_audit_commands
from aion_sdk.cli.commands.backups import install_backup_commands
from aion_sdk.cli.commands.beliefs import install_belief_commands
from aion_sdk.cli.commands.concepts import install_concept_commands
from aion_sdk.cli.commands.config import install_config_commands
from aion_sdk.cli.commands.decisions import install_decision_commands
from aion_sdk.cli.commands.dialogue import install_dialogue_commands
from aion_sdk.cli.commands.entities import install_entity_commands
from aion_sdk.cli.commands.explanations import install_explanation_commands
from aion_sdk.cli.commands.grounding import install_grounding_commands
from aion_sdk.cli.commands.instructions import install_instruction_commands
from aion_sdk.cli.commands.learning import install_learning_commands
from aion_sdk.cli.commands.model_outputs import install_model_output_commands
from aion_sdk.cli.commands.modules import install_modules_commands
from aion_sdk.cli.commands.operator import install_operator_commands
from aion_sdk.cli.commands.outcomes import install_outcome_commands
from aion_sdk.cli.commands.performance import install_performance_commands
from aion_sdk.cli.commands.policy import install_policy_commands
from aion_sdk.cli.commands.prompts import install_prompt_commands
from aion_sdk.cli.commands.release import install_release_commands
from aion_sdk.cli.commands.resilience import install_resilience_commands
from aion_sdk.cli.commands.sandbox import install_sandbox_commands
from aion_sdk.cli.commands.scenarios import install_scenarios_commands
from aion_sdk.cli.commands.security import install_security_commands
from aion_sdk.cli.commands.self_model import install_self_model_commands
from aion_sdk.cli.commands.situations import install_situation_commands
from aion_sdk.cli.commands.versioning import install_versioning_commands
from aion_sdk.client import AIONClient
from aion_sdk.config import AIONClientConfig
from aion_sdk.errors import AIONNotFoundError, AIONSDKError
from aion_sdk.types import JSONDict, JSONValue

console = Console()

app = typer.Typer(no_args_is_help=True, help="AION Brain developer CLI.")
kernel_app = typer.Typer(no_args_is_help=True, help="Kernel diagnostics.")
bootstrap_app = typer.Typer(no_args_is_help=True, help="Developer bootstrap helpers.")
events_app = typer.Typer(no_args_is_help=True, help="Event intake helpers.")
memory_app = typer.Typer(no_args_is_help=True, help="Memory helpers.")
commands_app = typer.Typer(no_args_is_help=True, help="Command Bus helpers.")
workflows_app = typer.Typer(no_args_is_help=True, help="Workflow helpers.")
autonomy_app = typer.Typer(no_args_is_help=True, help="Autonomy helpers.")
smoke_app = typer.Typer(no_args_is_help=True, help="Smoke test helpers.")
contracts_app = typer.Typer(no_args_is_help=True, help="Contract export helpers.")

app.add_typer(kernel_app, name="kernel")
app.add_typer(bootstrap_app, name="bootstrap")
app.add_typer(events_app, name="events")
app.add_typer(memory_app, name="memory")
app.add_typer(commands_app, name="commands")
app.add_typer(workflows_app, name="workflows")
app.add_typer(autonomy_app, name="autonomy")
app.add_typer(smoke_app, name="smoke")
app.add_typer(contracts_app, name="contracts")


def make_client(config: AIONClientConfig) -> AIONClient:
    """Factory kept separate for tests."""

    return AIONClient(config)


@app.callback()
def main(
    ctx: typer.Context,
    base_url: Annotated[
        str | None,
        typer.Option("--base-url", help="AION Brain base URL."),
    ] = None,
    actor_id: Annotated[
        str | None,
        typer.Option("--actor-id", help="Development actor id."),
    ] = None,
    workspace_id: Annotated[
        str | None,
        typer.Option("--workspace-id", help="Development workspace id."),
    ] = None,
    scope: Annotated[
        list[str] | None,
        typer.Option("--scope", help="Security scope. Can be passed multiple times."),
    ] = None,
    trace_id: Annotated[
        str | None,
        typer.Option("--trace-id", help="Trace id header."),
    ] = None,
    correlation_id: Annotated[
        str | None,
        typer.Option("--correlation-id", help="Correlation id header."),
    ] = None,
    idempotency_key: Annotated[
        str | None,
        typer.Option("--idempotency-key", help="Idempotency key header."),
    ] = None,
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Emit raw JSON."),
    ] = False,
) -> None:
    """Configure SDK access for aionctl commands."""

    config = AIONClientConfig.from_env().with_overrides(
        base_url=base_url,
        actor_id=actor_id,
        workspace_id=workspace_id,
        security_scope=scope,
        trace_id=trace_id,
        correlation_id=correlation_id,
        idempotency_key=idempotency_key,
    )
    ctx.obj = {"config": config, "json": json_output}


@app.command()
def health(ctx: typer.Context) -> None:
    """Return `/health`."""

    _render(ctx, _client(ctx).health.health())


@app.command()
def ready(ctx: typer.Context) -> None:
    """Return `/health/ready`."""

    _render(ctx, _client(ctx).health.ready())


@kernel_app.command("status")
def kernel_status(ctx: typer.Context) -> None:
    """Return kernel status."""

    _render(ctx, _client(ctx).kernel.status())


@kernel_app.command("self-test")
def kernel_self_test(
    ctx: typer.Context,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run/--no-dry-run", help="Run without external side effects."),
    ] = True,
) -> None:
    """Run deterministic kernel self-test."""

    scope = _scope(ctx)
    _render(ctx, _client(ctx).kernel.self_test(scope=scope, dry_run=dry_run))


@kernel_app.command("contracts")
def kernel_contracts(ctx: typer.Context) -> None:
    """Return contract export."""

    _render(ctx, _client(ctx).kernel.contracts())


@kernel_app.command("boundary-check")
def kernel_boundary_check(ctx: typer.Context) -> None:
    """Run architecture boundary check."""

    _render(ctx, _client(ctx).kernel.boundary_check())


@bootstrap_app.command("dev")
def bootstrap_dev(
    ctx: typer.Context,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run/--apply",
            help="Inspect by default; --apply creates safe dev records.",
        ),
    ] = True,
    set_run_level: Annotated[
        bool,
        typer.Option("--set-run-level", help="Set a bounded dry-run autonomy level."),
    ] = False,
    run_level: Annotated[
        str,
        typer.Option("--run-level", help="Bounded autonomy mode to set when requested."),
    ] = "dry_run",
) -> None:
    """Bootstrap a local developer context through public APIs only."""

    client = _client(ctx)
    config = _config(ctx)
    summary: JSONDict = {
        "dry_run": dry_run,
        "base_url": config.base_url,
        "actor_id": config.actor_id,
        "workspace_id": config.workspace_id,
        "created": [],
        "checked": [],
        "warnings": [],
        "autonomy_run_level_set": False,
    }
    _inspect_or_create_actor(client, config, summary, dry_run)
    _inspect_or_create_workspace(client, config, summary, dry_run)
    summary["me"] = _safe_call(lambda: client.get("/brain/me"), summary)
    summary["kernel_self_test"] = _safe_call(
        lambda: client.kernel.self_test(scope=_scope(ctx), dry_run=True),
        summary,
    )
    if set_run_level:
        if run_level not in {"disabled", "observe", "assist", "plan_only", "dry_run"}:
            raise typer.BadParameter("bootstrap only supports bounded non-controlled run levels")
        payload: JSONDict = {
            "actor_id": config.actor_id,
            "workspace_id": config.workspace_id,
            "run_level": run_level,
            "reason": "aionctl developer bootstrap",
            "constraints": ["developer_bootstrap", "no_external_side_effects"],
            "metadata": {"source": "aionctl"},
        }
        if dry_run:
            summary["planned_run_level"] = payload
        else:
            summary["run_level"] = client.autonomy.set_run_level(payload)
            summary["autonomy_run_level_set"] = True
    _render(ctx, summary)


@events_app.command("send")
def events_send(
    ctx: typer.Context,
    event_json: Annotated[
        str | None,
        typer.Option("--event-json", help="JSON object for AIONEvent."),
    ] = None,
    event_file: Annotated[
        Path | None,
        typer.Option("--event-file", help="File containing an AIONEvent JSON object."),
    ] = None,
) -> None:
    """Send a normalized event."""

    event = _load_json_object(event_json, event_file)
    _render(ctx, _client(ctx).events.ingest(event, idempotency_key=_config(ctx).idempotency_key))


@memory_app.command("retrieve")
def memory_retrieve(
    ctx: typer.Context,
    query: Annotated[str, typer.Argument(help="Lexical or semantic recall query.")],
    limit: Annotated[int, typer.Option("--limit", min=1, max=1000)] = 10,
) -> None:
    """Retrieve memory records."""

    _render(ctx, _client(ctx).memory.retrieve(query, scope=_scope(ctx), limit=limit))


@commands_app.command("dispatch")
def commands_dispatch(
    ctx: typer.Context,
    command_type: Annotated[str, typer.Option("--command-type")] = "noop",
    target_type: Annotated[str, typer.Option("--target-type")] = "noop",
    target_id: Annotated[str | None, typer.Option("--target-id")] = None,
    mode: Annotated[str, typer.Option("--mode")] = "dry_run",
    payload_json: Annotated[str | None, typer.Option("--payload-json")] = None,
) -> None:
    """Dispatch one generic Brain command."""

    if mode != "dry_run":
        raise typer.BadParameter("aionctl dispatch defaults to dry_run and rejects live modes")
    payload: JSONDict = {
        "command_type": command_type,
        "target_type": target_type,
        "target_id": target_id,
        "mode": mode,
        "owner_scope": _scope(ctx),
        "payload": (
            _load_inline_json_object(payload_json) if payload_json else {"source": "aionctl"}
        ),
        "approval_present": False,
    }
    _render(ctx, _client(ctx).commands.dispatch(payload, idempotency_key=_idempotency(ctx)))


@workflows_app.command("status")
def workflows_status(ctx: typer.Context) -> None:
    """Return workflow engine status."""

    _render(ctx, _client(ctx).workflows.status())


@autonomy_app.command("status")
def autonomy_status(ctx: typer.Context) -> None:
    """Return autonomy status."""

    config = _config(ctx)
    _render(
        ctx,
        _client(ctx).autonomy.status(
            scope=_scope(ctx),
            actor_id=config.actor_id,
            workspace_id=config.workspace_id,
        ),
    )


@smoke_app.command("run")
def smoke_run(ctx: typer.Context) -> None:
    """Run a side-effect-safe local smoke sequence."""

    client = _client(ctx)
    smoke_id = uuid4().hex
    results: list[JSONDict] = []
    critical_failure = False

    def step(name: str, action: Any, *, critical: bool = True) -> None:
        nonlocal critical_failure
        try:
            results.append({"name": name, "status": "ok", "result": action()})
        except AIONSDKError as exc:
            results.append({"name": name, "status": "fail", "error": str(exc)})
            critical_failure = critical_failure or critical

    step("health", client.health.health)
    step("kernel_status", client.kernel.status)
    step("kernel_self_test", lambda: client.kernel.self_test(scope=_scope(ctx), dry_run=True))
    step("autonomy_status", lambda: client.autonomy.status(scope=_scope(ctx)), critical=False)
    step(
        "event_ingest",
        lambda: client.events.ingest(
            _generic_event(smoke_id, _scope(ctx)),
            idempotency_key=f"aionctl-smoke-event-{smoke_id}",
        ),
        critical=False,
    )
    step(
        "noop_command",
        lambda: client.commands.dispatch(
            {
                "command_type": "noop",
                "target_type": "noop",
                "mode": "dry_run",
                "owner_scope": _scope(ctx),
                "payload": {"smoke_id": smoke_id},
                "approval_present": False,
            },
            idempotency_key=f"aionctl-smoke-command-{smoke_id}",
        ),
        critical=False,
    )
    step(
        "visual_map",
        lambda: client.visual.map({"scope": _scope(ctx), "limit": 25, "include_pulses": False}),
        critical=False,
    )
    payload: JSONDict = {"status": "failed" if critical_failure else "ok", "steps": results}
    _render(ctx, payload)
    if critical_failure:
        raise typer.Exit(code=1)


@contracts_app.command("export")
def contracts_export(
    ctx: typer.Context,
    output: Annotated[Path, typer.Option("--output", help="Contract JSON output path.")],
    openapi_output: Annotated[
        Path | None,
        typer.Option("--openapi-output", help="Optional OpenAPI JSON output path."),
    ] = None,
) -> None:
    """Export contracts from `/brain/kernel/contracts`."""

    export = _client(ctx).kernel.contracts()
    if not isinstance(export, dict):
        raise typer.BadParameter("contract export response was not an object")
    _write_json(output, export)
    if openapi_output is not None:
        openapi = export.get("openapi", {})
        if not isinstance(openapi, dict):
            openapi = {}
        _write_json(openapi_output, openapi)
    _render(ctx, {"exported": True, "output": str(output), "openapi_output": str(openapi_output)})


def _client(ctx: typer.Context) -> AIONClient:
    return make_client(_config(ctx))


def _state(ctx: typer.Context) -> dict[str, Any]:
    if not isinstance(ctx.obj, dict):
        ctx.obj = {"config": AIONClientConfig.from_env(), "json": False}
    return cast(dict[str, Any], ctx.obj)


def _config(ctx: typer.Context) -> AIONClientConfig:
    config = _state(ctx).get("config")
    if isinstance(config, AIONClientConfig):
        return config
    return AIONClientConfig.from_env()


def _scope(ctx: typer.Context) -> list[str]:
    scope = _config(ctx).security_scope
    return scope or ["workspace:main"]


def _idempotency(ctx: typer.Context) -> str | None:
    return _config(ctx).idempotency_key


def _render(ctx: typer.Context, payload: JSONValue) -> None:
    if bool(_state(ctx).get("json", False)):
        typer.echo(json_module.dumps(payload, indent=2, sort_keys=True, default=str))
        return
    if isinstance(payload, (dict, list)):
        console.print_json(json_module.dumps(payload, default=str))
    else:
        console.print(str(payload))


def _load_json_object(event_json: str | None, event_file: Path | None) -> JSONDict:
    if event_json and event_file:
        raise typer.BadParameter("pass either --event-json or --event-file, not both")
    if event_file is not None:
        return _load_inline_json_object(event_file.read_text())
    if event_json:
        return _load_inline_json_object(event_json)
    raise typer.BadParameter("event JSON is required")


def _load_inline_json_object(raw: str) -> JSONDict:
    try:
        parsed = json_module.loads(raw)
    except json_module.JSONDecodeError as exc:
        raise typer.BadParameter(f"invalid JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise typer.BadParameter("JSON value must be an object")
    return cast(JSONDict, parsed)


def _write_json(path: Path, payload: JSONValue) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json_module.dumps(payload, indent=2, sort_keys=True, default=str) + "\n")


def _generic_event(smoke_id: str, scope: list[str]) -> JSONDict:
    timestamp = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    return {
        "event_id": f"aionctl-smoke-{smoke_id}",
        "source": "aionctl",
        "event_type": "test.received",
        "payload_type": "test.payload",
        "payload": {"smoke_id": smoke_id, "dry_run": True},
        "timestamp": timestamp,
        "security_scope": scope,
    }


def _safe_call(action: Any, summary: JSONDict) -> JSONValue:
    try:
        return cast(JSONValue, action())
    except AIONSDKError as exc:
        warnings = summary.get("warnings")
        if isinstance(warnings, list):
            warnings.append(str(exc))
        return {"available": False, "error": str(exc)}


def _inspect_or_create_actor(
    client: AIONClient,
    config: AIONClientConfig,
    summary: JSONDict,
    dry_run: bool,
) -> None:
    if not config.actor_id:
        return
    try:
        client.get(f"/brain/identity/actors/{config.actor_id}")
        _append(summary, "checked", "actor")
    except AIONNotFoundError:
        if dry_run:
            _append(summary, "warnings", f"actor_missing:{config.actor_id}")
            return
        client.post(
            "/brain/identity/actors",
            json={
                "actor_id": config.actor_id,
                "actor_type": "user",
                "display_name": config.actor_id,
                "status": "active",
                "metadata": {"source": "aionctl"},
            },
        )
        _append(summary, "created", "actor")


def _inspect_or_create_workspace(
    client: AIONClient,
    config: AIONClientConfig,
    summary: JSONDict,
    dry_run: bool,
) -> None:
    if not config.workspace_id:
        return
    try:
        client.get(f"/brain/workspaces/{config.workspace_id}")
        _append(summary, "checked", "workspace")
    except AIONNotFoundError:
        if dry_run:
            _append(summary, "warnings", f"workspace_missing:{config.workspace_id}")
            return
        client.post(
            "/brain/workspaces",
            json={
                "workspace_id": config.workspace_id,
                "name": config.workspace_id,
                "status": "active",
                "owner_actor_id": config.actor_id,
                "metadata": {"source": "aionctl"},
            },
        )
        _append(summary, "created", "workspace")


def _append(summary: JSONDict, key: str, value: str) -> None:
    existing = summary.setdefault(key, [])
    if isinstance(existing, list):
        existing.append(value)


install_modules_commands(app, get_client=_client, get_scope=_scope, render=_render)
install_sandbox_commands(app, get_client=_client, get_scope=_scope, render=_render)
install_policy_commands(app, get_client=_client, get_scope=_scope, render=_render)
install_scenarios_commands(app, get_client=_client, get_scope=_scope, render=_render)
install_versioning_commands(app, get_client=_client, get_scope=_scope, render=_render)
install_release_commands(app, get_client=_client, get_scope=_scope, render=_render)
install_backup_commands(app, get_client=_client, get_scope=_scope, render=_render)
install_performance_commands(app, get_client=_client, get_scope=_scope, render=_render)
install_security_commands(app, get_client=_client, get_scope=_scope, render=_render)
install_config_commands(app, get_client=_client, get_scope=_scope, render=_render)
install_resilience_commands(app, get_client=_client, get_scope=_scope, render=_render)
install_audit_commands(app, get_client=_client, get_scope=_scope, render=_render)
install_operator_commands(app, get_client=_client, get_scope=_scope, render=_render)
install_dialogue_commands(app, get_client=_client, get_scope=_scope, render=_render)
install_belief_commands(app, get_client=_client, get_scope=_scope, render=_render)
install_concept_commands(app, get_client=_client, get_scope=_scope, render=_render)
install_entity_commands(app, get_client=_client, get_scope=_scope, render=_render)
install_situation_commands(app, get_client=_client, get_scope=_scope, render=_render)
install_decision_commands(app, get_client=_client, get_scope=_scope, render=_render)
install_outcome_commands(app, get_client=_client, get_scope=_scope, render=_render)
install_learning_commands(app, get_client=_client, get_scope=_scope, render=_render)
install_self_model_commands(app, get_client=_client, get_scope=_scope, render=_render)
install_explanation_commands(app, get_client=_client, get_scope=_scope, render=_render)
install_instruction_commands(app, get_client=_client, get_scope=_scope, render=_render)
install_grounding_commands(app, get_client=_client, get_scope=_scope, render=_render)
install_prompt_commands(app, get_client=_client, get_scope=_scope, render=_render)
install_model_output_commands(app, get_client=_client, get_scope=_scope, render=_render)
install_action_proposal_commands(app, get_client=_client, get_scope=_scope, render=_render)


if __name__ == "__main__":
    app()
