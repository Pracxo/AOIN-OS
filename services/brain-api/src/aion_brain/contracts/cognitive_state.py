"""Persistent cognitive-state contracts owned by AION Brain."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any, Literal, NoReturn, Self, cast

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.model_outputs import (
    reject_hidden_or_secret_text,
    reject_secret_like_payload,
)

SCHEMA_VERSION = "cognitive-state/v1"
CANONICALIZATION_VERSION = "cognitive-state-canonical-json/v1"
AUTHORIZATION_ID = "AION-183-CA-0001"
IMPLEMENTATION_TASK = "AION-184"

CognitiveEventType = Literal[
    "belief_recorded",
    "belief_revised",
    "goal_focused",
    "hypothesis_opened",
    "uncertainty_recorded",
    "expected_effect_recorded",
    "observed_effect_recorded",
    "resource_state_recorded",
    "contradiction_recorded",
    "retention_applied",
]
BeliefStatus = Literal["active", "revised", "rejected", "superseded"]
GoalStatus = Literal["active", "paused", "complete", "blocked"]
HypothesisStatus = Literal["open", "supported", "contradicted", "closed"]
UncertaintyDirection = Literal["increased", "reduced", "unchanged"]
ResourcePressure = Literal["low", "medium", "high", "critical"]
ContradictionSeverity = Literal["low", "medium", "high", "critical"]


class FrozenDict(dict[str, Any]):
    """Dict subtype that blocks mutation after validation."""

    def _blocked(self, *_args: object, **_kwargs: object) -> NoReturn:
        raise TypeError("cognitive-state payload is immutable")

    def __setitem__(self, key: str, value: Any) -> NoReturn:
        self._blocked(key, value)

    def __delitem__(self, key: str) -> NoReturn:
        self._blocked(key)

    def clear(self) -> NoReturn:
        self._blocked()

    def pop(self, key: str, default: Any = None) -> NoReturn:  # noqa: ARG002
        self._blocked(key, default)

    def popitem(self) -> NoReturn:
        self._blocked()

    def setdefault(self, key: str, default: Any = None) -> NoReturn:
        self._blocked(key, default)

    def update(self, *args: Any, **kwargs: Any) -> NoReturn:
        self._blocked(*args, **kwargs)


class CognitiveStateModel(BaseModel):
    """Base model for immutable cognitive-state contracts."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = SCHEMA_VERSION

    @field_validator("schema_version")
    @classmethod
    def schema_version_must_match(cls, value: str) -> str:
        if value != SCHEMA_VERSION:
            raise ValueError(f"schema_version must be {SCHEMA_VERSION}")
        return value


class CognitiveFingerprintedModel(CognitiveStateModel):
    """Immutable model with a deterministic SHA-256 fingerprint."""

    fingerprint: str | None = None

    @model_validator(mode="after")
    def fingerprint_must_match_payload(self) -> Self:
        expected = fingerprint_model(self, exclude={"fingerprint"})
        if self.fingerprint is None:
            object.__setattr__(self, "fingerprint", expected)
        elif self.fingerprint != expected:
            raise ValueError("fingerprint must match canonical payload")
        return self


class CognitiveStateProvenance(CognitiveFingerprintedModel):
    """Redacted evidence about one cognitive-state operation."""

    provenance_id: str = Field(min_length=1)
    operation_id: str = Field(min_length=1)
    actor_id: str | None = None
    source: str = Field(min_length=1)
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)
    redaction_applied: bool = True
    runtime_effect: bool = False
    source_modified: bool = False
    git_mutated: bool = False
    pull_request_created: bool = False
    approval_created: bool = False
    merged: bool = False
    production_exposure: bool = False
    model_weights_changed: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("operation_id", "actor_id", "source")
    @classmethod
    def text_must_be_safe(cls, value: str | None) -> str | None:
        if value is not None:
            reject_hidden_or_secret_text(value, "cognitive provenance text")
        return value

    @field_validator("evidence_refs")
    @classmethod
    def refs_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            reject_hidden_or_secret_text(item, "cognitive evidence ref")
        return value

    @model_validator(mode="after")
    def runtime_flags_must_remain_false(self) -> Self:
        for key in (
            "runtime_effect",
            "source_modified",
            "git_mutated",
            "pull_request_created",
            "approval_created",
            "merged",
            "production_exposure",
            "model_weights_changed",
        ):
            if getattr(self, key):
                raise ValueError(f"{key} must be false")
        if not self.redaction_applied:
            raise ValueError("redaction_applied must be true")
        return self


