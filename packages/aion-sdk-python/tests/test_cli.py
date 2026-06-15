from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from typer.testing import CliRunner

from aion_sdk.cli import main as cli_main
from aion_sdk.config import AIONClientConfig

runner = CliRunner()


class FakeHealth:
    def health(self) -> dict[str, str]:
        return {"status": "ok", "service": "aion-brain-api", "version": "0.1.0"}

    def ready(self) -> dict[str, object]:
        return {"status": "ready", "checks": {"postgres": "ok"}}


class FakeKernel:
    def __init__(self) -> None:
        self.self_test_payloads: list[tuple[list[str], bool]] = []

    def status(self) -> dict[str, str]:
        return {"status": "ready"}

    def self_test(self, scope: list[str] | None = None, *, dry_run: bool = True) -> dict[str, Any]:
        self.self_test_payloads.append((scope or [], dry_run))
        return {"status": "passed", "scope": scope, "dry_run": dry_run}

    def contracts(self) -> dict[str, object]:
        return {"export_id": "export-1", "contracts": {"AIONEvent": {}}, "openapi": {"paths": {}}}

    def boundary_check(self) -> dict[str, str]:
        return {"status": "passed"}


class FakeEvents:
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    def ingest(
        self,
        event: dict[str, Any],
        *,
        idempotency_key: str | None = None,
    ) -> dict[str, object]:
        self.events.append(event)
        return {
            "status": "accepted",
            "event_id": event["event_id"],
            "idempotency_key": idempotency_key,
        }


class FakeMemory:
    def retrieve(
        self,
        query: str,
        *,
        scope: list[str],
        limit: int = 10,
        memory_types: list[str] | None = None,
    ) -> list[dict[str, object]]:
        return [
            {
                "query": query,
                "scope": scope,
                "limit": limit,
                "memory_types": memory_types or [],
            }
        ]


class FakeCommands:
    def __init__(self) -> None:
        self.requests: list[dict[str, Any]] = []

    def dispatch(
        self,
        request: dict[str, Any],
        *,
        idempotency_key: str | None = None,
    ) -> dict[str, object]:
        self.requests.append(request)
        return {"message": "accepted", "request": request, "idempotency_key": idempotency_key}


class FakeWorkflows:
    def status(self) -> dict[str, str]:
        return {"status": "ready"}


class FakeAutonomy:
    def __init__(self) -> None:
        self.run_levels: list[dict[str, Any]] = []

    def status(
        self,
        *,
        scope: list[str] | None = None,
        actor_id: str | None = None,
        workspace_id: str | None = None,
    ) -> dict[str, object]:
        return {
            "effective_mode": "assist",
            "scope": scope,
            "actor_id": actor_id,
            "workspace_id": workspace_id,
        }

    def set_run_level(self, request: dict[str, Any]) -> dict[str, object]:
        self.run_levels.append(request)
        return {"run_level": request["run_level"]}


class FakeApprovals:
    def inbox(self, **kwargs: Any) -> list[dict[str, Any]]:
        return [{"kwargs": kwargs}]


class FakeVisual:
    def map(self, request: dict[str, Any]) -> dict[str, object]:
        return {"map_id": "map-1", "request": request}


class FakePolicy:
    def list_actions(
        self,
        *,
        category: str | None = None,
        status: str | None = None,
    ) -> list[dict[str, object]]:
        return [{"action_type": "policy.catalog.read", "category": category, "status": status}]

    def list_permissions(
        self,
        *,
        category: str | None = None,
        status: str | None = None,
    ) -> list[dict[str, object]]:
        return [{"permission": "policy.read", "category": category, "status": status}]

    def list_roles(self, *, status: str | None = None) -> list[dict[str, object]]:
        return [{"role_name": "viewer", "status": status}]

    def seed_actions(self, *, dry_run: bool = True) -> dict[str, object]:
        return {"dry_run": dry_run, "action_count": 1}

    def seed_roles(self, *, dry_run: bool = True) -> dict[str, object]:
        return {"dry_run": dry_run, "role_template_count": 1}

    def simulate(self, request: dict[str, Any]) -> dict[str, object]:
        return {"simulation_id": "simulation-1", "request": request}

    def run_tests(self, request: dict[str, Any]) -> dict[str, object]:
        return {"policy_test_run_id": "run-1", "request": request}

    def coverage(self) -> dict[str, object]:
        return {"status": "passed"}

    def export_bundle(self, request: dict[str, Any]) -> dict[str, object]:
        return {"policy_bundle_id": "bundle-1", "request": request}

    def opa_status(self) -> dict[str, object]:
        return {"available": True}


class FakeClient:
    def __init__(self, config: AIONClientConfig) -> None:
        self.config = config
        self.health = FakeHealth()
        self.kernel = FakeKernel()
        self.events = FakeEvents()
        self.memory = FakeMemory()
        self.commands = FakeCommands()
        self.workflows = FakeWorkflows()
        self.autonomy = FakeAutonomy()
        self.approvals = FakeApprovals()
        self.visual = FakeVisual()
        self.policy = FakePolicy()
        self.get_paths: list[str] = []
        self.post_paths: list[tuple[str, dict[str, Any] | None]] = []

    def get(self, path: str) -> dict[str, object]:
        self.get_paths.append(path)
        if path == "/brain/me":
            return {"actor_id": self.config.actor_id or "dev"}
        return {"path": path}

    def post(self, path: str, *, json: dict[str, Any] | None = None) -> dict[str, object]:
        self.post_paths.append((path, json))
        return {"path": path, "json": json or {}}


