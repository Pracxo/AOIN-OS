"""Audit integrity checkpoint service."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.audit_integrity.canonical import canonical_json
from aion_brain.audit_integrity.hashing import hash_checkpoint, sha256_text
from aion_brain.audit_integrity.repository import AuditIntegrityRepository
from aion_brain.contracts.audit_integrity import AuditIntegrityCheckpoint


class AuditCheckpointService:
    """Create and read local hash checkpoints."""

    def __init__(self, repository: AuditIntegrityRepository) -> None:
        self._repository = repository

    def create_checkpoint(
        self,
        from_sequence: int | None = None,
        to_sequence: int | None = None,
        created_by: str | None = None,
    ) -> AuditIntegrityCheckpoint:
        latest_entry = self._repository.latest_entry()
        if latest_entry is None:
            raise ValueError("no_audit_entries_to_checkpoint")
        start = from_sequence or 1
        end = to_sequence or latest_entry.sequence_number
        entries = self._repository.list_entries(
            from_sequence=start,
            to_sequence=end,
            limit=max(1, end - start + 1),
            ascending=True,
        )
        if not entries:
            raise ValueError("no_audit_entries_to_checkpoint")
        entry_hashes = [entry.entry_hash for entry in entries]
        previous_checkpoint = self._repository.latest_checkpoint()
        previous_hash = previous_checkpoint.checkpoint_hash if previous_checkpoint else None
        root_hash = sha256_text(canonical_json({"entry_hashes": entry_hashes}))
        checkpoint = AuditIntegrityCheckpoint(
            checkpoint_id=f"audit-checkpoint-{uuid4().hex}",
            from_sequence=entries[0].sequence_number,
            to_sequence=entries[-1].sequence_number,
            entry_count=len(entries),
            root_hash=root_hash,
            previous_checkpoint_hash=previous_hash,
            checkpoint_hash=hash_checkpoint(entry_hashes, previous_hash),
            hash_algorithm="sha256",
            status="created",
            metadata={"local_anchor": True},
            created_by=created_by,
            created_at=datetime.now(UTC),
        )
        return self._repository.save_checkpoint(checkpoint)

    def get_checkpoint(self, checkpoint_id: str) -> AuditIntegrityCheckpoint | None:
        """Return one checkpoint."""
        return self._repository.get_checkpoint(checkpoint_id)

    def list_checkpoints(self, limit: int = 50) -> list[AuditIntegrityCheckpoint]:
        """Return recent checkpoints."""
        return self._repository.list_checkpoints(limit=limit)