class BeliefRecord(CognitiveFingerprintedModel):
    """One current belief in persistent cognitive state."""

    belief_id: str = Field(min_length=1)
    statement: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    status: BeliefStatus = "active"
    source_refs: tuple[str, ...] = Field(default_factory=tuple)
    revision_sequence: int = Field(ge=1)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("belief_id", "statement")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "belief text")
        return value.strip()

    @field_validator("source_refs")
    @classmethod
    def refs_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            reject_hidden_or_secret_text(item, "belief source ref")
        return value


class BeliefRevision(CognitiveFingerprintedModel):
    """One explicit belief revision event."""

    revision_id: str = Field(min_length=1)
    belief_id: str = Field(min_length=1)
    previous_confidence: float = Field(ge=0.0, le=1.0)
    revised_confidence: float = Field(ge=0.0, le=1.0)
    reason: str = Field(min_length=1)
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("revision_id", "belief_id", "reason")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "belief revision text")
        return value.strip()

    @field_validator("evidence_refs")
    @classmethod
    def refs_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            reject_hidden_or_secret_text(item, "belief revision ref")
        return value


class GoalFocus(CognitiveFingerprintedModel):
    """One active or retained goal focus."""

    goal_id: str = Field(min_length=1)
    description: str = Field(min_length=1)
    priority: int = Field(ge=0, le=100)
    status: GoalStatus = "active"
    success_criteria: tuple[str, ...] = Field(default_factory=tuple)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("goal_id", "description")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "goal text")
        return value.strip()

    @field_validator("success_criteria")
    @classmethod
    def criteria_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            reject_hidden_or_secret_text(item, "goal success criterion")
        return value


class OpenHypothesis(CognitiveFingerprintedModel):
    """One tracked hypothesis with evidence references."""

    hypothesis_id: str = Field(min_length=1)
    statement: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    status: HypothesisStatus = "open"
    support_refs: tuple[str, ...] = Field(default_factory=tuple)
    contradicting_refs: tuple[str, ...] = Field(default_factory=tuple)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("hypothesis_id", "statement")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "hypothesis text")
        return value.strip()

    @field_validator("support_refs", "contradicting_refs")
    @classmethod
    def refs_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            reject_hidden_or_secret_text(item, "hypothesis ref")
        return value


class UncertaintyRecord(CognitiveFingerprintedModel):
    """One uncertainty estimate for a bounded subject."""

    uncertainty_id: str = Field(min_length=1)
    subject: str = Field(min_length=1)
    uncertainty_score: float = Field(ge=0.0, le=1.0)
    direction: UncertaintyDirection = "unchanged"
    rationale: str = Field(min_length=1)
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("uncertainty_id", "subject", "rationale")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "uncertainty text")
        return value.strip()

    @field_validator("evidence_refs")
    @classmethod
    def refs_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            reject_hidden_or_secret_text(item, "uncertainty ref")
        return value


class ExpectedActionEffect(CognitiveFingerprintedModel):
    """Expected effect of a proposed action reference."""

    expected_effect_id: str = Field(min_length=1)
    action_ref: str = Field(min_length=1)
    expected_outcome: str = Field(min_length=1)
    probability: float = Field(ge=0.0, le=1.0)
    reversible: bool
    resource_cost: float = Field(ge=0.0)
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("expected_effect_id", "action_ref", "expected_outcome")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "expected effect text")
        return value.strip()

    @field_validator("evidence_refs")
    @classmethod
    def refs_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            reject_hidden_or_secret_text(item, "expected effect ref")
        return value


class ObservedActionEffect(CognitiveFingerprintedModel):
    """Observed effect for a referenced action after review."""

    observed_effect_id: str = Field(min_length=1)
    action_ref: str = Field(min_length=1)
    observed_outcome: str = Field(min_length=1)
    expected_effect_id: str | None = None
    matches_expected: bool | None = None
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("observed_effect_id", "action_ref", "observed_outcome", "expected_effect_id")
    @classmethod
    def text_must_be_safe(cls, value: str | None) -> str | None:
        if value is not None:
            reject_hidden_or_secret_text(value, "observed effect text")
            return value.strip()
        return value

    @field_validator("evidence_refs")
    @classmethod
    def refs_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            reject_hidden_or_secret_text(item, "observed effect ref")
        return value


