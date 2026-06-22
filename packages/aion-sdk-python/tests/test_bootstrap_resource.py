from __future__ import annotations

from typing import Any

import httpx

from aion_sdk import AIONClient, AIONClientConfig


def _client(handler: Any) -> AIONClient:
    return AIONClient(
        AIONClientConfig(base_url="http://aion.test"),
        httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_bootstrap_resource_calls_expected_endpoints() -> None:
    seen: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path))
        return httpx.Response(200, json={"ok": True})

    client = _client(handler)
    scope = ["workspace:main"]
    client.bootstrap.seed_profiles(scope)
    client.bootstrap.list_profiles(scope)
    client.bootstrap.seed_bundles(scope)
    client.bootstrap.list_seed_bundles(scope)
    client.bootstrap.seed({"owner_scope": scope, "seed_bundle_key": "core.defaults"})
    client.bootstrap.doctor({"owner_scope": scope})
    client.bootstrap.run({"owner_scope": scope})
    client.bootstrap.list_runs(scope)
    client.bootstrap.get_run("run-1", scope)
    client.bootstrap.list_findings(scope)
    client.bootstrap.dismiss_finding("finding-1", scope)
    client.bootstrap.list_reports(scope)
    client.bootstrap.get_report("report-1", scope)

    assert seen == [
        ("POST", "/brain/bootstrap/profiles/seed-defaults"),
        ("GET", "/brain/bootstrap/profiles"),
        ("POST", "/brain/bootstrap/seed-bundles/seed-defaults"),
        ("GET", "/brain/bootstrap/seed-bundles"),
        ("POST", "/brain/bootstrap/seed"),
        ("POST", "/brain/bootstrap/doctor"),
        ("POST", "/brain/bootstrap/run"),
        ("GET", "/brain/bootstrap/runs"),
        ("GET", "/brain/bootstrap/runs/run-1"),
        ("GET", "/brain/bootstrap/findings"),
        ("POST", "/brain/bootstrap/findings/finding-1/dismiss"),
        ("GET", "/brain/bootstrap/reports"),
        ("GET", "/brain/bootstrap/reports/report-1"),
    ]


def test_bootstrap_resource_does_not_import_brain_package() -> None:
    import aion_sdk.resources.bootstrap as resource

    assert "aion_brain" not in resource.__dict__
