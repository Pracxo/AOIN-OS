from __future__ import annotations

from typing import Any

import httpx

from aion_sdk import AIONClient, AIONClientConfig


def _client(handler: Any) -> AIONClient:
    return AIONClient(
        AIONClientConfig(base_url="http://aion.test"),
        httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_golden_path_resource_calls_expected_endpoints() -> None:
    seen: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path))
        return httpx.Response(200, json={"ok": True})

    client = _client(handler)
    scope = ["workspace:main"]
    client.golden_path.create_scenario({"scenario_key": "golden.test"})
    client.golden_path.get_scenario("golden.test", scope)
    client.golden_path.list_scenarios(scope)
    client.golden_path.seed_default_scenarios(scope)
    client.golden_path.seed_default_fixtures(scope)
    client.golden_path.list_fixtures(scope)
    client.golden_path.run({"owner_scope": scope})
    client.golden_path.get_run("run-1", scope)
    client.golden_path.list_runs(scope)
    client.golden_path.release_smoke(scope)
    client.golden_path.get_report("report-1", scope)
    client.golden_path.list_reports(scope)
    client.golden_path.query({"scope": scope})

    assert seen == [
        ("POST", "/brain/golden-path/scenarios"),
        ("GET", "/brain/golden-path/scenarios/golden.test"),
        ("GET", "/brain/golden-path/scenarios"),
        ("POST", "/brain/golden-path/scenarios/seed-defaults"),
        ("POST", "/brain/golden-path/fixtures/seed-defaults"),
        ("GET", "/brain/golden-path/fixtures"),
        ("POST", "/brain/golden-path/run"),
        ("GET", "/brain/golden-path/runs/run-1"),
        ("GET", "/brain/golden-path/runs"),
        ("POST", "/brain/golden-path/release-smoke"),
        ("GET", "/brain/golden-path/reports/report-1"),
        ("GET", "/brain/golden-path/reports"),
        ("POST", "/brain/golden-path/query"),
    ]


def test_golden_path_resource_does_not_import_brain_package() -> None:
    import aion_sdk.resources.golden_path as resource

    assert "aion_brain" not in resource.__dict__
