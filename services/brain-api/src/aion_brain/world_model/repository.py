"""Append-only repositories for predictive world-model evidence."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Protocol

from aion_brain.contracts.world_model import TransitionEvidence, WorldModelSnapshot


class WorldModelRepositoryError(RuntimeError):
    """Base sanitized world-model repository error."""


class DuplicateTransitionEvidenceError(WorldModelRepositoryError):
    """Raised when transition evidence is reused with conflicting content."""


@dataclass(frozen=True)
class WorldModelAppendResult:
    """Result of one append-only transition evidence write."""

    evidence: TransitionEvidence
    duplicate: bool


class WorldModelRepository(Protocol):
    """Persistence protocol required by predictive world-model services."""

    def append_evidence(self, evidence: TransitionEvidence) -> WorldModelAppendResult: ...

    def list_evidence(self) -> tuple[TransitionEvidence, ...]: ...

    def latest_sequence(self) -> int: ...

    def save_snapshot(self, snapshot: WorldModelSnapshot) -> WorldModelSnapshot: ...

    def latest_snapshot(self) -> WorldModelSnapshot | None: ...


class InMemoryWorldModelRepository:
    """Thread-safe in-memory repository for local tests and dry runs."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._evidence: list[TransitionEvidence] = []
        self._evidence_by_id: dict[str, TransitionEvidence] = {}
        self._snapshots: list[WorldModelSnapshot] = []

    def append_evidence(self, evidence: TransitionEvidence) -> WorldModelAppendResult:
        with self._lock:
            existing = self._evidence_by_id.get(evidence.evidence_id)
            if existing is not None:
                if existing.fingerprint != evidence.fingerprint:
                    raise DuplicateTransitionEvidenceError("world_model_evidence_id_reused")
                return WorldModelAppendResult(evidence=existing, duplicate=True)
            self._evidence.append(evidence)
            self._evidence_by_id[evidence.evidence_id] = evidence
            return WorldModelAppendResult(evidence=evidence, duplicate=False)

    def list_evidence(self) -> tuple[TransitionEvidence, ...]:
        with self._lock:
            return tuple(self._evidence)

    def latest_sequence(self) -> int:
        with self._lock:
            return len(self._evidence)

    def save_snapshot(self, snapshot: WorldModelSnapshot) -> WorldModelSnapshot:
        with self._lock:
            self._snapshots.append(snapshot)
            return snapshot

    def latest_snapshot(self) -> WorldModelSnapshot | None:
        with self._lock:
            if not self._snapshots:
                return None
            return self._snapshots[-1]
