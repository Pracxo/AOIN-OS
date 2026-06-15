"""Request context middleware for AION Brain APIs."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any, Protocol, cast
from uuid import uuid4

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from aion_brain.contracts.api import AIONError, RequestContext
from aion_brain.contracts.performance import PerformanceSample
from aion_brain.contracts.telemetry import (
    VisualTelemetryEvent,
    VisualTelemetryEventType,
)


class _AuditService(Protocol):
    def start_record(self, context: RequestContext, request: Request) -> object:
        """Create a safe request audit record."""

    def complete_record(
        self,
        request_id: str,
        status_code: int,
        response_metadata: dict[str, Any],
        error: AIONError | None = None,
    ) -> object:
        """Complete a safe request audit record."""


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Create request context, propagate headers, and audit safe metadata."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        context = _build_context(request)
        request.state.aion_request_context = context
        audit_service = _audit_service(request)
        if audit_service is not None and _audit_enabled(request):
            try:
                audit_service.start_record(context, request)
            except Exception:
                request.state.aion_audit_failed = True
        _emit_api_telemetry(request, "api_request_started", context.request_id, 0.3)
        try:
            response = await call_next(request)
        except Exception:
            if audit_service is not None and _audit_enabled(request):
                _complete_audit(request, audit_service, context, 500)
            raise
        _apply_headers(request, response, context)
        error = getattr(request.state, "aion_error", None)
        _complete_audit(request, audit_service, context, response.status_code, error)
        _emit_api_telemetry(
            request,
            "api_request_completed",
            context.request_id,
            0.6 if response.status_code < 400 else 0.9,
        )
        _record_api_performance_sample(request, context, response.status_code)
        return response


def _build_context(request: Request) -> RequestContext:
    now = datetime.now(UTC)
    correlation_id = _header(request, "X-AION-Correlation-ID") or f"corr-{uuid4().hex}"
    return RequestContext(
        request_id=f"request-{uuid4().hex}",
        trace_id=_header(request, "X-AION-Trace-ID"),
        correlation_id=correlation_id,
        idempotency_key=_header(request, "X-AION-Idempotency-Key"),
        actor_id=_header(request, "X-AION-Actor-ID"),
        workspace_id=_header(request, "X-AION-Workspace-ID"),
        method=request.method,
        path=request.url.path,
        route_name=None,
        started_at=now,
        metadata={"api_version": _api_version(request)},
    )


def _apply_headers(request: Request, response: Response, context: RequestContext) -> None:
    response.headers["X-AION-Request-ID"] = context.request_id
    if context.correlation_id:
        response.headers["X-AION-Correlation-ID"] = context.correlation_id
    if context.trace_id:
        response.headers["X-AION-Trace-ID"] = context.trace_id
    response.headers["X-AION-Version"] = _api_version(request)


def _complete_audit(
    request: Request,
    audit_service: _AuditService | None,
    context: RequestContext,
    status_code: int,
    error: object | None = None,
) -> None:
    if audit_service is None or not _audit_enabled(request):
        return
    aion_error = error if isinstance(error, AIONError) else None
    try:
        audit_service.complete_record(
            context.request_id,
            status_code,
            {"status_code": status_code},
            aion_error,
        )
    except Exception:
        request.state.aion_audit_failed = True


def _emit_api_telemetry(
    request: Request,
    event_type: str,
    node_id: str,
    intensity: float,
) -> None:
    container = getattr(request.app.state, "kernel_container", None)
    telemetry = getattr(container, "telemetry_service", None)
    emit = getattr(telemetry, "emit", None)
    if not callable(emit):
        return
    context = getattr(request.state, "aion_request_context", None)
    trace_id = context.trace_id if isinstance(context, RequestContext) else node_id
    try:
        emit(
            VisualTelemetryEvent(
                telemetry_id=f"telemetry-{node_id}-{event_type}-{uuid4().hex}",
                trace_id=trace_id or node_id,
                event_type=cast(VisualTelemetryEventType, event_type),
                node_type="request",
                node_id=node_id,
                edge_from=None,
                edge_to=None,
                intensity=intensity,
                payload={"path": request.url.path, "method": request.method},
                created_at=datetime.now(UTC),
            )
        )
    except Exception:
        return


def _audit_service(request: Request) -> _AuditService | None:
    container = getattr(request.app.state, "kernel_container", None)
    service = getattr(container, "api_request_audit_service", None)
    if service is None:
        return None
    return cast(_AuditService, service)


def _audit_enabled(request: Request) -> bool:
    container = getattr(request.app.state, "kernel_container", None)
    settings = getattr(container, "settings", None)
    return bool(getattr(settings, "api_request_audit_enabled", True))


def _record_api_performance_sample(
    request: Request,
    context: RequestContext,
    status_code: int,
) -> None:
    container = getattr(request.app.state, "kernel_container", None)
    settings = getattr(container, "settings", None)
    if not bool(getattr(settings, "performance_sample_api_requests", True)):
        return
    repository = getattr(container, "performance_repository", None)
    save_sample = getattr(repository, "save_sample", None)
    if not callable(save_sample):
        return
    threshold_ms = int(getattr(settings, "performance_default_threshold_ms", 1000))
    duration = max(0, int((datetime.now(UTC) - context.started_at).total_seconds() * 1000))
    if status_code >= 500:
        status = "failed"
    elif status_code >= 400 or duration > threshold_ms:
        status = "warning"
    else:
        status = "passed"
    try:
        save_sample(
            PerformanceSample(
                performance_sample_id=f"performance-sample-{uuid4().hex}",
                trace_id=context.trace_id,
                benchmark_run_id=None,
                operation_type="api_request",
                component=context.route_name or context.path,
                status=status,  # type: ignore[arg-type]
                duration_ms=duration,
                input_size_bytes=None,
                output_size_bytes=None,
                item_count=1,
                error={"status_code": status_code} if status == "failed" else {},
                metadata={
                    "path": context.path,
                    "method": context.method,
                    "status_code": status_code,
                    "body_stored": False,
                },
                created_at=datetime.now(UTC),
            )
        )
    except Exception:
        request.state.aion_performance_sampling_failed = True


def _api_version(request: Request) -> str:
    container = getattr(request.app.state, "kernel_container", None)
    settings = getattr(container, "settings", None)
    return str(getattr(settings, "api_version", "v0.1"))


def _header(request: Request, name: str) -> str | None:
    value = request.headers.get(name)
    if value is None or not value.strip():
        return None
    return value.strip()
