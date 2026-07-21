"""AION-184 cognitive-state repository tests."""

from __future__ import annotations

import sqlite3
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

import pytest

from aion_brain.cognitive_architecture.repository import (
    CognitiveStateCheckpointError,
    DuplicateCognitiveEventError,
    ExplicitLocalCognitiveStateRepository,
    InMemoryCognitiveStateRepository,
    StaleCognitiveStateVersionError,
    validate_explicit_sqlite_path,
)
from aion_brain.cognitive_architecture.state import CognitiveStateService
from aion_brain.contracts.cognitive_state import (
    BeliefRecord,
    CognitiveEvent,
    CognitiveStateProvenance,
)

ROOT = Path(__file__).resolve().parents[3]
NOW = datetime(2026, 7, 21, 6, 45, tzinfo=UTC)


def provenance(operation_id: str) -> CognitiveStateProvenance:
    return CognitiveStateProvenance(
        provenance_id=f"prov-{operation_id}",
        operation_id=operation_id,
        actor_id="operator",
        source="synthetic-repository-test",
        evidence_refs=("aion://evidence/repository",),
        created_at=NOW,
    )


def belief_event(index: int, *, expected_previous_sequence: int | None = None) -> CognitiveEvent:
    sequence = index if expected_previous_sequence is None else expected_previous_sequence
    belief = BeliefRecord(
        belief_id=f"belief-{index}",
        statement=f"subject-{index}: observed",
        confidence=0.7,
        source_refs=("aion://evidence/repository",),
        revision_sequence=1,
        created_at=NOW,
        updated_at=NOW,
    )
    return CognitiveEvent(
        event_id=f"event-{index}",
        idempotency_key=f"idem-{index}",
        event_type="belief_recorded",
        expected_previous_sequence=sequence,
        payload=belief.model_dump(mode="json"),
        provenance=provenance(f"event-{index}"),
        created_at=NOW,
    )


def test_sqlite_repository_replays_after_restart(tmp_path: Path) -> None:
    database_path = tmp_path / "cognitive-state.sqlite"
    repository = ExplicitLocalCognitiveStateRepository(
        database_path=database_path,
        repo_root=ROOT,
        initialize=True,
    )
    service = CognitiveStateService(repository=repository)
    service.record_event(belief_event(0))
    first = service.record_event(belief_event(1)).snapshot

    restarted = CognitiveStateService(
        repository=ExplicitLocalCognitiveStateRepository(
            database_path=database_path,
            repo_root=ROOT,
        )
    )
    replayed = restarted.current_snapshot()

    assert replayed.content_hash == first.content_hash
    assert replayed.sequence == 2
    assert len(replayed.beliefs) == 2


def test_duplicate_event_is_not_applied_twice_and_conflicts_are_rejected() -> None:
    repository = InMemoryCognitiveStateRepository()
    service = CognitiveStateService(repository=repository)
    first = belief_event(0)

    created = service.record_event(first)
    duplicate = service.record_event(first)

    assert created.duplicate is False
    assert duplicate.duplicate is True
    assert service.current_snapshot().sequence == 1
    assert len(repository.list_events()) == 1

    conflicting = CognitiveEvent(
        event_id="event-conflict",
        idempotency_key=first.idempotency_key,
        event_type="belief_recorded",
        expected_previous_sequence=1,
        payload=BeliefRecord(
            belief_id="belief-conflict",
            statement="subject-conflict: observed",
            confidence=0.4,
            revision_sequence=1,
            created_at=NOW,
            updated_at=NOW,
        ).model_dump(mode="json"),
        provenance=provenance("conflict"),
        created_at=NOW,
    )
    with pytest.raises(DuplicateCognitiveEventError):
        service.record_event(conflicting)


def test_concurrent_writers_allow_one_winner_for_one_expected_sequence(tmp_path: Path) -> None:
    database_path = tmp_path / "concurrent-cognitive-state.sqlite"
    ExplicitLocalCognitiveStateRepository(
        database_path=database_path,
        repo_root=ROOT,
        initialize=True,
    )

    def write_once(index: int) -> str:
        repository = ExplicitLocalCognitiveStateRepository(
            database_path=database_path,
            repo_root=ROOT,
        )
        service = CognitiveStateService(repository=repository)
        try:
            service.record_event(belief_event(index, expected_previous_sequence=0))
            return "created"
        except StaleCognitiveStateVersionError:
            return "stale"

    with ThreadPoolExecutor(max_workers=8) as executor:
        outcomes = list(executor.map(write_once, range(16)))

    assert outcomes.count("created") == 1
    assert outcomes.count("stale") == 15
    repository = ExplicitLocalCognitiveStateRepository(
        database_path=database_path,
        repo_root=ROOT,
    )
    assert repository.latest_sequence() == 1


def test_checkpoint_restore_detects_corruption(tmp_path: Path) -> None:
    database_path = tmp_path / "checkpoint-cognitive-state.sqlite"
    repository = ExplicitLocalCognitiveStateRepository(
        database_path=database_path,
        repo_root=ROOT,
        initialize=True,
    )
    service = CognitiveStateService(repository=repository)
    service.record_event(belief_event(0))
    checkpoint = service.create_checkpoint(
        checkpoint_id="checkpoint-1",
        provenance=provenance("checkpoint"),
    )

    restored = service.restore_checkpoint(checkpoint.checkpoint_id)
    assert restored.content_hash == checkpoint.snapshot_hash

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            UPDATE cognitive_state_checkpoints
            SET checkpoint_json = ?
            WHERE checkpoint_id = ?
            """,
            ("{}", checkpoint.checkpoint_id),
        )

    with pytest.raises(CognitiveStateCheckpointError):
        service.restore_checkpoint(checkpoint.checkpoint_id)


def test_explicit_retention_requires_checkpoint_and_keeps_replay_continuity() -> None:
    repository = InMemoryCognitiveStateRepository()
    service = CognitiveStateService(repository=repository)
    service.record_event(belief_event(0))
    checkpoint = service.create_checkpoint(
        checkpoint_id="checkpoint-retain-1",
        provenance=provenance("checkpoint-retain"),
    )
    service.record_event(belief_event(1))

    retained = service.apply_retention(
        retain_from_sequence=2,
        provenance=provenance("retention"),
        idempotency_key="idem-retention",
    ).snapshot

    assert checkpoint.sequence == 1
    assert retained.retained_from_sequence == 2
    assert tuple(event.sequence for event in repository.list_events()) == (2, 3)
    assert service.current_snapshot().content_hash == retained.content_hash


def test_local_sqlite_path_rejects_hidden_repo_relative_and_symlink_paths(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        validate_explicit_sqlite_path("relative.sqlite", repo_root=ROOT)

    with pytest.raises(ValueError):
        validate_explicit_sqlite_path(ROOT / "cognitive-state.sqlite", repo_root=ROOT)

    with pytest.raises(ValueError):
        validate_explicit_sqlite_path(tmp_path / ".hidden" / "state.sqlite", repo_root=ROOT)

    target = tmp_path / "target.sqlite"
    target.touch()
    link = tmp_path / "link.sqlite"
    link.symlink_to(target)
    with pytest.raises(ValueError):
        validate_explicit_sqlite_path(link, repo_root=ROOT)

    assert validate_explicit_sqlite_path(tmp_path / "allowed.sqlite", repo_root=ROOT).is_absolute()
