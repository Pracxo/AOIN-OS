"""Observe-only disabled request identity ASGI middleware."""

from __future__ import annotations

import asyncio
from collections.abc import MutableMapping
from typing import Any

from starlette.requests import ClientDisconnect
from starlette.types import ASGIApp, Receive, Scope, Send

from aion_brain.contracts.api import RequestContext
from aion_brain.production_auth.request_boundary import ProductionAuthRequestIdentityBoundary

REQUEST_IDENTITY_STATE_KEYS: tuple[str, ...] = (
    "aion_request_identity_context",
    "aion_request_identity_verification",
    "aion_request_identity_audit_event",
    "aion_request_identity_provenance",
    "aion_request_identity_boundary_bundle",
    "aion_request_identity_boundary_attached",
    "aion_request_identity_boundary_failed",
    "aion_request_identity_boundary_failure_reason",
)


class ProductionAuthRequestIdentityMiddleware:
    """Attach anonymous disabled identity evidence without authenticating requests."""

    def __init__(
        self,
        app: ASGIApp,
        *,
        boundary: ProductionAuthRequestIdentityBoundary | None = None,
    ) -> None:
        self.app = app
        self._boundary = boundary or ProductionAuthRequestIdentityBoundary()

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        state = _scope_state(scope)
        forged_state_replaced = _replace_forged_identity_state(state)
        context = state.get("aion_request_context")
        if not isinstance(context, RequestContext):
            _mark_identity_failure(state, "request_context_absent")
            await self.app(scope, receive, send)
            return

        try:
            bundle = await self._boundary.build_bundle(
                request_id=context.request_id,
                trace_id=context.trace_id,
                correlation_id=context.correlation_id,
                registered=True,
            )
        except asyncio.CancelledError:
            _clear_identity_state(state)
            raise
        except Exception:
            _mark_identity_failure(
                state,
                (
                    "forged_state_replacement_failed_closed"
                    if forged_state_replaced
                    else "boundary_construction_failed_closed"
                ),
            )
            await self.app(scope, receive, send)
            return

        _attach_identity_bundle(state, bundle)
        try:
            await self.app(scope, receive, send)
        except asyncio.CancelledError:
            _clear_identity_state(state)
            raise
        except Exception as exc:
            if _is_client_disconnect(exc):
                _mark_identity_failure(state, "downstream_client_disconnect")
            raise


def register_production_auth_request_identity_middleware(
    app: Any,
    *,
    boundary: ProductionAuthRequestIdentityBoundary | None,
    enabled: bool,
) -> None:
    """Register the disabled request-identity middleware at most once."""

    if not enabled:
        return
    existing = [
        item
        for item in getattr(app, "user_middleware", ())
        if getattr(item, "cls", None) is ProductionAuthRequestIdentityMiddleware
    ]
    if existing:
        raise RuntimeError("production auth request identity middleware already registered")
    app.add_middleware(
        ProductionAuthRequestIdentityMiddleware,
        boundary=boundary,
    )


def _scope_state(scope: Scope) -> MutableMapping[str, Any]:
    state = scope.get("state")
    if isinstance(state, MutableMapping):
        return state
    replacement: dict[str, Any] = {}
    scope["state"] = replacement
    return replacement


def _replace_forged_identity_state(state: MutableMapping[str, Any]) -> bool:
    forged = any(key in state for key in REQUEST_IDENTITY_STATE_KEYS)
    if forged:
        _clear_identity_state(state)
        state["aion_request_identity_forged_state_replaced"] = True
        return True
    state.pop("aion_request_identity_forged_state_replaced", None)
    return False


def _clear_identity_state(state: MutableMapping[str, Any]) -> None:
    for key in REQUEST_IDENTITY_STATE_KEYS:
        state.pop(key, None)


def _attach_identity_bundle(
    state: MutableMapping[str, Any],
    bundle: Any,
) -> None:
    _clear_identity_state(state)
    state["aion_request_identity_context"] = bundle.identity_context
    state["aion_request_identity_verification"] = bundle.verification
    state["aion_request_identity_audit_event"] = bundle.audit_event
    state["aion_request_identity_provenance"] = bundle.provenance
    state["aion_request_identity_boundary_bundle"] = bundle
    state["aion_request_identity_boundary_failed"] = False
    state["aion_request_identity_boundary_failure_reason"] = None
    state["aion_request_identity_boundary_attached"] = True


def _mark_identity_failure(
    state: MutableMapping[str, Any],
    reason: str,
) -> None:
    _clear_identity_state(state)
    state["aion_request_identity_boundary_failed"] = True
    state["aion_request_identity_boundary_failure_reason"] = reason
    state["aion_request_identity_boundary_attached"] = False


def _is_client_disconnect(exc: Exception) -> bool:
    return isinstance(exc, ClientDisconnect) or exc.__class__.__name__ == "ClientDisconnect"


__all__ = [
    "ProductionAuthRequestIdentityMiddleware",
    "REQUEST_IDENTITY_STATE_KEYS",
    "register_production_auth_request_identity_middleware",
]
