"""Memory consolidation contracts owned by AION Brain."""

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

SCHEMA_VERSION = "memory-consolidation/v1"
CANONICALIZATION_VERSION = "memory-consolidation-canonical-json/v1"
AUTHORIZATION_ID = "AION-189-CA-0004"
IMPLEMENTATION_TASK = "AION-190"

CandidateType = Literal[
    "semantic",
    "procedural",
    "contradiction_resolution",
    "forgetting",
]
PromotionStatus = Literal["operator_review_required", "approved_by_existing_governance", "rejected"]


class MemoryConsolidationModel(BaseModel):
    """Base model for immutable memory-consolidation contracts."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = SCHEMA_VERSION

    @field_validator("schema_version")
    @classmethod
    def schema_version_must_match(cls, value: str) -> str:
        if value != SCHEMA_VERSION:
            raise ValueError(f"schema_version must be {SCHEMA_VERSION}")
        return value


class MemoryConsolidationFingerprintedModel(MemoryConsolidationModel):
    """Immutable model with a deterministic SHA-256 fingerprint."""

    fingerprint: str | None = None

    @model_validator(mode="after")
    def fingerprint_must_match_payload(self) -> Self:
        expected = fingerprint_model(self, exclude={"fingerprint"})
        if self.fingerprint is None:
            object.__setattr__(self, "fingerprint", expected)
        elif self.fingerprint != expected:
            raise ValueError("fingerprint must match canonical consolidation payload")
        return self


class MemoryConsolidationRuntimeBoundaryModel(MemoryConsolidationFingerprintedModel):
    """False-by-default runtime boundary for consolidation records."""

    runtime_effect: bool = False
    direct_action_execution: bool = False
    network_calls: int = Field(default=0, ge=0)
    connector_calls: int = Field(default=0, ge=0)
    model_provider_calls: int = Field(default=0, ge=0)
    model_call_made: bool = False
    production_exposure: bool = False
    model_weights_changed: bool = False
    automatic_promotion: bool = False
    source_rewrite: bool = False
    background_consolidation: bool = False
    hidden_memory_mutation: bool = False
    deletion_without_policy_evidence: bool = False

    @model_validator(mode="after")
    def runtime_boundaries_must_remain_disabled(self) -> Self:
        for key in (
            "runtime_effect",
            "direct_action_execution",
            "model_call_made",
            "production_exposure",
            "model_weights_changed",
            "automatic_promotion",
            "source_rewrite",
            "background_consolidation",
            "hidden_memory_mutation",
            "deletion_without_policy_evidence",
        ):
            if getattr(self, key):
                raise ValueError(f"{key} must be false")
        for key in ("network_calls", "connector_calls", "model_provider_calls"):
            if getattr(self, key) != 0:
                raise ValueError(f"{key} must be zero")
        return self


class EpisodicMemoryReference(MemoryConsolidationFingerprintedModel):
    """One operational episode eligible for local replay selection."""

    episode_id: str = Field(min_length=1)
    source: str = Field(min_length=1)
    content_summary: str = Field(min_length=1)
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    salience_tags: tuple[str, ...] = Field(default_factory=tuple)
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    safety_critical: bool = False
    retention_required: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("episode_id", "source", "content_summary")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "episodic memory reference text")
        return value.strip()

    @field_validator("salience_tags", "evidence_refs")
    @classmethod
    def refs_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            reject_hidden_or_secret_text(item, "episodic memory reference ref")
        return tuple(sorted(dict.fromkeys(item.strip() for item in value if item.strip())))

    @field_validator("metadata", mode="after")
    @classmethod
    def metadata_must_be_safe(cls, value: dict[str, Any]) -> FrozenDict:
        reject_secret_like_payload(value)
        for key, nested in value.items():
            reject_hidden_or_secret_text(str(key), "episodic memory metadata key")
            if isinstance(nested, str):
                reject_hidden_or_secret_text(nested, "episodic memory metadata value")
        return cast(FrozenDict, freeze_payload(value))


class ReplayBatch(MemoryConsolidationRuntimeBoundaryModel):
    """Deterministic replay batch selected from operational episodes."""

    batch_id: str = Field(min_length=1)
    references: tuple[EpisodicMemoryReference, ...]
    selection_reason: str = Field(min_length=1)
    max_items: int = Field(ge=1)
    replay_hash: str | None = None
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("batch_id", "selection_reason")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "replay batch text")
        return value.strip()

    @model_validator(mode="after")
    def replay_batch_must_be_unique_and_hashed(self) -> Self:
        if not self.references:
            raise ValueError("replay batch requires at least one reference")
        if len(self.references) > self.max_items:
            raise ValueError("replay batch exceeds max_items")
        episode_ids = [reference.episode_id for reference in self.references]
        if len(episode_ids) != len(set(episode_ids)):
            raise ValueError("replay batch references must be unique")
        expected_hash = fingerprint_payload(
            {
                "batch_id": self.batch_id,
                "references": [reference.fingerprint for reference in self.references],
                "selection_reason": self.selection_reason,
                "max_items": self.max_items,
            }
        )
        if self.replay_hash is None:
            object.__setattr__(self, "replay_hash", expected_hash)
        elif self.replay_hash != expected_hash:
            raise ValueError("replay_hash must match replay batch payload")
        object.__setattr__(self, "fingerprint", fingerprint_model(self, exclude={"fingerprint"}))
        return self


class ConsolidationCandidate(MemoryConsolidationRuntimeBoundaryModel):
    """Base candidate that always requires operator review before promotion."""

    candidate_id: str = Field(min_length=1)
    candidate_type: CandidateType
    source_episode_ids: tuple[str, ...]
    summary: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)
    operator_review_required: bool = True
    approved_for_promotion: bool = False
    promotion_allowed: bool = False
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("candidate_id", "summary")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "consolidation candidate text")
        return value.strip()

    @field_validator("source_episode_ids", "evidence_refs")
    @classmethod
    def refs_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            reject_hidden_or_secret_text(item, "consolidation candidate ref")
        return tuple(sorted(dict.fromkeys(item.strip() for item in value if item.strip())))

    @model_validator(mode="after")
    def promotion_must_remain_review_gated(self) -> Self:
        if not self.source_episode_ids:
            raise ValueError("candidate requires source episodes")
        if not self.evidence_refs:
            raise ValueError("candidate requires evidence refs")
        if not self.operator_review_required:
            raise ValueError("operator review is required")
        if self.approved_for_promotion or self.promotion_allowed:
            raise ValueError("promotion must remain blocked until existing governance approves")
        return self


class SemanticCandidate(ConsolidationCandidate):
    """Candidate durable semantic statement derived from replay clusters."""

    candidate_type: Literal["semantic"] = "semantic"
    concept_key: str = Field(min_length=1)
    normalized_statement: str = Field(min_length=1)
    supporting_episode_ids: tuple[str, ...]
    contradicting_episode_ids: tuple[str, ...] = Field(default_factory=tuple)

    @field_validator("concept_key", "normalized_statement")
    @classmethod
    def semantic_text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "semantic candidate text")
        return value.strip()

    @field_validator("supporting_episode_ids", "contradicting_episode_ids")
    @classmethod
    def semantic_refs_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            reject_hidden_or_secret_text(item, "semantic candidate ref")
        return tuple(sorted(dict.fromkeys(item.strip() for item in value if item.strip())))

    @model_validator(mode="after")
    def semantic_support_must_be_present(self) -> Self:
        if not self.supporting_episode_ids:
            raise ValueError("semantic candidate requires supporting episodes")
        return self


class ProceduralCandidate(ConsolidationCandidate):
    """Candidate procedural pattern derived from replayed operational steps."""

    candidate_type: Literal["procedural"] = "procedural"
    procedure_name: str = Field(min_length=1)
    steps: tuple[str, ...]
    success_episode_ids: tuple[str, ...]
    failure_episode_ids: tuple[str, ...] = Field(default_factory=tuple)

    @field_validator("procedure_name")
    @classmethod
    def procedure_name_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "procedural candidate name")
        return value.strip()

    @field_validator("steps", "success_episode_ids", "failure_episode_ids")
    @classmethod
    def procedural_refs_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            reject_hidden_or_secret_text(item, "procedural candidate ref")
        return tuple(item.strip() for item in value if item.strip())

    @model_validator(mode="after")
    def procedure_must_have_steps_and_support(self) -> Self:
        if not self.steps:
            raise ValueError("procedural candidate requires steps")
        if not self.success_episode_ids:
            raise ValueError("procedural candidate requires successful episodes")
        return self


class ContradictionResolutionCandidate(ConsolidationCandidate):
    """Candidate resolution for contradictory semantic candidates."""

    candidate_type: Literal["contradiction_resolution"] = "contradiction_resolution"
    contradiction_set_id: str = Field(min_length=1)
    preferred_candidate_id: str = Field(min_length=1)
    rejected_candidate_ids: tuple[str, ...]
    resolution_rationale: str = Field(min_length=1)

    @field_validator("contradiction_set_id", "preferred_candidate_id", "resolution_rationale")
    @classmethod
    def contradiction_text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "contradiction candidate text")
        return value.strip()

    @field_validator("rejected_candidate_ids")
    @classmethod
    def rejected_refs_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            reject_hidden_or_secret_text(item, "contradiction candidate ref")
        return tuple(sorted(dict.fromkeys(item.strip() for item in value if item.strip())))

    @model_validator(mode="after")
    def contradiction_resolution_must_not_drop_evidence(self) -> Self:
        if not self.rejected_candidate_ids:
            raise ValueError("contradiction resolution requires rejected candidate ids")
        if self.preferred_candidate_id in self.rejected_candidate_ids:
            raise ValueError("preferred candidate cannot also be rejected")
        return self


class ForgettingCandidate(ConsolidationCandidate):
    """Candidate retention action that cannot delete without explicit policy evidence."""

    candidate_type: Literal["forgetting"] = "forgetting"
    retention_policy: str = Field(min_length=1)
    candidate_episode_ids: tuple[str, ...]
    explicit_policy_evidence_refs: tuple[str, ...]
    deletion_allowed: bool = False

    @field_validator("retention_policy")
    @classmethod
    def retention_policy_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "forgetting candidate policy")
        return value.strip()

    @field_validator("candidate_episode_ids", "explicit_policy_evidence_refs")
    @classmethod
    def forgetting_refs_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            reject_hidden_or_secret_text(item, "forgetting candidate ref")
        return tuple(sorted(dict.fromkeys(item.strip() for item in value if item.strip())))

    @model_validator(mode="after")
    def forgetting_candidate_must_remain_non_destructive(self) -> Self:
        if not self.candidate_episode_ids:
            raise ValueError("forgetting candidate requires episode ids")
        if not self.explicit_policy_evidence_refs:
            raise ValueError("forgetting candidate requires policy evidence")
        if self.deletion_allowed:
            raise ValueError("AION-190 may not authorize deletion")
        return self


class ConsolidationEvidence(MemoryConsolidationRuntimeBoundaryModel):
    """Benchmark evidence for a consolidation checkpoint."""

    evidence_id: str = Field(min_length=1)
    replay_batch_id: str = Field(min_length=1)
    candidate_ids: tuple[str, ...]
    retained_critical_memories_rate: float = Field(ge=0.0, le=1.0)
    duplicate_reduction_rate: float = Field(ge=0.0, le=1.0)
    contradiction_loss_rate: float = Field(ge=0.0, le=1.0)
    catastrophic_forgetting_rate: float = Field(ge=0.0, le=1.0)
    provenance_coverage: float = Field(ge=0.0, le=1.0)
    unauthorized_promotion_count: int = Field(ge=0)
    deterministic_replay_hash: str = Field(min_length=1)
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("evidence_id", "replay_batch_id", "deterministic_replay_hash")
    @classmethod
    def evidence_text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "consolidation evidence text")
        return value.strip()

    @field_validator("candidate_ids", "evidence_refs")
    @classmethod
    def evidence_refs_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            reject_hidden_or_secret_text(item, "consolidation evidence ref")
        return tuple(sorted(dict.fromkeys(item.strip() for item in value if item.strip())))

    @model_validator(mode="after")
    def evidence_must_meet_safety_floor(self) -> Self:
        if self.retained_critical_memories_rate < 1.0:
            raise ValueError("critical memories must be retained")
        if self.contradiction_loss_rate != 0.0:
            raise ValueError("contradiction evidence must not be lost")
        if self.unauthorized_promotion_count != 0:
            raise ValueError("unauthorized promotions must be zero")
        if self.provenance_coverage < 1.0:
            raise ValueError("provenance coverage must be complete")
        return self


class ConsolidationCheckpoint(MemoryConsolidationRuntimeBoundaryModel):
    """Operator-review checkpoint for consolidation candidates."""

    checkpoint_id: str = Field(min_length=1)
    replay_batch: ReplayBatch
    candidates: tuple[ConsolidationCandidate, ...]
    evidence: ConsolidationEvidence
    operator_review_required: bool = True
    promotion_status: PromotionStatus = "operator_review_required"
    approved_by_governance_ref: str | None = None
    automatic_promotion_performed: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("checkpoint_id", "approved_by_governance_ref")
    @classmethod
    def checkpoint_text_must_be_safe(cls, value: str | None) -> str | None:
        if value is not None:
            reject_hidden_or_secret_text(value, "consolidation checkpoint text")
            return value.strip()
        return value

    @model_validator(mode="after")
    def checkpoint_must_match_evidence(self) -> Self:
        if not self.operator_review_required:
            raise ValueError("operator review is required")
        if self.automatic_promotion_performed:
            raise ValueError("automatic promotion must not be performed")
        if self.promotion_status == "approved_by_existing_governance":
            if not self.approved_by_governance_ref:
                raise ValueError("approved promotion requires governance ref")
        elif self.approved_by_governance_ref is not None:
            raise ValueError("governance ref is only allowed for approved promotion")
        candidate_ids = {candidate.candidate_id for candidate in self.candidates}
        if candidate_ids != set(self.evidence.candidate_ids):
            raise ValueError("checkpoint candidates must match evidence candidate ids")
        if self.replay_batch.batch_id != self.evidence.replay_batch_id:
            raise ValueError("checkpoint evidence must reference replay batch")
        return self


class ConsolidationOutcome(MemoryConsolidationRuntimeBoundaryModel):
    """Complete local consolidation pipeline output."""

    outcome_id: str = Field(min_length=1)
    checkpoint: ConsolidationCheckpoint
    semantic_candidates: tuple[SemanticCandidate, ...] = Field(default_factory=tuple)
    procedural_candidates: tuple[ProceduralCandidate, ...] = Field(default_factory=tuple)
    contradiction_resolutions: tuple[ContradictionResolutionCandidate, ...] = Field(
        default_factory=tuple
    )
    forgetting_candidates: tuple[ForgettingCandidate, ...] = Field(default_factory=tuple)
    pipeline_stages: tuple[str, ...]
    approved_promotions: tuple[str, ...] = Field(default_factory=tuple)
    promotion_performed: bool = False
    source_rewrite_performed: bool = False
    hidden_mutation_performed: bool = False
    deletion_performed: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("outcome_id")
    @classmethod
    def outcome_text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "consolidation outcome text")
        return value.strip()

    @field_validator("pipeline_stages", "approved_promotions")
    @classmethod
    def outcome_refs_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            reject_hidden_or_secret_text(item, "consolidation outcome ref")
        return tuple(item.strip() for item in value if item.strip())

    @model_validator(mode="after")
    def outcome_must_remain_review_gated(self) -> Self:
        if self.approved_promotions:
            raise ValueError("AION-190 must not record approved promotions")
        for key in (
            "promotion_performed",
            "source_rewrite_performed",
            "hidden_mutation_performed",
            "deletion_performed",
        ):
            if getattr(self, key):
                raise ValueError(f"{key} must be false")
        candidate_ids = {candidate.candidate_id for candidate in self.checkpoint.candidates}
        typed_ids = {
            candidate.candidate_id
            for candidate in (
                *self.semantic_candidates,
                *self.procedural_candidates,
                *self.contradiction_resolutions,
                *self.forgetting_candidates,
            )
        }
        if candidate_ids != typed_ids:
            raise ValueError("outcome typed candidates must match checkpoint candidates")
        return self


__all__ = [
    "AUTHORIZATION_ID",
    "CANONICALIZATION_VERSION",
    "IMPLEMENTATION_TASK",
    "SCHEMA_VERSION",
    "CandidateType",
    "ConsolidationCandidate",
    "ConsolidationCheckpoint",
    "ConsolidationEvidence",
    "ConsolidationOutcome",
    "ContradictionResolutionCandidate",
    "EpisodicMemoryReference",
    "ForgettingCandidate",
    "MemoryConsolidationFingerprintedModel",
    "MemoryConsolidationModel",
    "MemoryConsolidationRuntimeBoundaryModel",
    "ProceduralCandidate",
    "PromotionStatus",
    "ReplayBatch",
    "SemanticCandidate",
    "fingerprint_payload",
]
