from __future__ import annotations

import asyncio
from datetime import UTC, datetime

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
                request_id="request-stream",
                trace_id="trace-stream",
                correlation_id="corr-stream",
                method="GET",
                path="/stream",
                started_at=FIXED_NOW,
            )
        },
    }


def test_streaming_response_events_are_forwarded_unchanged_and_lazy() -> None:
    sent: list[dict[str, object]] = []
    background_executed: list[bool] = []
    yielded_chunks: list[bytes] = []
    chunks = [b"alpha", b"beta", b"gamma"]

    async def downstream(scope, receive, send) -> None:  # noqa: ANN001
        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [(b"content-type", b"text/plain")],
            }
        )
        for chunk in chunks:
            yielded_chunks.append(chunk)
            await send(
                {
                    "type": "http.response.body",
                    "body": chunk,
                    "more_body": True,
                }
            )
            await asyncio.sleep(0)
        await send({"type": "http.response.body", "body": b"", "more_body": False})
        background_executed.append(True)

    async def receive() -> dict[str, object]:
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message: dict[str, object]) -> None:
        sent.append(message.copy())

    asyncio.run(ProductionAuthRequestIdentityMiddleware(downstream)(_scope(), receive, send))

    assert sent == [
        {
            "type": "http.response.start",
            "status": 200,
            "headers": [(b"content-type", b"text/plain")],
        },
        {"type": "http.response.body", "body": b"alpha", "more_body": True},
        {"type": "http.response.body", "body": b"beta", "more_body": True},
        {"type": "http.response.body", "body": b"gamma", "more_body": True},
        {"type": "http.response.body", "body": b"", "more_body": False},
    ]
    assert yielded_chunks == chunks
    assert background_executed == [True]
