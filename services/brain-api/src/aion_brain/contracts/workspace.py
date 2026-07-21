"""Global cognitive workspace contracts owned by AION Brain."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal, Self, cast

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.cognitive_state import (
    FrozenDict,
    fingerprint_model,
    fingerprint_payload,
    freeze_payload,
)
from aion_brain.contracts.model_outputs import (
    reject_hidden_or_secret_text,
    reject_secret_like_payload,
)

SCHEMA_VERSION = "global-workspace/v1"
CANONICALIZATION_VERSION = "global-workspace-canonical-json/v1"
AUTHORIZATION_ID = "AION-187-CA-0003"
IMPLEMENTATION_TASK = "AION-188"

WorkspaceItemType = Literal[
    "goal",
    "belief",
    "hypothesis",
    "uncertainty",
    "world_prediction",
    "safety_finding",
    "operator_context",
    "memory_signal",
]
BidKind = Literal["ordinary", "critical_safety"]
CycleStatus = Literal["started", "attention_selected", "broadcasted", "complete", "blocked"]
AuditEventType = Literal[
    "bid_received",
    "duplicate_bid_rejected",
    "capacity_rejected",
    "attention_selected",
    "broadcast_created",
    "specialist_response_recorded",
    "cycle_completed",
]


class WorkspaceModel(BaseModel):
    """Base model for immutable workspace contracts."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = SCHEMA_VERSION

    @field_validator("schema_version")
    @classmethod
    def schema_version_must_match(cls, value: str) -> str:
        if value != SCHEMA_VERSION:
            raise ValueError(f"schema_version must be {SCHEMA_VERSION}")
        return value


class WorkspaceFingerprintedModel(WorkspaceModel):
    """Immutable model with a deterministic SHA-256 fingerprint."""

    fingerprint: str | None = None

    @model_validator(mode="after")
    def fingerprint_must_match_payload(self) -> Self:
        expected = fingerprint_model(self, exclude={"fingerprint"})
        if self.fingerprint is None:
            object.__setattr__(self, "fingerprint", expected)
        elif self.fingerprint != expected:
            raise ValueError("fingerprint must match canonical workspace payload")
        return self


class WorkspaceRuntimeBoundaryModel(WorkspaceFingerprintedModel):
    """Common false-by-default runtime boundary for workspace records."""

    runtime_effect: bool = False
    direct_action_execution: bool = False
    network_calls: int = Field(default=0, ge=0)
    connector_calls: int = Field(default=0, ge=0)
    model_provider_calls: int = Field(default=0, ge=0)
    model_call_made: bool = False
    production_exposure: bool = False
    model_weights_changed: bool = False

    @model_validator(mode="after")
    def runtime_boundaries_must_remain_disabled(self) -> Self:
        for key in (
            "runtime_effect",
            "direct_action_execution",
            "model_call_made",
            "production_exposure",
            "model_weights_changed",
        ):
            if getattr(self, key):
                raise ValueError(f"{key} must be false")
        for key in ("network_calls", "connector_calls", "model_provider_calls"):
            if getattr(self, key) != 0:
                raise ValueError(f"{key} must be zero")
        return self


class SalienceVector(WorkspaceFingerprintedModel):
    """Bounded salience dimensions used by deterministic attention arbitration."""

    goal_relevance: float = Field(ge=0.0, le=1.0)
    urgency: float = Field(ge=0.0, le=1.0)
    novelty: float = Field(ge=0.0, le=1.0)
    recurrence: float = Field(ge=0.0, le=1.0)
    uncertainty: float = Field(ge=0.0, le=1.0)
    expected_uncertainty_reduction: float = Field(ge=0.0, le=1.0)
    information_gain: float = Field(ge=0.0, le=1.0)
    expected_goal_progress: float = Field(ge=0.0, le=1.0)
    safety_risk: float = Field(ge=0.0, le=1.0)
    resource_cost: float = Field(ge=0.0, le=1.0)
    irreversibility: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)

    def weighted_score(self) -> float:
        """Return a deterministic scalar for ordering ordinary bids."""

        positive = (
            self.goal_relevance
            + self.urgency
            + self.novelty
            + self.recurrence
            + self.uncertainty
            + self.expected_uncertainty_reduction
            + self.information_gain
            + self.expected_goal_progress
            + (2.0 * self.safety_risk)
            + self.irreversibility
            + self.confidence
        )
        return round(positive - self.resource_cost, 12)


