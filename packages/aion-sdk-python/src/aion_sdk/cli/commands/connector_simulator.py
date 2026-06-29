"""aionctl connector simulator commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Any, cast

import typer

from aion_sdk.client import AIONClient
from aion_sdk.types import JSONDict

connector_simulator_app = typer.Typer(
    no_args_is_help=True,
    help="Synthetic connector dry-run simulator commands.",
)


def install_connector_simulator_commands(
    app: typer.Typer,
    *,
    get_client: Any,
    get_scope: Any,
    render: Any,
) -> None:
    """Install connector-simulator commands."""

    app.add_typer(connector_simulator_app, name="connector-simulator")

    @connector_simulator_app.command("simulate")
    def simulate(
        ctx: typer.Context,
        payload_file: Annotated[Path | None, typer.Option("--payload-file")] = None,
        connector_key: Annotated[str, typer.Option("--connector-key")] = "mock.local.preview",
    ) -> None:
        payload = _load_payload(payload_file)
        payload.setdefault("connector_key", connector_key)
        payload.setdefault("owner_scope", get_scope(ctx))
        payload.setdefault("simulation_type", "dry_run")
        payload.setdefault("request_shape", {"object": "synthetic_request"})
        payload.setdefault("expected_response_shape", {"object": "synthetic_response"})
        payload.setdefault("evidence_refs", ["docs/connectors/connector-dry-run-simulator.md"])
        render(ctx, _client(get_client(ctx)).connector_simulator.simulate(payload))

    @connector_simulator_app.command("replay")
    def replay(
        ctx: typer.Context,
        payload_file: Annotated[Path | None, typer.Option("--payload-file")] = None,
        connector_key: Annotated[str, typer.Option("--connector-key")] = "mock.local.preview",
    ) -> None:
        payload = _load_payload(payload_file)
        payload.setdefault("replay_fixture_id", "connector-replay-fixture-local")
        payload.setdefault("connector_key", connector_key)
        payload.setdefault("name", "Local Synthetic Replay")
        payload.setdefault("description", "Local fixture replay for connector simulator.")
        payload.setdefault("owner_scope", get_scope(ctx))
        payload.setdefault("fixture_type", "synthetic_replay")
        payload.setdefault("request_shape", {"object": "synthetic_request"})
        payload.setdefault("response_shape", {"object": "synthetic_response"})
        payload.setdefault("expected_findings", ["untrusted_ingress"])
        payload.setdefault("synthetic", True)
        payload.setdefault("trusted", False)
        render(ctx, _client(get_client(ctx)).connector_simulator.replay(payload))

    @connector_simulator_app.command("policy-readiness")
    def policy_readiness(
        ctx: typer.Context,
        payload_file: Annotated[Path | None, typer.Option("--payload-file")] = None,
        connector_key: Annotated[str, typer.Option("--connector-key")] = "mock.local.preview",
    ) -> None:
        payload = _load_payload(payload_file)
        payload.setdefault("connector_key", connector_key)
        payload.setdefault("owner_scope", get_scope(ctx))
        payload.setdefault(
            "declared_policy_actions",
            [
                "connector_simulator.simulate",
                "connector_simulator.replay",
                "connector_simulator.policy_readiness",
            ],
        )
        payload.setdefault("declared_scopes", get_scope(ctx))
        payload.setdefault("sandbox_required", True)
        payload.setdefault("audit_required", True)
        payload.setdefault("provenance_required", True)
        render(ctx, _client(get_client(ctx)).connector_simulator.policy_readiness(payload))

    @connector_simulator_app.command("status")
    def status(ctx: typer.Context) -> None:
        render(ctx, _client(get_client(ctx)).connector_simulator.status(get_scope(ctx)))


def _load_payload(path: Path | None) -> JSONDict:
    if path is None:
        return {}
    loaded = json.loads(path.read_text())
    if not isinstance(loaded, dict):
        raise typer.BadParameter("payload file must contain a JSON object")
    return cast(JSONDict, loaded)


def _client(value: object) -> AIONClient:
    return cast(AIONClient, value)


__all__ = ["install_connector_simulator_commands"]
