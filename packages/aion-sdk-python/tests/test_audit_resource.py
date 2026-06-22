from __future__ import annotations

from typing import Any

import httpx

from aion_sdk import AIONClient, AIONClientConfig


def _client(handler: Any) -> AIONClient:
    return AIONClient(
        AIONClientConfig(base_url="http://aion.test"),
        httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_audit_resource_status_verify_export_and_trace_call_endpoints() -> None:
    seen: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path))
        return httpx.Response(200, json={"ok": True})

    client = _client(handler)
    client.audit.status()
    client.audit.verify({})
    client.audit.export({"owner_scope": ["workspace:main"]})
    client.audit.trace_provenance("trace-1")

    assert seen == [
        ("GET", "/brain/audit/status"),
        ("POST", "/brain/audit/verify"),
        ("POST", "/brain/audit/export"),
        ("GET", "/brain/provenance/traces/trace-1"),
    ]


def test_sdk_does_not_import_aion_brain() -> None:
    import sys

    assert "aion_brain" not in {
        name for name in sys.modules if name == "aion_brain" or name.startswith("aion_brain.")
    }
