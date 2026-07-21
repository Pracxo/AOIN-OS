"""Append-only repositories for persistent cognitive state."""

from __future__ import annotations

import json
import sqlite3
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from aion_brain.contracts.cognitive_state import (
    CognitiveEvent,
    CognitiveStateCheckpoint,
)

ALLOWED_SQLITE_SUFFIXES = {".sqlite", ".sqlite3", ".db"}


class CognitiveStateRepositoryError(RuntimeError):
    """Base sanitized repository error."""


class DuplicateCognitiveEventError(CognitiveStateRepositoryError):
    """Raised when an idempotency key is reused for a different event."""


class StaleCognitiveStateVersionError(CognitiveStateRepositoryError):
    """Raised when optimistic concurrency detects a stale expected sequence."""


class CognitiveStateCheckpointError(CognitiveStateRepositoryError):
    """Raised when checkpoint storage or verification fails."""


@dataclass(frozen=True)
class CognitiveStateAppendResult:
    """Result of one append-only event write."""

    event: CognitiveEvent
    duplicate: bool


class CognitiveStateRepository(Protocol):
    """Persistence protocol required by the cognitive-state service."""

    def append_event(self, event: CognitiveEvent) -> CognitiveStateAppendResult: ...

    def list_events(
        self,
        *,
        from_sequence: int = 1,
        limit: int | None = None,
    ) -> tuple[CognitiveEvent, ...]: ...

    def latest_sequence(self) -> int: ...

    def save_checkpoint(self, checkpoint: CognitiveStateCheckpoint) -> CognitiveStateCheckpoint: ...

    def get_checkpoint(self, checkpoint_id: str) -> CognitiveStateCheckpoint | None: ...

    def latest_checkpoint(self) -> CognitiveStateCheckpoint | None: ...

    def delete_events_before(self, sequence: int) -> int: ...


