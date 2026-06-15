from __future__ import annotations

from typing import Any

import httpx

from aion_sdk import AIONClient, AIONClientConfig


def _client(handler: Any) -> AIONClient:
    return AIONClient(
        AIONClientConfig(base_url="http://aion.test"),
        httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_config_resource_status_calls_correct_endpoint() -> None:
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["path"] = request.url.path
        return httpx.Response(200, json={"validation_status": "passed"})

    _client(handler).runtime_config.status(["workspace:main"])

    assert seen == {"method": "GET", "path": "/brain/runtime-config/status"}


def test_config_resource_is_exposed_as_client_config_alias() -> None:
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["path"] = request.url.path
        return httpx.Response(200, json={"validation_status": "passed"})

    _client(handler).config.status(["workspace:main"])

    assert seen == {"method": "GET", "path": "/brain/runtime-config/status"}


def test_config_resource_validate_calls_correct_endpoint() -> None:
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["path"] = request.url.path
        return httpx.Response(200, json={"config_validation_id": "validation-1"})

    _client(handler).runtime_config.validate({"owner_scope": ["workspace:main"]})

    assert seen == {"method": "POST", "path": "/brain/runtime-config/validate"}


def test_config_resource_create_snapshot_calls_correct_endpoint() -> None:
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["path"] = request.url.path
        return httpx.Response(200, json={"config_snapshot_id": "snapshot-1"})

    _client(handler).runtime_config.create_snapshot({"owner_scope": ["workspace:main"]})

    assert seen == {"method": "POST", "path": "/brain/runtime-config/snapshots"}


def test_sdk_does_not_import_aion_brain() -> None:
    import sys

    assert "aion_brain" not in sys.modules
