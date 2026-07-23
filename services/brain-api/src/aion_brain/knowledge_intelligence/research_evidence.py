"""Redacted research evidence, diagnostics, incidents, and results."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Literal, Self

from pydantic import BaseModel, Field, field_validator, model_validator

from aion_brain.contracts.knowledge_research import (
    FROZEN_MODEL_CONFIG,
    RESEARCH_DIAGNOSTICS_SCHEMA_VERSION,
    RESEARCH_EVIDENCE_SCHEMA_VERSION,
    RESEARCH_INCIDENT_SCHEMA_VERSION,
    CitationReference,
    ResearchPlanOutcome,
    ensure_utc,
    reject_protected_material,
    validate_hex64,
    validate_reason_codes,
    validate_safe_identifier,
)
from aion_brain.knowledge_intelligence.research_budget import ResearchBudgetDecision
from aion_brain.knowledge_intelligence.source_deduplication import (
    SourceDeduplicationDecision,
    SourceLineageRecord,
)
from aion_brain.knowledge_intelligence.source_provenance import SourceProvenanceRecord
from aion_brain.knowledge_intelligence.source_snapshot import SourceSnapshot


class ResearchIncidentRecord(BaseModel):
    """Redacted incident record for fail-closed research events."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-research-incident/v1"] = (
        RESEARCH_INCIDENT_SCHEMA_VERSION
    )
    incident_id: str
    plan_id: str
    severity: Literal["low", "medium", "high", "critical"]
    reason_codes: tuple[str, ...]
    redacted_summary: str = Field(max_length=300)
    created_at: datetime
    fingerprint: str
    redacted: Literal[True] = True
    runtime_effect: Literal[False] = False

    @field_validator("incident_id", "plan_id")
    @classmethod
    def ids_are_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "incident identifier")

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_are_registered(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_reason_codes(value)

    @field_validator("redacted_summary")
    @classmethod
    def summary_is_safe(cls, value: str) -> str:
        reject_protected_material(value, "incident summary")
        return value

    @field_validator("created_at")
    @classmethod
    def created_at_is_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value, "incident created_at")

    @field_validator("fingerprint")
    @classmethod
    def fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "incident fingerprint")


