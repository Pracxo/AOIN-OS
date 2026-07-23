"""Redacted evidence for append-only source-registry operations."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Literal, Self

from pydantic import BaseModel, Field, field_validator, model_validator

from aion_brain.contracts.knowledge_research import (
    FROZEN_MODEL_CONFIG,
    ensure_utc,
    fingerprint_payload,
    reject_protected_material,
    utc_now,
    validate_hex64,
    validate_safe_identifier,
)
from aion_brain.contracts.knowledge_source_registry import (
    AUTHORIZATION_SCOPE,
    AUTHORIZATION_TRANSACTION_ID,
    FORMAL_CLOSEOUT_TASK,
    IMPLEMENTATION_TASK,
    PROGRAM_ID,
    SourceRegistryAppendDecision,
    SourceRegistryBudgetDecision,
    SourceRegistryRecordKind,
    validate_source_registry_reason_codes,
)
from aion_brain.knowledge_intelligence.source_registry_integrity import (
    SourceRegistryIntegrityReport,
)


class SourceRegistryIncidentRecord(BaseModel):
    """Redacted incident record for registry projection or replay failures."""

    model_config = FROZEN_MODEL_CONFIG

    incident_id: str
    severity: Literal["low", "medium", "high", "critical"]
    reason_codes: tuple[str, ...]
    redacted_summary: str = Field(max_length=240)
    created_at: datetime
    fingerprint: str
    runtime_effect: Literal[False] = False

    @field_validator("incident_id")
    @classmethod
    def incident_id_is_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "source registry incident_id")

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_source_registry_reason_codes(value)

    @field_validator("redacted_summary")
    @classmethod
    def summary_is_safe(cls, value: str) -> str:
        _reject_evidence_leakage(value, "source registry incident summary")
        return value

    @field_validator("created_at")
    @classmethod
    def created_at_is_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value, "source registry incident timestamp")

    @field_validator("fingerprint")
    @classmethod
    def fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "source registry incident fingerprint")


class SourceRegistryDiagnostics(BaseModel):
    """Bounded diagnostics with no source content or exception text."""

    model_config = FROZEN_MODEL_CONFIG

    diagnostic_id: str
    record_count: int = Field(ge=0)
    record_kinds: tuple[SourceRegistryRecordKind, ...]
    source_classes: tuple[str, ...]
    integrity_status: Literal["passed", "failed"]
    budget_status: Literal["within_budget", "blocked"]
    append_outcome: Literal["simulated_append", "persistent_write_rejected"]
    unresolved_reference_count: int = Field(ge=0)
    duplicate_count: int = Field(ge=0)
    supersession_count: int = Field(ge=0)
    authorization_lineage: tuple[str, ...]
    runtime_disabled: Literal[True] = True
    persistent_write_enabled: Literal[False] = False
    claim_verification_enabled: Literal[False] = False
    knowledge_promotion_enabled: Literal[False] = False
    belief_mutation_enabled: Literal[False] = False
    network_access_enabled: Literal[False] = False
    created_at: datetime
    fingerprint: str
    runtime_effect: Literal[False] = False

    @field_validator("diagnostic_id")
    @classmethod
    def diagnostic_id_is_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "source registry diagnostic_id")

    @field_validator("source_classes", "authorization_lineage")
    @classmethod
    def tuple_values_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            reject_protected_material(item, "source registry diagnostic")
        return value

    @field_validator("created_at")
    @classmethod
    def created_at_is_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value, "source registry diagnostics timestamp")

    @field_validator("fingerprint")
    @classmethod
    def fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "source registry diagnostics fingerprint")


class SourceRegistryOperatorReviewItem(BaseModel):
    """Operator review item for future persistence and claim verification gates."""

    model_config = FROZEN_MODEL_CONFIG

    review_item_id: str
    registry_batch_fingerprint: str
    integrity_report_fingerprint: str
    append_decision_fingerprint: str
    operator_review_required: Literal[True] = True
    claim_verification_required: Literal[True] = True
    persistent_write_authorization_required: Literal[True] = True
    knowledge_promotion_authorized: Literal[False] = False
    belief_mutation_authorized: Literal[False] = False
    approval_created: Literal[False] = False
    implementation_authorization_created: Literal[False] = False
    created_at: datetime
    expires_at: datetime
    fingerprint: str
    runtime_effect: Literal[False] = False

    @field_validator("review_item_id")
    @classmethod
    def review_item_id_is_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "source registry review_item_id")

    @field_validator(
        "registry_batch_fingerprint",
        "integrity_report_fingerprint",
        "append_decision_fingerprint",
        "fingerprint",
    )
    @classmethod
    def fingerprints_are_hex(cls, value: str) -> str:
        return validate_hex64(value, "source registry review fingerprint")

    @field_validator("created_at", "expires_at")
    @classmethod
    def timestamps_are_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value, "source registry review timestamp")

    @model_validator(mode="after")
    def review_expiry_is_bounded(self) -> Self:
        if self.expires_at <= self.created_at:
            raise ValueError("review expiry must be after creation")
        if self.expires_at - self.created_at > timedelta(days=7):
            raise ValueError("review expiry must be within seven days")
        return self


class SourceRegistryEvidenceBundle(BaseModel):
    """Redacted evidence bundle for source-registry operations."""

    model_config = FROZEN_MODEL_CONFIG

    program_id: Literal["AION-KNOWLEDGE-INTELLIGENCE-001"] = PROGRAM_ID
    authorization_transaction_id: Literal["AION-206-KI-0002"] = AUTHORIZATION_TRANSACTION_ID
    implementation_task: Literal["AION-207"] = IMPLEMENTATION_TASK
    formal_closeout_task: Literal["AION-208"] = FORMAL_CLOSEOUT_TASK
    authorization_scope: Literal[
        "append-only-immutable-source-snapshot-provenance-lineage-citation-registry-core"
    ] = AUTHORIZATION_SCOPE
    evidence_bundle_id: str
    diagnostics: SourceRegistryDiagnostics
    incidents: tuple[SourceRegistryIncidentRecord, ...]
    operator_review_items: tuple[SourceRegistryOperatorReviewItem, ...]
    integrity_report: SourceRegistryIntegrityReport
    budget_decision: SourceRegistryBudgetDecision
    append_decision: SourceRegistryAppendDecision
    created_at: datetime
    fingerprint: str
    read_only: Literal[True] = True
    redacted: Literal[True] = True
    source_body_present: Literal[False] = False
    source_body_bytes: Literal[0] = 0
    claim_verification_enabled: Literal[False] = False
    knowledge_promotion_enabled: Literal[False] = False
    belief_mutation_enabled: Literal[False] = False
    persistent_write_applied: Literal[False] = False
    runtime_effect: Literal[False] = False

    @field_validator("evidence_bundle_id")
    @classmethod
    def evidence_bundle_id_is_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "source registry evidence_bundle_id")

    @field_validator("created_at")
    @classmethod
    def created_at_is_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value, "source registry evidence timestamp")

    @field_validator("fingerprint")
    @classmethod
    def fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "source registry evidence fingerprint")


def build_source_registry_evidence_bundle(
    *,
    record_kinds: tuple[SourceRegistryRecordKind, ...],
    source_classes: tuple[str, ...],
    integrity_report: SourceRegistryIntegrityReport,
    budget_decision: SourceRegistryBudgetDecision,
    append_decision: SourceRegistryAppendDecision,
    registry_batch_fingerprint: str,
    clock: object = utc_now,
) -> SourceRegistryEvidenceBundle:
    """Build redacted evidence for a registry operation."""

    now = clock() if callable(clock) else utc_now()
    duplicate_count = sum(
        1
        for finding in integrity_report.findings
        if "source_registry_duplicate_identifier" in finding.reason_codes
    )
    diagnostics_payload = {
        "record_count": integrity_report.record_count,
        "record_kinds": record_kinds,
        "source_classes": source_classes,
        "integrity_status": integrity_report.status,
        "budget_status": "within_budget" if budget_decision.within_budget else "blocked",
        "append_outcome": (
            "simulated_append"
            if append_decision.append_allowed
            else "persistent_write_rejected"
        ),
        "finding_count": len(integrity_report.findings),
        "duplicate_count": duplicate_count,
    }
    diagnostics = SourceRegistryDiagnostics(
        diagnostic_id="source-registry-diagnostics-0001",
        record_count=integrity_report.record_count,
        record_kinds=record_kinds,
        source_classes=source_classes,
        integrity_status=integrity_report.status,
        budget_status="within_budget" if budget_decision.within_budget else "blocked",
        append_outcome=(
            "simulated_append"
            if append_decision.append_allowed
            else "persistent_write_rejected"
        ),
        unresolved_reference_count=sum(
            1
            for finding in integrity_report.findings
            if "source_registry_chain_broken" in finding.reason_codes
        ),
        duplicate_count=duplicate_count,
        supersession_count=sum(
            1
            for finding in integrity_report.findings
            if "source_registry_supersession_missing" in finding.reason_codes
            or "source_registry_supersession_cycle" in finding.reason_codes
        ),
        authorization_lineage=(
            AUTHORIZATION_TRANSACTION_ID,
            IMPLEMENTATION_TASK,
            FORMAL_CLOSEOUT_TASK,
        ),
        created_at=now,
        fingerprint=fingerprint_payload(diagnostics_payload),
    )
    review_payload = {
        "registry_batch": registry_batch_fingerprint,
        "integrity": integrity_report.report_fingerprint,
        "append": append_decision.fingerprint,
        "created_at": now.isoformat(),
    }
    review = SourceRegistryOperatorReviewItem(
        review_item_id="source-registry-review-0001",
        registry_batch_fingerprint=registry_batch_fingerprint,
        integrity_report_fingerprint=integrity_report.report_fingerprint,
        append_decision_fingerprint=append_decision.fingerprint,
        created_at=now,
        expires_at=now + timedelta(days=7),
        fingerprint=fingerprint_payload(review_payload),
    )
    payload = {
        "diagnostics": diagnostics.fingerprint,
        "integrity": integrity_report.report_fingerprint,
        "budget": budget_decision.fingerprint,
        "append": append_decision.fingerprint,
        "review": review.fingerprint,
        "created_at": now.isoformat(),
    }
    return SourceRegistryEvidenceBundle(
        evidence_bundle_id="source-registry-evidence-0001",
        diagnostics=diagnostics,
        incidents=(),
        operator_review_items=(review,),
        integrity_report=integrity_report,
        budget_decision=budget_decision,
        append_decision=append_decision,
        created_at=now,
        fingerprint=fingerprint_payload(payload),
    )


def _reject_evidence_leakage(value: str, field_name: str) -> None:
    reject_protected_material(value, field_name)
    lowered = value.lower()
    for marker in (
        "http://",
        "https://",
        "traceback",
        "exception",
        "raw prompt",
        "hidden reasoning",
        "raw user message",
        "source patch",
        "raw diff",
        "authorization header",
        "cookie",
    ):
        if marker in lowered:
            raise ValueError(f"{field_name} contains forbidden evidence")


__all__ = [
    "SourceRegistryDiagnostics",
    "SourceRegistryEvidenceBundle",
    "SourceRegistryIncidentRecord",
    "SourceRegistryOperatorReviewItem",
    "build_source_registry_evidence_bundle",
]
