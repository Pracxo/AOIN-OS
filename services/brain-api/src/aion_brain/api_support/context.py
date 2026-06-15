"""Request context accessors."""

from fastapi import Request

from aion_brain.contracts.api import RequestContext


def get_request_context(request: Request) -> RequestContext:
    """Return the current request context, creating a minimal fallback if absent."""
    context = getattr(request.state, "aion_request_context", None)
    if isinstance(context, RequestContext):
        return context
    raise RuntimeError("AION request context is not configured")


def get_request_id(request: Request) -> str:
    """Return the AION request ID."""
    return get_request_context(request).request_id


def get_trace_id(request: Request) -> str | None:
    """Return the propagated trace ID."""
    return get_request_context(request).trace_id


def get_correlation_id(request: Request) -> str | None:
    """Return the propagated correlation ID."""
    return get_request_context(request).correlation_id


def get_idempotency_key(request: Request) -> str | None:
    """Return the propagated idempotency key."""
    return get_request_context(request).idempotency_key