class WorkspaceItem(WorkspaceFingerprintedModel):
    """One bounded item offered to the shared workspace."""

    item_id: str = Field(min_length=1)
    source_specialist_id: str = Field(min_length=1)
    item_type: WorkspaceItemType
    content_summary: str = Field(min_length=1)
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)
    metadata: dict[str, Any] = Field(default_factory=dict)
    safety_critical: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("item_id", "source_specialist_id", "content_summary")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "workspace item text")
        return value.strip()

    @field_validator("evidence_refs")
    @classmethod
    def refs_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            reject_hidden_or_secret_text(item, "workspace evidence ref")
        return value

    @field_validator("metadata", mode="after")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> FrozenDict:
        reject_secret_like_payload(value)
        for key, nested in value.items():
            reject_hidden_or_secret_text(str(key), "workspace metadata key")
            if isinstance(nested, str):
                reject_hidden_or_secret_text(nested, "workspace metadata value")
        return cast(FrozenDict, freeze_payload(value))


class SpecialistBid(WorkspaceFingerprintedModel):
    """Immutable specialist bid for attention selection."""

    bid_id: str = Field(min_length=1)
    specialist_id: str = Field(min_length=1)
    item: WorkspaceItem
    salience: SalienceVector
    bid_kind: BidKind = "ordinary"
    requested_capacity_units: int = Field(default=1, ge=1)
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)
    submitted_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("bid_id", "specialist_id")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "workspace bid text")
        return value.strip()

    @field_validator("evidence_refs")
    @classmethod
    def refs_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            reject_hidden_or_secret_text(item, "workspace bid evidence ref")
        return value

    @model_validator(mode="after")
    def bid_must_match_item_and_safety_bounds(self) -> Self:
        if self.item.source_specialist_id != self.specialist_id:
            raise ValueError("bid specialist must match workspace item source")
        if self.bid_kind == "critical_safety":
            if not self.item.safety_critical:
                raise ValueError("critical safety bids require a safety-critical item")
            if self.salience.safety_risk < 0.8:
                raise ValueError("critical safety bids require high safety_risk")
        return self

    @property
    def dedupe_key(self) -> str:
        """Return the deterministic duplicate key for this bid."""

        return self.item.item_id

    @property
    def is_safety_critical(self) -> bool:
        """Return true when this bid must preempt ordinary bids."""

        return self.bid_kind == "critical_safety" and self.item.safety_critical


class AttentionDecision(WorkspaceRuntimeBoundaryModel):
    """Bounded attention selection for one cognitive cycle."""

    decision_id: str = Field(min_length=1)
    cycle_id: str = Field(min_length=1)
    selected_bids: tuple[SpecialistBid, ...] = Field(default_factory=tuple)
    deferred_bids: tuple[SpecialistBid, ...] = Field(default_factory=tuple)
    rejected_bids: tuple[SpecialistBid, ...] = Field(default_factory=tuple)
    capacity_limit: int = Field(ge=1)
    capacity_units_limit: int = Field(ge=1)
    used_capacity_units: int = Field(ge=0)
    safety_preemption_applied: bool = False
    starvation_protection_applied: bool = False
    reason_codes: tuple[str, ...] = Field(default_factory=tuple)
    deterministic_replay_hash: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("decision_id", "cycle_id")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "workspace decision text")
        return value.strip()

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            reject_hidden_or_secret_text(item, "workspace decision reason")
        return value

    @model_validator(mode="after")
    def selection_must_match_capacity_and_hash(self) -> Self:
        selected_ids = [bid.bid_id for bid in self.selected_bids]
        if len(selected_ids) != len(set(selected_ids)):
            raise ValueError("selected bids must be unique")
        used = sum(bid.requested_capacity_units for bid in self.selected_bids)
        if used != self.used_capacity_units:
            raise ValueError("used_capacity_units must match selected bids")
        if len(self.selected_bids) > self.capacity_limit:
            raise ValueError("selected bid count exceeds capacity_limit")
        if self.used_capacity_units > self.capacity_units_limit:
            raise ValueError("used capacity exceeds capacity_units_limit")
        expected_hash = fingerprint_payload(
            {
                "cycle_id": self.cycle_id,
                "selected": [bid.fingerprint for bid in self.selected_bids],
                "deferred": [bid.fingerprint for bid in self.deferred_bids],
                "rejected": [bid.fingerprint for bid in self.rejected_bids],
                "capacity_limit": self.capacity_limit,
                "capacity_units_limit": self.capacity_units_limit,
                "used_capacity_units": self.used_capacity_units,
                "reason_codes": self.reason_codes,
            }
        )
        if self.deterministic_replay_hash is None:
            object.__setattr__(self, "deterministic_replay_hash", expected_hash)
        elif self.deterministic_replay_hash != expected_hash:
            raise ValueError("deterministic_replay_hash must match attention payload")
        object.__setattr__(self, "fingerprint", fingerprint_model(self, exclude={"fingerprint"}))
        return self