class ResearchDiagnostics(BaseModel):
    """Bounded diagnostics without source bodies or exception text."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-research-diagnostics/v1"] = (
        RESEARCH_DIAGNOSTICS_SCHEMA_VERSION
    )
    plan_id: str
    reason_codes: tuple[str, ...]
    bounded_counts: dict[str, int]
    adapter_state: dict[str, bool]
    incident_ids: tuple[str, ...] = Field(default_factory=tuple)
    created_at: datetime
    fingerprint: str
    redacted: Literal[True] = True

    @field_validator("plan_id", "incident_ids")
    @classmethod
    def identifiers_are_safe(cls, value: object) -> object:
        if isinstance(value, str):
            return validate_safe_identifier(value, "diagnostic identifier")
        if isinstance(value, tuple):
            for item in value:
                validate_safe_identifier(item, "diagnostic identifier")
        return value

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_are_registered(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_reason_codes(value)

    @field_validator("bounded_counts")
    @classmethod
    def bounded_counts_are_safe(cls, value: dict[str, int]) -> dict[str, int]:
        for count in value.values():
            if count < 0:
                raise ValueError("diagnostic counts must not be negative")
        return value

    @field_validator("created_at")
    @classmethod
    def created_at_is_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value, "diagnostics created_at")

    @field_validator("fingerprint")
    @classmethod
    def fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "diagnostics fingerprint")


class ResearchOperatorReviewItem(BaseModel):
    """Operator review item for untrusted acquired evidence."""

    model_config = FROZEN_MODEL_CONFIG

    review_item_id: str
    plan_id: str
    snapshot_ids: tuple[str, ...]
    source_class_distribution: dict[str, int]
    policy_rejections: tuple[str, ...]
    budget_status: str
    lineage_summary: dict[str, int]
    citation_reference_ids: tuple[str, ...]
    incident_ids: tuple[str, ...]
    operator_review_required: Literal[True] = True
    claim_verification_required: Literal[True] = True
    knowledge_promotion_authorized: Literal[False] = False
    belief_mutation_authorized: Literal[False] = False
    created_at: datetime
    expires_at: datetime
    fingerprint: str

    @field_validator("review_item_id", "plan_id")
    @classmethod
    def ids_are_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "review identifier")

    @field_validator("snapshot_ids", "citation_reference_ids", "incident_ids")
    @classmethod
    def tuple_ids_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            validate_safe_identifier(item, "review reference")
        return value

    @field_validator("policy_rejections")
    @classmethod
    def policy_rejections_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            reject_protected_material(item, "policy rejection")
        return value

    @field_validator("created_at", "expires_at")
    @classmethod
    def timestamps_are_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value, "review timestamp")

    @field_validator("fingerprint")
    @classmethod
    def fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "review fingerprint")

    @model_validator(mode="after")
    def expiry_is_bounded(self) -> Self:
        if self.expires_at <= self.created_at:
            raise ValueError("review expiry must be after creation")
        if self.expires_at - self.created_at > timedelta(days=7):
            raise ValueError("review expiry must be within seven days")
        return self


class ResearchEvidenceBundle(BaseModel):
    """Immutable redacted bundle of source-evidence metadata."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-research-evidence/v1"] = (
        RESEARCH_EVIDENCE_SCHEMA_VERSION
    )
    plan_id: str
    snapshots: tuple[SourceSnapshot, ...]
    provenance_records: tuple[SourceProvenanceRecord, ...]
    citation_references: tuple[CitationReference, ...]
    lineage_records: tuple[SourceLineageRecord, ...]
    deduplication_decisions: tuple[SourceDeduplicationDecision, ...]
    diagnostics: ResearchDiagnostics
    incidents: tuple[ResearchIncidentRecord, ...]
    operator_review_items: tuple[ResearchOperatorReviewItem, ...]
    created_at: datetime
    fingerprint: str
    redacted: Literal[True] = True
    read_only: Literal[True] = True
    source_claims_verified: Literal[False] = False
    knowledge_promoted: Literal[False] = False
    belief_created: Literal[False] = False
    runtime_effect: Literal[False] = False

    @field_validator("plan_id")
    @classmethod
    def plan_id_is_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "plan_id")

    @field_validator("created_at")
    @classmethod
    def created_at_is_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value, "evidence created_at")

    @field_validator("fingerprint")
    @classmethod
    def fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "evidence fingerprint")


class ResearchAcquisitionResult(BaseModel):
    """Final immutable result of one explicit controlled acquisition run."""

    model_config = FROZEN_MODEL_CONFIG

    plan_id: str
    outcome: ResearchPlanOutcome
    budget_decision: ResearchBudgetDecision
    evidence_bundle: ResearchEvidenceBundle | None
    incidents: tuple[ResearchIncidentRecord, ...]
    diagnostics: ResearchDiagnostics
    reason_codes: tuple[str, ...]
    created_at: datetime
    fingerprint: str
    knowledge_candidate_created: Literal[False] = False
    belief_created: Literal[False] = False
    approval_created: Literal[False] = False
    authorization_created: Literal[False] = False
    runtime_effect: Literal[False] = False

    @field_validator("plan_id")
    @classmethod
    def plan_id_is_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "plan_id")

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_are_registered(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_reason_codes(value)

    @field_validator("created_at")
    @classmethod
    def created_at_is_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value, "result created_at")

    @field_validator("fingerprint")
    @classmethod
    def fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "result fingerprint")


__all__ = [
    "ResearchAcquisitionResult",
    "ResearchDiagnostics",
    "ResearchEvidenceBundle",
    "ResearchIncidentRecord",
    "ResearchOperatorReviewItem",
]
