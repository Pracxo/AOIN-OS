"""Observe-only disabled request identity middleware."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from aion_brain.contracts.api import RequestContext
from aion_brain.production_auth.request_boundary import ProductionAuthRequestIdentityBoundary


class ProductionAuthRequestIdentityMiddleware(BaseHTTPMiddleware):
    """Attach anonymous disabled identity evidence without authenticating requests."""

    def __init__(
        self,
        app: ASGIApp,
        *,
        boundary: ProductionAuthRequestIdentityBoundary | None = None,
    ) -> None:
        super().__init__(app)
        self._boundary = boundary or ProductionAuthRequestIdentityBoundary()

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        context = getattr(request.state, "aion_request_context", None)
        if not isinstance(context, RequestContext):
            request.state.aion_request_identity_boundary_failed = True
            request.state.aion_request_identity_boundary_failure_reason = (
                "request_context_absent"
            )
            return await call_next(request)
        try:
            bundle = await self._boundary.build_bundle(context, registered=True)
        except Exception:
            request.state.aion_request_identity_boundary_failed = True
            request.state.aion_request_identity_boundary_failure_reason = "failed_closed"
            return await call_next(request)

        request.state.aion_request_identity_context = bundle.identity_context
        request.state.aion_request_identity_verification = bundle.verification
        request.state.aion_request_identity_audit_event = bundle.audit_event
        request.state.aion_request_identity_provenance = bundle.provenance
        request.state.aion_request_identity_boundary_bundle = bundle
        request.state.aion_request_identity_boundary_failed = False
        return await call_next(request)


__all__ = ["ProductionAuthRequestIdentityMiddleware"]
