from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx

from aion_sdk import AIONClient, AIONClientConfig


def _client(handler: Any) -> AIONClient:
    return AIONClient(
        AIONClientConfig(base_url="http://aion.test"),
        httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_sandbox_resource_create_profile_calls_correct_endpoint() -> None:
    seen: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["path"] = request.url.path
        seen["payload"] = json.loads(request.content)
        return httpx.Response(200, json={"sandbox_profile_id": "sandbox-profile-1"})

    result = _client(handler).sandbox.create_profile({"name": "Generic"})

    assert result == {"sandbox_profile_id": "sandbox-profile-1"}
    assert seen == {
        "method": "POST",
        "path": "/brain/sandbox/profiles",
        "payload": {"name": "Generic"},
    }


def test_sandbox_resource_run_defaults_to_dry_run_payload() -> None:
    seen: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["payload"] = json.loads(request.content)
        return httpx.Response(200, json={"status": "dry_run"})

    _client(handler).sandbox.run({"sandbox_profile_id": "sandbox-profile-1", "target_type": "test"})

    assert seen["path"] == "/brain/sandbox/run"
    assert seen["payload"] == {
        "mode": "dry_run",
        "sandbox_profile_id": "sandbox-profile-1",
        "target_type": "test",
    }


def test_sandbox_resource_create_secret_ref_sends_metadata_only_request() -> None:
    seen: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["payload"] = json.loads(request.content)
        return httpx.Response(200, json={"secret_ref_id": "secret-ref-1"})

    _client(handler).sandbox.create_secret_ref(
        {"name": "Generic", "external_ref": "env:AION_GENERIC_REF"}
    )

    assert seen["path"] == "/brain/secret-refs"
    assert seen["payload"] == {
        "name": "Generic",
        "external_ref": "env:AION_GENERIC_REF",
    }


def test_sandbox_resource_create_connector_calls_correct_endpoint() -> None:
    seen: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["payload"] = json.loads(request.content)
        return httpx.Response(200, json={"connector_id": "connector-1"})

    _client(handler).sandbox.create_connector({"name": "Generic"})

    assert seen["path"] == "/brain/connectors"
    assert seen["payload"] == {"name": "Generic"}


def test_sdk_does_not_import_aion_brain() -> None:
    sdk_root = Path(__file__).resolve().parents[1] / "src" / "aion_sdk"

    assert "aion_brain" not in "\n".join(
        path.read_text(encoding="utf-8") for path in sdk_root.rglob("*.py")
    )
