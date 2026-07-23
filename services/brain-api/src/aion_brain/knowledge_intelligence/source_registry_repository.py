"""Immutable in-memory source-registry repository and fixture replay."""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Literal, Protocol

from pydantic import BaseModel, Field, field_validator, model_validator

from aion_brain.contracts.knowledge_research import (
    FROZEN_MODEL_CONFIG,
    fingerprint_payload,
    reject_protected_material,
)
from aion_brain.contracts.knowledge_source_registry import (
    AUTHORIZATION_SCOPE,
    AUTHORIZATION_TRANSACTION_ID,
    FORMAL_CLOSEOUT_TASK,
    IMPLEMENTATION_TASK,
    PROGRAM_ID,
    SourceRegistryProposedBatch,
    SourceRegistryRecordEnvelope,
)
from aion_brain.knowledge_intelligence.source_registry_integrity import (
    calculate_record_fingerprint,
    validate_record_envelope,
)

MAXIMUM_FIXTURE_BYTES = 819_200


class SourceRegistryRepository(Protocol):
    """Read-only source-registry repository protocol."""

    def snapshot(self) -> tuple[SourceRegistryRecordEnvelope, ...]:
        """Return an immutable registry snapshot."""

    def records(self) -> tuple[SourceRegistryRecordEnvelope, ...]:
        """Return deterministic immutable records."""

    def record_count(self) -> int:
        """Return the current record count."""


class InMemorySourceRegistryRepository:
    """Immutable in-memory source-registry state with pure simulated append."""

    def __init__(self, records: Iterable[SourceRegistryRecordEnvelope] = ()) -> None:
        ordered = tuple(sorted(records, key=lambda item: item.sequence_number))
        _validate_record_chain(ordered)
        self._records = ordered

    def snapshot(self) -> tuple[SourceRegistryRecordEnvelope, ...]:
        """Return an immutable registry snapshot."""

        return self._records

    def records(self) -> tuple[SourceRegistryRecordEnvelope, ...]:
        """Return deterministic immutable records."""

        return self._records

    def record_count(self) -> int:
        """Return the current record count."""

        return len(self._records)

    def record_by_id(self, record_id: str) -> SourceRegistryRecordEnvelope | None:
        """Return one exact record by ID without exposing a mutable index."""

        for record in self._records:
            if record.record_id == record_id:
                return record
        return None

    def with_simulated_append(
        self,
        proposed_batch: SourceRegistryProposedBatch,
    ) -> InMemorySourceRegistryRepository:
        """Return a new repository with a simulated append applied in memory only."""

        existing_by_id = {record.record_id: record for record in self._records}
        appended = list(self._records)
        next_sequence = len(appended) + 1
        previous_fingerprint = appended[-1].record_fingerprint if appended else None

        for record in proposed_batch.records:
            existing = existing_by_id.get(record.record_id)
            if existing is not None:
                if existing.record_fingerprint != record.record_fingerprint:
                    raise ValueError("same record ID with changed payload rejected")
                continue
            if record.sequence_number != next_sequence:
                raise ValueError("simulated append requires contiguous record sequence")
            if record.previous_record_fingerprint != previous_fingerprint:
                raise ValueError("simulated append requires matching previous fingerprint")
            validate_record_envelope(record)
            appended.append(record)
            existing_by_id[record.record_id] = record
            previous_fingerprint = record.record_fingerprint
            next_sequence += 1

        return InMemorySourceRegistryRepository(tuple(appended))


