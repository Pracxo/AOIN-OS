from __future__ import annotations

from typing import Any

import httpx

from aion_sdk import AIONClient, AIONClientConfig


def _client(handler: Any) -> AIONClient:
    return AIONClient(
        AIONClientConfig(base_url="http://aion.test"),
        httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_module_mock_runtime_resource_calls_expected_endpoints() -> None:
    seen: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path))
        return httpx.Response(200, json={"ok": True})

    client = _client(handler)
    scope = ["workspace:main"]
    client.module_mock_runtime.create_profile({"profile_key": "generic.mock"})
    client.module_mock_runtime.seed_profiles({"scope": scope, "dry_run": True})
    client.module_mock_runtime.list_profiles(scope)
    client.module_mock_runtime.get_profile("profile-1", scope)
    client.module_mock_runtime.invoke(
        {
            "capability_binding_id": "binding-1",
            "capability_key": "generic.mock",
            "owner_scope": scope,
        }
    )
    client.module_mock_runtime.list_runs(scope)
    client.module_mock_runtime.get_run("run-1", scope)
    client.module_mock_runtime.outputs(scope)
    client.module_mock_runtime.get_output("output-1", scope)
    client.module_mock_runtime.list_findings(scope)
    client.module_mock_runtime.dismiss_finding("finding-1", {"reason": "accepted"})
    client.module_mock_runtime.query({"scope": scope})

    assert seen == [
        ("POST", "/brain/module-mock/profiles"),
        ("POST", "/brain/module-mock/profiles/seed-defaults"),
        ("GET", "/brain/module-mock/profiles"),
        ("GET", "/brain/module-mock/profiles/profile-1"),
        ("POST", "/brain/module-mock/invoke"),
        ("GET", "/brain/module-mock/runs"),
        ("GET", "/brain/module-mock/runs/run-1"),
        ("GET", "/brain/module-mock/outputs"),
        ("GET", "/brain/module-mock/outputs/output-1"),
        ("GET", "/brain/module-mock/findings"),
        ("POST", "/brain/module-mock/findings/finding-1/dismiss"),
        ("POST", "/brain/module-mock/query"),
    ]


def test_module_mock_runtime_resource_does_not_import_brain_package() -> None:
    import aion_sdk.resources.module_mock_runtime as resource

    assert "aion_brain" not in resource.__dict__
