from __future__ import annotations

from typing import Any

import httpx

from aion_sdk import AIONClient, AIONClientConfig


def _client(handler: Any) -> AIONClient:
    return AIONClient(
        AIONClientConfig(base_url="http://aion.test"),
        httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_resilience_resource_status_and_dependencies_call_endpoints() -> None:
    seen: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path))
        return httpx.Response(200, json={"ok": True})

    client = _client(handler)
    client.resilience.status(["workspace:main"])
    client.resilience.check_dependencies(["workspace:main"])
    client.resilience.list_dependencies(component="postgres")

    assert seen == [
        ("GET", "/brain/resilience/status"),
        ("POST", "/brain/resilience/dependencies/check"),
        ("GET", "/brain/resilience/dependencies"),
    ]


def test_resilience_resource_retry_breaker_fault_and_test_endpoints() -> None:
    seen: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path))
        return httpx.Response(200, json={"ok": True})

    client = _client(handler)
    client.resilience.create_retry_policy({"name": "retry"})
    client.resilience.list_retry_policies(status="active")
    client.resilience.seed_retry_policies(dry_run=True)
    client.resilience.create_circuit_breaker({"name": "breaker"})
    client.resilience.list_circuit_breakers(target_type="command")
    client.resilience.reset_circuit_breaker("breaker", "reset")
    client.resilience.list_degraded(component="memory")
    client.resilience.resolve_degraded("degraded-1", "resolved")
    client.resilience.create_fault_rule({"name": "fault"})
    client.resilience.list_fault_rules(status="active")
    client.resilience.disable_fault_rule("fault-1", "disable")
    client.resilience.run_test({"owner_scope": ["workspace:main"]})
    client.resilience.get_test_run("run-1", ["workspace:main"])

    assert seen == [
        ("POST", "/brain/resilience/retry-policies"),
        ("GET", "/brain/resilience/retry-policies"),
        ("POST", "/brain/resilience/retry-policies/seed-defaults"),
        ("POST", "/brain/resilience/circuit-breakers"),
        ("GET", "/brain/resilience/circuit-breakers"),
        ("POST", "/brain/resilience/circuit-breakers/breaker/reset"),
        ("GET", "/brain/resilience/degraded"),
        ("POST", "/brain/resilience/degraded/degraded-1/resolve"),
        ("POST", "/brain/resilience/fault-rules"),
        ("GET", "/brain/resilience/fault-rules"),
        ("POST", "/brain/resilience/fault-rules/fault-1/disable"),
        ("POST", "/brain/resilience/test/run"),
        ("GET", "/brain/resilience/test-runs/run-1"),
    ]
