"""Immutable in-memory claim-graph repository and synthetic fixture replay."""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Literal, Protocol

from pydantic import BaseModel, Field, field_validator, model_validator

from aion_brain.contracts.knowledge_claim_graph import (
    AUTHORIZATION_SCOPE,
    AUTHORIZATION_TRANSACTION_ID,
    CLAIM_GRAPH_FIXTURE_SCHEMA_VERSION,
    FORMAL_CLOSEOUT_TASK,
    IMPLEMENTATION_TASK,
    MAXIMUM_FIXTURE_BYTES,
    MAXIMUM_FIXTURE_RECORDS,
    PROGRAM_ID,
    ClaimEvidenceBinding,
    ClaimGraphProposedBatch,
    ClaimGraphRecordEnvelope,
    ClaimGraphState,
    ClaimRelationEdge,
    StructuralConflictCandidate,
    UnverifiedClaimAssertion,
)
from aion_brain.contracts.knowledge_research import (
    FROZEN_MODEL_CONFIG,
    fingerprint_payload,
    reject_protected_material,
    validate_hex64,
)
from aion_brain.knowledge_intelligence.claim_graph_integrity import (
    calculate_claim_graph_record_fingerprint,
    validate_claim_graph_record,
)


class TemporalClaimGraphRepository(Protocol):
    """Read-only temporal claim-graph repository protocol."""

    def snapshot(self) -> tuple[ClaimGraphRecordEnvelope, ...]:
        """Return an immutable graph snapshot."""

    def records(self) -> tuple[ClaimGraphRecordEnvelope, ...]:
        """Return deterministic immutable records."""

    def record_count(self) -> int:
        """Return the graph record count."""

    def claim_count(self) -> int:
        """Return the claim assertion count."""

    def binding_count(self) -> int:
        """Return the evidence binding count."""

    def relation_count(self) -> int:
        """Return the relation count."""


class InMemoryTemporalClaimGraphRepository:
    """Immutable in-memory graph state with pure simulated append."""

    def __init__(self, records: Iterable[ClaimGraphRecordEnvelope] = ()) -> None:
        ordered = tuple(sorted(records, key=lambda item: item.sequence_number))
        _validate_record_chain(ordered)
        self._records = ordered

    def snapshot(self) -> tuple[ClaimGraphRecordEnvelope, ...]:
        """Return an immutable graph snapshot."""

        return self._records

    def records(self) -> tuple[ClaimGraphRecordEnvelope, ...]:
        """Return deterministic immutable records."""

        return self._records

    def record_count(self) -> int:
        """Return the graph record count."""

        return len(self._records)

    def claim_count(self) -> int:
        """Return the claim assertion count."""

        return sum(isinstance(record.payload, UnverifiedClaimAssertion) for record in self._records)

    def binding_count(self) -> int:
        """Return the evidence binding count."""

        return sum(isinstance(record.payload, ClaimEvidenceBinding) for record in self._records)

    def relation_count(self) -> int:
        """Return the relation count."""

        return sum(isinstance(record.payload, ClaimRelationEdge) for record in self._records)

    def structural_conflict_candidate_count(self) -> int:
        """Return the structural conflict candidate count."""

        return sum(
            isinstance(record.payload, StructuralConflictCandidate) for record in self._records
        )

    def record_by_id(self, record_id: str) -> ClaimGraphRecordEnvelope | None:
        """Return one exact record without exposing mutable indexes."""

        for record in self._records:
            if record.record_id == record_id:
                return record
        return None

    def claim_by_id(self, claim_id: str) -> UnverifiedClaimAssertion | None:
        """Return one exact claim assertion without exposing mutable indexes."""

        for record in self._records:
            if (
                isinstance(record.payload, UnverifiedClaimAssertion)
                and record.payload.claim_id == claim_id
            ):
                return record.payload
        return None

    def state(self, graph_id: str = "temporal-claim-evidence-graph") -> ClaimGraphState:
        """Return a redacted immutable graph-state summary."""

        payload = {
            "graph_id": graph_id,
            "record_count": self.record_count(),
            "claim_count": self.claim_count(),
            "binding_count": self.binding_count(),
            "relation_count": self.relation_count(),
            "structural_conflict_candidate_count": self.structural_conflict_candidate_count(),
            "chain_head": self._records[-1].record_fingerprint if self._records else None,
        }
        return ClaimGraphState(
            graph_id=graph_id,
            record_count=self.record_count(),
            claim_count=self.claim_count(),
            evidence_binding_count=self.binding_count(),
            relation_count=self.relation_count(),
            structural_conflict_candidate_count=self.structural_conflict_candidate_count(),
            chain_head_fingerprint=self._records[-1].record_fingerprint if self._records else None,
            state_fingerprint=fingerprint_payload(payload),
        )

    def with_simulated_append(
        self,
        proposed_batch: ClaimGraphProposedBatch,
    ) -> InMemoryTemporalClaimGraphRepository:
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
            validate_claim_graph_record(record)
            appended.append(record)
            existing_by_id[record.record_id] = record
            previous_fingerprint = record.record_fingerprint
            next_sequence += 1

        return InMemoryTemporalClaimGraphRepository(tuple(appended))


