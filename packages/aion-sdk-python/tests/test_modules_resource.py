from __future__ import annotations

from typing import Any

import httpx

from aion_sdk import AIONClient, AIONClientConfig


def _client(handler: Any) -> AIONClient:
    return AIONClient(
        AIONClientConfig(base_url="http://aion.test"),
        httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_modules_resource_submit_package_calls_correct_endpoint() -> None:
    seen: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["path"] = request.url.path
        return httpx.Response(200, json={"module_package_id": "pkg-1"})

    result = _client(handler).modules.submit_package({"module_id": "generic.example"})

    assert result == {"module_package_id": "pkg-1"}
    assert seen == {"method": "POST", "path": "/brain/module-developer/packages"}


def test_modules_resource_certify_calls_correct_endpoint() -> None:
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        return httpx.Response(200, json={"status": "passed"})

    _client(handler).modules.certify("pkg-1", {"module_package_id": "pkg-1"})

    assert seen["path"] == "/brain/module-developer/packages/pkg-1/certify"


def test_modules_resource_scaffold_calls_correct_endpoint() -> None:
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        return httpx.Response(200, json={"files": {}})

    _client(handler).modules.scaffold({"module_id": "generic.example"})

    assert seen["path"] == "/brain/module-developer/scaffold"
