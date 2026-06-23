from __future__ import annotations

from typing import Any

import httpx

from aion_sdk import AIONClient, AIONClientConfig


def _client(handler: Any) -> AIONClient:
    return AIONClient(
        AIONClientConfig(base_url="http://aion.test"),
        httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_model_provider_hardening_resource_calls_expected_endpoints() -> None:
    seen: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path))
        return httpx.Response(200, json={"ok": True})

    client = _client(handler)
    scope = ["workspace:main"]
    client.model_provider_hardening.create_profile({"provider_key": "generic.metadata_only"})
    client.model_provider_hardening.get_profile("profile-1", scope)
    client.model_provider_hardening.list_profiles(scope)
    client.model_provider_hardening.seed_profiles({"scope": scope, "dry_run": True})
    client.model_provider_hardening.egress_preview({"owner_scope": scope})
    client.model_provider_hardening.simulate({"owner_scope": scope})
    client.model_provider_hardening.assess_readiness({"owner_scope": scope})
    client.model_provider_hardening.blockers(scope)
    client.model_provider_hardening.dismiss_blocker("blocker-1", {"reason": "reviewed"})
    client.model_provider_hardening.query({"scope": scope})

    assert seen == [
        ("POST", "/brain/model-providers/profiles"),
        ("GET", "/brain/model-providers/profiles/profile-1"),
        ("GET", "/brain/model-providers/profiles"),
        ("POST", "/brain/model-providers/profiles/seed-defaults"),
        ("POST", "/brain/model-providers/egress-preview"),
        ("POST", "/brain/model-providers/simulate"),
        ("POST", "/brain/model-providers/readiness"),
        ("GET", "/brain/model-providers/blockers"),
        ("POST", "/brain/model-providers/blockers/blocker-1/dismiss"),
        ("POST", "/brain/model-providers/query"),
    ]


def test_model_provider_hardening_resource_does_not_import_brain_package() -> None:
    import aion_sdk.resources.model_provider_hardening as resource

    assert "aion_brain" not in resource.__dict__