class ClaimGraphFixtureEnvelope(BaseModel):
    """Explicit synthetic fixture containing claim-graph record envelopes only."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-claim-graph-fixture/v1"] = (
        CLAIM_GRAPH_FIXTURE_SCHEMA_VERSION
    )
    program_id: Literal["AION-KNOWLEDGE-INTELLIGENCE-001"] = PROGRAM_ID
    authorization_transaction_id: Literal["AION-208-KI-0003"] = AUTHORIZATION_TRANSACTION_ID
    implementation_task: Literal["AION-209"] = IMPLEMENTATION_TASK
    formal_closeout_task: Literal["AION-210"] = FORMAL_CLOSEOUT_TASK
    authorization_scope: Literal[
        "append-only-immutable-temporal-claim-evidence-provenance-jurisdiction-version-contradiction-graph-core"
    ] = AUTHORIZATION_SCOPE
    records: tuple[ClaimGraphRecordEnvelope, ...] = Field(max_length=MAXIMUM_FIXTURE_RECORDS)
    synthetic: Literal[True] = True
    read_only: Literal[True] = True
    redacted: Literal[True] = True
    source_body_present: Literal[False] = False
    source_body_bytes: Literal[0] = 0
    persistent_write_applied: Literal[False] = False
    runtime_effect: Literal[False] = False
    fixture_fingerprint: str

    @field_validator("fixture_fingerprint")
    @classmethod
    def fixture_fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "claim graph fixture fingerprint")

    @model_validator(mode="after")
    def fixture_fingerprint_matches(self) -> ClaimGraphFixtureEnvelope:
        payload = self.model_dump(mode="json")
        payload.pop("fixture_fingerprint", None)
        if self.fixture_fingerprint != fingerprint_payload(payload):
            raise ValueError("claim graph fixture fingerprint mismatch")
        return self


class ExplicitLocalClaimGraphFixtureReplay:
    """Replay operator-supplied local synthetic fixtures into memory only."""

    def __init__(self, maximum_fixture_bytes: int = MAXIMUM_FIXTURE_BYTES) -> None:
        self._maximum_fixture_bytes = maximum_fixture_bytes

    def replay(
        self,
        fixture_path: str | Path,
        *,
        repository_root: str | Path,
    ) -> InMemoryTemporalClaimGraphRepository:
        """Validate and replay a claim-graph fixture without file mutation."""

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
        reject_protected_material(text, "claim graph fixture")
        payload = json.loads(text)
        fixture = ClaimGraphFixtureEnvelope.model_validate(payload)
        _validate_record_chain(fixture.records)
        return InMemoryTemporalClaimGraphRepository(fixture.records)


def claim_graph_fixture_payload(
    records: tuple[ClaimGraphRecordEnvelope, ...],
) -> dict[str, object]:
    """Build a deterministic fixture payload for tests and examples."""

    payload: dict[str, object] = {
        "schema_version": CLAIM_GRAPH_FIXTURE_SCHEMA_VERSION,
        "program_id": PROGRAM_ID,
        "authorization_transaction_id": AUTHORIZATION_TRANSACTION_ID,
        "implementation_task": IMPLEMENTATION_TASK,
        "formal_closeout_task": FORMAL_CLOSEOUT_TASK,
        "authorization_scope": AUTHORIZATION_SCOPE,
        "records": [record.model_dump(mode="json") for record in records],
        "synthetic": True,
        "read_only": True,
        "redacted": True,
        "source_body_present": False,
        "source_body_bytes": 0,
        "persistent_write_applied": False,
        "runtime_effect": False,
    }
    return {**payload, "fixture_fingerprint": fingerprint_payload(payload)}


def _validate_record_chain(records: tuple[ClaimGraphRecordEnvelope, ...]) -> None:
    seen_ids: dict[str, ClaimGraphRecordEnvelope] = {}
    previous: str | None = None
    for expected_sequence, record in enumerate(records, start=1):
        if record.sequence_number != expected_sequence:
            raise ValueError("claim graph record sequence must be contiguous")
        if record.previous_record_fingerprint != previous:
            raise ValueError("claim graph fingerprint chain is broken")
        if calculate_claim_graph_record_fingerprint(record) != record.record_fingerprint:
            raise ValueError("claim graph record fingerprint mismatch")
        existing = seen_ids.get(record.record_id)
        if existing is not None and existing.record_fingerprint != record.record_fingerprint:
            raise ValueError("same record ID with changed payload rejected")
        seen_ids[record.record_id] = record
        previous = record.record_fingerprint


__all__ = [
    "ClaimGraphFixtureEnvelope",
    "ExplicitLocalClaimGraphFixtureReplay",
    "InMemoryTemporalClaimGraphRepository",
    "TemporalClaimGraphRepository",
    "claim_graph_fixture_payload",
]
