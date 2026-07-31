"""Append-only redacted model-gateway audit ledger."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from aion_brain.contracts.model_gateway import (
    MAXIMUM_AUDIT_RECORDS_PER_SESSION,
    ZERO_FINGERPRINT,
    ModelGatewayAuditRecord,
    model_gateway_fingerprint,
)


class InMemoryModelGatewayAuditLedger:
    """Append-only hash-chain audit ledger scoped by gateway session."""

    def __init__(self) -> None:
        self._records: dict[str, tuple[ModelGatewayAuditRecord, ...]] = {}

    def append(
        self,
        *,
        session_id: str,
        event_type: str,
        outcome: str,
        created_at: datetime,
        request_id: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> ModelGatewayAuditRecord:
        """Append a redacted record and return it."""

        current = self._records.get(session_id, ())
        if len(current) >= MAXIMUM_AUDIT_RECORDS_PER_SESSION:
            raise ValueError("model-gateway audit record limit exceeded")
        previous = current[-1].record_fingerprint if current else ZERO_FINGERPRINT
        record = ModelGatewayAuditRecord(
            audit_record_id=f"audit-{session_id}-{len(current) + 1:04d}",
            session_id=session_id,
            request_id=request_id,
            event_type=event_type,
            outcome=outcome,
            payload_fingerprint=model_gateway_fingerprint(payload or {}),
            previous_record_fingerprint=previous or ZERO_FINGERPRINT,
            sequence=len(current) + 1,
            created_at=created_at,
        )
        self._records = {**self._records, session_id: (*current, record)}
        return record

    def records_for_session(self, session_id: str) -> tuple[ModelGatewayAuditRecord, ...]:
        """Return the session audit chain."""

        return self._records.get(session_id, ())

    def chain_head(self, session_id: str) -> str:
        """Return the current audit chain head fingerprint."""

        records = self.records_for_session(session_id)
        if not records:
            return ZERO_FINGERPRINT
        return records[-1].record_fingerprint or ZERO_FINGERPRINT
