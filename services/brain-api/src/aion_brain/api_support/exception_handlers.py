"""Standard exception handlers for AION Brain APIs."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import Response

from aion_brain.api_support import error_codes
from aion_brain.api_support.context import get_request_context
from aion_brain.api_support.errors import AIONException, sanitize_detail
from aion_brain.api_support.responses import error_response
from aion_brain.contracts.api import AIONError, APIErrorCategory
from aion_brain.contracts.observability import ObservabilityEvent
from aion_brain.contracts.telemetry import VisualTelemetryEvent


def register_exception_handlers(app: FastAPI) -> None:
    """Install standard AION exception handlers."""
    app.add_exception_handler(AIONException, cast(Any, _handle_aion_exception))
    app.add_exception_handler(RequestValidationError, cast(Any, _handle_validation_error))
    app.add_exception_handler(StarletteHTTPException, cast(Any, _handle_http_exception))
    app.add_exception_handler(Exception, _handle_generic_exception)
    app.state.aion_exception_handlers_present = True


async def _handle_aion_exception(request: Request, exc: AIONException) -> Response:
    error = _error_from_exception(request, exc)
    _record_error(request, error)
    return error_response(error, exc.status_code)


async def _handle_validation_error(request: Request, exc: RequestValidationError) -> Response:
    error = _build_error(
        request,
        code=error_codes.AION_VALIDATION_ERROR,
        category="validation",
        message="AION request validation failed.",
        detail={"errors": sanitize_detail(exc.errors())},
        retryable=False,
    )
    _record_error(request, error)
    return error_response(error, 422)


async def _handle_http_exception(request: Request, exc: StarletteHTTPException) -> Response:
    code, category, message = _http_error_mapping(request, exc)
    error = _build_error(
        request,
        code=code,
        category=category,
        message=message,
        detail=sanitize_detail(exc.detail),
        retryable=error_codes.retryable_for_code(code),
    )
    _record_error(request, error)
    return error_response(error, exc.status_code)


async def _handle_generic_exception(request: Request, exc: Exception) -> Response:
    error = _build_error(
        request,
        code=error_codes.AION_INTERNAL_ERROR,
        category="internal",
        message="An internal AION error occurred.",
        detail={},
        retryable=False,
    )
    _record_error(request, error)
    return error_response(error, 500)


def _error_from_exception(request: Request, exc: AIONException) -> AIONError:
    return _build_error(
        request,
        code=exc.code,
        category=exc.category,
        message=exc.message,
        detail=exc.detail,
        retryable=exc.retryable,
    )


def _build_error(
    request: Request,
    *,
    code: str,
    category: str,
    message: str,
    detail: dict[str, Any],
    retryable: bool,
) -> AIONError:
    try:
        context = get_request_context(request)
        trace_id = context.trace_id
        correlation_id = context.correlation_id
        request_id = context.request_id
    except Exception:
        trace_id = None
        correlation_id = None
        request_id = None
    return AIONError(
        code=code,
        category=cast(APIErrorCategory, category),
        message=message,
        detail=detail,
        trace_id=trace_id,
        correlation_id=correlation_id,
        request_id=request_id,
        retryable=retryable,
        created_at=datetime.now(UTC),
    )


def _http_error_mapping(
    request: Request,
    exc: StarletteHTTPException,
) -> tuple[str, str, str]:
    if exc.status_code == 404:
        route = request.scope.get("route")
        code = error_codes.AION_NOT_FOUND if route is not None else error_codes.AION_ROUTE_NOT_FOUND
        return code, "not_found", "AION route or resource was not found."
    if exc.status_code == 405:
        return error_codes.AION_METHOD_NOT_ALLOWED, "unsupported", "AION method is not allowed."
    if exc.status_code == 401:
        return error_codes.AION_UNAUTHORIZED, "authentication", "AION authentication is required."
    if exc.status_code == 403:
        return error_codes.AION_FORBIDDEN, "authorization", "AION authorization failed."
    if exc.status_code == 409:
        return error_codes.AION_CONFLICT, "conflict", "AION request conflicted with state."
    if exc.status_code == 413:
        return error_codes.AION_REQUEST_TOO_LARGE, "validation", "AION request is too large."
    if exc.status_code == 429:
        return error_codes.AION_RATE_LIMITED, "rate_limit", "AION rate limit exceeded."
    if exc.status_code >= 500:
        return error_codes.AION_INTERNAL_ERROR, "internal", "AION request failed."
    return error_codes.AION_VALIDATION_ERROR, "validation", "AION request failed."


def _record_error(request: Request, error: AIONError) -> None:
    request.state.aion_error = error
    _emit_error_telemetry(request, error)
    _record_observability(request, error)


def _emit_error_telemetry(request: Request, error: AIONError) -> None:
    container = getattr(request.app.state, "kernel_container", None)
    telemetry = getattr(container, "telemetry_service", None)
    emit = getattr(telemetry, "emit", None)
    if not callable(emit):
        return
    node_id = error.request_id or f"api-error-{uuid4().hex}"
    try:
        emit(
            VisualTelemetryEvent(
                telemetry_id=f"telemetry-{node_id}-api_error_recorded-{uuid4().hex}",
                trace_id=error.trace_id or node_id,
                event_type="api_error_recorded",
                node_type="error",
                node_id=node_id,
                edge_from=None,
                edge_to=None,
                intensity=0.9,
                payload={"code": error.code, "category": error.category},
                created_at=datetime.now(UTC),
            )
        )
    except Exception:
        return


def _record_observability(request: Request, error: AIONError) -> None:
    container = getattr(request.app.state, "kernel_container", None)
    observability = getattr(container, "observability_service", None)
    record_event = getattr(observability, "record_event", None)
    if not callable(record_event):
        return
    try:
        record_event(
            ObservabilityEvent(
                observability_event_id=f"observability-{uuid4().hex}",
                trace_id=error.trace_id,
                correlation_id=error.correlation_id,
                event_type="api_error_recorded",
                component="api",
                level="error" if error.category == "internal" else "warning",
                message=error.message,
                payload={"code": error.code, "category": error.category},
                created_at=datetime.now(UTC),
            )
        )
    except Exception:
        return
