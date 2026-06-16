"""Audit integrity status helpers."""

from __future__ import annotations

from datetime import UTC, datetime

from aion_brain.audit_integrity.repository import AuditIntegrityRepository
from aion_brain.contracts.audit_integrity import AuditIntegrityStatus


def build_audit_integrity_status(repository: AuditIntegrityRepository) -> AuditIntegrityStatus:
    """Return current audit integrity status from local records."""
    latest_entry = repository.latest_entry()
    latest_checkpoint = repository.latest_checkpoint()
    latest_verification = repository.latest_verification_run()
    verification_status = latest_verification.status if latest_verification else "not_run"
    open_violations = latest_verification.invalid_count if latest_verification else 0
    return AuditIntegrityStatus(
        latest_sequence=latest_entry.sequence_number if latest_entry else 0,
        latest_entry_hash=latest_entry.entry_hash if latest_entry else None,
        latest_checkpoint_id=latest_checkpoint.checkpoint_id if latest_checkpoint else None,
        latest_checkpoint_hash=(latest_checkpoint.checkpoint_hash if latest_checkpoint else None),
        verification_status=verification_status,
        open_violations=open_violations,
        generated_at=datetime.now(UTC),
    )
