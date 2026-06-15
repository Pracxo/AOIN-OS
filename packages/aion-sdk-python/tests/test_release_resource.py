from __future__ import annotations

from typing import Any

import httpx

from aion_sdk import AIONClient, AIONClientConfig


def _client(handler: Any) -> AIONClient:
    return AIONClient(
        AIONClientConfig(base_url="http://aion.test"),
        httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_release_resource_create_package_calls_public_endpoint() -> None:
    seen: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["path"] = request.url.path
        return httpx.Response(200, json={"release_package_id": "package-1"})

    _client(handler).release.create_package(
        {"version": "0.1.0", "owner_scope": ["workspace:main"]}
    )

    assert seen == {"method": "POST", "path": "/brain/release-package/create"}


def test_release_resource_list_packages_uses_scope_query() -> None:
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["scope"] = request.url.params.get("scope", "")
        return httpx.Response(200, json=[])

    _client(handler).release.list_packages(scope=["workspace:main"], version="0.1.0")

    assert seen["path"] == "/brain/release-package"
    assert seen["scope"] == "workspace:main"


def test_release_resource_handoff_calls_public_endpoint() -> None:
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["path"] = request.url.path
        return httpx.Response(200, json={"status": "ready"})

    _client(handler).release.handoff("package-1", ["workspace:main"])

    assert seen == {"method": "GET", "path": "/brain/release-package/package-1/handoff"}