class ResourceState(CognitiveFingerprintedModel):
    """Current bounded resource state."""

    resource_id: str = Field(min_length=1)
    resource_type: str = Field(min_length=1)
    capacity: float = Field(ge=0.0)
    used: float = Field(ge=0.0)
    pressure: ResourcePressure
    measured_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("resource_id", "resource_type")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "resource text")
        return value.strip()

    @model_validator(mode="after")
    def usage_must_fit_capacity(self) -> Self:
        if self.used > self.capacity:
            raise ValueError("used resource cannot exceed capacity")
        return self


class ContradictionRecord(CognitiveFingerprintedModel):
    """One detected contradiction retained for review."""

    contradiction_id: str = Field(min_length=1)
    subject: str = Field(min_length=1)
    belief_ids: tuple[str, str]
    severity: ContradictionSeverity
    resolved: bool = False
    reason: str = Field(min_length=1)
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("contradiction_id", "subject", "reason")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "contradiction text")
        return value.strip()

    @field_validator("belief_ids", "evidence_refs")
    @classmethod
    def refs_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            reject_hidden_or_secret_text(item, "contradiction ref")
        return value

    @model_validator(mode="after")
    def beliefs_must_be_distinct(self) -> Self:
        if self.belief_ids[0] == self.belief_ids[1]:
            raise ValueError("contradiction belief ids must be distinct")
        return self


class CognitiveEvent(CognitiveStateModel):
    """Append-only event with optimistic concurrency and idempotency metadata."""

    event_id: str = Field(min_length=1)
    idempotency_key: str = Field(min_length=1)
    event_type: CognitiveEventType
    expected_previous_sequence: int = Field(ge=0)
    sequence: int = Field(default=0, ge=0)
    payload: dict[str, Any] = Field(default_factory=dict)
    payload_hash: str | None = None
    event_hash: str | None = None
    provenance: CognitiveStateProvenance
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("event_id", "idempotency_key")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "cognitive event text")
        return value.strip()

    @field_validator("payload", mode="after")
    @classmethod
    def payload_must_be_safe(cls, value: dict[str, Any]) -> FrozenDict:
        reject_secret_like_payload(value)
        return cast(FrozenDict, freeze_payload(value))

    @model_validator(mode="after")
    def hashes_must_match_payload(self) -> Self:
        expected_payload_hash = fingerprint_payload(
            {
                "event_type": self.event_type,
                "payload": self.payload,
                "expected_previous_sequence": self.expected_previous_sequence,
            }
        )
        if self.payload_hash is None:
            object.__setattr__(self, "payload_hash", expected_payload_hash)
        elif self.payload_hash != expected_payload_hash:
            raise ValueError("payload_hash must match canonical event payload")
        expected_event_hash = fingerprint_model(self, exclude={"event_hash"})
        if self.event_hash is None:
            object.__setattr__(self, "event_hash", expected_event_hash)
        elif self.event_hash != expected_event_hash:
            raise ValueError("event_hash must match canonical event")
        return self


class CognitiveStateTransition(CognitiveFingerprintedModel):
    """One deterministic state transition created by applying an event."""

    transition_id: str = Field(min_length=1)
    event_id: str = Field(min_length=1)
    event_type: CognitiveEventType
    previous_sequence: int = Field(ge=0)
    next_sequence: int = Field(ge=1)
    before_hash: str = Field(min_length=64, max_length=64)
    after_hash: str = Field(min_length=64, max_length=64)
    idempotent_replay: bool = False
    provenance: CognitiveStateProvenance
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("transition_id", "event_id", "before_hash", "after_hash")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "cognitive transition text")
        return value.strip()


class CognitiveStateSnapshot(CognitiveStateModel):
    """Deterministic current view produced from cognitive events."""

    snapshot_id: str = Field(min_length=1)
    sequence: int = Field(ge=0)
    event_count: int = Field(ge=0)
    beliefs: tuple[BeliefRecord, ...] = Field(default_factory=tuple)
    belief_revisions: tuple[BeliefRevision, ...] = Field(default_factory=tuple)
    goals: tuple[GoalFocus, ...] = Field(default_factory=tuple)
    hypotheses: tuple[OpenHypothesis, ...] = Field(default_factory=tuple)
    uncertainties: tuple[UncertaintyRecord, ...] = Field(default_factory=tuple)
    expected_effects: tuple[ExpectedActionEffect, ...] = Field(default_factory=tuple)
    observed_effects: tuple[ObservedActionEffect, ...] = Field(default_factory=tuple)
    resources: tuple[ResourceState, ...] = Field(default_factory=tuple)
    contradictions: tuple[ContradictionRecord, ...] = Field(default_factory=tuple)
    provenance: tuple[CognitiveStateProvenance, ...] = Field(default_factory=tuple)
    retained_from_sequence: int = Field(default=0, ge=0)
    content_hash: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("snapshot_id")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "cognitive snapshot id")
        return value.strip()

    @model_validator(mode="after")
    def content_hash_must_match_payload(self) -> Self:
        expected = fingerprint_model(self, exclude={"content_hash", "created_at"})
        if self.content_hash is None:
            object.__setattr__(self, "content_hash", expected)
        elif self.content_hash != expected:
            raise ValueError("content_hash must match canonical snapshot")
        if self.event_count < self.sequence:
            raise ValueError("event_count cannot be smaller than sequence")
        if self.retained_from_sequence > self.sequence:
            raise ValueError("retained_from_sequence cannot exceed sequence")
        return self