class InMemoryCognitiveStateRepository:
    """Thread-safe in-memory repository for local tests and dry runs."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._events: list[CognitiveEvent] = []
        self._events_by_id: dict[str, CognitiveEvent] = {}
        self._events_by_idempotency: dict[str, CognitiveEvent] = {}
        self._checkpoints: dict[str, CognitiveStateCheckpoint] = {}

    def append_event(self, event: CognitiveEvent) -> CognitiveStateAppendResult:
        with self._lock:
            existing = self._events_by_idempotency.get(event.idempotency_key)
            if existing is not None:
                _assert_same_idempotent_event(existing, event)
                return CognitiveStateAppendResult(event=existing, duplicate=True)
            if event.event_id in self._events_by_id:
                raise DuplicateCognitiveEventError("cognitive_state_event_id_reused")
            latest_sequence = self._events[-1].sequence if self._events else 0
            _assert_expected_sequence(latest_sequence, event.expected_previous_sequence)
            stored = assign_event_sequence(event, latest_sequence + 1)
            self._events.append(stored)
            self._events_by_id[stored.event_id] = stored
            self._events_by_idempotency[stored.idempotency_key] = stored
            return CognitiveStateAppendResult(event=stored, duplicate=False)

    def list_events(
        self,
        *,
        from_sequence: int = 1,
        limit: int | None = None,
    ) -> tuple[CognitiveEvent, ...]:
        with self._lock:
            events = [event for event in self._events if event.sequence >= from_sequence]
            if limit is not None:
                events = events[:limit]
            return tuple(events)

    def latest_sequence(self) -> int:
        with self._lock:
            return self._events[-1].sequence if self._events else 0

    def save_checkpoint(self, checkpoint: CognitiveStateCheckpoint) -> CognitiveStateCheckpoint:
        with self._lock:
            existing = self._checkpoints.get(checkpoint.checkpoint_id)
            if existing is not None and existing.checkpoint_hash != checkpoint.checkpoint_hash:
                raise CognitiveStateCheckpointError("cognitive_state_checkpoint_id_reused")
            self._checkpoints[checkpoint.checkpoint_id] = checkpoint
            return checkpoint

    def get_checkpoint(self, checkpoint_id: str) -> CognitiveStateCheckpoint | None:
        with self._lock:
            return self._checkpoints.get(checkpoint_id)

    def latest_checkpoint(self) -> CognitiveStateCheckpoint | None:
        with self._lock:
            if not self._checkpoints:
                return None
            return max(self._checkpoints.values(), key=lambda checkpoint: checkpoint.sequence)

    def delete_events_before(self, sequence: int) -> int:
        if sequence < 1:
            raise ValueError("sequence must be at least 1")
        with self._lock:
            removed = [event for event in self._events if event.sequence < sequence]
            self._events = [event for event in self._events if event.sequence >= sequence]
            self._events_by_id = {event.event_id: event for event in self._events}
            self._events_by_idempotency = {
                event.idempotency_key: event for event in self._events
            }
            return len(removed)


class ExplicitLocalCognitiveStateRepository:
    """Explicit operator-supplied local SQLite cognitive-state repository."""

    def __init__(
        self,
        *,
        database_path: Path | str,
        repo_root: Path | str | None = None,
        initialize: bool = False,
        timeout_seconds: float = 5.0,
    ) -> None:
        self.database_path = validate_explicit_sqlite_path(database_path, repo_root=repo_root)
        self._timeout_seconds = timeout_seconds
        if initialize:
            self.initialize_schema()

    def initialize_schema(self) -> None:
        """Explicitly initialize the local SQLite schema."""

        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS cognitive_state_events (
                    sequence INTEGER PRIMARY KEY,
                    event_id TEXT NOT NULL UNIQUE,
                    idempotency_key TEXT NOT NULL UNIQUE,
                    event_type TEXT NOT NULL,
                    payload_hash TEXT NOT NULL,
                    event_hash TEXT NOT NULL,
                    event_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS cognitive_state_checkpoints (
                    checkpoint_id TEXT PRIMARY KEY,
                    sequence INTEGER NOT NULL,
                    snapshot_hash TEXT NOT NULL,
                    checkpoint_hash TEXT NOT NULL,
                    checkpoint_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS ix_cognitive_state_events_event_type
                    ON cognitive_state_events(event_type);
                CREATE INDEX IF NOT EXISTS ix_cognitive_state_checkpoints_sequence
                    ON cognitive_state_checkpoints(sequence);
                """
            )

    def append_event(self, event: CognitiveEvent) -> CognitiveStateAppendResult:
        with self._connect() as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                row = connection.execute(
                    """
                    SELECT event_json
                    FROM cognitive_state_events
                    WHERE idempotency_key = ?
                    """,
                    (event.idempotency_key,),
                ).fetchone()
                if row is not None:
                    existing = _event_from_json(str(row["event_json"]))
                    _assert_same_idempotent_event(existing, event)
                    connection.commit()
                    return CognitiveStateAppendResult(event=existing, duplicate=True)
                if (
                    connection.execute(
                        "SELECT 1 FROM cognitive_state_events WHERE event_id = ?",
                        (event.event_id,),
                    ).fetchone()
                    is not None
                ):
                    connection.rollback()
                    raise DuplicateCognitiveEventError("cognitive_state_event_id_reused")
                latest_sequence = int(
                    connection.execute(
                        "SELECT COALESCE(MAX(sequence), 0) AS latest FROM cognitive_state_events"
                    ).fetchone()["latest"]
                )
                _assert_expected_sequence(latest_sequence, event.expected_previous_sequence)
                stored = assign_event_sequence(event, latest_sequence + 1)
                connection.execute(
                    """
                    INSERT INTO cognitive_state_events (
                        sequence,
                        event_id,
                        idempotency_key,
                        event_type,
                        payload_hash,
                        event_hash,
                        event_json,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        stored.sequence,
                        stored.event_id,
                        stored.idempotency_key,
                        stored.event_type,
                        stored.payload_hash,
                        stored.event_hash,
                        _model_json(stored),
                        stored.created_at.isoformat(),
                    ),
                )
                connection.commit()
                return CognitiveStateAppendResult(event=stored, duplicate=False)
            except sqlite3.IntegrityError as exc:
                connection.rollback()
                raise DuplicateCognitiveEventError("cognitive_state_duplicate_event") from exc
            except sqlite3.OperationalError as exc:
                connection.rollback()
                raise CognitiveStateRepositoryError("cognitive_state_schema_unavailable") from exc

    def list_events(
        self,
        *,
        from_sequence: int = 1,
        limit: int | None = None,
    ) -> tuple[CognitiveEvent, ...]:
        query = """
            SELECT event_json
            FROM cognitive_state_events
            WHERE sequence >= ?
            ORDER BY sequence ASC
        """
        params: tuple[int, ...] = (from_sequence,)
        if limit is not None:
            query = f"{query} LIMIT ?"  # noqa: S608 - static SQL with bound limit value.
            params = (from_sequence, limit)
        try:
            with self._connect() as connection:
                rows = connection.execute(query, params).fetchall()
        except sqlite3.OperationalError as exc:
            raise CognitiveStateRepositoryError("cognitive_state_schema_unavailable") from exc
        return tuple(_event_from_json(str(row["event_json"])) for row in rows)

    def latest_sequence(self) -> int:
        try:
            with self._connect() as connection:
                row = connection.execute(
                    "SELECT COALESCE(MAX(sequence), 0) AS latest FROM cognitive_state_events"
                ).fetchone()
        except sqlite3.OperationalError as exc:
            raise CognitiveStateRepositoryError("cognitive_state_schema_unavailable") from exc
        return int(row["latest"])

    def save_checkpoint(self, checkpoint: CognitiveStateCheckpoint) -> CognitiveStateCheckpoint:
        try:
            with self._connect() as connection:
                existing = connection.execute(
                    """
                    SELECT checkpoint_hash
                    FROM cognitive_state_checkpoints
                    WHERE checkpoint_id = ?
                    """,
                    (checkpoint.checkpoint_id,),
                ).fetchone()
                if (
                    existing is not None
                    and existing["checkpoint_hash"] != checkpoint.checkpoint_hash
                ):
                    raise CognitiveStateCheckpointError("cognitive_state_checkpoint_id_reused")
                connection.execute(
                    """
                    INSERT OR IGNORE INTO cognitive_state_checkpoints (
                        checkpoint_id,
                        sequence,
                        snapshot_hash,
                        checkpoint_hash,
                        checkpoint_json,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        checkpoint.checkpoint_id,
                        checkpoint.sequence,
                        checkpoint.snapshot_hash,
                        checkpoint.checkpoint_hash,
                        _model_json(checkpoint),
                        checkpoint.created_at.isoformat(),
                    ),
                )
        except sqlite3.OperationalError as exc:
            raise CognitiveStateRepositoryError("cognitive_state_schema_unavailable") from exc
        return checkpoint

    def get_checkpoint(self, checkpoint_id: str) -> CognitiveStateCheckpoint | None:
        try:
            with self._connect() as connection:
                row = connection.execute(
                    """
                    SELECT checkpoint_json, checkpoint_hash
                    FROM cognitive_state_checkpoints
                    WHERE checkpoint_id = ?
                    """,
                    (checkpoint_id,),
                ).fetchone()
        except sqlite3.OperationalError as exc:
            raise CognitiveStateRepositoryError("cognitive_state_schema_unavailable") from exc
        if row is None:
            return None
        return _checkpoint_from_row(row["checkpoint_json"], row["checkpoint_hash"])

    def latest_checkpoint(self) -> CognitiveStateCheckpoint | None:
        try:
            with self._connect() as connection:
                row = connection.execute(
                    """
                    SELECT checkpoint_json, checkpoint_hash
                    FROM cognitive_state_checkpoints
                    ORDER BY sequence DESC
                    LIMIT 1
                    """
                ).fetchone()
        except sqlite3.OperationalError as exc:
            raise CognitiveStateRepositoryError("cognitive_state_schema_unavailable") from exc
        if row is None:
            return None
        return _checkpoint_from_row(row["checkpoint_json"], row["checkpoint_hash"])

    def delete_events_before(self, sequence: int) -> int:
        if sequence < 1:
            raise ValueError("sequence must be at least 1")
        try:
            with self._connect() as connection:
                cursor = connection.execute(
                    "DELETE FROM cognitive_state_events WHERE sequence < ?",
                    (sequence,),
                )
                return int(cursor.rowcount)
        except sqlite3.OperationalError as exc:
            raise CognitiveStateRepositoryError("cognitive_state_schema_unavailable") from exc

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, timeout=self._timeout_seconds)
        connection.row_factory = sqlite3.Row
        return connection