class WorkspaceBroadcast(WorkspaceRuntimeBoundaryModel):
    """Broadcast of selected workspace items to approved specialists."""

    broadcast_id: str = Field(min_length=1)
    cycle_id: str = Field(min_length=1)
    decision_id: str = Field(min_length=1)
    selected_items: tuple[WorkspaceItem, ...] = Field(default_factory=tuple)
    approved_specialist_ids: tuple[str, ...] = Field(default_factory=tuple)
    broadcast_hash: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("broadcast_id", "cycle_id", "decision_id")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "workspace broadcast text")
        return value.strip()

    @field_validator("approved_specialist_ids")
    @classmethod
    def specialists_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            reject_hidden_or_secret_text(item, "workspace approved specialist")
        return value

    @model_validator(mode="after")
    def broadcast_must_be_bounded_and_hashed(self) -> Self:
        if len(self.approved_specialist_ids) != len(set(self.approved_specialist_ids)):
            raise ValueError("approved specialists must be unique")
        if len(self.selected_items) != len({item.item_id for item in self.selected_items}):
            raise ValueError("selected workspace items must be unique")
        expected_hash = fingerprint_payload(
            {
                "cycle_id": self.cycle_id,
                "decision_id": self.decision_id,
                "items": [item.fingerprint for item in self.selected_items],
                "approved_specialist_ids": self.approved_specialist_ids,
            }
        )
        if self.broadcast_hash is None:
            object.__setattr__(self, "broadcast_hash", expected_hash)
        elif self.broadcast_hash != expected_hash:
            raise ValueError("broadcast_hash must match selected payload")
        object.__setattr__(self, "fingerprint", fingerprint_model(self, exclude={"fingerprint"}))
        return self


class SpecialistResponse(WorkspaceRuntimeBoundaryModel):
    """In-process response from an approved specialist after a broadcast."""

    response_id: str = Field(min_length=1)
    cycle_id: str = Field(min_length=1)
    broadcast_id: str = Field(min_length=1)
    specialist_id: str = Field(min_length=1)
    accepted_item_ids: tuple[str, ...] = Field(default_factory=tuple)
    produced_bids: tuple[SpecialistBid, ...] = Field(default_factory=tuple)
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("response_id", "cycle_id", "broadcast_id", "specialist_id")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "workspace response text")
        return value.strip()

    @field_validator("accepted_item_ids", "evidence_refs")
    @classmethod
    def refs_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            reject_hidden_or_secret_text(item, "workspace response ref")
        return value


class WorkspaceAuditEvent(WorkspaceRuntimeBoundaryModel):
    """Sanitized audit event for workspace arbitration and broadcast."""

    event_id: str = Field(min_length=1)
    event_type: AuditEventType
    cycle_id: str = Field(min_length=1)
    specialist_id: str | None = None
    item_refs: tuple[str, ...] = Field(default_factory=tuple)
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("event_id", "cycle_id", "specialist_id")
    @classmethod
    def text_must_be_safe(cls, value: str | None) -> str | None:
        if value is not None:
            reject_hidden_or_secret_text(value, "workspace audit text")
            return value.strip()
        return value

    @field_validator("item_refs", "evidence_refs")
    @classmethod
    def refs_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            reject_hidden_or_secret_text(item, "workspace audit ref")
        return value


