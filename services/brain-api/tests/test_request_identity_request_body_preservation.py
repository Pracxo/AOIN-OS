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
                request_id="request-body",
                trace_id="trace-body",
                correlation_id="corr-body",
                method="POST",
                path="/body",
                started_at=FIXED_NOW,
            )
        },
    }


def test_receive_callable_and_body_events_are_preserved() -> None:
    original_events = [
        {"type": "http.request", "body": b"one", "more_body": True},
        {"type": "http.request", "body": b"two", "more_body": True},
        {"type": "http.request", "body": b"", "more_body": False},
        {"type": "http.disconnect"},
    ]
    events = list(original_events)
    received: list[dict[str, object]] = []
    receive_calls = 0
    receive_identity_preserved = False
    send_identity_preserved = False

    async def receive() -> dict[str, object]:
        nonlocal receive_calls
        receive_calls += 1
        return events.pop(0)

    async def send(message: dict[str, object]) -> None:
        return None

    async def downstream(scope, receive_arg, send_arg) -> None:  # noqa: ANN001
        nonlocal receive_identity_preserved, send_identity_preserved
        receive_identity_preserved = receive_arg is receive
        send_identity_preserved = send_arg is send
        while True:
            message = await receive_arg()
            received.append(message)
            if message["type"] == "http.disconnect" or not message.get("more_body", False):
                break
        await send_arg({"type": "http.response.start", "status": 204, "headers": []})
        await send_arg({"type": "http.response.body", "body": b"", "more_body": False})

    asyncio.run(ProductionAuthRequestIdentityMiddleware(downstream)(_scope(), receive, send))

    assert receive_identity_preserved is True
    assert send_identity_preserved is True
    assert receive_calls == 3
    assert received == original_events[:3]
    assert events == [original_events[3]]


def test_empty_body_request_remains_unchanged() -> None:
    events = [{"type": "http.request", "body": b"", "more_body": False}]
    received: list[dict[str, object]] = []

    async def receive() -> dict[str, object]:
        return events.pop(0)

    async def send(message: dict[str, object]) -> None:
        return None

    async def downstream(scope, receive_arg, send_arg) -> None:  # noqa: ANN001
        received.append(await receive_arg())
        await send_arg({"type": "http.response.start", "status": 204, "headers": []})
        await send_arg({"type": "http.response.body", "body": b"", "more_body": False})

    asyncio.run(ProductionAuthRequestIdentityMiddleware(downstream)(_scope(), receive, send))

    assert received == [{"type": "http.request", "body": b"", "more_body": False}]