class CognitiveStateCheckpoint(CognitiveStateModel):
    """Verifiable checkpoint for restoring cognitive state."""

    checkpoint_id: str = Field(min_length=1)
    sequence: int = Field(ge=0)
    snapshot: CognitiveStateSnapshot
    snapshot_hash: str = Field(min_length=64, max_length=64)
    checkpoint_hash: str | None = None
    provenance: CognitiveStateProvenance
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("checkpoint_id", "snapshot_hash")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "cognitive checkpoint text")
        return value.strip()

    @model_validator(mode="after")
    def checkpoint_hashes_must_match(self) -> Self:
        if self.snapshot.sequence != self.sequence:
            raise ValueError("checkpoint sequence must match snapshot sequence")
        if self.snapshot.content_hash != self.snapshot_hash:
            raise ValueError("checkpoint snapshot_hash must match snapshot content_hash")
        expected = fingerprint_model(self, exclude={"checkpoint_hash", "created_at"})
        if self.checkpoint_hash is None:
            object.__setattr__(self, "checkpoint_hash", expected)
        elif self.checkpoint_hash != expected:
            raise ValueError("checkpoint_hash must match canonical checkpoint")
        return self


def canonical_json_bytes(value: Any) -> bytes:
    """Return deterministic JSON bytes for cognitive-state hashing."""

    return json.dumps(
        to_jsonable(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")


def fingerprint_payload(value: Any) -> str:
    """Return a SHA-256 fingerprint for a JSON-compatible payload."""

    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def fingerprint_model(model: BaseModel, *, exclude: set[str] | None = None) -> str:
    """Return a SHA-256 fingerprint for a Pydantic model payload."""

    return fingerprint_payload(model.model_dump(mode="json", exclude=exclude or set()))


def freeze_payload(value: Any) -> Any:
    """Freeze nested event payloads after validation."""

    if isinstance(value, dict):
        return FrozenDict({str(key): freeze_payload(nested) for key, nested in value.items()})
    if isinstance(value, list | tuple):
        return tuple(freeze_payload(item) for item in value)
    return value


def to_jsonable(value: Any) -> Any:
    """Convert frozen payloads and datetimes to deterministic JSON values."""

    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return {str(key): to_jsonable(nested) for key, nested in value.items()}
    if isinstance(value, list | tuple):
        return [to_jsonable(item) for item in value]
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
    return value


def empty_cognitive_state_snapshot(
    *,
    snapshot_id: str = "cognitive-state-empty",
) -> CognitiveStateSnapshot:
    """Return an empty deterministic cognitive-state snapshot."""

    return CognitiveStateSnapshot(snapshot_id=snapshot_id, sequence=0, event_count=0)


__all__ = [
    "AUTHORIZATION_ID",
    "CANONICALIZATION_VERSION",
    "IMPLEMENTATION_TASK",
    "SCHEMA_VERSION",
    "BeliefRecord",
    "BeliefRevision",
    "CognitiveEvent",
    "CognitiveEventType",
    "CognitiveStateCheckpoint",
    "CognitiveStateProvenance",
    "CognitiveStateSnapshot",
    "CognitiveStateTransition",
    "ContradictionRecord",
    "ExpectedActionEffect",
    "FrozenDict",
    "GoalFocus",
    "ObservedActionEffect",
    "OpenHypothesis",
    "ResourceState",
    "UncertaintyRecord",
    "canonical_json_bytes",
    "empty_cognitive_state_snapshot",
    "fingerprint_model",
    "fingerprint_payload",
    "freeze_payload",
    "to_jsonable",
]
