"""Redacted diagnostics and operator-review evidence for claim graphs."""

from __future__ import annotations

from datetime import datetime, timedelta
from enum import StrEnum
from typing import Literal, Self

from pydantic import BaseModel, Field, field_validator, model_validator

from aion_brain.contracts.knowledge_claim_graph import (
    AUTHORIZATION_SCOPE,
    AUTHORIZATION_TRANSACTION_ID,
    CLAIM_GRAPH_EVIDENCE_SCHEMA_VERSION,
    FORMAL_CLOSEOUT_TASK,
    IMPLEMENTATION_TASK,
    PROGRAM_ID,
    ClaimGraphAppendOutcome,
    ClaimGraphIntegrityStatus,
    ClaimModality,
    ClaimRelationType,
    validate_claim_graph_reason_codes,
)
from aion_brain.contracts.knowledge_research import (
    FROZEN_MODEL_CONFIG,
    ensure_utc,
    fingerprint_payload,
    reject_protected_material,
    validate_hex64,
    validate_safe_identifier,
)


class ClaimGraphIncidentRecord(BaseModel):
    """Redacted claim-graph incident evidence without claim or source text."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-claim-graph-evidence/v1"] = (
        CLAIM_GRAPH_EVIDENCE_SCHEMA_VERSION
    )
    incident_id: str
    severity: Literal["low", "medium", "high", "critical"]
    reason_codes: tuple[str, ...]
    affected_record_ids: tuple[str, ...] = Field(default_factory=tuple, max_length=50)
    affected_claim_ids: tuple[str, ...] = Field(default_factory=tuple, max_length=50)
    redacted_summary: str = Field(max_length=240)
    created_at: datetime
    incident_fingerprint: str
    source_body_present: Literal[False] = False
    truth_value_assigned: Literal[False] = False
    epistemic_confidence_assigned: Literal[False] = False
    knowledge_promoted: Literal[False] = False
    belief_mutated: Literal[False] = False
    runtime_effect: Literal[False] = False

    @field_validator("incident_id")
    @classmethod
    def incident_id_is_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "claim graph incident_id")

    @field_validator("affected_record_ids", "affected_claim_ids")
    @classmethod
    def identifiers_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if len(set(value)) != len(value):
            raise ValueError("duplicate claim graph incident IDs rejected")
        for item in value:
            validate_safe_identifier(item, "claim graph incident identifier")
        return tuple(sorted(value))

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_claim_graph_reason_codes(value)

    @field_validator("redacted_summary")
    @classmethod
    def summary_is_redacted(cls, value: str) -> str:
        _reject_diagnostic_text(value, "claim graph incident summary")
        return value

    @field_validator("created_at")
    @classmethod
    def created_at_is_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value, "claim graph incident timestamp")

    @field_validator("incident_fingerprint")
    @classmethod
    def incident_fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "claim graph incident fingerprint")

    @model_validator(mode="after")
    def incident_fingerprint_matches(self) -> Self:
        payload = self.model_dump(mode="json")
        payload.pop("incident_fingerprint", None)
        if self.incident_fingerprint != fingerprint_payload(payload):
            raise ValueError("claim graph incident fingerprint mismatch")
        return self


class ClaimGraphDiagnostics(BaseModel):
    """Bounded graph diagnostics that expose counts, IDs, and fingerprints only."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-claim-graph-evidence/v1"] = (
        CLAIM_GRAPH_EVIDENCE_SCHEMA_VERSION
    )
    diagnostic_id: str
    record_count: int = Field(ge=0)
    claim_count: int = Field(ge=0)
    evidence_binding_count: int = Field(ge=0)
    relation_count: int = Field(ge=0)
    structural_conflict_candidate_count: int = Field(ge=0)
    claim_modalities: tuple[ClaimModality, ...] = Field(default_factory=tuple, max_length=20)
    relation_types: tuple[ClaimRelationType, ...] = Field(default_factory=tuple, max_length=20)
    jurisdiction_scope_count: int = Field(ge=0)
    version_scope_count: int = Field(ge=0)
    temporal_overlap_count: int = Field(ge=0)
    integrity_status: ClaimGraphIntegrityStatus
    budget_within_limits: bool
    append_outcome: ClaimGraphAppendOutcome
    authorization_transaction_id: Literal["AION-208-KI-0003"] = AUTHORIZATION_TRANSACTION_ID
    chain_head_fingerprint: str | None
    diagnostic_fingerprint: str
    source_body_present: Literal[False] = False
    truth_value_assigned: Literal[False] = False
    epistemic_confidence_assigned: Literal[False] = False
    knowledge_promoted: Literal[False] = False
    belief_mutated: Literal[False] = False
    persistent_write_applied: Literal[False] = False
    runtime_effect: Literal[False] = False

    @field_validator("diagnostic_id")
    @classmethod
    def diagnostic_id_is_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "claim graph diagnostic_id")

    @field_validator("chain_head_fingerprint", "diagnostic_fingerprint")
    @classmethod
    def fingerprints_are_hex(cls, value: str | None) -> str | None:
        if value is not None:
            return validate_hex64(value, "claim graph diagnostic fingerprint")
        return value

    @model_validator(mode="after")
    def diagnostic_fingerprint_matches(self) -> Self:
        payload = self.model_dump(mode="json")
        payload.pop("diagnostic_fingerprint", None)
        if self.diagnostic_fingerprint != fingerprint_payload(payload):
            raise ValueError("claim graph diagnostic fingerprint mismatch")
        return self