class CognitiveCycleState(WorkspaceRuntimeBoundaryModel):
    """Deterministic local state for one workspace cycle."""

    cycle_id: str = Field(min_length=1)
    sequence: int = Field(ge=1)
    status: CycleStatus
    decision: AttentionDecision | None = None
    broadcast: WorkspaceBroadcast | None = None
    responses: tuple[SpecialistResponse, ...] = Field(default_factory=tuple)
    audit_events: tuple[WorkspaceAuditEvent, ...] = Field(default_factory=tuple)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("cycle_id")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "workspace cycle text")
        return value.strip()

    @model_validator(mode="after")
    def cycle_status_must_match_payload(self) -> Self:
        if self.status in {"broadcasted", "complete"} and self.broadcast is None:
            raise ValueError("broadcasted and complete cycles require a broadcast")
        if self.status == "attention_selected" and self.decision is None:
            raise ValueError("attention_selected cycles require a decision")
        object.__setattr__(self, "fingerprint", fingerprint_model(self, exclude={"fingerprint"}))
        return self


class WorkspaceSnapshot(WorkspaceRuntimeBoundaryModel):
    """Deterministic snapshot of the current global workspace."""

    snapshot_id: str = Field(min_length=1)
    cycle_id: str = Field(min_length=1)
    sequence: int = Field(ge=1)
    active_items: tuple[WorkspaceItem, ...] = Field(default_factory=tuple)
    selected_item_ids: tuple[str, ...] = Field(default_factory=tuple)
    deferred_item_ids: tuple[str, ...] = Field(default_factory=tuple)
    approved_specialist_ids: tuple[str, ...] = Field(default_factory=tuple)
    audit_events: tuple[WorkspaceAuditEvent, ...] = Field(default_factory=tuple)
    snapshot_hash: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("snapshot_id", "cycle_id")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "workspace snapshot text")
        return value.strip()

    @field_validator("selected_item_ids", "deferred_item_ids", "approved_specialist_ids")
    @classmethod
    def refs_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            reject_hidden_or_secret_text(item, "workspace snapshot ref")
        return value

    @model_validator(mode="after")
    def snapshot_hash_must_match_payload(self) -> Self:
        active_ids = [item.item_id for item in self.active_items]
        if len(active_ids) != len(set(active_ids)):
            raise ValueError("active workspace items must be unique")
        expected_hash = fingerprint_payload(
            {
                "cycle_id": self.cycle_id,
                "sequence": self.sequence,
                "active_items": [item.fingerprint for item in self.active_items],
                "selected_item_ids": self.selected_item_ids,
                "deferred_item_ids": self.deferred_item_ids,
                "approved_specialist_ids": self.approved_specialist_ids,
                "audit_events": [event.fingerprint for event in self.audit_events],
            }
        )
        if self.snapshot_hash is None:
            object.__setattr__(self, "snapshot_hash", expected_hash)
        elif self.snapshot_hash != expected_hash:
            raise ValueError("snapshot_hash must match workspace payload")
        object.__setattr__(self, "fingerprint", fingerprint_model(self, exclude={"fingerprint"}))
        return self


__all__ = [
    "AUTHORIZATION_ID",
    "CANONICALIZATION_VERSION",
    "IMPLEMENTATION_TASK",
    "SCHEMA_VERSION",
    "AttentionDecision",
    "AuditEventType",
    "BidKind",
    "CognitiveCycleState",
    "CycleStatus",
    "SalienceVector",
    "SpecialistBid",
    "SpecialistResponse",
    "WorkspaceAuditEvent",
    "WorkspaceBroadcast",
    "WorkspaceItem",
    "WorkspaceItemType",
    "WorkspaceModel",
    "WorkspaceSnapshot",
    "fingerprint_payload",
]
