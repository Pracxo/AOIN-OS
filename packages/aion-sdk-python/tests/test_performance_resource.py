from __future__ import annotations

from typing import Any

import httpx

from aion_sdk import AIONClient, AIONClientConfig


def _client(handler: Any) -> AIONClient:
    return AIONClient(
        AIONClientConfig(base_url="http://aion.test"),
        httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_performance_resource_list_benchmarks_calls_endpoint() -> None:
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["path"] = request.url.path
        return httpx.Response(200, json=[])

    _client(handler).performance.list_benchmarks()

    assert seen == {"method": "GET", "path": "/brain/performance/benchmarks"}


def test_performance_resource_run_benchmark_calls_endpoint() -> None:
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["path"] = request.url.path
        return httpx.Response(200, json={"benchmark_run_id": "run-1"})

    _client(handler).performance.run_benchmark({"benchmark_id": "benchmark-1"})

    assert seen == {"method": "POST", "path": "/brain/performance/benchmarks/run"}


def test_performance_resource_create_baseline_and_summary_call_endpoints() -> None:
    seen: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path))
        return httpx.Response(200, json={"ok": True})

    client = _client(handler)
    client.performance.create_baseline({"benchmark_run_ids": ["run-1"]})
    client.performance.summary(["workspace:main"])

    assert seen == [
        ("POST", "/brain/performance/baselines/from-runs"),
        ("GET", "/brain/performance/summary"),
    ]