class ClaimGraphOperatorReviewItem(BaseModel):
    """Operator review requirement; this is evidence and never approval."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-claim-graph-evidence/v1"] = (
        CLAIM_GRAPH_EVIDENCE_SCHEMA_VERSION
    )
    review_item_id: str
    graph_id: str
    diagnostic_id: str
    incident_ids: tuple[str, ...] = Field(default_factory=tuple, max_length=50)
    evidence_bundle_fingerprint: str
    operator_review_required: Literal[True] = True
    claim_verification_required: Literal[True] = True
    truth_engine_authorization_required: Literal[True] = True
    persistent_graph_write_authorization_required: Literal[True] = True
    knowledge_promotion_authorized: Literal[False] = False
    belief_mutation_authorized: Literal[False] = False
    approval_created: Literal[False] = False
    implementation_authorization_created: Literal[False] = False
    created_at: datetime
    expires_at: datetime
    review_fingerprint: str
    runtime_effect: Literal[False] = False

    @field_validator("review_item_id", "graph_id", "diagnostic_id")
    @classmethod
    def identifiers_are_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "claim graph review identifier")

    @field_validator("incident_ids")
    @classmethod
    def incident_ids_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if len(set(value)) != len(value):
            raise ValueError("duplicate incident IDs rejected")
        for item in value:
            validate_safe_identifier(item, "claim graph review incident_id")
        return tuple(sorted(value))

    @field_validator("evidence_bundle_fingerprint", "review_fingerprint")
    @classmethod
    def fingerprints_are_hex(cls, value: str) -> str:
        return validate_hex64(value, "claim graph review fingerprint")

    @field_validator("created_at", "expires_at")
    @classmethod
    def timestamps_are_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value, "claim graph review timestamp")

    @model_validator(mode="after")
    def review_is_bounded_and_fingerprinted(self) -> Self:
        if self.expires_at <= self.created_at:
            raise ValueError("claim graph review expiry must be after creation")
        if self.expires_at - self.created_at > timedelta(days=7):
            raise ValueError("claim graph review expiry must be within seven days")
        payload = self.model_dump(mode="json")
        payload.pop("review_fingerprint", None)
        if self.review_fingerprint != fingerprint_payload(payload):
            raise ValueError("claim graph review fingerprint mismatch")
        return self


class ClaimGraphEvidenceBundle(BaseModel):
    """Redacted evidence bundle for claim-graph operator review."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-claim-graph-evidence/v1"] = (
        CLAIM_GRAPH_EVIDENCE_SCHEMA_VERSION
    )
    program_id: Literal["AION-KNOWLEDGE-INTELLIGENCE-001"] = PROGRAM_ID
    authorization_transaction_id: Literal["AION-208-KI-0003"] = AUTHORIZATION_TRANSACTION_ID
    implementation_task: Literal["AION-209"] = IMPLEMENTATION_TASK
    formal_closeout_task: Literal["AION-210"] = FORMAL_CLOSEOUT_TASK
    authorization_scope: Literal[
        "append-only-immutable-temporal-claim-evidence-provenance-jurisdiction-version-contradiction-graph-core"
    ] = AUTHORIZATION_SCOPE
    bundle_id: str
    graph_id: str
    diagnostics: ClaimGraphDiagnostics
    incidents: tuple[ClaimGraphIncidentRecord, ...]
    operator_review_items: tuple[ClaimGraphOperatorReviewItem, ...]
    synthetic: Literal[True] = True
    read_only: Literal[True] = True
    redacted: Literal[True] = True
    source_body_present: Literal[False] = False
    persistent_write_applied: Literal[False] = False
    truth_value_assigned: Literal[False] = False
    epistemic_confidence_assigned: Literal[False] = False
    knowledge_promoted: Literal[False] = False
    belief_mutated: Literal[False] = False
    runtime_effect: Literal[False] = False
    bundle_fingerprint: str

    @field_validator("bundle_id", "graph_id")
    @classmethod
    def identifiers_are_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "claim graph evidence bundle identifier")

    @field_validator("bundle_fingerprint")
    @classmethod
    def bundle_fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "claim graph evidence bundle fingerprint")

    @model_validator(mode="after")
    def bundle_fingerprint_matches(self) -> Self:
        payload = self.model_dump(mode="json")
        payload.pop("bundle_fingerprint", None)
        if self.bundle_fingerprint != fingerprint_payload(payload):
            raise ValueError("claim graph evidence bundle fingerprint mismatch")
        return self


