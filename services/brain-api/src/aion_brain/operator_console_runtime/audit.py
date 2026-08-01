"""In-memory redacted audit chain for the local console bridge."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable

from aion_brain.contracts.operator_console_integration import (
    ZERO_FINGERPRINT,
    OperatorConsoleAuditProjection,
    OperatorConsoleAuditRecord,
    OperatorConsoleIntegrityStatus,
    OperatorConsoleRouteKind,
    fingerprint_text,
    utc_now,
)


class InMemoryOperatorConsoleAuditLedger:
    """Append-only hash chain containing event metadata and fingerprints only."""

    def __init__(self) -> None:
        self._records: dict[str, tuple[OperatorConsoleAuditRecord, ...]] = {}

    def append(
        self,
        *,
        session_id: str,
        event_type: str,
        request_id: str | None = None,
        subject_fingerprints: Iterable[str] = (),
        reason_codes: Iterable[str] = (),
    ) -> OperatorConsoleAuditRecord:
        prior = self.chain_head(session_id)
        records = self._records.get(session_id, ())
        record = OperatorConsoleAuditRecord(
            session_id=session_id,
            request_id=request_id,
            sequence_number=len(records) + 1,
            event_type=event_type,
            prior_record_fingerprint=prior,
            subject_fingerprints=tuple(subject_fingerprints),
            reason_codes=tuple(reason_codes),
            created_at=utc_now(),
        )
        self._records = {**self._records, session_id: (*records, record)}
        return record

    def records_by_session(self, session_id: str) -> tuple[OperatorConsoleAuditRecord, ...]:
        return self._records.get(session_id, ())

    def chain_head(self, session_id: str) -> str:
        records = self._records.get(session_id, ())
        if not records:
            return ZERO_FINGERPRINT
        return records[-1].record_fingerprint or ZERO_FINGERPRINT

    def event_counts(self, session_id: str) -> dict[str, int]:
        counter: Counter[str] = Counter(
            record.event_type for record in self.records_by_session(session_id)
        )
        return dict(sorted(counter.items()))

    def verify_chain(self, session_id: str) -> bool:
        prior = ZERO_FINGERPRINT
        for record in self.records_by_session(session_id):
            if record.prior_record_fingerprint != prior:
                return False
            prior = record.record_fingerprint or ZERO_FINGERPRINT
        return True

    def projection(
        self,
        *,
        session_id: str,
        receipt_chain_heads: dict[str, str],
    ) -> OperatorConsoleAuditProjection:
        records = self.records_by_session(session_id)
        latest = records[-1].created_at if records else utc_now()
        return OperatorConsoleAuditProjection(
            event_type_counts=self.event_counts(session_id),
            audit_chain_head=self.chain_head(session_id),
            receipt_chain_heads=receipt_chain_heads,
            latest_safe_timestamps={"latest_audit_record": latest},
            integrity_status=(
                OperatorConsoleIntegrityStatus.passed
                if self.verify_chain(session_id)
                else OperatorConsoleIntegrityStatus.failed
            ),
        )


def route_event_type(route_path: str, route_kind: OperatorConsoleRouteKind) -> str:
    if route_kind == OperatorConsoleRouteKind.read_projection:
        return route_path.rsplit("/", 1)[-1] + "_projected"
    return fingerprint_text("route-event", f"{route_kind.value}:{route_path}")[:32]