def validate_explicit_sqlite_path(
    database_path: Path | str,
    *,
    repo_root: Path | str | None = None,
) -> Path:
    """Validate an explicit non-hidden local SQLite path."""

    path = Path(database_path)
    if not path.is_absolute():
        raise ValueError("cognitive-state SQLite path must be absolute")
    if ".." in path.parts:
        raise ValueError("cognitive-state SQLite path cannot contain traversal")
    if path.suffix.lower() not in ALLOWED_SQLITE_SUFFIXES:
        raise ValueError("cognitive-state SQLite path must use a SQLite suffix")
    hidden_parts = [part for part in path.parts[1:] if part.startswith(".")]
    if hidden_parts:
        raise ValueError("cognitive-state SQLite path cannot use hidden path parts")
    resolved = path.resolve(strict=False)
    if repo_root is not None:
        resolved_repo_root = Path(repo_root).resolve(strict=False)
        if _is_relative_to(resolved, resolved_repo_root):
            raise ValueError("cognitive-state SQLite path cannot be inside the repository")
    if path.exists() and path.is_symlink():
        raise ValueError("cognitive-state SQLite path cannot be a symlink")
    for parent in resolved.parents:
        if parent.exists() and parent.is_symlink():
            raise ValueError("cognitive-state SQLite parent path cannot be a symlink")
    return resolved