def _install_fake(monkeypatch) -> FakeClient:  # type: ignore[no-untyped-def]
    holder: dict[str, FakeClient] = {}

    def factory(config: AIONClientConfig) -> FakeClient:
        client = FakeClient(config)
        holder["client"] = client
        return client

    monkeypatch.setattr(cli_main, "make_client", factory)
    return holder.setdefault("client", FakeClient(AIONClientConfig()))


def _json(result) -> Any:  # type: ignore[no-untyped-def]
    return json.loads(result.stdout)


def test_cli_health_json(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    _install_fake(monkeypatch)

    result = runner.invoke(cli_main.app, ["--json", "health"])

    assert result.exit_code == 0
    assert _json(result)["status"] == "ok"


def test_cli_kernel_self_test_scope(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    _install_fake(monkeypatch)

    result = runner.invoke(
        cli_main.app,
        ["--json", "--scope", "workspace:main", "kernel", "self-test"],
    )

    assert result.exit_code == 0
    assert _json(result)["scope"] == ["workspace:main"]
    assert _json(result)["dry_run"] is True


def test_cli_events_send(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    _install_fake(monkeypatch)
    event = {
        "event_id": "event-1",
        "source": "test",
        "event_type": "test.received",
        "payload_type": "test.payload",
        "payload": {},
        "timestamp": "2026-06-12T00:00:00Z",
        "security_scope": ["workspace:main"],
    }

    result = runner.invoke(
        cli_main.app,
        ["--json", "events", "send", "--event-json", json.dumps(event)],
    )

    assert result.exit_code == 0
    assert _json(result)["event_id"] == "event-1"


def test_cli_memory_retrieve(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    _install_fake(monkeypatch)

    result = runner.invoke(
        cli_main.app,
        ["--json", "--scope", "workspace:main", "memory", "retrieve", "remember"],
    )

    assert result.exit_code == 0
    assert _json(result)[0]["query"] == "remember"


def test_cli_command_dispatch_rejects_live_mode(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    _install_fake(monkeypatch)

    result = runner.invoke(cli_main.app, ["commands", "dispatch", "--mode", "controlled"])

    assert result.exit_code != 0
    assert "rejects live modes" in result.output


def test_cli_bootstrap_dev_is_bounded(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    _install_fake(monkeypatch)

    result = runner.invoke(
        cli_main.app,
        [
            "--json",
            "--actor-id",
            "dev",
            "--workspace-id",
            "main",
            "bootstrap",
            "dev",
            "--set-run-level",
        ],
    )

    assert result.exit_code == 0
    payload = _json(result)
    assert payload["dry_run"] is True
    assert payload["planned_run_level"]["run_level"] == "dry_run"
    assert payload["planned_run_level"]["metadata"]["source"] == "aionctl"


def test_cli_contracts_export(monkeypatch, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    _install_fake(monkeypatch)
    output = tmp_path / "contracts" / "aion-contracts.json"
    openapi = tmp_path / "openapi" / "openapi.json"

    result = runner.invoke(
        cli_main.app,
        [
            "--json",
            "contracts",
            "export",
            "--output",
            str(output),
            "--openapi-output",
            str(openapi),
        ],
    )

    assert result.exit_code == 0
    assert json.loads(output.read_text())["export_id"] == "export-1"
    assert json.loads(openapi.read_text()) == {"paths": {}}


def test_cli_smoke_run(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    _install_fake(monkeypatch)

    result = runner.invoke(cli_main.app, ["--json", "smoke", "run"])

    assert result.exit_code == 0
    payload = _json(result)
    assert payload["status"] == "ok"
    assert [step["name"] for step in payload["steps"]][0] == "health"


def test_cli_policy_actions(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    _install_fake(monkeypatch)

    result = runner.invoke(cli_main.app, ["--json", "policy", "actions"])

    assert result.exit_code == 0
    assert _json(result)[0]["action_type"] == "policy.catalog.read"


def test_cli_policy_seed_defaults(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    _install_fake(monkeypatch)

    result = runner.invoke(cli_main.app, ["--json", "policy", "seed-defaults", "--apply"])

    assert result.exit_code == 0
    payload = _json(result)
    assert payload["actions"]["dry_run"] is False
    assert payload["roles"]["dry_run"] is False


def test_cli_policy_simulate(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    _install_fake(monkeypatch)

    result = runner.invoke(
        cli_main.app,
        ["--json", "--scope", "workspace:main", "policy", "simulate"],
    )

    assert result.exit_code == 0
    assert _json(result)["request"]["security_scope"] == ["workspace:main"]


def test_cli_policy_bundle_export(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    _install_fake(monkeypatch)

    result = runner.invoke(cli_main.app, ["--json", "policy", "bundle", "export"])

    assert result.exit_code == 0
    assert _json(result)["policy_bundle_id"] == "bundle-1"
