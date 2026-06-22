from __future__ import annotations

from typing import Any

import httpx

from aion_sdk import AIONClient, AIONClientConfig


def _client(handler: Any) -> AIONClient:
    return AIONClient(
        AIONClientConfig(base_url="http://aion.test"),
        httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_module_activation_resource_calls_expected_endpoints() -> None:
    seen: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path))
        return httpx.Response(200, json={"ok": True})

    client = _client(handler)
    scope = ["workspace:main"]
    client.module_activation.create_request({"module_slot_id": "slot-1", "owner_scope": scope})
    client.module_activation.list_requests(scope)
    client.module_activation.get_request("request-1", scope)
    client.module_activation.archive_request("request-1", {"reason": "done"})
    client.module_activation.delete_request("request-1", {"reason": "done"})
    client.module_activation.run_gate("request-1", {"scope": scope})
    client.module_activation.list_gate_runs("request-1", scope)
    client.module_activation.list_blockers(scope)
    client.module_activation.dismiss_blocker("blocker-1", {"reason": "accepted"})
    client.module_activation.create_review({"activation_request_id": "request-1"}, scope)
    client.module_activation.list_reviews(scope)
    client.module_activation.create_plan("request-1", {"scope": scope})
    client.module_activation.list_plans(scope)
    client.module_activation.get_plan("plan-1", scope)
    client.module_activation.create_runtime_registration_preview("request-1", {"scope": scope})
    client.module_activation.list_runtime_registration_previews(scope)
    client.module_activation.get_runtime_registration_preview("preview-1", scope)
    client.module_activation.query({"scope": scope})

    assert seen == [
        ("POST", "/brain/module-activation/requests"),
        ("GET", "/brain/module-activation/requests"),
        ("GET", "/brain/module-activation/requests/request-1"),
        ("POST", "/brain/module-activation/requests/request-1/archive"),
        ("DELETE", "/brain/module-activation/requests/request-1"),
        ("POST", "/brain/module-activation/requests/request-1/gate"),
        ("GET", "/brain/module-activation/requests/request-1/gate-runs"),
        ("GET", "/brain/module-activation/blockers"),
        ("POST", "/brain/module-activation/blockers/blocker-1/dismiss"),
        ("POST", "/brain/module-activation/reviews"),
        ("GET", "/brain/module-activation/reviews"),
        ("POST", "/brain/module-activation/requests/request-1/plans"),
        ("GET", "/brain/module-activation/plans"),
        ("GET", "/brain/module-activation/plans/plan-1"),
        ("POST", "/brain/module-activation/requests/request-1/runtime-registration-preview"),
        ("GET", "/brain/module-activation/runtime-registration-previews"),
        ("GET", "/brain/module-activation/runtime-registration-previews/preview-1"),
        ("POST", "/brain/module-activation/query"),
    ]


def test_module_activation_resource_does_not_import_brain_package() -> None:
    import aion_sdk.resources.module_activation as resource

    assert "aion_brain" not in resource.__dict__
