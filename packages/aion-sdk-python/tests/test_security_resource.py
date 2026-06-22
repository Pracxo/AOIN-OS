from __future__ import annotations

from typing import Any

import httpx

from aion_sdk import AIONClient, AIONClientConfig


def _client(handler: Any) -> AIONClient:
    return AIONClient(
        AIONClientConfig(base_url="http://aion.test"),
        httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_security_resource_run_scan_calls_correct_endpoint() -> None:
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["path"] = request.url.path
        return httpx.Response(200, json={"security_scan_id": "scan-1"})

    _client(handler).security.run_scan({"scan_type": "full", "owner_scope": ["workspace:main"]})

    assert seen == {"method": "POST", "path": "/brain/security/scans/run"}


def test_security_resource_run_hardening_gate_calls_correct_endpoint() -> None:
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["path"] = request.url.path
        return httpx.Response(200, json={"hardening_gate_id": "gate-1"})

    _client(handler).security.run_hardening_gate({"owner_scope": ["workspace:main"]})

    assert seen == {"method": "POST", "path": "/brain/security/hardening-gate/run"}


def test_security_resource_seed_threat_models_calls_correct_endpoint() -> None:
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["path"] = request.url.path
        return httpx.Response(200, json={"seeded": False})

    _client(handler).security.seed_threat_models(["workspace:main"])

    assert seen == {"method": "POST", "path": "/brain/security/threat-models/seed-defaults"}


def test_sdk_does_not_import_aion_brain() -> None:
    import sys

    assert "aion_brain" not in sys.modules
