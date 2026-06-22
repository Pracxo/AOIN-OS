"""AION API response helpers."""

from typing import Any

from fastapi import Request
from starlette.responses import JSONResponse

from aion_brain.api_support.context import get_request_context
from aion_brain.contracts.api import AIONError, AIONErrorResponse, AIONSuccessEnvelope


def success(
    data: Any,
    request: Request,
    metadata: dict[str, Any] | None = None,
) -> AIONSuccessEnvelope:
    """Build an optional success envelope for new support endpoints."""
    context = get_request_context(request)
    return AIONSuccessEnvelope(
        data=data,
        trace_id=context.trace_id,
        correlation_id=context.correlation_id,
        request_id=context.request_id,
        metadata=metadata or {},
    )


def error_response(error: AIONError, status_code: int) -> JSONResponse:
    """Build the standard JSON error response."""
    return JSONResponse(
        status_code=status_code,
        content=AIONErrorResponse(error=error).model_dump(mode="json"),
    )
