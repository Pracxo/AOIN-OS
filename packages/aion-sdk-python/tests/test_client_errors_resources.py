from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import httpx
import pytest

from aion_sdk import AIONClient, AIONClientConfig
from aion_sdk.errors import (
    AIONConflictError,
    AIONHTTPError,
    AIONPolicyDeniedError,
    AIONValidationError,
)


def _client(handler: Any) -> AIONClient:
    transport = httpx.MockTransport(handler)
    return AIONClient(
        AIONClientConfig(
            base_url="http://aion.test",
            actor_id="actor",
            workspace_id="workspace",
            security_scope=["workspace:main"],
        ),
        httpx.Client(transport=transport),
    )


def test_client_sends_headers_and_decodes_success() -> None:
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["actor"] = request.headers["X-AION-Actor-ID"]
        seen["scope"] = request.headers["X-AION-Security-Scope"]
        return httpx.Response(200, json={"status": "ok"})

    client = _client(handler)

    assert client.health.health() == {"status": "ok"}
    assert seen == {
        "url": "http://aion.test/health",
        "actor": "actor",
        "scope": "workspace:main",
    }


@pytest.mark.parametrize(
    ("category", "status_code", "expected"),
    [
        ("validation", 422, AIONValidationError),
        ("policy", 403, AIONPolicyDeniedError),
        ("conflict", 409, AIONConflictError),
    ],
)
def test_client_maps_aion_error_envelope(
    category: str,
    status_code: int,
    expected: type[Exception],
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code,
            json={
                "error": {
                    "code": f"AION_{category.upper()}",
                    "category": category,
                    "message": "blocked",
                    "detail": {"field": "value"},
                    "trace_id": "trace-1",
                    "correlation_id": "corr-1",
                    "request_id": "req-1",
                    "retryable": False,
                    "created_at": datetime.now(UTC).isoformat(),
                }
            },
        )

    with pytest.raises(expected):
        _client(handler).kernel.status()


def test_client_non_aion_http_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"detail": "server failed"})

    with pytest.raises(AIONHTTPError):
        _client(handler).kernel.status()


def test_client_does_not_retry() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(503, json={"detail": "unavailable"})

    with pytest.raises(AIONHTTPError):
        _client(handler).kernel.status()

    assert calls == 1


def test_resource_paths_are_public_http_paths() -> None:
    calls: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append((request.method, request.url.path))
        return httpx.Response(200, json={"ok": True})

    client = _client(handler)
    client.kernel.self_test(["workspace:main"])
    client.events.ingest(
        {
            "event_id": "event-1",
            "source": "test",
            "event_type": "test.received",
            "payload_type": "test.payload",
            "payload": {},
            "timestamp": datetime.now(UTC).isoformat(),
            "security_scope": ["workspace:main"],
        }
    )
    client.memory.retrieve("remember", scope=["workspace:main"])
    client.reasoning.reason({"reasoning_id": "reason-1"})
    client.commands.dispatch(
        {
            "command_type": "noop",
            "target_type": "noop",
            "mode": "dry_run",
            "owner_scope": ["workspace:main"],
            "payload": {},
        }
    )
    client.workflows.status()
    client.autonomy.status(scope=["workspace:main"])
    client.approvals.inbox(scope=["workspace:main"])
    client.visual.map({"scope": ["workspace:main"]})
    client.policy.list_actions()
    client.policy.simulate(
        {
            "action_type": "memory.retrieve",
            "resource_type": "memory_record",
            "security_scope": ["workspace:main"],
        }
    )
    client.policy.run_tests({"dry_run": True})
    client.policy.coverage()
    client.policy.export_bundle({"bundle_type": "full"})
    client.policy.opa_status()

    assert calls == [
        ("POST", "/brain/kernel/self-test"),
        ("POST", "/brain/events"),
        ("POST", "/brain/memory/retrieve"),
        ("POST", "/brain/reason"),
        ("POST", "/brain/commands"),
        ("GET", "/brain/workflows/engine/status"),
        ("GET", "/brain/autonomy/status"),
        ("GET", "/brain/approvals"),
        ("POST", "/brain/visual/map"),
        ("GET", "/brain/policy-catalog/actions"),
        ("POST", "/brain/policy/simulate"),
        ("POST", "/brain/policy/tests/run"),
        ("GET", "/brain/policy/coverage"),
        ("POST", "/brain/policy/bundles/export"),
        ("GET", "/brain/policy/opa/status"),
    ]
