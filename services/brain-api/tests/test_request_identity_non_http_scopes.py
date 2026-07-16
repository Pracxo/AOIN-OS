from __future__ import annotations

import asyncio

import pytest

from aion_brain.production_auth.request_middleware import (
    ProductionAuthRequestIdentityMiddleware,
)


@pytest.mark.parametrize("scope_type", ["websocket", "lifespan", "custom_unknown_scope"])
def test_non_http_scopes_bypass_identity_boundary(scope_type: str) -> None:
    class Boundary:
        calls = 0

        async def build_bundle(self, **kwargs):  # noqa: ANN003
            self.calls += 1
            raise AssertionError("boundary must not run for non-HTTP scopes")

    boundary = Boundary()
    downstream_calls = 0
    receive_identity_preserved = False
    send_identity_preserved = False
    scope = {"type": scope_type, "state": {}}

    async def receive() -> dict[str, object]:
        return {"type": f"{scope_type}.receive"}

    async def send(message: dict[str, object]) -> None:
        return None

    async def downstream(scope_arg, receive_arg, send_arg) -> None:  # noqa: ANN001
        nonlocal downstream_calls, receive_identity_preserved, send_identity_preserved
        downstream_calls += 1
        receive_identity_preserved = receive_arg is receive
        send_identity_preserved = send_arg is send
        assert scope_arg is scope

    asyncio.run(
        ProductionAuthRequestIdentityMiddleware(
            downstream,
            boundary=boundary,  # type: ignore[arg-type]
        )(scope, receive, send)
    )

    assert downstream_calls == 1
    assert boundary.calls == 0
    assert receive_identity_preserved is True
    assert send_identity_preserved is True
    assert scope["state"] == {}
