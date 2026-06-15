"""API request audit tests."""

from datetime import UTC, datetime

from fastapi import Request
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from aion_brain.api_support.request_audit import APIRequestAuditService
from aion_brain.contracts.api import RequestContext


def _request() -> Request:
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/brain/test",
            "headers": [(b"user-agent", b"pytest"), (b"authorization", b"secret")],
            "client": ("127.0.0.1", 1234),
            "query_string": b"token=secret",
            "server": ("testserver", 80),
            "scheme": "http",
        }
    )


def _service() -> APIRequestAuditService:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    return APIRequestAuditService(engine=engine)


def test_request_audit_service_creates_record_without_request_body_or_raw_headers() -> None:
    service = _service()
    context = RequestContext(
        request_id="request-test",
        trace_id="trace-test",
        correlation_id="corr-test",
        idempotency_key=None,
        actor_id="actor-test",
        workspace_id="workspace-test",
        method="GET",
        path="/brain/test",
        route_name=None,
        started_at=datetime.now(UTC),
        metadata={},
    )

    record = service.start_record(context, _request())

    assert record.request_id == "request-test"
    assert "body" not in record.request_metadata
    assert "headers" not in record.request_metadata
    assert record.request_metadata == {"query_param_count": 1}


def test_request_audit_service_completes_record_with_status_code() -> None:
    service = _service()
    context = RequestContext(
        request_id="request-test",
        method="GET",
        path="/brain/test",
        started_at=datetime.now(UTC),
        metadata={},
    )
    service.start_record(context, _request())

    completed = service.complete_record("request-test", 200, {"status_code": 200})

    assert completed.status_code == 200
    assert completed.completed_at is not None
