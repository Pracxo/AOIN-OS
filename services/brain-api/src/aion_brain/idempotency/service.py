"""Idempotency service."""

from datetime import UTC, datetime, timedelta
from typing import Any, cast

from aion_brain.config import Settings
from aion_brain.contracts.idempotency import (
    IdempotencyCheckRequest,
    IdempotencyCheckResult,
    IdempotencyRecord,
)
from aion_brain.contracts.telemetry import (
    VisualTelemetryEvent,
    VisualTelemetryEventType,
)
from aion_brain.idempotency.hashing import sha256_json, sha256_response
from aion_brain.idempotency.repository import IdempotencyRepository


class IdempotencyService:
    """Prevent duplicate effects for retryable requests."""

    def __init__(
        self,
        repository: IdempotencyRepository,
        *,
        telemetry_service: object | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._repository = repository
        self._telemetry_service = telemetry_service
        self._settings = settings

    def check(self, request: IdempotencyCheckRequest) -> IdempotencyCheckResult:
        """Check whether a request is new, duplicate, or conflicting."""
        request_hash = sha256_json(request.request_payload)
        existing = self._repository.get(request.idempotency_key)
        if existing is None or existing.status == "expired":
            return IdempotencyCheckResult(
                duplicate=False,
                conflict=False,
                record=existing,
                reason=None,
            )
        if existing.route != request.route or existing.request_hash != request_hash:
            self._emit(
                "idempotency_conflict_detected",
                request.idempotency_key,
                0.8,
                {"route": request.route},
            )
            return IdempotencyCheckResult(
                duplicate=True,
                conflict=True,
                record=existing,
                reason="idempotency_conflict",
            )
        if existing.status == "completed":
            self._emit(
                "idempotency_duplicate_detected",
                request.idempotency_key,
                0.6,
                {"route": request.route},
            )
            return IdempotencyCheckResult(
                duplicate=True,
                conflict=False,
                record=existing,
                reason="idempotency_completed",
            )
        return IdempotencyCheckResult(
            duplicate=False,
            conflict=False,
            record=existing,
            reason=existing.status,
        )

    def start(self, request: IdempotencyCheckRequest) -> IdempotencyRecord:
        """Start idempotent processing."""
        now = datetime.now(UTC)
        ttl = (
            self._settings.idempotency_default_ttl_seconds if self._settings is not None else 86400
        )
        record = IdempotencyRecord(
            idempotency_key=request.idempotency_key,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            route=request.route,
            request_hash=sha256_json(request.request_payload),
            response_hash=None,
            status="started",
            response={},
            expires_at=request.expires_at or now + timedelta(seconds=ttl),
            created_at=now,
            updated_at=now,
        )
        saved = self._repository.save(record)
        self._emit(
            "idempotency_record_started",
            saved.idempotency_key,
            0.5,
            {"route": saved.route},
        )
        return saved

    def complete(self, idempotency_key: str, response: dict[str, Any]) -> IdempotencyRecord:
        """Store a successful idempotent response."""
        record = self._required(idempotency_key)
        return self._repository.save(
            record.model_copy(
                update={
                    "status": "completed",
                    "response": response,
                    "response_hash": sha256_response(response),
                }
            )
        )

    def fail(self, idempotency_key: str, error: dict[str, Any]) -> IdempotencyRecord:
        """Store a failed idempotent response."""
        record = self._required(idempotency_key)
        return self._repository.save(
            record.model_copy(
                update={
                    "status": "failed",
                    "response": {"error": error},
                    "response_hash": sha256_response({"error": error}),
                }
            )
        )

    def expire_old(self, now: datetime | None = None, limit: int = 100) -> int:
        """Expire old idempotency records."""
        return self._repository.expire_old(now or datetime.now(UTC), limit)

    def get(self, idempotency_key: str) -> IdempotencyRecord | None:
        """Return one idempotency record."""
        return self._repository.get(idempotency_key)

    def _required(self, idempotency_key: str) -> IdempotencyRecord:
        record = self._repository.get(idempotency_key)
        if record is None:
            raise ValueError("idempotency_record_not_found")
        return record

    def _emit(
        self,
        event_type: str,
        node_id: str,
        intensity: float,
        payload: dict[str, object],
    ) -> None:
        if self._telemetry_service is None:
            return
        event = VisualTelemetryEvent(
            telemetry_id=f"telemetry-{event_type}-{node_id}",
            trace_id=str(payload.get("trace_id") or node_id),
            event_type=cast(VisualTelemetryEventType, event_type),
            node_type="idempotency",
            node_id=node_id,
            edge_from=None,
            edge_to=node_id,
            intensity=intensity,
            payload=payload,
            created_at=datetime.now(UTC),
        )
        try:
            emit = getattr(self._telemetry_service, "emit", None)
            if callable(emit):
                emit(event)
        except Exception:
            return