def assign_event_sequence(event: CognitiveEvent, sequence: int) -> CognitiveEvent:
    """Return a validated event with an assigned monotonic sequence."""

    payload = event.model_dump(mode="python", exclude={"event_hash"})
    payload["sequence"] = sequence
    return CognitiveEvent.model_validate(payload)


def _assert_same_idempotent_event(existing: CognitiveEvent, event: CognitiveEvent) -> None:
    if existing.event_type != event.event_type or existing.payload_hash != event.payload_hash:
        raise DuplicateCognitiveEventError("cognitive_state_idempotency_key_conflict")


def _assert_expected_sequence(latest_sequence: int, expected_previous_sequence: int) -> None:
    if expected_previous_sequence != latest_sequence:
        raise StaleCognitiveStateVersionError("cognitive_state_stale_expected_sequence")


def _event_from_json(value: str) -> CognitiveEvent:
    return CognitiveEvent.model_validate(json.loads(value))


def _checkpoint_from_row(value: str, stored_hash: str) -> CognitiveStateCheckpoint:
    try:
        checkpoint = CognitiveStateCheckpoint.model_validate(json.loads(value))
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise CognitiveStateCheckpointError("cognitive_state_checkpoint_corrupt") from exc
    if checkpoint.checkpoint_hash != stored_hash:
        raise CognitiveStateCheckpointError("cognitive_state_checkpoint_hash_mismatch")
    return checkpoint


def _model_json(model: CognitiveEvent | CognitiveStateCheckpoint) -> str:
    return json.dumps(model.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))


def _is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
        return True
    except ValueError:
        return False


__all__ = [
    "CognitiveStateAppendResult",
    "CognitiveStateCheckpointError",
    "CognitiveStateRepository",
    "CognitiveStateRepositoryError",
    "DuplicateCognitiveEventError",
    "ExplicitLocalCognitiveStateRepository",
    "InMemoryCognitiveStateRepository",
    "StaleCognitiveStateVersionError",
    "assign_event_sequence",
    "validate_explicit_sqlite_path",
]
