from __future__ import annotations

import json
from typing import Any

from typer.testing import CliRunner

from aion_sdk.cli import main as cli_main
from aion_sdk.config import AIONClientConfig

runner = CliRunner()


class FakeSandbox:
    def __init__(self) -> None:
        self.calls: list[tuple[str, Any]] = []

    def create_profile(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.calls.append(("create_profile", payload))
        return {"sandbox_profile_id": "sandbox-profile-1", "payload": payload}

    def list_profiles(self, scope: list[str], status: str | None = None) -> list[dict[str, Any]]:
        self.calls.append(("list_profiles", {"scope": scope, "status": status}))
        return [{"sandbox_profile_id": "sandbox-profile-1", "scope": scope}]

    def validate_profile(self, sandbox_profile_id: str, scope: list[str]) -> dict[str, Any]:
        self.calls.append(("validate_profile", {"id": sandbox_profile_id, "scope": scope}))
        return {"status": "passed", "sandbox_profile_id": sandbox_profile_id}

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.calls.append(("run", payload))
        return {"status": "dry_run", "payload": payload}

    def create_secret_ref(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.calls.append(("create_secret_ref", payload))
        return {"secret_ref_id": "secret-ref-1", "payload": payload}

    def list_secret_refs(
        self,
        scope: list[str],
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        self.calls.append(("list_secret_refs", {"scope": scope, "status": status}))
        return [{"secret_ref_id": "secret-ref-1", "scope": scope}]

    def create_connector(self, payload: dict[str, Any]) -> dict[str, Any]:
        self.calls.append(("create_connector", payload))
        return {"connector_id": "connector-1", "payload": payload}

    def list_connectors(
        self,
        scope: list[str],
        status: str | None = None,
        connector_type: str | None = None,
    ) -> list[dict[str, Any]]:
        self.calls.append(
            (
                "list_connectors",
                {"scope": scope, "status": status, "connector_type": connector_type},
            )
        )
        return [{"connector_id": "connector-1", "scope": scope}]

    def validate_connector(self, connector_id: str, scope: list[str]) -> dict[str, Any]:
        self.calls.append(("validate_connector", {"id": connector_id, "scope": scope}))
        return {"status": "passed", "connector_id": connector_id}


class FakeClient:
    def __init__(self, config: AIONClientConfig) -> None:
        self.config = config
        self.sandbox = FakeSandbox()


def _install_fake(monkeypatch) -> dict[str, FakeClient]:  # type: ignore[no-untyped-def]
    holder: dict[str, FakeClient] = {}

    def factory(config: AIONClientConfig) -> FakeClient:
        client = FakeClient(config)
        holder["client"] = client
        return client

    monkeypatch.setattr(cli_main, "make_client", factory)
    return holder


def _json(stdout: str) -> Any:
    return json.loads(stdout)


def test_cli_sandbox_profile_list_works_with_mocked_sdk(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    _install_fake(monkeypatch)

    result = runner.invoke(
        cli_main.app,
        ["--json", "--scope", "workspace:main", "sandbox", "profile", "list"],
    )

    assert result.exit_code == 0
    assert _json(result.stdout)[0]["sandbox_profile_id"] == "sandbox-profile-1"


def test_cli_secrets_create_ref_rejects_raw_value_flag(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    _install_fake(monkeypatch)

    result = runner.invoke(
        cli_main.app,
        [
            "--json",
            "--scope",
            "workspace:main",
            "secrets",
            "create-ref",
            "--name",
            "Generic",
            "--description",
            "Reference",
            "--raw-value",
            "sk-test",
        ],
    )

    assert result.exit_code != 0
    assert "raw secret values are not accepted" in result.output


def test_cli_connectors_list_works_with_mocked_sdk(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    _install_fake(monkeypatch)

    result = runner.invoke(
        cli_main.app,
        ["--json", "--scope", "workspace:main", "connectors", "list"],
    )

    assert result.exit_code == 0
    assert _json(result.stdout)[0]["connector_id"] == "connector-1"
