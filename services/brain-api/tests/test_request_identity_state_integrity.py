from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from aion_brain.contracts.api import RequestContext
from aion_brain.production_auth.request_middleware import (
    ProductionAuthRequestIdentityMiddleware,
)

FIXED_NOW = datetime(2026, 7, 16, 10, 0, 0, tzinfo=UTC)


def _context(request_id: str = "request-state") -> RequestContext:
    return RequestContext(
        request_id=request_id,
        trace_id=f"trace-{request_id}",
        correlation_id=f"corr-{request_id}",
        actor_id="forged-actor-must-not-survive",
        workspace_id="workspace-must-not-survive",
        idempotency_key="idem-must-not-survive",
        method="POST",
        path="/state",
        started_at=FIXED_NOW,
        metadata={"source": "request-context"},
    )


async def _receive() -> dict[str, object]:
    return {"type": "http.request", "body": b"", "more_body": False}


async def _send(message: dict[str, object]) -> None:
    return None


def test_forged_authenticated_identity_state_is_replaced_with_disabled_evidence() -> None:
    seen: dict[str, object] = {}

    class ForgedIdentity:
        authenticated = True
        actor_id = "attacker"

    async def downstream(scope, receive, send) -> None:  # noqa: ANN001
        state = scope["state"]
        identity = state["aion_request_identity_context"]
        seen["forged_replaced"] = state["aion_request_identity_forged_state_replaced"]
        seen["authenticated"] = identity.authenticated
        seen["actor_id"] = identity.actor_id
        seen["request_id"] = identity.request_id
        seen["serialized"] = str(state["aion_request_identity_boundary_bundle"].model_dump())

    scope = {
        "type": "http",
        "state": {
            "aion_request_context": _context(),
            "aion_request_identity_context": ForgedIdentity(),
            "aion_request_identity_boundary_attached": True,
            "aion_request_identity_boundary_failed": False,
        },
    }

    asyncio.run(
        ProductionAuthRequestIdentityMiddleware(downstream)(scope, _receive, _send)
    )

    assert seen["forged_replaced"] is True
    assert seen["authenticated"] is False
    assert seen["actor_id"] is None
    assert seen["request_id"] == "request-state"
    assert "attacker" not in str(seen["serialized"])
    assert "workspace-must-not-survive" not in str(seen["serialized"])
    assert "idem-must-not-survive" not in str(seen["serialized"])


def test_forged_state_reconstruction_failure_uses_fixed_safe_reason() -> None:
    class FailingBoundary:
        async def build_bundle(self, **kwargs):  # noqa: ANN003
            raise RuntimeError("do not leak this text")

    seen: dict[str, object] = {}

    async def downstream(scope, receive, send) -> None:  # noqa: ANN001
        state = scope["state"]
        seen["failed"] = state["aion_request_identity_boundary_failed"]
        seen["reason"] = state["aion_request_identity_boundary_failure_reason"]
        seen["attached"] = state["aion_request_identity_boundary_attached"]
        seen["has_context"] = "aion_request_identity_context" in state

    scope = {
        "type": "http",
        "state": {
            "aion_request_context": _context("request-failed"),
            "aion_request_identity_context": object(),
        },
    }

    asyncio.run(
        ProductionAuthRequestIdentityMiddleware(
            downstream,
            boundary=FailingBoundary(),  # type: ignore[arg-type]
        )(scope, _receive, _send)
    )

    assert seen == {
        "failed": True,
        "reason": "forged_state_replacement_failed_closed",
        "attached": False,
        "has_context": False,
    }
    assert "do not leak this text" not in str(scope["state"])


def test_missing_context_fails_closed_without_identity_evidence() -> None:
    seen: dict[str, object] = {}

    async def downstream(scope, receive, send) -> None:  # noqa: ANN001
        state = scope["state"]
        seen["failed"] = state["aion_request_identity_boundary_failed"]
        seen["reason"] = state["aion_request_identity_boundary_failure_reason"]
        seen["attached"] = state["aion_request_identity_boundary_attached"]
        seen["has_context"] = "aion_request_identity_context" in state

    scope = {"type": "http", "state": {}}

    asyncio.run(
        ProductionAuthRequestIdentityMiddleware(downstream)(scope, _receive, _send)
    )

    assert seen == {
        "failed": True,
        "reason": "request_context_absent",
        "attached": False,
        "has_context": False,
    }
