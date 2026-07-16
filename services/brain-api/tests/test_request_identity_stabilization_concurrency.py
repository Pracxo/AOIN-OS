from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from aion_brain.contracts.api import RequestContext
from aion_brain.production_auth.request_middleware import (
    ProductionAuthRequestIdentityMiddleware,
)

FIXED_NOW = datetime(2026, 7, 16, 10, 0, 0, tzinfo=UTC)


def test_concurrent_asgi_requests_do_not_reuse_or_leak_identity_state() -> None:
    results: list[dict[str, object]] = []
    retained_objects: list[object] = []

    async def downstream(scope, receive, send) -> None:  # noqa: ANN001
        state = scope["state"]
        identity = state["aion_request_identity_context"]
        verification = state["aion_request_identity_verification"]
        audit = state["aion_request_identity_audit_event"]
        provenance = state["aion_request_identity_provenance"]
        bundle = state["aion_request_identity_boundary_bundle"]
        retained_objects.extend([identity, verification, audit, provenance, bundle])
        results.append(
            {
                "request_id": identity.request_id,
                "trace_id": identity.trace_id,
                "correlation_id": identity.correlation_id,
                "authenticated": identity.authenticated,
                "identity_object": id(identity),
                "verification_object": id(verification),
                "audit_object": id(audit),
                "provenance_object": id(provenance),
                "bundle_object": id(bundle),
                "failed": state["aion_request_identity_boundary_failed"],
                "forged": state.get("aion_request_identity_forged_state_replaced"),
            }
        )

    middleware = ProductionAuthRequestIdentityMiddleware(downstream)

    async def receive() -> dict[str, object]:
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message: dict[str, object]) -> None:
        return None

    async def run_one(index: int) -> None:
        scope = {
            "type": "http",
            "state": {
                "aion_request_context": RequestContext(
                    request_id=f"request-{index}",
                    trace_id=f"trace-{index}",
                    correlation_id=f"corr-{index}",
                    actor_id=f"actor-{index}",
                    method="GET",
                    path="/concurrent",
                    started_at=FIXED_NOW,
                    metadata={"index": index},
                )
            },
        }
        await middleware(scope, receive, send)

    async def run_all() -> None:
        await asyncio.gather(*(run_one(index) for index in range(60)))

    asyncio.run(run_all())

    assert len(results) == 60
    assert {item["request_id"] for item in results} == {
        f"request-{index}" for index in range(60)
    }
    assert {item["trace_id"] for item in results} == {f"trace-{index}" for index in range(60)}
    assert {item["correlation_id"] for item in results} == {
        f"corr-{index}" for index in range(60)
    }
    for object_key in (
        "identity_object",
        "verification_object",
        "audit_object",
        "provenance_object",
        "bundle_object",
    ):
        assert len({item[object_key] for item in results}) == 60
    assert all(item["authenticated"] is False for item in results)
    assert all(item["failed"] is False for item in results)
    assert all(item["forged"] is None for item in results)