def claim_graph_incident_payload(
    *,
    incident_id: str,
    reason_codes: tuple[str, ...],
    created_at: datetime,
    severity: Literal["low", "medium", "high", "critical"] = "high",
    affected_record_ids: tuple[str, ...] = (),
    affected_claim_ids: tuple[str, ...] = (),
    redacted_summary: str = "Claim graph operator review is required.",
) -> dict[str, object]:
    """Build a deterministic redacted incident payload."""

    payload = {
        "schema_version": CLAIM_GRAPH_EVIDENCE_SCHEMA_VERSION,
        "incident_id": incident_id,
        "severity": severity,
        "reason_codes": reason_codes,
        "affected_record_ids": tuple(sorted(affected_record_ids)),
        "affected_claim_ids": tuple(sorted(affected_claim_ids)),
        "redacted_summary": redacted_summary,
        "created_at": created_at,
        "source_body_present": False,
        "truth_value_assigned": False,
        "epistemic_confidence_assigned": False,
        "knowledge_promoted": False,
        "belief_mutated": False,
        "runtime_effect": False,
    }
    return {**payload, "incident_fingerprint": _evidence_fingerprint(payload)}


def claim_graph_diagnostics_payload(
    *,
    diagnostic_id: str,
    record_count: int,
    claim_count: int,
    evidence_binding_count: int,
    relation_count: int,
    structural_conflict_candidate_count: int,
    claim_modalities: tuple[ClaimModality, ...],
    relation_types: tuple[ClaimRelationType, ...],
    jurisdiction_scope_count: int,
    version_scope_count: int,
    temporal_overlap_count: int,
    integrity_status: ClaimGraphIntegrityStatus,
    budget_within_limits: bool,
    append_outcome: ClaimGraphAppendOutcome,
    chain_head_fingerprint: str | None,
) -> dict[str, object]:
    """Build a deterministic diagnostics payload."""

    payload = {
        "schema_version": CLAIM_GRAPH_EVIDENCE_SCHEMA_VERSION,
        "diagnostic_id": diagnostic_id,
        "record_count": record_count,
        "claim_count": claim_count,
        "evidence_binding_count": evidence_binding_count,
        "relation_count": relation_count,
        "structural_conflict_candidate_count": structural_conflict_candidate_count,
        "claim_modalities": tuple(sorted(item.value for item in claim_modalities)),
        "relation_types": tuple(sorted(item.value for item in relation_types)),
        "jurisdiction_scope_count": jurisdiction_scope_count,
        "version_scope_count": version_scope_count,
        "temporal_overlap_count": temporal_overlap_count,
        "integrity_status": integrity_status.value,
        "budget_within_limits": budget_within_limits,
        "append_outcome": append_outcome.value,
        "authorization_transaction_id": AUTHORIZATION_TRANSACTION_ID,
        "chain_head_fingerprint": chain_head_fingerprint,
        "source_body_present": False,
        "truth_value_assigned": False,
        "epistemic_confidence_assigned": False,
        "knowledge_promoted": False,
        "belief_mutated": False,
        "persistent_write_applied": False,
        "runtime_effect": False,
    }
    return {**payload, "diagnostic_fingerprint": _evidence_fingerprint(payload)}


