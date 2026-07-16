from __future__ import annotations

import asyncio
from datetime import UTC, datetime

import pytest

from aion_brain.contracts.api import RequestContext
from aion_brain.production_auth.request_middleware import (
    ProductionAuthRequestIdentityMiddleware,
)

FIXED_NOW = datetime(2026, 7, 16, 10, 0, 0, tzinfo=UTC)


def _scope() -> dict[str, object]:
    return {
        "type": "http",
        "state": {
            "aion_request_context": RequestContext(
                request_id="request-cancel",
                trace_id="trace-cancel",
                correlation_id="corr-cancel",
                method="GET",
                path="/cancel",
                started_at=FIXED_NOW,
            )
        },
    }


async def _receive() -> dict[str, object]:
    return {"type": "http.request", "body": b"", "more_body": False}


async def _send(message: dict[str, object]) -> None:
    return None


def test_boundary_cancellation_clears_partial_state_and_propagates() -> None:
    class CancellingBoundary:
        async def build_bundle(self, **kwargs):  # noqa: ANN003
            raise asyncio.CancelledError

    async def downstream(scope, receive, send) -> None:  # noqa: ANN001
        raise AssertionError("downstream must not run after boundary cancellation")

    scope = _scope()
    middleware = ProductionAuthRequestIdentityMiddleware(
        downstream,
        boundary=CancellingBoundary(),  # type: ignore[arg-type]
    )

    with pytest.raises(asyncio.CancelledError):
        asyncio.run(middleware(scope, _receive, _send))

    assert not any(key.startswith("aion_request_identity_") for key in scope["state"])


def test_downstream_cancellation_clears_identity_state_and_propagates() -> None:
    async def downstream(scope, receive, send) -> None:  # noqa: ANN001
        assert scope["state"]["aion_request_identity_boundary_attached"] is True
        raise asyncio.CancelledError

    scope = _scope()

    with pytest.raises(asyncio.CancelledError):
        asyncio.run(ProductionAuthRequestIdentityMiddleware(downstream)(scope, _receive, _send))

    assert not any(key.startswith("aion_request_identity_") for key in scope["state"])
