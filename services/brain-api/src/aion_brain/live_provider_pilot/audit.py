"""Audit helpers for AION-248."""

from __future__ import annotations

from datetime import datetime

from aion_brain.contracts.live_provider_pilot import (
    ZERO_FINGERPRINT,
    LiveProviderAuditOutcome,
    LiveProviderAuditRecord,
)


class InMemoryLiveProviderAuditLedger:
    """In-memory audit ledger for deterministic tests and runner evidence."""

    def __init__(self) -> None:
        self._records: tuple[LiveProviderAuditRecord, ...] = ()

    def record_audit(
        self,
        *,
        audit_id: str,
        event_type: str,
        outcome: LiveProviderAuditOutcome,
        subject_fingerprint: str = ZERO_FINGERPRINT,
        created_at: datetime,
    ) -> LiveProviderAuditRecord:
        """Append an audit event and return the new chain head."""

        previous = self.chain_head()
        record = LiveProviderAuditRecord(
            audit_id=audit_id,
            event_type=event_type,
            outcome=outcome,
            subject_fingerprint=subject_fingerprint,
            previous_audit_fingerprint=previous,
            created_at=created_at,
        )
        self._records = (*self._records, record)
        return record

    def chain_head(self) -> str:
        """Return the current audit chain head."""

        if not self._records:
            return ZERO_FINGERPRINT
        return self._records[-1].audit_fingerprint or ZERO_FINGERPRINT

    def list_records(self) -> tuple[LiveProviderAuditRecord, ...]:
        """Return records in append order."""

        return self._records
