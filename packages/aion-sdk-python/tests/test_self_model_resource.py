from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx

from aion_sdk import AIONClient, AIONClientConfig


def _client(handler: Any) -> AIONClient:
    return AIONClient(
        AIONClientConfig(base_url="http://aion.test"),
        httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_self_model_resource_calls_expected_endpoints() -> None:
    seen: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path))
        return httpx.Response(200, json={"ok": True})

    client = _client(handler)
    client.self_model.describe(["workspace:main"])
    client.self_model.capabilities(["workspace:main"])
    client.self_model.refresh_capabilities(["workspace:main"])
    client.self_model.create_limitation({"limitation_key": "generic.sdk_limit"})
    client.self_model.list_limitations(["workspace:main"])
    client.self_model.seed_limitations(["workspace:main"])
    client.self_model.resolve_limitation("limitation-1", "reviewed")
    client.self_model.calibrate_confidence({"source_type": "generic"})
    client.self_model.list_confidence(limit=10)
    client.self_model.run_assessment({"owner_scope": ["workspace:main"]})
    client.self_model.get_assessment("assessment-1")
    client.self_model.create_introspection({"owner_scope": ["workspace:main"]})
    client.self_model.get_introspection("snapshot-1", ["workspace:main"])
    client.self_model.list_introspection(["workspace:main"])

    assert seen == [
        ("GET", "/brain/self"),
        ("GET", "/brain/self/capabilities"),
        ("POST", "/brain/self/capabilities/refresh"),
        ("POST", "/brain/self/limitations"),
        ("GET", "/brain/self/limitations"),
        ("POST", "/brain/self/limitations/seed-defaults"),
        ("POST", "/brain/self/limitations/limitation-1/resolve"),
        ("POST", "/brain/self/confidence/calibrate"),
        ("GET", "/brain/self/confidence"),
        ("POST", "/brain/self/assessment/run"),
        ("GET", "/brain/self/assessment/assessment-1"),
        ("POST", "/brain/self/introspection"),
        ("GET", "/brain/self/introspection/snapshot-1"),
        ("GET", "/brain/self/introspection"),
    ]


def test_self_model_sdk_resource_does_not_import_brain_package() -> None:
    source = Path("src/aion_sdk/resources/self_model.py").read_text()

    assert "aion_brain" not in source
