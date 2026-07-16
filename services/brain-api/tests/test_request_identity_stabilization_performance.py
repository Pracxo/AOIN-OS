from __future__ import annotations

import asyncio
import time
from datetime import UTC, datetime

from aion_brain.contracts.api import RequestContext
from aion_brain.production_auth.request_middleware import (
    ProductionAuthRequestIdentityMiddleware,
)

FIXED_NOW = datetime(2026, 7, 16, 10, 0, 0, tzinfo=UTC)


def test_pure_asgi_middleware_performance_smoke_has_no_response_buffering() -> None:
    completed = 0

    async def downstream(scope, receive, send) -> None:  # noqa: ANN001
        nonlocal completed
        completed += 1
        await send({"type": "http.response.start", "status": 204, "headers": []})
        await send({"type": "http.response.body", "body": b"", "more_body": False})

    middleware = ProductionAuthRequestIdentityMiddleware(downstream)

    async def receive() -> dict[str, object]:
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message: dict[str, object]) -> None:
        return None

    async def run_many() -> None:
        for index in range(250):
            scope = {
                "type": "http",
                "state": {
                    "aion_request_context": RequestContext(
                        request_id=f"request-perf-{index}",
                        trace_id=f"trace-perf-{index}",
                        correlation_id=f"corr-perf-{index}",
                        method="GET",
                        path="/perf",
                        started_at=FIXED_NOW,
                    )
                },
            }
            await middleware(scope, receive, send)

    start = time.perf_counter()
    asyncio.run(run_many())
    elapsed = time.perf_counter() - start

    assert completed == 250
    assert elapsed < 5.0
