"""In-memory semantic memory adapter for tests."""

import re
from datetime import UTC, datetime

from aion_brain.contracts.memory import MemoryRecord, MemoryType


class InMemorySemanticMemoryAdapter:
    """Deterministic semantic memory adapter for tests and local units."""

    def __init__(self) -> None:
        self._records: dict[str, MemoryRecord] = {}
        self._deleted_at: dict[str, datetime] = {}

    def remember(self, record: MemoryRecord) -> str:
        """Store a memory record."""
        self._records[record.memory_id] = record
        self._deleted_at.pop(record.memory_id, None)
        return record.memory_id

    def get(self, memory_id: str) -> MemoryRecord | None:
        """Return a stored record if it has not been deleted."""
        if memory_id in self._deleted_at:
            return None
        record = self._records.get(memory_id)
        if record is not None and _is_expired(record.expires_at):
            return None
        return record

    def retrieve(
        self,
        query: str,
        scope: list[str],
        limit: int = 10,
        memory_types: list[MemoryType] | None = None,
    ) -> list[MemoryRecord]:
        """Retrieve active memory using deterministic lexical ranking."""
        allowed_types = set(memory_types or [])
        candidates = [
            record
            for record in self._records.values()
            if record.memory_id not in self._deleted_at
            and _scope_matches(record.owner_scope, scope)
            and (not allowed_types or record.memory_type in allowed_types)
            and not _is_expired(record.expires_at)
        ]
        return rank_memory_records(query, candidates)[:limit]

    def forget(self, memory_id: str) -> bool:
        """Soft-delete a memory record."""
        if memory_id not in self._records or memory_id in self._deleted_at:
            return False
        self._deleted_at[memory_id] = datetime.now(UTC)
        return True

    def list_active(
        self,
        scope: list[str],
        *,
        limit: int = 100,
        memory_types: list[MemoryType] | None = None,
    ) -> list[MemoryRecord]:
        """List active non-expired memory records."""
        allowed_types = set(memory_types or [])
        records = [
            record
            for record in self._records.values()
            if record.memory_id not in self._deleted_at
            and _scope_matches(record.owner_scope, scope)
            and (not allowed_types or record.memory_type in allowed_types)
            and not _is_expired(record.expires_at)
        ]
        return sorted(records, key=lambda record: record.created_at, reverse=True)[:limit]

    def update_metadata(self, memory_id: str, metadata: dict[str, object]) -> MemoryRecord | None:
        """Update metadata for a stored active record."""
        record = self.get(memory_id)
        if record is None:
            return None
        updated = record.model_copy(update={"metadata": dict(metadata)})
        self._records[memory_id] = updated
        return updated

    def expire(self, memory_id: str, expires_at: datetime | None = None) -> bool:
        """Expire a record without marking it deleted."""
        record = self.get(memory_id)
        if record is None:
            return False
        self._records[memory_id] = record.model_copy(
            update={"expires_at": expires_at or datetime.now(UTC)}
        )
        return True


def rank_memory_records(query: str, records: list[MemoryRecord]) -> list[MemoryRecord]:
    """Rank memory by lexical overlap, then recency, then confidence."""
    query_tokens = _tokens(query)

    def sort_key(record: MemoryRecord) -> tuple[int, float, float]:
        overlap = len(query_tokens.intersection(_tokens(record.summary)))
        return (overlap, record.created_at.timestamp(), record.confidence)

    return sorted(records, key=sort_key, reverse=True)


def _tokens(value: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", value.lower()))


def _scope_matches(record_scope: list[str], requested_scope: list[str]) -> bool:
    return bool(set(record_scope).intersection(requested_scope))


def _is_expired(expires_at: datetime | None) -> bool:
    if expires_at is None:
        return False
    current = datetime.now(UTC)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    return expires_at <= current
