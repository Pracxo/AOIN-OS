from __future__ import annotations

import asyncio
from datetime import UTC, datetime

import pytest
from starlette.requests import ClientDisconnect

from aion_brain.contracts.api import RequestContext
from aion_brain.production_auth.request_middleware import (
    ProductionAuthRequestIdentityMiddleware,
)

FIXED_NOW = datetime(2026, 7, 16, 10, 0, 0, tzinfo=UTC)


def test_downstream_client_disconnect_clears_identity_and_preserves_safe_failure() -> None:
    async def downstream(scope, receive, send) -> None:  # noqa: ANN001
        assert scope["state"]["aion_request_identity_boundary_attached"] is True
        raise ClientDisconnect

    scope = {
        "type": "http",
        "state": {
            "aion_request_context": RequestContext(
                request_id="request-disconnect",
                trace_id="trace-disconnect",
                correlation_id="corr-disconnect",
                method="GET",
                path="/disconnect",
                started_at=FIXED_NOW,
            )
        },
    }

    async def receive() -> dict[str, object]:
        return {"type": "http.disconnect"}

    async def send(message: dict[str, object]) -> None:
        return None

    with pytest.raises(ClientDisconnect):
        asyncio.run(ProductionAuthRequestIdentityMiddleware(downstream)(scope, receive, send))

    state = scope["state"]
    assert "aion_request_identity_context" not in state
    assert "aion_request_identity_verification" not in state
    assert "aion_request_identity_boundary_bundle" not in state
    assert state["aion_request_identity_boundary_failed"] is True
    assert (
        state["aion_request_identity_boundary_failure_reason"]
        == "downstream_client_disconnect"
    )
    assert state["aion_request_identity_boundary_attached"] is False