class SourceRegistryFixtureEnvelope(BaseModel):
    """Explicit synthetic fixture containing registry record envelopes only."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-source-registry-fixture/v1"] = (
        "aion-knowledge-source-registry-fixture/v1"
    )
    program_id: Literal["AION-KNOWLEDGE-INTELLIGENCE-001"] = PROGRAM_ID
    authorization_transaction_id: Literal["AION-206-KI-0002"] = AUTHORIZATION_TRANSACTION_ID
    implementation_task: Literal["AION-207"] = IMPLEMENTATION_TASK
    formal_closeout_task: Literal["AION-208"] = FORMAL_CLOSEOUT_TASK
    authorization_scope: Literal[
        "append-only-immutable-source-snapshot-provenance-lineage-citation-registry-core"
    ] = AUTHORIZATION_SCOPE
    records: tuple[SourceRegistryRecordEnvelope, ...] = Field(max_length=100)
    synthetic: Literal[True] = True
    read_only: Literal[True] = True
    redacted: Literal[True] = True
    persistent_write_applied: Literal[False] = False
    runtime_effect: Literal[False] = False
    fixture_fingerprint: str

    @field_validator("fixture_fingerprint")
    @classmethod
    def fixture_fingerprint_is_safe(cls, value: str) -> str:
        from aion_brain.contracts.knowledge_research import validate_hex64

        return validate_hex64(value, "source registry fixture fingerprint")

    @model_validator(mode="after")
    def fixture_fingerprint_matches(self) -> SourceRegistryFixtureEnvelope:
        payload = self.model_dump(mode="json")
        payload.pop("fixture_fingerprint", None)
        if self.fixture_fingerprint != fingerprint_payload(payload):
            raise ValueError("fixture fingerprint mismatch")
        return self


class ExplicitLocalSourceRegistryFixtureReplay:
    """Replay an operator-supplied local synthetic fixture into memory only."""

    def __init__(self, maximum_fixture_bytes: int = MAXIMUM_FIXTURE_BYTES) -> None:
        self._maximum_fixture_bytes = maximum_fixture_bytes

    def replay(
        self,
        fixture_path: str | Path,
        *,
        repository_root: str | Path,
    ) -> InMemorySourceRegistryRepository:
        """Validate and replay a source-registry fixture without file mutation."""

        path_text = str(fixture_path)
        if "://" in path_text:
            raise ValueError("fixture path must be a local absolute path")
        if "$" in path_text or path_text.startswith("~"):
            raise ValueError("fixture path expansion is rejected")
        path = Path(path_text)
        if not path.is_absolute():
            raise ValueError("fixture path must be absolute")
        if any(part.startswith(".") for part in path.parts if part not in {path.anchor, "/"}):
            raise ValueError("hidden fixture paths are rejected")
        try:
            stat_result = path.lstat()
        except FileNotFoundError as exc:
            raise ValueError("fixture file is unavailable") from exc
        if path.is_symlink():
            raise ValueError("fixture symlink is rejected")
        if not path.is_file():
            raise ValueError("fixture path must be a regular file")
        if stat_result.st_size > self._maximum_fixture_bytes:
            raise ValueError("fixture file exceeds size budget")
        root = Path(repository_root).resolve()
        resolved = path.resolve()
        try:
            resolved.relative_to(root)
        except ValueError:
            pass
        else:
            raise ValueError("fixture path must be outside the repository")
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError("fixture file must be valid UTF-8") from exc
        reject_protected_material(text, "source registry fixture")
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError("fixture file must be valid JSON") from exc
        fixture = SourceRegistryFixtureEnvelope.model_validate(payload)
        _validate_record_chain(fixture.records)
        return InMemorySourceRegistryRepository(fixture.records)


def source_registry_fixture_payload(
    records: tuple[SourceRegistryRecordEnvelope, ...],
) -> dict[str, object]:
    """Build a deterministic fixture payload for tests and examples."""

    payload: dict[str, object] = {
        "schema_version": "aion-knowledge-source-registry-fixture/v1",
        "program_id": PROGRAM_ID,
        "authorization_transaction_id": AUTHORIZATION_TRANSACTION_ID,
        "implementation_task": IMPLEMENTATION_TASK,
        "formal_closeout_task": FORMAL_CLOSEOUT_TASK,
        "authorization_scope": AUTHORIZATION_SCOPE,
        "records": [record.model_dump(mode="json") for record in records],
        "synthetic": True,
        "read_only": True,
        "redacted": True,
        "persistent_write_applied": False,
        "runtime_effect": False,
    }
    return {**payload, "fixture_fingerprint": fingerprint_payload(payload)}


def _validate_record_chain(records: tuple[SourceRegistryRecordEnvelope, ...]) -> None:
    seen_ids: dict[str, SourceRegistryRecordEnvelope] = {}
    previous: str | None = None
    for expected_sequence, record in enumerate(records, start=1):
        if record.sequence_number != expected_sequence:
            raise ValueError("record sequence must be contiguous")
        if record.previous_record_fingerprint != previous:
            raise ValueError("record fingerprint chain is broken")
        if calculate_record_fingerprint(record) != record.record_fingerprint:
            raise ValueError("record fingerprint mismatch")
        existing = seen_ids.get(record.record_id)
        if existing is not None:
            if existing.record_fingerprint == record.record_fingerprint:
                previous = record.record_fingerprint
                continue
            raise ValueError("same record ID with changed payload rejected")
        if record.supersedes_record_id is not None:
            superseded = seen_ids.get(record.supersedes_record_id)
            if superseded is None:
                raise ValueError("superseded record must already exist")
            if superseded.record_version + 1 != record.record_version:
                raise ValueError("record version must increment by one")
        validate_record_envelope(record)
        seen_ids[record.record_id] = record
        previous = record.record_fingerprint


__all__ = [
    "ExplicitLocalSourceRegistryFixtureReplay",
    "InMemorySourceRegistryRepository",
    "SourceRegistryFixtureEnvelope",
    "SourceRegistryRepository",
    "source_registry_fixture_payload",
]
