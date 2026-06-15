from __future__ import annotations

from typing import Any

import httpx

from aion_sdk import AIONClient, AIONClientConfig


def _client(handler: Any) -> AIONClient:
    return AIONClient(
        AIONClientConfig(base_url="http://aion.test"),
        httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_scenarios_resource_list_calls_correct_endpoint() -> None:
    seen: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["path"] = request.url.path
        return httpx.Response(200, json=[])

    _client(handler).scenarios.list(status="active")

    assert seen == {"method": "GET", "path": "/brain/scenarios"}


def test_scenarios_resource_run_calls_correct_endpoint() -> None:
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        return httpx.Response(200, json={"status": "passed"})

    _client(handler).scenarios.run({"scenario_id": "golden_path_brain"})

    assert seen["path"] == "/brain/scenarios/run"


def test_scenarios_resource_seed_defaults_calls_correct_endpoint() -> None:
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        return httpx.Response(200, json={"dry_run": True})

    _client(handler).scenarios.seed_defaults(["workspace:main"])

    assert seen["path"] == "/brain/scenarios/seed-defaults"


def test_scenarios_resource_run_release_baseline_calls_correct_endpoint() -> None:
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        return httpx.Response(200, json={"status": "passed"})

    _client(handler).scenarios.run_release_baseline({"version": "0.1.0"})

    assert seen["path"] == "/brain/release-baseline/run"