def claim_graph_operator_review_payload(
    *,
    review_item_id: str,
    graph_id: str,
    diagnostic_id: str,
    incident_ids: tuple[str, ...],
    evidence_bundle_fingerprint: str,
    created_at: datetime,
    expires_at: datetime,
) -> dict[str, object]:
    """Build a deterministic operator-review item payload."""

    payload = {
        "schema_version": CLAIM_GRAPH_EVIDENCE_SCHEMA_VERSION,
        "review_item_id": review_item_id,
        "graph_id": graph_id,
        "diagnostic_id": diagnostic_id,
        "incident_ids": tuple(sorted(incident_ids)),
        "evidence_bundle_fingerprint": evidence_bundle_fingerprint,
        "operator_review_required": True,
        "claim_verification_required": True,
        "truth_engine_authorization_required": True,
        "persistent_graph_write_authorization_required": True,
        "knowledge_promotion_authorized": False,
        "belief_mutation_authorized": False,
        "approval_created": False,
        "implementation_authorization_created": False,
        "created_at": created_at,
        "expires_at": expires_at,
        "runtime_effect": False,
    }
    return {**payload, "review_fingerprint": _evidence_fingerprint(payload)}


def claim_graph_evidence_bundle_payload(
    *,
    bundle_id: str,
    graph_id: str,
    diagnostics: ClaimGraphDiagnostics,
    incidents: tuple[ClaimGraphIncidentRecord, ...],
    operator_review_items: tuple[ClaimGraphOperatorReviewItem, ...],
) -> dict[str, object]:
    """Build a deterministic redacted evidence-bundle payload."""

    payload = {
        "schema_version": CLAIM_GRAPH_EVIDENCE_SCHEMA_VERSION,
        "program_id": PROGRAM_ID,
        "authorization_transaction_id": AUTHORIZATION_TRANSACTION_ID,
        "implementation_task": IMPLEMENTATION_TASK,
        "formal_closeout_task": FORMAL_CLOSEOUT_TASK,
        "authorization_scope": AUTHORIZATION_SCOPE,
        "bundle_id": bundle_id,
        "graph_id": graph_id,
        "diagnostics": diagnostics.model_dump(mode="json"),
        "incidents": [item.model_dump(mode="json") for item in incidents],
        "operator_review_items": [item.model_dump(mode="json") for item in operator_review_items],
        "synthetic": True,
        "read_only": True,
        "redacted": True,
        "source_body_present": False,
        "persistent_write_applied": False,
        "truth_value_assigned": False,
        "epistemic_confidence_assigned": False,
        "knowledge_promoted": False,
        "belief_mutated": False,
        "runtime_effect": False,
    }
    return {**payload, "bundle_fingerprint": _evidence_fingerprint(payload)}


def _reject_diagnostic_text(value: str, field_name: str) -> None:
    reject_protected_material(value, field_name)
    lowered = value.lower()
    for marker in (
        "://",
        "/",
        "claim statement",
        "object value",
        "source body",
        "source preview",
        "raw prompt",
        "hidden reasoning",
        "raw user message",
        "raw diff",
        "traceback",
        "exception",
    ):
        if marker in lowered:
            raise ValueError("claim graph evidence must remain redacted")


def _evidence_fingerprint(payload: dict[str, object]) -> str:
    return fingerprint_payload(_json_ready(payload))


def _json_ready(value: object) -> object:
    if isinstance(value, datetime):
        text = value.isoformat()
        if text.endswith("+00:00"):
            return f"{text[:-6]}Z"
        return text
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value


__all__ = [
    "ClaimGraphDiagnostics",
    "ClaimGraphEvidenceBundle",
    "ClaimGraphIncidentRecord",
    "ClaimGraphOperatorReviewItem",
    "claim_graph_diagnostics_payload",
    "claim_graph_evidence_bundle_payload",
    "claim_graph_incident_payload",
    "claim_graph_operator_review_payload",
]
