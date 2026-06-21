from __future__ import annotations

from typing import Any

import httpx

from aion_sdk import AIONClient, AIONClientConfig


def _client(handler: Any) -> AIONClient:
    return AIONClient(
        AIONClientConfig(base_url="http://aion.test"),
        httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_conformance_resource_calls_expected_endpoints() -> None:
    seen: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path))
        return httpx.Response(200, json={"ok": True})

    client = _client(handler)
    scope = ["workspace:main"]
    client.conformance.create_profile({"name": "Generic"})
    client.conformance.get_profile("profile-1", scope)
    client.conformance.list_profiles(scope)
    client.conformance.seed_default_profiles(scope)
    client.conformance.create_test_vector({"name": "Vector"})
    client.conformance.get_test_vector("vector-1", scope)
    client.conformance.list_test_vectors(scope)
    client.conformance.generate_test_vectors("binding-1", scope)
    client.conformance.run({"capability_binding_id": "binding-1"})
    client.conformance.get_run("run-1")
    client.conformance.list_findings(scope)
    client.conformance.dismiss_finding("finding-1", {"reason": "accepted"}, scope)
    client.conformance.assess_readiness({"capability_binding_id": "binding-1"})
    client.conformance.get_readiness_assessment("readiness-1", scope)
    client.conformance.list_readiness_assessments(scope)
    client.conformance.query({"scope": scope})

    assert seen == [
        ("POST", "/brain/conformance/profiles"),
        ("GET", "/brain/conformance/profiles/profile-1"),
        ("GET", "/brain/conformance/profiles"),
        ("POST", "/brain/conformance/profiles/seed-defaults"),
        ("POST", "/brain/conformance/test-vectors"),
        ("GET", "/brain/conformance/test-vectors/vector-1"),
        ("GET", "/brain/conformance/test-vectors"),
        ("POST", "/brain/conformance/test-vectors/generate-for-binding/binding-1"),
        ("POST", "/brain/conformance/run"),
        ("GET", "/brain/conformance/runs/run-1"),
        ("GET", "/brain/conformance/findings"),
        ("POST", "/brain/conformance/findings/finding-1/dismiss"),
        ("POST", "/brain/readiness/assess"),
        ("GET", "/brain/readiness/assessments/readiness-1"),
        ("GET", "/brain/readiness/assessments"),
        ("POST", "/brain/conformance/query"),
    ]


def test_conformance_resource_does_not_import_brain_package() -> None:
    import aion_sdk.resources.conformance as resource

    assert "aion_brain" not in resource.__dict__
