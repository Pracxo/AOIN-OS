"""Governed learning and memory promotion-planning contracts.

These contracts implement the AION-221-authorized AION-222 dry-run planning
surface. They produce reviewable transaction plans only: no approval creation,
knowledge persistence, cognitive-memory write, belief mutation, network access,
tool execution, or runtime registration is performed here.
"""

from __future__ import annotations

import json
import math
import re
from collections.abc import Iterable, Mapping
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator, model_validator

from aion_brain.contracts.approvals import ApprovalDecision, ApprovalRequest
from aion_brain.contracts.beliefs import BeliefSensitivity
from aion_brain.contracts.knowledge_epistemic_assessment import (
    ContradictionStatus,
    FreshnessStatus,
    ScopeApplicability,
)
from aion_brain.contracts.knowledge_research import (
    ensure_utc,
    fingerprint_payload,
    reject_protected_material,
    validate_hex64,
)
from aion_brain.contracts.knowledge_verified_memory import (
    IntegratedKnowledgeLineage,
    VerifiedKnowledgeCandidate,
    VerifiedKnowledgeCandidateKind,
    VerifiedKnowledgeEligibilityStatus,
    VerifiedKnowledgeIntegrityReport,
    VerifiedKnowledgeIntegrityStatus,
    VerifiedKnowledgeLifecycleStatus,
)

GOVERNED_LEARNING_MEMORY_CONTRACT_SCHEMA_VERSION: Final[
    Literal["aion-governed-learning-memory/v1"]
] = "aion-governed-learning-memory/v1"
KNOWLEDGE_PROMOTION_REQUEST_SCHEMA_VERSION: Final[
    Literal["aion-glm-knowledge-promotion-request/v1"]
] = "aion-glm-knowledge-promotion-request/v1"
PROMOTION_CANDIDATE_BINDING_SCHEMA_VERSION: Final[
    Literal["aion-glm-promotion-candidate-binding/v1"]
] = "aion-glm-promotion-candidate-binding/v1"
OPERATOR_APPROVAL_EVIDENCE_SCHEMA_VERSION: Final[
    Literal["aion-glm-operator-approval-evidence/v1"]
] = "aion-glm-operator-approval-evidence/v1"
APPROVAL_EVIDENCE_BUNDLE_SCHEMA_VERSION: Final[
    Literal["aion-glm-approval-evidence-bundle/v1"]
] = "aion-glm-approval-evidence-bundle/v1"
PROMOTION_ELIGIBILITY_SNAPSHOT_SCHEMA_VERSION: Final[
    Literal["aion-glm-promotion-eligibility-snapshot/v1"]
] = "aion-glm-promotion-eligibility-snapshot/v1"
EXISTING_KNOWLEDGE_VERSION_REFERENCE_SCHEMA_VERSION: Final[
    Literal["aion-glm-existing-knowledge-version-reference/v1"]
] = (
    "aion-glm-existing-knowledge-version-reference/v1"
)
KNOWLEDGE_IDENTITY_PLAN_SCHEMA_VERSION: Final[
    Literal["aion-glm-knowledge-identity-plan/v1"]
] = "aion-glm-knowledge-identity-plan/v1"
KNOWLEDGE_CONFLICT_REPORT_SCHEMA_VERSION: Final[
    Literal["aion-glm-knowledge-conflict-report/v1"]
] = "aion-glm-knowledge-conflict-report/v1"
KNOWLEDGE_VERSION_PLAN_SCHEMA_VERSION: Final[
    Literal["aion-glm-knowledge-version-plan/v1"]
] = "aion-glm-knowledge-version-plan/v1"
MEMORY_PROJECTION_RECORD_PLAN_SCHEMA_VERSION: Final[
    Literal["aion-glm-memory-projection-record-plan/v1"]
] = "aion-glm-memory-projection-record-plan/v1"
MEMORY_PROJECTION_PLAN_SCHEMA_VERSION: Final[
    Literal["aion-glm-memory-projection-plan/v1"]
] = "aion-glm-memory-projection-plan/v1"
PROMOTION_ROLLBACK_PLAN_SCHEMA_VERSION: Final[
    Literal["aion-glm-promotion-rollback-plan/v1"]
] = "aion-glm-promotion-rollback-plan/v1"
PROMOTION_COMPENSATION_PLAN_SCHEMA_VERSION: Final[
    Literal["aion-glm-promotion-compensation-plan/v1"]
] = "aion-glm-promotion-compensation-plan/v1"
PROMOTION_TRANSACTION_PLAN_SCHEMA_VERSION: Final[
    Literal["aion-glm-promotion-transaction-plan/v1"]
] = "aion-glm-promotion-transaction-plan/v1"
PROMOTION_TRANSACTION_RESULT_SCHEMA_VERSION: Final[
    Literal["aion-glm-promotion-transaction-result/v1"]
] = "aion-glm-promotion-transaction-result/v1"
PROMOTION_TRANSACTION_JOURNAL_SCHEMA_VERSION: Final[
    Literal["aion-glm-promotion-transaction-journal/v1"]
] = "aion-glm-promotion-transaction-journal/v1"
PROMOTION_TRANSACTION_QUERY_SCHEMA_VERSION: Final[
    Literal["aion-glm-promotion-transaction-query/v1"]
] = "aion-glm-promotion-transaction-query/v1"
PROMOTION_TRANSACTION_QUERY_RESULT_SCHEMA_VERSION: Final[
    Literal["aion-glm-promotion-transaction-query-result/v1"]
] = "aion-glm-promotion-transaction-query-result/v1"
PROMOTION_FIXTURE_SCHEMA_VERSION: Final[
    Literal["aion-glm-promotion-fixture/v1"]
] = "aion-glm-promotion-fixture/v1"
PROMOTION_INTEGRITY_SCHEMA_VERSION: Final[
    Literal["aion-glm-promotion-integrity/v1"]
] = "aion-glm-promotion-integrity/v1"
PROMOTION_EVIDENCE_SCHEMA_VERSION: Final[
    Literal["aion-glm-promotion-evidence/v1"]
] = "aion-glm-promotion-evidence/v1"
PROMOTION_REASON_CODE_REGISTRY_VERSION = "aion-glm-promotion-reasons/v1"

PROGRAM_ID = "AION-GOVERNED-LEARNING-MEMORY-001"
AUTHORIZATION_TRANSACTION_ID = "AION-221-GLM-0001"
APPROVAL_RECORD_ID = "AION-221-GLM-0001"
IMPLEMENTATION_TASK = "AION-222"
FORMAL_CLOSEOUT_TASK = "AION-223"
AUTHORIZATION_SCOPE = (
    "verified-candidate-operator-approval-provenance-revalidation-deduplication-"
    "conflict-supersession-rollback-dry-run-cognitive-memory-projection-core"
)

MODEL_CONFIG = ConfigDict(extra="forbid", hide_input_in_errors=True)
FROZEN_MODEL_CONFIG = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

MAXIMUM_PROMOTION_REQUESTS_PER_BATCH = 100
MAXIMUM_CANDIDATES_PER_REQUEST = 100
MAXIMUM_LINEAGE_REFERENCES_PER_CANDIDATE = 500
MAXIMUM_SOURCE_REFERENCES_PER_CANDIDATE = 100
MAXIMUM_CLAIM_REFERENCES_PER_CANDIDATE = 20
MAXIMUM_ASSESSMENT_REFERENCES_PER_CANDIDATE = 20
MAXIMUM_MESH_REFERENCES_PER_CANDIDATE = 20
MAXIMUM_TOOL_SESSION_REFERENCES_PER_CANDIDATE = 20
MAXIMUM_APPROVAL_EVIDENCE_RECORDS_PER_TRANSACTION = 4
MAXIMUM_PROJECTION_RECORDS_PER_TRANSACTION = 100
MAXIMUM_VERSIONS_PER_KNOWLEDGE_IDENTITY = 100
MAXIMUM_ROLLBACK_STEPS_PER_TRANSACTION = 50
MAXIMUM_COMPENSATION_STEPS_PER_TRANSACTION = 50
MAXIMUM_OPERATOR_REVIEW_ITEMS = 100
MAXIMUM_IN_MEMORY_TRANSACTIONS = 1000
MAXIMUM_QUERY_RESULTS = 1000
MAXIMUM_FIXTURE_RECORDS = 5000
MAXIMUM_FIXTURE_BYTES = 4_194_304
MAXIMUM_CONCURRENCY = 4

_SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_PROTECTED_KEY_MARKERS = (
    "source_body",
    "source-preview",
    "source_preview",
    "raw_prompt",
    "hidden_reasoning",
    "raw_user_message",
    "credential",
    "token",
    "cookie",
    "authorization_header",
    "private_key",
    "client_certificate",
    "personal_data",
    "source_patch",
    "raw_diff",
)
_PROTECTED_VALUE_MARKERS = (
    "source body",
    "source preview",
    "raw prompt",
    "hidden reasoning",
    "raw user message",
    "credential",
    "token:",
    "cookie:",
    "authorization:",
    "private key",
    "client certificate",
    "personal data",
    "source patch",
    "raw diff",
    "diff --git",
    "sk-",
    "ghp_",
    "gho_",
    "xoxb-",
)


class PromotionRequestKind(StrEnum):
    INITIAL_VERSION = "initial_version"
    NEW_VERSION = "new_version"
    SUPERSESSION = "supersession"
    RETRACTION = "retraction"
    EXPIRY = "expiry"
    REVALIDATION_ONLY = "revalidation_only"


class PromotionRiskClass(StrEnum):
    MINIMAL = "minimal"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class PromotionCandidateDisposition(StrEnum):
    ELIGIBLE_FOR_DRY_RUN = "eligible_for_dry_run"
    INELIGIBLE = "ineligible"
    REVALIDATION_REQUIRED = "revalidation_required"
    EXACT_DUPLICATE_NO_OP = "exact_duplicate_no_op"
    CONFLICT_BLOCKED = "conflict_blocked"
    APPROVAL_BLOCKED = "approval_blocked"
    ABSTAINED = "abstained"


class ApprovalEvidenceStatus(StrEnum):
    VALID = "valid"
    EXPIRED = "expired"
    REVOKED = "revoked"
    DENIED = "denied"
    CANCELLED = "cancelled"
    SCOPE_MISMATCH = "scope_mismatch"
    RESOURCE_MISMATCH = "resource_mismatch"
    BINDING_MISMATCH = "binding_mismatch"
    SEPARATION_OF_DUTIES_FAILED = "separation_of_duties_failed"
    INSUFFICIENT_APPROVALS = "insufficient_approvals"


class KnowledgeIdentityDisposition(StrEnum):
    NEW_IDENTITY = "new_identity"
    EXISTING_IDENTITY = "existing_identity"
    DUPLICATE_IDENTITY = "duplicate_identity"
    CONFLICTING_IDENTITY = "conflicting_identity"


class KnowledgeConflictKind(StrEnum):
    EXACT_DUPLICATE = "exact_duplicate"
    LINEAGE_DUPLICATE = "lineage_duplicate"
    DIRECT_POSTURE_CONFLICT = "direct_posture_conflict"
    TEMPORAL_SCOPE_CONFLICT = "temporal_scope_conflict"
    JURISDICTION_SCOPE_CONFLICT = "jurisdiction_scope_conflict"
    VERSION_SCOPE_CONFLICT = "version_scope_conflict"
    RETRACTION_CONFLICT = "retraction_conflict"
    SUPERSESSION_CONFLICT = "supersession_conflict"
    UNRESOLVED_DISSENT_CONFLICT = "unresolved_dissent_conflict"
    APPROVAL_CONFLICT = "approval_conflict"


class KnowledgeVersionDisposition(StrEnum):
    INITIAL_VERSION_PLANNED = "initial_version_planned"
    NEW_VERSION_PLANNED = "new_version_planned"
    SUPERSESSION_PLANNED = "supersession_planned"
    RETRACTION_PLANNED = "retraction_planned"
    EXPIRY_PLANNED = "expiry_planned"
    REVALIDATION_ONLY = "revalidation_only"
    NO_OP_DUPLICATE = "no_op_duplicate"
    BLOCKED = "blocked"


class MemoryProjectionTarget(StrEnum):
    SEMANTIC_MEMORY = "semantic_memory"
    EPISODIC_MEMORY = "episodic_memory"
    PROCEDURAL_MEMORY = "procedural_memory"
    BELIEF_CANDIDATE = "belief_candidate"


class MemoryProjectionStatus(StrEnum):
    PLANNED = "planned"
    SKIPPED_NOT_APPLICABLE = "skipped_not_applicable"
    BLOCKED = "blocked"
    ABSTAINED = "abstained"


class PromotionTransactionStatus(StrEnum):
    DRAFTED = "drafted"
    VALIDATED = "validated"
    DRY_RUN_PASSED = "dry_run_passed"
    DRY_RUN_NO_OP_DUPLICATE = "dry_run_no_op_duplicate"
    BLOCKED = "blocked"
    ABSTAINED = "abstained"
    INTEGRITY_FAILED = "integrity_failed"
    PERSISTENT_WRITE_DISABLED = "persistent_write_disabled"


class PromotionIntegrityStatus(StrEnum):
    PASSED = "passed"
    FAILED = "failed"


class PersistentWriteOutcome(StrEnum):
    PERSISTENT_WRITE_DISABLED = "persistent_write_disabled"


PROMOTION_REASON_CODES: tuple[str, ...] = (
    "promotion_request_valid",
    "promotion_request_invalid",
    "promotion_request_budget_exceeded",
    "promotion_candidate_binding_valid",
    "promotion_candidate_binding_invalid",
    "promotion_candidate_ineligible",
    "promotion_candidate_revalidation_required",
    "promotion_candidate_expired",
    "promotion_candidate_lineage_invalid",
    "promotion_candidate_integrity_invalid",
    "promotion_candidate_confidence_non_amplification_passed",
    "approval_evidence_valid",
    "approval_evidence_expired",
    "approval_evidence_revoked",
    "approval_evidence_denied",
    "approval_evidence_cancelled",
    "approval_scope_mismatch",
    "approval_resource_mismatch",
    "approval_candidate_binding_mismatch",
    "approval_transaction_binding_mismatch",
    "approval_separation_of_duties_passed",
    "approval_separation_of_duties_failed",
    "approval_insufficient_independent_approvers",
    "approval_runtime_creation_blocked",
    "knowledge_identity_derived",
    "knowledge_identity_existing",
    "knowledge_identity_collision",
    "knowledge_exact_duplicate",
    "knowledge_lineage_duplicate",
    "knowledge_direct_conflict",
    "knowledge_temporal_scope_conflict",
    "knowledge_jurisdiction_scope_conflict",
    "knowledge_version_scope_conflict",
    "knowledge_retraction_conflict",
    "knowledge_supersession_conflict",
    "knowledge_dissent_conflict",
    "knowledge_initial_version_planned",
    "knowledge_new_version_planned",
    "knowledge_supersession_planned",
    "knowledge_retraction_planned",
    "knowledge_expiry_planned",
    "knowledge_history_preserved",
    "knowledge_hard_delete_blocked",
    "semantic_memory_projection_planned",
    "episodic_memory_projection_planned",
    "procedural_memory_projection_planned",
    "belief_candidate_projection_planned",
    "memory_projection_blocked",
    "memory_projection_write_disabled",
    "belief_projection_is_candidate_only",
    "promotion_idempotency_passed",
    "promotion_idempotency_failed",
    "promotion_rollback_valid",
    "promotion_rollback_invalid",
    "promotion_compensation_valid",
    "promotion_compensation_invalid",
    "promotion_resource_budget_valid",
    "promotion_resource_budget_exceeded",
    "promotion_transaction_dry_run_passed",
    "promotion_transaction_duplicate_no_op",
    "promotion_transaction_blocked",
    "promotion_transaction_abstained",
    "promotion_transaction_integrity_passed",
    "promotion_transaction_integrity_failed",
    "persistent_knowledge_write_blocked",
    "persistent_verified_knowledge_write_blocked",
    "semantic_memory_write_blocked",
    "episodic_memory_write_blocked",
    "procedural_memory_write_blocked",
    "cognitive_memory_write_blocked",
    "belief_creation_blocked",
    "belief_mutation_blocked",
    "automatic_candidate_approval_blocked",
    "automatic_knowledge_promotion_blocked",
    "automatic_memory_ingestion_blocked",
    "engagement_automatic_application_blocked",
    "network_access_blocked",
    "tool_execution_blocked",
    "runtime_disabled",
)
PROMOTION_REASON_CODE_SET = frozenset(PROMOTION_REASON_CODES)
ROLLBACK_OPERATION_REGISTRY: tuple[str, ...] = (
    "append_retraction_marker_plan",
    "append_superseding_version_plan",
    "restore_prior_active_version_pointer_plan",
    "invalidate_pending_projection_plan",
    "restore_prior_projection_pointer_plan",
    "revalidate_candidate_lineage",
    "invalidate_approval_binding",
    "create_operator_review_item",
    "preserve_audit_evidence",
)


def validate_promotion_reason_codes(values: Iterable[str]) -> tuple[str, ...]:
    reason_codes = tuple(values)
    seen: set[str] = set()
    for code in reason_codes:
        if code not in PROMOTION_REASON_CODE_SET:
            raise ValueError("unknown governed learning memory reason code")
        if code in seen:
            raise ValueError("duplicate governed learning memory reason code")
        seen.add(code)
    return reason_codes


def _q(value: Decimal | int | str | float) -> Decimal:
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            raise ValueError("confidence must be finite")
        value = str(value)
    try:
        decimal = Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("confidence must be a decimal value") from exc
    if decimal.is_nan() or decimal.is_infinite():
        raise ValueError("confidence must be finite")
    quantized = decimal.quantize(QUANT)
    if quantized < ZERO or quantized > ONE:
        raise ValueError("confidence must be between zero and one")
    return quantized


def _validate_identifier(value: str, field_name: str = "identifier") -> str:
    if value != value.strip():
        raise ValueError(f"{field_name} must not contain surrounding whitespace")
    if "/" in value or "\\" in value:
        raise ValueError(f"{field_name} must not contain path separators")
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise ValueError(f"{field_name} must not contain control characters")
    try:
        value.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError(f"{field_name} must be safe ASCII") from exc
    if not _SAFE_ID_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be 1..128 safe ASCII characters")
    _reject_protected(value, field_name)
    return value


def _reject_protected(
    value: Any, field_name: str = "payload", seen: set[int] | None = None
) -> None:
    if seen is None:
        seen = set()
    marker = id(value)
    if marker in seen:
        raise ValueError(f"{field_name} contains recursive material")
    if isinstance(value, (Mapping, list, tuple, set, frozenset)):
        seen.add(marker)
    if callable(value) or isinstance(value, BaseException):
        raise ValueError(f"{field_name} contains executable material")
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = str(key).lower().replace("-", "_")
            if any(part in key_text for part in _PROTECTED_KEY_MARKERS):
                raise ValueError(f"{field_name} contains protected material")
            _reject_protected(nested, field_name, seen)
    elif isinstance(value, (list, tuple, set, frozenset)):
        for item in value:
            _reject_protected(item, field_name, seen)
    elif isinstance(value, str):
        lowered = value.lower()
        if any(part in lowered for part in _PROTECTED_VALUE_MARKERS):
            raise ValueError(f"{field_name} contains protected material")
        reject_protected_material(value, field_name)


def _jsonable(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, Decimal):
        return f"{_q(value):.6f}"
    if isinstance(value, datetime):
        return ensure_utc(value).isoformat().replace("+00:00", "Z")
    if isinstance(value, Mapping):
        return {str(key): _jsonable(nested) for key, nested in value.items()}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    return value


def governed_learning_memory_fingerprint(value: Any) -> str:
    return fingerprint_payload(_jsonable(value))


def _model_fingerprint(model: BaseModel, exclude: set[str]) -> str:
    return governed_learning_memory_fingerprint(model.model_dump(mode="python", exclude=exclude))


def _build[T: BaseModel](
    model: type[T], payload: Mapping[str, Any], fingerprint_field: str
) -> T:
    base = dict(payload)
    base[fingerprint_field] = ""
    draft = model.model_construct(**base)
    base[fingerprint_field] = _model_fingerprint(draft, {fingerprint_field})
    return model.model_validate(base)


class StrictFrozenModel(BaseModel):
    model_config = FROZEN_MODEL_CONFIG

    @field_validator("*", mode="after", check_fields=False)
    @classmethod
    def normalize_decimal_fields(cls, value: Any, info: ValidationInfo) -> Any:
        if isinstance(value, Decimal):
            return _q(value)
        field_name = info.field_name or ""
        if isinstance(value, tuple) and "confidence" in field_name:
            return tuple(_q(item) if isinstance(item, Decimal) else item for item in value)
        return value

    @field_validator("reason_codes", check_fields=False)
    @classmethod
    def reason_codes_are_known(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_promotion_reason_codes(value)

    @model_validator(mode="after")
    def values_are_safe(self) -> Self:
        for field_name, value in self.__dict__.items():
            if isinstance(value, datetime):
                ensure_utc(value, field_name)
            if field_name.endswith("_fingerprint") and isinstance(value, str):
                validate_hex64(value, field_name)
            if field_name.endswith("_fingerprints"):
                for item in tuple(value or ()):
                    validate_hex64(str(item), field_name)
            if field_name.endswith("_id") and isinstance(value, str):
                _validate_identifier(value, field_name)
            if field_name.endswith("_ids"):
                for item in tuple(value or ()):
                    _validate_identifier(str(item), field_name)
            _reject_protected(value, field_name)
        return self


class KnowledgePromotionRequest(StrictFrozenModel):
    schema_version: Literal["aion-glm-knowledge-promotion-request/v1"] = (
        KNOWLEDGE_PROMOTION_REQUEST_SCHEMA_VERSION
    )
    promotion_request_id: str
    transaction_id: str
    request_kind: PromotionRequestKind
    candidate_ids: tuple[str, ...]
    candidate_fingerprints: tuple[str, ...]
    requested_projection_targets: tuple[MemoryProjectionTarget, ...]
    risk_class: PromotionRiskClass
    owner_scope_fingerprints: tuple[str, ...]
    requested_at: datetime
    expires_at: datetime
    approval_evidence_ids: tuple[str, ...]
    operator_requested: Literal[True] = True
    dry_run_only: Literal[True] = True
    persistent_write_requested: Literal[False] = False
    cognitive_memory_write_requested: Literal[False] = False
    belief_mutation_requested: Literal[False] = False
    automatic_promotion_requested: Literal[False] = False
    runtime_effect: Literal[False] = False
    request_fingerprint: str

    @model_validator(mode="after")
    def validate_request(self) -> Self:
        if not self.candidate_ids:
            raise ValueError("promotion request requires at least one candidate")
        if len(self.candidate_ids) > MAXIMUM_CANDIDATES_PER_REQUEST:
            raise ValueError("candidate limit exceeded")
        if len(set(self.candidate_ids)) != len(self.candidate_ids):
            raise ValueError("candidate IDs must be unique")
        if len(set(self.candidate_fingerprints)) != len(self.candidate_fingerprints):
            raise ValueError("candidate fingerprints must be unique")
        if len(self.candidate_ids) != len(self.candidate_fingerprints):
            raise ValueError("candidate IDs and fingerprints must match")
        if not self.requested_projection_targets:
            raise ValueError("projection target required")
        if self.expires_at <= self.requested_at:
            raise ValueError("expiration must be after request time")
        if self.expires_at - self.requested_at > timedelta(hours=24):
            raise ValueError("request expiration exceeds 24 hours")
        expected = _model_fingerprint(self, {"request_fingerprint"})
        if self.request_fingerprint != expected:
            raise ValueError("promotion request fingerprint mismatch")
        return self


def build_knowledge_promotion_request(
    *,
    promotion_request_id: str,
    transaction_id: str,
    request_kind: PromotionRequestKind,
    candidate_ids: tuple[str, ...],
    candidate_fingerprints: tuple[str, ...],
    requested_projection_targets: tuple[MemoryProjectionTarget, ...],
    risk_class: PromotionRiskClass,
    owner_scope_fingerprints: tuple[str, ...],
    requested_at: datetime,
    approval_evidence_ids: tuple[str, ...],
    expires_at: datetime | None = None,
) -> KnowledgePromotionRequest:
    return _build(
        KnowledgePromotionRequest,
        {
            "promotion_request_id": promotion_request_id,
            "transaction_id": transaction_id,
            "request_kind": request_kind,
            "candidate_ids": candidate_ids,
            "candidate_fingerprints": candidate_fingerprints,
            "requested_projection_targets": requested_projection_targets,
            "risk_class": risk_class,
            "owner_scope_fingerprints": owner_scope_fingerprints,
            "requested_at": requested_at,
            "expires_at": expires_at or requested_at + timedelta(hours=1),
            "approval_evidence_ids": approval_evidence_ids,
        },
        "request_fingerprint",
    )


class PromotionCandidateBinding(StrictFrozenModel):
    schema_version: Literal["aion-glm-promotion-candidate-binding/v1"] = (
        PROMOTION_CANDIDATE_BINDING_SCHEMA_VERSION
    )
    binding_id: str
    promotion_request_id: str
    transaction_id: str
    candidate: VerifiedKnowledgeCandidate
    candidate_id: str
    candidate_fingerprint: str
    candidate_identity_id: str
    candidate_version: int = Field(ge=1)
    integrated_lineage_fingerprint: str
    candidate_integrity_report: VerifiedKnowledgeIntegrityReport
    lineage_integrity_report: VerifiedKnowledgeIntegrityReport
    policy_status_integrity_report: VerifiedKnowledgeIntegrityReport
    memory_snapshot_id: str
    memory_snapshot_fingerprint: str
    binding_fingerprint: str
    read_only: Literal[True] = True
    redacted: Literal[True] = True
    runtime_effect: Literal[False] = False

    @model_validator(mode="after")
    def validate_binding(self) -> Self:
        if self.candidate_id != self.candidate.candidate_id:
            raise ValueError("candidate ID binding mismatch")
        if self.candidate_fingerprint != self.candidate.candidate_fingerprint:
            raise ValueError("candidate fingerprint binding mismatch")
        if self.candidate_identity_id != self.candidate.candidate_identity_id:
            raise ValueError("candidate identity binding mismatch")
        if self.candidate_version != self.candidate.candidate_version:
            raise ValueError("candidate version binding mismatch")
        if (
            self.integrated_lineage_fingerprint
            != self.candidate.integrated_lineage.lineage_fingerprint
        ):
            raise ValueError("lineage fingerprint binding mismatch")
        expected = _model_fingerprint(self, {"binding_fingerprint"})
        if self.binding_fingerprint != expected:
            raise ValueError("candidate binding fingerprint mismatch")
        return self


def bind_promotion_candidate(
    request: KnowledgePromotionRequest,
    candidate: VerifiedKnowledgeCandidate,
    *,
    candidate_integrity_report: VerifiedKnowledgeIntegrityReport,
    lineage_integrity_report: VerifiedKnowledgeIntegrityReport,
    policy_status_integrity_report: VerifiedKnowledgeIntegrityReport,
    memory_snapshot_id: str,
    memory_snapshot_fingerprint: str,
) -> PromotionCandidateBinding:
    if candidate.candidate_id not in request.candidate_ids:
        raise ValueError("candidate is not bound to request")
    index = request.candidate_ids.index(candidate.candidate_id)
    if request.candidate_fingerprints[index] != candidate.candidate_fingerprint:
        raise ValueError("candidate fingerprint is not bound to request")
    return _build(
        PromotionCandidateBinding,
        {
            "binding_id": f"binding-{candidate.candidate_id}",
            "promotion_request_id": request.promotion_request_id,
            "transaction_id": request.transaction_id,
            "candidate": candidate,
            "candidate_id": candidate.candidate_id,
            "candidate_fingerprint": candidate.candidate_fingerprint,
            "candidate_identity_id": candidate.candidate_identity_id,
            "candidate_version": candidate.candidate_version,
            "integrated_lineage_fingerprint": candidate.integrated_lineage.lineage_fingerprint,
            "candidate_integrity_report": candidate_integrity_report,
            "lineage_integrity_report": lineage_integrity_report,
            "policy_status_integrity_report": policy_status_integrity_report,
            "memory_snapshot_id": memory_snapshot_id,
            "memory_snapshot_fingerprint": memory_snapshot_fingerprint,
        },
        "binding_fingerprint",
    )


class OperatorApprovalEvidence(StrictFrozenModel):
    schema_version: Literal["aion-glm-operator-approval-evidence/v1"] = (
        OPERATOR_APPROVAL_EVIDENCE_SCHEMA_VERSION
    )
    approval_evidence_id: str
    approval_request_id: str
    approval_decision_id: str
    approval_request_fingerprint: str
    approval_decision_fingerprint: str
    requester_identity_fingerprint: str
    approver_identity_fingerprint: str
    action_type: Literal["governed_learning_memory.promotion_plan"]
    resource_type: Literal["verified_knowledge_candidate"]
    resource_id: str
    decision: Literal["approve"]
    status: ApprovalEvidenceStatus
    approval_scope: Literal["governed-learning-memory:promotion-plan"]
    constraint_fingerprints: tuple[str, ...]
    bound_candidate_ids: tuple[str, ...]
    bound_candidate_fingerprints: tuple[str, ...]
    promotion_request_fingerprint: str
    transaction_id: str
    requested_at: datetime
    decided_at: datetime
    expires_at: datetime
    revoked_at: datetime | None = None
    evidence_origin: Literal["operator_supplied_existing_approval"] = (
        "operator_supplied_existing_approval"
    )
    approval_creation_performed_by_aion222: Literal[False] = False
    approval_decision_performed_by_aion222: Literal[False] = False
    read_only: Literal[True] = True
    redacted: Literal[True] = True
    runtime_effect: Literal[False] = False
    evidence_fingerprint: str

    @model_validator(mode="after")
    def validate_evidence(self) -> Self:
        if self.revoked_at is not None:
            raise ValueError("revoked approval evidence is rejected")
        if self.expires_at <= self.decided_at:
            raise ValueError("approval evidence expires before decision")
        if self.approver_identity_fingerprint == self.requester_identity_fingerprint:
            raise ValueError("requester and approver must differ")
        if not self.bound_candidate_ids:
            raise ValueError("approval evidence requires candidate binding")
        if len(self.bound_candidate_ids) != len(self.bound_candidate_fingerprints):
            raise ValueError("approval candidate binding mismatch")
        expected = _model_fingerprint(self, {"evidence_fingerprint"})
        if self.evidence_fingerprint != expected:
            raise ValueError("approval evidence fingerprint mismatch")
        return self


def _approval_fingerprint(payload: Mapping[str, Any]) -> str:
    return governed_learning_memory_fingerprint(payload)


def project_existing_approval_evidence(
    approval_request: ApprovalRequest,
    approval_decision: ApprovalDecision,
    *,
    approval_evidence_id: str,
    transaction_id: str,
    promotion_request_fingerprint: str,
    candidate_ids: tuple[str, ...],
    candidate_fingerprints: tuple[str, ...],
    observed_at: datetime,
    revoked_at: datetime | None = None,
) -> OperatorApprovalEvidence:
    if approval_request.approval_request_id != approval_decision.approval_request_id:
        raise ValueError("approval request and decision ID mismatch")
    if approval_request.status == "expired":
        raise ValueError("expired approval is rejected")
    if approval_request.status == "cancelled":
        raise ValueError("cancelled approval is rejected")
    if approval_request.status == "denied" or approval_decision.decision == "deny":
        raise ValueError("denied approval is rejected")
    if approval_request.status != "approved" or approval_decision.decision != "approve":
        raise ValueError("approval evidence requires an approved decision")
    if approval_request.action_type != "governed_learning_memory.promotion_plan":
        raise ValueError("approval action scope mismatch")
    if approval_request.resource_type != "verified_knowledge_candidate":
        raise ValueError("approval resource type mismatch")
    if "governed-learning-memory:promotion-plan" not in approval_request.approval_scope:
        raise ValueError("approval scope mismatch")
    if approval_request.resource_id not in (*candidate_ids, transaction_id):
        raise ValueError("approval resource binding mismatch")
    requested_at = ensure_utc(approval_request.created_at or observed_at)
    decided_at = ensure_utc(approval_decision.created_at or observed_at)
    expires_at = ensure_utc(approval_request.expires_at or (requested_at + timedelta(hours=1)))
    observed_at = ensure_utc(observed_at)
    if expires_at <= observed_at:
        raise ValueError("approval evidence expired")
    if revoked_at is not None:
        raise ValueError("approval evidence revoked")
    payload_fingerprints = tuple(
        approval_request.payload.get("candidate_fingerprints", tuple(candidate_fingerprints))
    )
    if payload_fingerprints != candidate_fingerprints:
        raise ValueError("approval candidate fingerprint mismatch")
    payload_transaction = approval_request.payload.get("transaction_id", transaction_id)
    if payload_transaction != transaction_id:
        raise ValueError("approval transaction binding mismatch")
    payload_request_fp = approval_request.payload.get(
        "promotion_request_fingerprint",
        promotion_request_fingerprint,
    )
    if payload_request_fp != promotion_request_fingerprint:
        raise ValueError("approval request fingerprint mismatch")
    requester = approval_request.requested_by or approval_request.actor_id or "requester"
    approver = approval_decision.decided_by or approval_request.assigned_to or "approver"
    request_fp = _approval_fingerprint(
        {
            "approval_request_id": approval_request.approval_request_id,
            "action_type": approval_request.action_type,
            "resource_type": approval_request.resource_type,
            "resource_id": approval_request.resource_id,
            "approval_scope": sorted(approval_request.approval_scope),
            "status": approval_request.status,
        }
    )
    decision_fp = _approval_fingerprint(
        {
            "approval_decision_id": approval_decision.approval_decision_id,
            "approval_request_id": approval_decision.approval_request_id,
            "decision": approval_decision.decision,
            "created_at": decided_at,
        }
    )
    return _build(
        OperatorApprovalEvidence,
        {
            "approval_evidence_id": approval_evidence_id,
            "approval_request_id": approval_request.approval_request_id,
            "approval_decision_id": approval_decision.approval_decision_id,
            "approval_request_fingerprint": request_fp,
            "approval_decision_fingerprint": decision_fp,
            "requester_identity_fingerprint": governed_learning_memory_fingerprint(requester),
            "approver_identity_fingerprint": governed_learning_memory_fingerprint(approver),
            "action_type": "governed_learning_memory.promotion_plan",
            "resource_type": "verified_knowledge_candidate",
            "resource_id": approval_request.resource_id or transaction_id,
            "decision": "approve",
            "status": ApprovalEvidenceStatus.VALID,
            "approval_scope": "governed-learning-memory:promotion-plan",
            "constraint_fingerprints": tuple(
                sorted(
                    governed_learning_memory_fingerprint(item)
                    for item in approval_request.constraints
                )
            ),
            "bound_candidate_ids": tuple(sorted(candidate_ids)),
            "bound_candidate_fingerprints": tuple(sorted(candidate_fingerprints)),
            "promotion_request_fingerprint": promotion_request_fingerprint,
            "transaction_id": transaction_id,
            "requested_at": requested_at,
            "decided_at": decided_at,
            "expires_at": expires_at,
            "revoked_at": None,
        },
        "evidence_fingerprint",
    )


class ApprovalEvidenceBundle(StrictFrozenModel):
    schema_version: Literal["aion-glm-approval-evidence-bundle/v1"] = (
        APPROVAL_EVIDENCE_BUNDLE_SCHEMA_VERSION
    )
    bundle_id: str
    evidence_records: tuple[OperatorApprovalEvidence, ...]
    independent_approver_fingerprints: tuple[str, ...]
    independent_approver_count: int = Field(ge=0)
    required_approver_count: int = Field(ge=1, le=2)
    separation_of_duties_passed: bool
    approval_status: ApprovalEvidenceStatus
    reason_codes: tuple[str, ...]
    bundle_fingerprint: str
    read_only: Literal[True] = True
    redacted: Literal[True] = True
    runtime_effect: Literal[False] = False

    @model_validator(mode="after")
    def validate_bundle(self) -> Self:
        if len(self.evidence_records) > MAXIMUM_APPROVAL_EVIDENCE_RECORDS_PER_TRANSACTION:
            raise ValueError("approval evidence record limit exceeded")
        if self.independent_approver_count != len(self.independent_approver_fingerprints):
            raise ValueError("approver count mismatch")
        if self.separation_of_duties_passed != (
            self.independent_approver_count >= self.required_approver_count
        ):
            raise ValueError("separation-of-duties result mismatch")
        expected = _model_fingerprint(self, {"bundle_fingerprint"})
        if self.bundle_fingerprint != expected:
            raise ValueError("approval bundle fingerprint mismatch")
        return self


def build_approval_evidence_bundle(
    *,
    bundle_id: str,
    evidence_records: tuple[OperatorApprovalEvidence, ...],
    risk_class: PromotionRiskClass,
    requested_targets: tuple[MemoryProjectionTarget, ...],
) -> ApprovalEvidenceBundle:
    required = 2 if risk_class in {PromotionRiskClass.HIGH, PromotionRiskClass.CRITICAL} else 1
    if MemoryProjectionTarget.BELIEF_CANDIDATE in requested_targets:
        required = 2
    approvers = tuple(sorted({record.approver_identity_fingerprint for record in evidence_records}))
    passed = len(approvers) >= required
    status = (
        ApprovalEvidenceStatus.VALID if passed else ApprovalEvidenceStatus.INSUFFICIENT_APPROVALS
    )
    reasons: tuple[str, ...] = (
        "approval_separation_of_duties_passed",
        "approval_evidence_valid",
    )
    if not passed:
        reasons = (
            "approval_insufficient_independent_approvers",
            "approval_separation_of_duties_failed",
        )
    return _build(
        ApprovalEvidenceBundle,
        {
            "bundle_id": bundle_id,
            "evidence_records": evidence_records,
            "independent_approver_fingerprints": approvers,
            "independent_approver_count": len(approvers),
            "required_approver_count": required,
            "separation_of_duties_passed": passed,
            "approval_status": status,
            "reason_codes": reasons,
        },
        "bundle_fingerprint",
    )


class PromotionEligibilitySnapshot(StrictFrozenModel):
    schema_version: Literal["aion-glm-promotion-eligibility-snapshot/v1"] = (
        PROMOTION_ELIGIBILITY_SNAPSHOT_SCHEMA_VERSION
    )
    snapshot_id: str
    candidate_id: str
    candidate_fingerprint: str
    candidate_identity_id: str
    candidate_kind: VerifiedKnowledgeCandidateKind
    candidate_version: int = Field(ge=1)
    eligibility_status: VerifiedKnowledgeEligibilityStatus
    lifecycle_status: VerifiedKnowledgeLifecycleStatus
    candidate_confidence_cap: Decimal
    lineage_fingerprint: str
    candidate_integrity_fingerprint: str
    lineage_integrity_fingerprint: str
    policy_integrity_fingerprint: str
    freshness_status: FreshnessStatus
    scope_applicability_status: ScopeApplicability
    contradiction_status: ContradictionStatus
    unresolved_dissent_count: int = Field(ge=0)
    source_independence_count: int = Field(ge=0)
    citation_coverage: Decimal
    provenance_completeness: Decimal
    evidence_coverage: Decimal
    tool_session_count: int = Field(ge=0)
    attestation_count: int = Field(ge=0)
    revalidated_at: datetime
    valid_until: datetime
    disposition: PromotionCandidateDisposition
    reason_codes: tuple[str, ...]
    operator_review_required: Literal[True] = True
    automatic_promotion: Literal[False] = False
    persistent_write_applied: Literal[False] = False
    cognitive_memory_written: Literal[False] = False
    belief_mutated: Literal[False] = False
    runtime_effect: Literal[False] = False
    snapshot_fingerprint: str

    @model_validator(mode="after")
    def validate_snapshot(self) -> Self:
        if self.valid_until <= self.revalidated_at:
            raise ValueError("eligibility snapshot validity window invalid")
        expected = _model_fingerprint(self, {"snapshot_fingerprint"})
        if self.snapshot_fingerprint != expected:
            raise ValueError("eligibility snapshot fingerprint mismatch")
        return self


def revalidate_promotion_candidate(
    binding: PromotionCandidateBinding,
    *,
    revalidated_at: datetime,
    valid_until: datetime,
) -> PromotionEligibilitySnapshot:
    candidate = binding.candidate
    reports = (
        binding.candidate_integrity_report,
        binding.lineage_integrity_report,
        binding.policy_status_integrity_report,
    )
    integrity_passed = all(
        report.status is VerifiedKnowledgeIntegrityStatus.PASSED for report in reports
    )
    eligible = (
        integrity_passed
        and candidate.eligibility_decision.status
        is VerifiedKnowledgeEligibilityStatus.ELIGIBLE_FOR_OPERATOR_REVIEW
        and candidate.lifecycle_status is VerifiedKnowledgeLifecycleStatus.OPERATOR_REVIEW_PENDING
        and candidate.operator_review_required
        and not candidate.automatic_promotion
        and not candidate.verified_knowledge_created
        and not candidate.persistent_write_applied
        and not candidate.cognitive_memory_written
        and not candidate.belief_mutated
        and not candidate.runtime_effect
        and (candidate.expires_at is None or candidate.expires_at > revalidated_at)
        and (
            candidate.revalidation_due_at is None or candidate.revalidation_due_at >= revalidated_at
        )
        and candidate.freshness_status is FreshnessStatus.CURRENT
        and candidate.scope_applicability_status is ScopeApplicability.APPLICABLE
        and candidate.contradiction_status is ContradictionStatus.NONE_DETECTED
        and candidate.citation_coverage == ONE
        and candidate.provenance_completeness == ONE
        and candidate.evidence_coverage == ONE
        and candidate.candidate_confidence_cap <= candidate.assessment_confidence
    )
    disposition = (
        PromotionCandidateDisposition.ELIGIBLE_FOR_DRY_RUN
        if eligible
        else PromotionCandidateDisposition.REVALIDATION_REQUIRED
    )
    reasons: tuple[str, ...] = (
        "promotion_candidate_confidence_non_amplification_passed",
    )
    if eligible:
        reasons = ("promotion_candidate_binding_valid", *reasons)
    else:
        reasons = ("promotion_candidate_revalidation_required", *reasons)
    return _build(
        PromotionEligibilitySnapshot,
        {
            "snapshot_id": f"eligibility-{candidate.candidate_id}",
            "candidate_id": candidate.candidate_id,
            "candidate_fingerprint": candidate.candidate_fingerprint,
            "candidate_identity_id": candidate.candidate_identity_id,
            "candidate_kind": candidate.candidate_kind,
            "candidate_version": candidate.candidate_version,
            "eligibility_status": candidate.eligibility_decision.status,
            "lifecycle_status": candidate.lifecycle_status,
            "candidate_confidence_cap": candidate.candidate_confidence_cap,
            "lineage_fingerprint": candidate.integrated_lineage.lineage_fingerprint,
            "candidate_integrity_fingerprint": (
                binding.candidate_integrity_report.report_fingerprint
            ),
            "lineage_integrity_fingerprint": binding.lineage_integrity_report.report_fingerprint,
            "policy_integrity_fingerprint": (
                binding.policy_status_integrity_report.report_fingerprint
            ),
            "freshness_status": candidate.freshness_status,
            "scope_applicability_status": candidate.scope_applicability_status,
            "contradiction_status": candidate.contradiction_status,
            "unresolved_dissent_count": len(candidate.unresolved_dissent_ids),
            "source_independence_count": len(
                candidate.integrated_lineage.source_independence_group_ids
            ),
            "citation_coverage": candidate.citation_coverage,
            "provenance_completeness": candidate.provenance_completeness,
            "evidence_coverage": candidate.evidence_coverage,
            "tool_session_count": len(candidate.tool_verification_session_ids),
            "attestation_count": len(candidate.attestation_chain_head_fingerprints),
            "revalidated_at": revalidated_at,
            "valid_until": valid_until,
            "disposition": disposition,
            "reason_codes": reasons,
        },
        "snapshot_fingerprint",
    )


class ExistingKnowledgeVersionReference(StrictFrozenModel):
    schema_version: Literal["aion-glm-existing-knowledge-version-reference/v1"] = (
        EXISTING_KNOWLEDGE_VERSION_REFERENCE_SCHEMA_VERSION
    )
    reference_id: str
    knowledge_identity_id: str
    version_number: int = Field(ge=1, le=MAXIMUM_VERSIONS_PER_KNOWLEDGE_IDENTITY)
    candidate_kind: VerifiedKnowledgeCandidateKind
    claim_identity_fingerprint: str
    target_valid_time_fingerprint: str
    jurisdiction_scope_fingerprint: str
    version_scope_fingerprint: str
    candidate_fingerprint: str
    lineage_fingerprint: str
    approval_bundle_fingerprint: str
    knowledge_version_fingerprint: str
    lifecycle_status: str
    effective_from: datetime
    effective_to: datetime | None = None
    supersedes_version_id: str | None = None
    retracted: bool = False
    expired: bool = False
    synthetic_or_operator_supplied: Literal[True] = True
    persistent_record_created_by_aion222: Literal[False] = False
    read_only: Literal[True] = True
    redacted: Literal[True] = True
    runtime_effect: Literal[False] = False


class KnowledgeIdentityPlan(StrictFrozenModel):
    schema_version: Literal["aion-glm-knowledge-identity-plan/v1"] = (
        KNOWLEDGE_IDENTITY_PLAN_SCHEMA_VERSION
    )
    identity_plan_id: str
    knowledge_identity_id: str
    claim_id: str
    claim_identity_fingerprint: str
    target_valid_time_fingerprint: str
    jurisdiction_scope_fingerprint: str
    version_scope_fingerprint: str
    candidate_kind: VerifiedKnowledgeCandidateKind
    candidate_id: str
    candidate_fingerprint: str
    lineage_fingerprint: str
    approval_bundle_fingerprint: str
    disposition: KnowledgeIdentityDisposition
    identity_fingerprint: str
    persistent_identity_created: Literal[False] = False
    runtime_effect: Literal[False] = False

    @model_validator(mode="after")
    def validate_identity(self) -> Self:
        expected_id = derive_knowledge_identity_id(
            self.claim_identity_fingerprint,
            self.target_valid_time_fingerprint,
            self.jurisdiction_scope_fingerprint,
            self.version_scope_fingerprint,
        )
        if self.knowledge_identity_id != expected_id:
            raise ValueError("knowledge identity derivation mismatch")
        expected = _model_fingerprint(self, {"identity_fingerprint"})
        if self.identity_fingerprint != expected:
            raise ValueError("knowledge identity fingerprint mismatch")
        return self


def derive_knowledge_identity_id(
    claim_identity_fingerprint: str,
    target_valid_time_fingerprint: str,
    jurisdiction_scope_fingerprint: str,
    version_scope_fingerprint: str,
) -> str:
    digest = governed_learning_memory_fingerprint(
        {
            "claim_identity_fingerprint": claim_identity_fingerprint,
            "target_valid_time_fingerprint": target_valid_time_fingerprint,
            "jurisdiction_scope_fingerprint": jurisdiction_scope_fingerprint,
            "version_scope_fingerprint": version_scope_fingerprint,
        }
    )
    return f"knowledge-{digest[:32]}"


def derive_knowledge_identity_plan(
    snapshot: PromotionEligibilitySnapshot,
    *,
    lineage: IntegratedKnowledgeLineage,
    approval_bundle_fingerprint: str,
    existing_references: tuple[ExistingKnowledgeVersionReference, ...] = (),
) -> KnowledgeIdentityPlan:
    knowledge_identity_id = derive_knowledge_identity_id(
        lineage.claim_identity_fingerprint,
        lineage.target_valid_time_fingerprint,
        lineage.jurisdiction_scope_fingerprint,
        lineage.version_scope_fingerprint,
    )
    disposition = KnowledgeIdentityDisposition.NEW_IDENTITY
    if any(ref.knowledge_identity_id == knowledge_identity_id for ref in existing_references):
        disposition = KnowledgeIdentityDisposition.EXISTING_IDENTITY
    return _build(
        KnowledgeIdentityPlan,
        {
            "identity_plan_id": f"identity-{snapshot.candidate_id}",
            "knowledge_identity_id": knowledge_identity_id,
            "claim_id": lineage.claim_id,
            "claim_identity_fingerprint": lineage.claim_identity_fingerprint,
            "target_valid_time_fingerprint": lineage.target_valid_time_fingerprint,
            "jurisdiction_scope_fingerprint": lineage.jurisdiction_scope_fingerprint,
            "version_scope_fingerprint": lineage.version_scope_fingerprint,
            "candidate_kind": snapshot.candidate_kind,
            "candidate_id": snapshot.candidate_id,
            "candidate_fingerprint": snapshot.candidate_fingerprint,
            "lineage_fingerprint": lineage.lineage_fingerprint,
            "approval_bundle_fingerprint": approval_bundle_fingerprint,
            "disposition": disposition,
        },
        "identity_fingerprint",
    )


class KnowledgeConflictFinding(StrictFrozenModel):
    finding_id: str
    conflict_kind: KnowledgeConflictKind
    knowledge_identity_id: str
    candidate_ids: tuple[str, ...]
    candidate_fingerprints: tuple[str, ...]
    reason_codes: tuple[str, ...]
    material_hold: bool
    finding_fingerprint: str
    runtime_effect: Literal[False] = False

    @model_validator(mode="after")
    def validate_finding(self) -> Self:
        expected = _model_fingerprint(self, {"finding_fingerprint"})
        if self.finding_fingerprint != expected:
            raise ValueError("conflict finding fingerprint mismatch")
        return self


class KnowledgeConflictReport(StrictFrozenModel):
    schema_version: Literal["aion-glm-knowledge-conflict-report/v1"] = (
        KNOWLEDGE_CONFLICT_REPORT_SCHEMA_VERSION
    )
    report_id: str
    findings: tuple[KnowledgeConflictFinding, ...]
    duplicate_count: int = Field(ge=0)
    conflict_count: int = Field(ge=0)
    material_hold: bool
    reason_codes: tuple[str, ...]
    report_fingerprint: str
    runtime_effect: Literal[False] = False

    @model_validator(mode="after")
    def validate_report(self) -> Self:
        duplicates = sum(
            1
            for finding in self.findings
            if finding.conflict_kind
            in {KnowledgeConflictKind.EXACT_DUPLICATE, KnowledgeConflictKind.LINEAGE_DUPLICATE}
        )
        conflicts = len(self.findings) - duplicates
        if self.duplicate_count != duplicates or self.conflict_count != conflicts:
            raise ValueError("conflict report counts mismatch")
        if self.material_hold != any(finding.material_hold for finding in self.findings):
            raise ValueError("conflict material hold mismatch")
        expected = _model_fingerprint(self, {"report_fingerprint"})
        if self.report_fingerprint != expected:
            raise ValueError("conflict report fingerprint mismatch")
        return self


def _conflict_finding(
    *,
    finding_id: str,
    conflict_kind: KnowledgeConflictKind,
    knowledge_identity_id: str,
    plans: tuple[KnowledgeIdentityPlan, ...],
    reason_codes: tuple[str, ...],
    material_hold: bool,
) -> KnowledgeConflictFinding:
    return _build(
        KnowledgeConflictFinding,
        {
            "finding_id": finding_id,
            "conflict_kind": conflict_kind,
            "knowledge_identity_id": knowledge_identity_id,
            "candidate_ids": tuple(sorted(plan.candidate_id for plan in plans)),
            "candidate_fingerprints": tuple(sorted(plan.candidate_fingerprint for plan in plans)),
            "reason_codes": reason_codes,
            "material_hold": material_hold,
        },
        "finding_fingerprint",
    )


def detect_knowledge_duplicates_and_conflicts(
    identity_plans: tuple[KnowledgeIdentityPlan, ...],
    *,
    existing_references: tuple[ExistingKnowledgeVersionReference, ...] = (),
    unresolved_material_dissent: bool = False,
) -> KnowledgeConflictReport:
    findings: list[KnowledgeConflictFinding] = []
    by_identity: dict[str, list[KnowledgeIdentityPlan]] = {}
    for plan in identity_plans:
        by_identity.setdefault(plan.knowledge_identity_id, []).append(plan)
        for reference in existing_references:
            exact_duplicate = (
                reference.knowledge_identity_id == plan.knowledge_identity_id
                and reference.candidate_fingerprint == plan.candidate_fingerprint
                and reference.lineage_fingerprint == plan.lineage_fingerprint
                and reference.approval_bundle_fingerprint == plan.approval_bundle_fingerprint
            )
            if exact_duplicate:
                findings.append(
                    _conflict_finding(
                        finding_id=f"duplicate-{plan.candidate_id}",
                        conflict_kind=KnowledgeConflictKind.EXACT_DUPLICATE,
                        knowledge_identity_id=plan.knowledge_identity_id,
                        plans=(plan,),
                        reason_codes=("knowledge_exact_duplicate",),
                        material_hold=False,
                    )
                )
            elif (
                reference.knowledge_identity_id == plan.knowledge_identity_id
                and reference.retracted
            ):
                findings.append(
                    _conflict_finding(
                        finding_id=f"retraction-{plan.candidate_id}",
                        conflict_kind=KnowledgeConflictKind.RETRACTION_CONFLICT,
                        knowledge_identity_id=plan.knowledge_identity_id,
                        plans=(plan,),
                        reason_codes=("knowledge_retraction_conflict",),
                        material_hold=True,
                    )
                )
            elif reference.knowledge_identity_id == plan.knowledge_identity_id:
                findings.append(
                    _conflict_finding(
                        finding_id=f"direct-conflict-{plan.candidate_id}",
                        conflict_kind=KnowledgeConflictKind.DIRECT_POSTURE_CONFLICT,
                        knowledge_identity_id=plan.knowledge_identity_id,
                        plans=(plan,),
                        reason_codes=("knowledge_direct_conflict",),
                        material_hold=True,
                    )
                )
    for identity_id, plans in by_identity.items():
        postures = {plan.candidate_kind for plan in plans}
        if len(postures) > 1:
            findings.append(
                _conflict_finding(
                    finding_id=f"direct-conflict-{identity_id}",
                    conflict_kind=KnowledgeConflictKind.DIRECT_POSTURE_CONFLICT,
                    knowledge_identity_id=identity_id,
                    plans=tuple(plans),
                    reason_codes=("knowledge_direct_conflict",),
                    material_hold=True,
                )
            )
    if unresolved_material_dissent:
        dissent_plans = tuple(identity_plans[:1])
        if dissent_plans:
            findings.append(
                _conflict_finding(
                    finding_id=f"dissent-{dissent_plans[0].candidate_id}",
                    conflict_kind=KnowledgeConflictKind.UNRESOLVED_DISSENT_CONFLICT,
                    knowledge_identity_id=dissent_plans[0].knowledge_identity_id,
                    plans=dissent_plans,
                    reason_codes=("knowledge_dissent_conflict",),
                    material_hold=True,
                )
            )
    reasons: tuple[str, ...] = ("knowledge_identity_derived",)
    if any(f.conflict_kind is KnowledgeConflictKind.EXACT_DUPLICATE for f in findings):
        reasons = (*reasons, "knowledge_exact_duplicate")
    if any(f.material_hold for f in findings):
        reasons = (*reasons, "knowledge_direct_conflict")
    return _build(
        KnowledgeConflictReport,
        {
            "report_id": "knowledge-conflicts",
            "findings": tuple(sorted(findings, key=lambda item: item.finding_id)),
            "duplicate_count": sum(
                1
                for finding in findings
                if finding.conflict_kind
                in {KnowledgeConflictKind.EXACT_DUPLICATE, KnowledgeConflictKind.LINEAGE_DUPLICATE}
            ),
            "conflict_count": sum(
                1
                for finding in findings
                if finding.conflict_kind
                not in {
                    KnowledgeConflictKind.EXACT_DUPLICATE,
                    KnowledgeConflictKind.LINEAGE_DUPLICATE,
                }
            ),
            "material_hold": any(finding.material_hold for finding in findings),
            "reason_codes": tuple(dict.fromkeys(reasons)),
        },
        "report_fingerprint",
    )


class KnowledgeVersionPlan(StrictFrozenModel):
    schema_version: Literal["aion-glm-knowledge-version-plan/v1"] = (
        KNOWLEDGE_VERSION_PLAN_SCHEMA_VERSION
    )
    version_plan_id: str
    knowledge_identity_id: str
    request_kind: PromotionRequestKind
    disposition: KnowledgeVersionDisposition
    planned_version_number: int = Field(ge=1, le=MAXIMUM_VERSIONS_PER_KNOWLEDGE_IDENTITY)
    previous_version_id: str | None = None
    previous_version_fingerprint: str | None = None
    candidate_id: str
    candidate_fingerprint: str
    candidate_kind: VerifiedKnowledgeCandidateKind
    lineage_fingerprint: str
    approval_bundle_fingerprint: str
    candidate_confidence_cap: Decimal
    effective_from: datetime
    effective_to: datetime | None = None
    supersedes_version_id: str | None = None
    retracts_version_id: str | None = None
    expires_version_id: str | None = None
    append_only: Literal[True] = True
    historical_versions_preserved: Literal[True] = True
    persistent_version_created: Literal[False] = False
    reason_codes: tuple[str, ...]
    runtime_effect: Literal[False] = False
    version_plan_fingerprint: str

    @model_validator(mode="after")
    def validate_version_plan(self) -> Self:
        if self.disposition is KnowledgeVersionDisposition.NO_OP_DUPLICATE:
            if "knowledge_exact_duplicate" not in self.reason_codes:
                raise ValueError("duplicate version plan requires duplicate reason")
        expected = _model_fingerprint(self, {"version_plan_fingerprint"})
        if self.version_plan_fingerprint != expected:
            raise ValueError("version plan fingerprint mismatch")
        return self


def plan_knowledge_version(
    *,
    identity_plan: KnowledgeIdentityPlan,
    snapshot: PromotionEligibilitySnapshot,
    request_kind: PromotionRequestKind,
    conflict_report: KnowledgeConflictReport,
    existing_references: tuple[ExistingKnowledgeVersionReference, ...] = (),
    effective_from: datetime,
    effective_to: datetime | None = None,
) -> KnowledgeVersionPlan:
    refs = sorted(
        (
            ref
            for ref in existing_references
            if ref.knowledge_identity_id == identity_plan.knowledge_identity_id
        ),
        key=lambda item: item.version_number,
    )
    duplicate = any(
        finding.conflict_kind is KnowledgeConflictKind.EXACT_DUPLICATE
        and identity_plan.candidate_fingerprint in finding.candidate_fingerprints
        for finding in conflict_report.findings
    )
    material_hold = conflict_report.material_hold
    previous = refs[-1] if refs else None
    disposition = KnowledgeVersionDisposition.INITIAL_VERSION_PLANNED
    reason = "knowledge_initial_version_planned"
    version_number = 1
    if duplicate:
        disposition = KnowledgeVersionDisposition.NO_OP_DUPLICATE
        reason = "knowledge_exact_duplicate"
        version_number = previous.version_number if previous else 1
    elif material_hold:
        disposition = KnowledgeVersionDisposition.BLOCKED
        reason = "knowledge_direct_conflict"
        version_number = previous.version_number + 1 if previous else 1
    elif request_kind is PromotionRequestKind.REVALIDATION_ONLY:
        disposition = KnowledgeVersionDisposition.REVALIDATION_ONLY
        reason = "knowledge_history_preserved"
        version_number = previous.version_number if previous else 1
    elif request_kind is PromotionRequestKind.SUPERSESSION:
        disposition = KnowledgeVersionDisposition.SUPERSESSION_PLANNED
        reason = "knowledge_supersession_planned"
        version_number = previous.version_number + 1 if previous else 1
    elif request_kind is PromotionRequestKind.RETRACTION:
        disposition = KnowledgeVersionDisposition.RETRACTION_PLANNED
        reason = "knowledge_retraction_planned"
        version_number = previous.version_number + 1 if previous else 1
    elif request_kind is PromotionRequestKind.EXPIRY:
        disposition = KnowledgeVersionDisposition.EXPIRY_PLANNED
        reason = "knowledge_expiry_planned"
        version_number = previous.version_number + 1 if previous else 1
    elif previous is not None:
        disposition = KnowledgeVersionDisposition.NEW_VERSION_PLANNED
        reason = "knowledge_new_version_planned"
        version_number = previous.version_number + 1
    if version_number > MAXIMUM_VERSIONS_PER_KNOWLEDGE_IDENTITY:
        raise ValueError("knowledge version limit exceeded")
    return _build(
        KnowledgeVersionPlan,
        {
            "version_plan_id": f"version-plan-{identity_plan.candidate_id}",
            "knowledge_identity_id": identity_plan.knowledge_identity_id,
            "request_kind": request_kind,
            "disposition": disposition,
            "planned_version_number": version_number,
            "previous_version_id": previous.reference_id if previous else None,
            "previous_version_fingerprint": previous.knowledge_version_fingerprint
            if previous
            else None,
            "candidate_id": identity_plan.candidate_id,
            "candidate_fingerprint": identity_plan.candidate_fingerprint,
            "candidate_kind": identity_plan.candidate_kind,
            "lineage_fingerprint": identity_plan.lineage_fingerprint,
            "approval_bundle_fingerprint": identity_plan.approval_bundle_fingerprint,
            "candidate_confidence_cap": snapshot.candidate_confidence_cap,
            "effective_from": effective_from,
            "effective_to": effective_to,
            "supersedes_version_id": previous.reference_id
            if request_kind is PromotionRequestKind.SUPERSESSION and previous
            else None,
            "retracts_version_id": previous.reference_id
            if request_kind is PromotionRequestKind.RETRACTION and previous
            else None,
            "expires_version_id": previous.reference_id
            if request_kind is PromotionRequestKind.EXPIRY and previous
            else None,
            "reason_codes": (reason, "knowledge_history_preserved"),
        },
        "version_plan_fingerprint",
    )


class MemoryProjectionRecordPlan(StrictFrozenModel):
    schema_version: Literal["aion-glm-memory-projection-record-plan/v1"] = (
        MEMORY_PROJECTION_RECORD_PLAN_SCHEMA_VERSION
    )
    projection_record_id: str
    transaction_id: str
    knowledge_identity_id: str
    knowledge_version_plan_id: str
    target: MemoryProjectionTarget
    planned_record_id: str
    candidate_id: str
    candidate_fingerprint: str
    lineage_fingerprint: str
    approval_bundle_fingerprint: str
    content_reference_fingerprint: str
    summary_fingerprint: str
    owner_scope_fingerprints: tuple[str, ...]
    confidence_cap: Decimal
    sensitivity: BeliefSensitivity
    source_reference_ids: tuple[str, ...]
    evidence_reference_fingerprints: tuple[str, ...]
    valid_from: datetime
    valid_to: datetime | None = None
    projection_status: MemoryProjectionStatus
    reason_codes: tuple[str, ...]
    memory_record_created: Literal[False] = False
    cognitive_memory_written: Literal[False] = False
    belief_created: Literal[False] = False
    belief_mutated: Literal[False] = False
    persistent_write_applied: Literal[False] = False
    runtime_effect: Literal[False] = False
    projection_fingerprint: str

    @model_validator(mode="after")
    def validate_projection(self) -> Self:
        expected = _model_fingerprint(self, {"projection_fingerprint"})
        if self.projection_fingerprint != expected:
            raise ValueError("projection fingerprint mismatch")
        return self


class MemoryProjectionPlan(StrictFrozenModel):
    schema_version: Literal["aion-glm-memory-projection-plan/v1"] = (
        MEMORY_PROJECTION_PLAN_SCHEMA_VERSION
    )
    projection_plan_id: str
    transaction_id: str
    records: tuple[MemoryProjectionRecordPlan, ...]
    record_count: int = Field(ge=0, le=MAXIMUM_PROJECTION_RECORDS_PER_TRANSACTION)
    requested_targets: tuple[MemoryProjectionTarget, ...]
    planned_targets: tuple[MemoryProjectionTarget, ...]
    blocked_targets: tuple[MemoryProjectionTarget, ...]
    operator_review_required: Literal[True] = True
    persistent_write_authorized: Literal[False] = False
    cognitive_memory_write_authorized: Literal[False] = False
    belief_mutation_authorized: Literal[False] = False
    plan_fingerprint: str
    runtime_effect: Literal[False] = False

    @model_validator(mode="after")
    def validate_plan(self) -> Self:
        if self.record_count != len(self.records):
            raise ValueError("projection record count mismatch")
        expected = _model_fingerprint(self, {"plan_fingerprint"})
        if self.plan_fingerprint != expected:
            raise ValueError("projection plan fingerprint mismatch")
        return self


def _projection_reason(target: MemoryProjectionTarget) -> str:
    return {
        MemoryProjectionTarget.SEMANTIC_MEMORY: "semantic_memory_projection_planned",
        MemoryProjectionTarget.EPISODIC_MEMORY: "episodic_memory_projection_planned",
        MemoryProjectionTarget.PROCEDURAL_MEMORY: "procedural_memory_projection_planned",
        MemoryProjectionTarget.BELIEF_CANDIDATE: "belief_candidate_projection_planned",
    }[target]


def plan_memory_projections(
    *,
    request: KnowledgePromotionRequest,
    version_plans: tuple[KnowledgeVersionPlan, ...],
    approval_bundle: ApprovalEvidenceBundle,
    source_reference_ids: tuple[str, ...],
    valid_from: datetime,
    valid_to: datetime | None = None,
) -> MemoryProjectionPlan:
    records: list[MemoryProjectionRecordPlan] = []
    blocked: set[MemoryProjectionTarget] = set()
    for version_plan in version_plans:
        if version_plan.disposition in {
            KnowledgeVersionDisposition.BLOCKED,
            KnowledgeVersionDisposition.NO_OP_DUPLICATE,
        }:
            continue
        for target in request.requested_projection_targets:
            status = MemoryProjectionStatus.PLANNED
            reasons: tuple[str, ...] = (
                _projection_reason(target),
                "memory_projection_write_disabled",
            )
            if target is MemoryProjectionTarget.BELIEF_CANDIDATE:
                reasons = (*reasons, "belief_projection_is_candidate_only")
                if approval_bundle.required_approver_count < 2:
                    status = MemoryProjectionStatus.BLOCKED
                    blocked.add(target)
                    reasons = ("memory_projection_blocked", "belief_projection_is_candidate_only")
            projection_seed = {
                "target": target,
                "transaction_id": request.transaction_id,
                "version_plan": version_plan.version_plan_fingerprint,
            }
            record_id = f"projection-{target.value}-{version_plan.candidate_id}"
            records.append(
                _build(
                    MemoryProjectionRecordPlan,
                    {
                        "projection_record_id": record_id,
                        "transaction_id": request.transaction_id,
                        "knowledge_identity_id": version_plan.knowledge_identity_id,
                        "knowledge_version_plan_id": version_plan.version_plan_id,
                        "target": target,
                        "planned_record_id": f"planned-{target.value}-{version_plan.candidate_id}",
                        "candidate_id": version_plan.candidate_id,
                        "candidate_fingerprint": version_plan.candidate_fingerprint,
                        "lineage_fingerprint": version_plan.lineage_fingerprint,
                        "approval_bundle_fingerprint": version_plan.approval_bundle_fingerprint,
                        "content_reference_fingerprint": governed_learning_memory_fingerprint(
                            projection_seed
                        ),
                        "summary_fingerprint": governed_learning_memory_fingerprint(
                            {"summary": projection_seed}
                        ),
                        "owner_scope_fingerprints": request.owner_scope_fingerprints,
                        "confidence_cap": version_plan.candidate_confidence_cap,
                        "sensitivity": "internal",
                        "source_reference_ids": source_reference_ids,
                        "evidence_reference_fingerprints": (
                            version_plan.candidate_fingerprint,
                            version_plan.lineage_fingerprint,
                            version_plan.approval_bundle_fingerprint,
                        ),
                        "valid_from": valid_from,
                        "valid_to": valid_to,
                        "projection_status": status,
                        "reason_codes": reasons,
                    },
                    "projection_fingerprint",
                )
            )
    if len(records) > MAXIMUM_PROJECTION_RECORDS_PER_TRANSACTION:
        raise ValueError("projection record limit exceeded")
    planned = tuple(
        sorted(
            {
                record.target
                for record in records
                if record.projection_status is MemoryProjectionStatus.PLANNED
            }
        )
    )
    return _build(
        MemoryProjectionPlan,
        {
            "projection_plan_id": f"projection-plan-{request.transaction_id}",
            "transaction_id": request.transaction_id,
            "records": tuple(sorted(records, key=lambda item: item.projection_record_id)),
            "record_count": len(records),
            "requested_targets": tuple(sorted(request.requested_projection_targets)),
            "planned_targets": planned,
            "blocked_targets": tuple(sorted(blocked)),
        },
        "plan_fingerprint",
    )


class PromotionRollbackStep(StrictFrozenModel):
    step_id: str
    operation: Literal[
        "append_retraction_marker_plan",
        "append_superseding_version_plan",
        "restore_prior_active_version_pointer_plan",
        "invalidate_pending_projection_plan",
        "restore_prior_projection_pointer_plan",
        "revalidate_candidate_lineage",
        "invalidate_approval_binding",
        "create_operator_review_item",
        "preserve_audit_evidence",
    ]
    depends_on: tuple[str, ...] = ()
    reference_ids: tuple[str, ...] = ()
    reason_codes: tuple[str, ...]
    actual_execution: Literal[False] = False
    persistent_write_applied: Literal[False] = False
    memory_write_applied: Literal[False] = False
    belief_mutation_applied: Literal[False] = False
    step_fingerprint: str

    @model_validator(mode="after")
    def validate_step(self) -> Self:
        expected = _model_fingerprint(self, {"step_fingerprint"})
        if self.step_fingerprint != expected:
            raise ValueError("rollback step fingerprint mismatch")
        return self


class PromotionRollbackPlan(StrictFrozenModel):
    schema_version: Literal["aion-glm-promotion-rollback-plan/v1"] = (
        PROMOTION_ROLLBACK_PLAN_SCHEMA_VERSION
    )
    rollback_plan_id: str
    transaction_id: str
    steps: tuple[PromotionRollbackStep, ...]
    step_count: int = Field(ge=0, le=MAXIMUM_ROLLBACK_STEPS_PER_TRANSACTION)
    no_op_duplicate: bool = False
    reason_codes: tuple[str, ...]
    valid: bool
    plan_fingerprint: str
    runtime_effect: Literal[False] = False

    @model_validator(mode="after")
    def validate_plan(self) -> Self:
        ids = tuple(step.step_id for step in self.steps)
        if len(set(ids)) != len(ids):
            raise ValueError("rollback step IDs must be unique")
        if self.step_count != len(self.steps):
            raise ValueError("rollback step count mismatch")
        seen = set(ids)
        for step in self.steps:
            if not set(step.depends_on).issubset(seen):
                raise ValueError("rollback dependency does not resolve")
            if step.step_id in step.depends_on:
                raise ValueError("rollback dependency cycle detected")
        expected = _model_fingerprint(self, {"plan_fingerprint"})
        if self.plan_fingerprint != expected:
            raise ValueError("rollback plan fingerprint mismatch")
        return self


class PromotionCompensationStep(PromotionRollbackStep):
    pass


class PromotionCompensationPlan(StrictFrozenModel):
    schema_version: Literal["aion-glm-promotion-compensation-plan/v1"] = (
        PROMOTION_COMPENSATION_PLAN_SCHEMA_VERSION
    )
    compensation_plan_id: str
    transaction_id: str
    steps: tuple[PromotionCompensationStep, ...]
    step_count: int = Field(ge=0, le=MAXIMUM_COMPENSATION_STEPS_PER_TRANSACTION)
    no_op_duplicate: bool = False
    reason_codes: tuple[str, ...]
    valid: bool
    plan_fingerprint: str
    runtime_effect: Literal[False] = False

    @model_validator(mode="after")
    def validate_plan(self) -> Self:
        ids = tuple(step.step_id for step in self.steps)
        if len(set(ids)) != len(ids):
            raise ValueError("compensation step IDs must be unique")
        if self.step_count != len(self.steps):
            raise ValueError("compensation step count mismatch")
        expected = _model_fingerprint(self, {"plan_fingerprint"})
        if self.plan_fingerprint != expected:
            raise ValueError("compensation plan fingerprint mismatch")
        return self


def _build_step[T: PromotionRollbackStep | PromotionCompensationStep](
    model: type[T],
    *,
    step_id: str,
    operation: str,
    reference_ids: tuple[str, ...],
    reason_codes: tuple[str, ...],
) -> T:
    return _build(
        model,
        {
            "step_id": step_id,
            "operation": operation,
            "reference_ids": tuple(sorted(reference_ids)),
            "reason_codes": reason_codes,
        },
        "step_fingerprint",
    )


def build_rollback_plan(
    transaction_id: str,
    version_plans: tuple[KnowledgeVersionPlan, ...],
) -> PromotionRollbackPlan:
    no_op = all(
        plan.disposition is KnowledgeVersionDisposition.NO_OP_DUPLICATE for plan in version_plans
    )
    steps: tuple[PromotionRollbackStep, ...] = ()
    reasons: tuple[str, ...] = ("promotion_rollback_valid",)
    if no_op:
        reasons = ("promotion_rollback_valid", "promotion_idempotency_passed")
    else:
        steps = (
            _build_step(
                PromotionRollbackStep,
                step_id=f"rollback-{transaction_id}-001",
                operation="append_retraction_marker_plan",
                reference_ids=tuple(plan.version_plan_id for plan in version_plans),
                reason_codes=("promotion_rollback_valid",),
            ),
            _build_step(
                PromotionRollbackStep,
                step_id=f"rollback-{transaction_id}-002",
                operation="preserve_audit_evidence",
                reference_ids=tuple(plan.version_plan_id for plan in version_plans),
                reason_codes=("promotion_rollback_valid",),
            ),
        )
    return _build(
        PromotionRollbackPlan,
        {
            "rollback_plan_id": f"rollback-plan-{transaction_id}",
            "transaction_id": transaction_id,
            "steps": steps,
            "step_count": len(steps),
            "no_op_duplicate": no_op,
            "reason_codes": reasons,
            "valid": True,
        },
        "plan_fingerprint",
    )


def build_compensation_plan(
    transaction_id: str,
    version_plans: tuple[KnowledgeVersionPlan, ...],
) -> PromotionCompensationPlan:
    no_op = all(
        plan.disposition is KnowledgeVersionDisposition.NO_OP_DUPLICATE for plan in version_plans
    )
    steps: tuple[PromotionCompensationStep, ...] = ()
    if not no_op:
        steps = (
            _build_step(
                PromotionCompensationStep,
                step_id=f"compensation-{transaction_id}-001",
                operation="create_operator_review_item",
                reference_ids=tuple(plan.version_plan_id for plan in version_plans),
                reason_codes=("promotion_compensation_valid",),
            ),
        )
    return _build(
        PromotionCompensationPlan,
        {
            "compensation_plan_id": f"compensation-plan-{transaction_id}",
            "transaction_id": transaction_id,
            "steps": steps,
            "step_count": len(steps),
            "no_op_duplicate": no_op,
            "reason_codes": ("promotion_compensation_valid",),
            "valid": True,
        },
        "plan_fingerprint",
    )


class PromotionResourceBudget(StrictFrozenModel):
    maximum_promotion_requests_per_batch: Literal[100] = 100
    maximum_candidates_per_request: Literal[100] = 100
    maximum_lineage_references_per_candidate: Literal[500] = 500
    maximum_source_references_per_candidate: Literal[100] = 100
    maximum_claim_references_per_candidate: Literal[20] = 20
    maximum_assessment_references_per_candidate: Literal[20] = 20
    maximum_mesh_references_per_candidate: Literal[20] = 20
    maximum_tool_session_references_per_candidate: Literal[20] = 20
    maximum_approval_evidence_records_per_transaction: Literal[4] = 4
    maximum_projection_records_per_transaction: Literal[100] = 100
    maximum_versions_per_knowledge_identity: Literal[100] = 100
    maximum_rollback_steps_per_transaction: Literal[50] = 50
    maximum_compensation_steps_per_transaction: Literal[50] = 50
    maximum_operator_review_items: Literal[100] = 100
    maximum_in_memory_transactions: Literal[1000] = 1000
    maximum_query_results: Literal[1000] = 1000
    maximum_fixture_records: Literal[5000] = 5000
    maximum_fixture_bytes: Literal[4194304] = 4_194_304
    maximum_concurrency: Literal[4] = 4
    maximum_persistent_knowledge_writes: Literal[0] = 0
    maximum_persistent_verified_knowledge_writes: Literal[0] = 0
    maximum_cognitive_memory_writes: Literal[0] = 0
    maximum_semantic_memory_writes: Literal[0] = 0
    maximum_episodic_memory_writes: Literal[0] = 0
    maximum_procedural_memory_writes: Literal[0] = 0
    maximum_belief_creations: Literal[0] = 0
    maximum_belief_mutations: Literal[0] = 0
    maximum_automatic_knowledge_promotions: Literal[0] = 0
    maximum_automatic_candidate_approvals: Literal[0] = 0
    maximum_engagement_fact_promotions: Literal[0] = 0
    maximum_engagement_confidence_effects: Literal[0] = 0
    maximum_network_calls: Literal[0] = 0
    maximum_search_provider_calls: Literal[0] = 0
    maximum_connector_calls: Literal[0] = 0
    maximum_model_provider_calls: Literal[0] = 0
    maximum_actual_tool_executions: Literal[0] = 0
    maximum_shell_commands: Literal[0] = 0
    maximum_subprocess_executions: Literal[0] = 0
    maximum_browser_actions: Literal[0] = 0
    maximum_source_mutations: Literal[0] = 0
    maximum_git_operations: Literal[0] = 0
    maximum_runtime_created_pull_requests: Literal[0] = 0
    maximum_runtime_created_approvals: Literal[0] = 0
    maximum_deployments: Literal[0] = 0
    maximum_model_weight_changes: Literal[0] = 0


class PromotionResourceUsage(StrictFrozenModel):
    promotion_requests: int = Field(default=1, ge=0)
    candidates: int = Field(default=0, ge=0)
    approval_evidence_records: int = Field(default=0, ge=0)
    projection_records: int = Field(default=0, ge=0)
    rollback_steps: int = Field(default=0, ge=0)
    compensation_steps: int = Field(default=0, ge=0)
    operator_review_items: int = Field(default=0, ge=0)
    in_memory_transactions: int = Field(default=0, ge=0)
    query_results: int = Field(default=0, ge=0)
    fixture_records: int = Field(default=0, ge=0)
    fixture_bytes: int = Field(default=0, ge=0)
    concurrency: int = Field(default=1, ge=0)
    persistent_knowledge_writes: Literal[0] = 0
    persistent_verified_knowledge_writes: Literal[0] = 0
    cognitive_memory_writes: Literal[0] = 0
    semantic_memory_writes: Literal[0] = 0
    episodic_memory_writes: Literal[0] = 0
    procedural_memory_writes: Literal[0] = 0
    belief_creations: Literal[0] = 0
    belief_mutations: Literal[0] = 0
    automatic_knowledge_promotions: Literal[0] = 0
    automatic_candidate_approvals: Literal[0] = 0
    engagement_fact_promotions: Literal[0] = 0
    engagement_confidence_effects: Literal[0] = 0
    network_calls: Literal[0] = 0
    search_provider_calls: Literal[0] = 0
    connector_calls: Literal[0] = 0
    model_provider_calls: Literal[0] = 0
    actual_tool_executions: Literal[0] = 0
    shell_commands: Literal[0] = 0
    subprocess_executions: Literal[0] = 0
    browser_actions: Literal[0] = 0
    source_mutations: Literal[0] = 0
    git_operations: Literal[0] = 0
    runtime_created_pull_requests: Literal[0] = 0
    runtime_created_approvals: Literal[0] = 0
    deployments: Literal[0] = 0
    model_weight_changes: Literal[0] = 0


class PromotionBudgetDecision(StrictFrozenModel):
    budget_id: str
    budget: PromotionResourceBudget
    usage: PromotionResourceUsage
    passed: bool
    reason_codes: tuple[str, ...]
    budget_fingerprint: str
    runtime_effect: Literal[False] = False

    @model_validator(mode="after")
    def validate_budget(self) -> Self:
        expected = _model_fingerprint(self, {"budget_fingerprint"})
        if self.budget_fingerprint != expected:
            raise ValueError("budget decision fingerprint mismatch")
        return self


def evaluate_resource_budget(
    usage: PromotionResourceUsage,
    budget: PromotionResourceBudget | None = None,
) -> PromotionBudgetDecision:
    budget = budget or PromotionResourceBudget()
    passed = (
        usage.promotion_requests <= budget.maximum_promotion_requests_per_batch
        and usage.candidates <= budget.maximum_candidates_per_request
        and usage.approval_evidence_records
        <= budget.maximum_approval_evidence_records_per_transaction
        and usage.projection_records <= budget.maximum_projection_records_per_transaction
        and usage.rollback_steps <= budget.maximum_rollback_steps_per_transaction
        and usage.compensation_steps <= budget.maximum_compensation_steps_per_transaction
        and usage.operator_review_items <= budget.maximum_operator_review_items
        and usage.in_memory_transactions <= budget.maximum_in_memory_transactions
        and usage.query_results <= budget.maximum_query_results
        and usage.fixture_records <= budget.maximum_fixture_records
        and usage.fixture_bytes <= budget.maximum_fixture_bytes
        and usage.concurrency <= budget.maximum_concurrency
    )
    return _build(
        PromotionBudgetDecision,
        {
            "budget_id": "promotion-budget",
            "budget": budget,
            "usage": usage,
            "passed": passed,
            "reason_codes": (
                "promotion_resource_budget_valid"
                if passed
                else "promotion_resource_budget_exceeded",
            ),
        },
        "budget_fingerprint",
    )


class PromotionIntegrityFinding(StrictFrozenModel):
    finding_id: str
    status: PromotionIntegrityStatus
    reason_codes: tuple[str, ...]
    safe_ids: tuple[str, ...] = ()
    fingerprints: tuple[str, ...] = ()
    bounded_count: int = Field(default=0, ge=0)
    redacted_summary: str = "redacted promotion integrity finding"
    finding_fingerprint: str
    runtime_effect: Literal[False] = False

    @model_validator(mode="after")
    def validate_finding(self) -> Self:
        expected = _model_fingerprint(self, {"finding_fingerprint"})
        if self.finding_fingerprint != expected:
            raise ValueError("integrity finding fingerprint mismatch")
        return self


class PromotionIntegrityReport(StrictFrozenModel):
    schema_version: Literal["aion-glm-promotion-integrity/v1"] = PROMOTION_INTEGRITY_SCHEMA_VERSION
    report_id: str
    status: PromotionIntegrityStatus
    findings: tuple[PromotionIntegrityFinding, ...]
    finding_count: int = Field(ge=0)
    report_fingerprint: str
    read_only: Literal[True] = True
    redacted: Literal[True] = True
    runtime_effect: Literal[False] = False

    @model_validator(mode="after")
    def validate_report(self) -> Self:
        if self.finding_count != len(self.findings):
            raise ValueError("integrity finding count mismatch")
        if self.status is PromotionIntegrityStatus.PASSED and any(
            finding.status is PromotionIntegrityStatus.FAILED for finding in self.findings
        ):
            raise ValueError("passed integrity report cannot contain failed finding")
        expected = _model_fingerprint(self, {"report_fingerprint"})
        if self.report_fingerprint != expected:
            raise ValueError("integrity report fingerprint mismatch")
        return self


def _integrity_report(
    report_id: str,
    safe_ids: tuple[str, ...],
    fingerprints: tuple[str, ...],
    passed: bool,
    reason_code: str,
) -> PromotionIntegrityReport:
    finding = _build(
        PromotionIntegrityFinding,
        {
            "finding_id": f"finding-{report_id}",
            "status": PromotionIntegrityStatus.PASSED
            if passed
            else PromotionIntegrityStatus.FAILED,
            "reason_codes": (reason_code,),
            "safe_ids": tuple(sorted(safe_ids)),
            "fingerprints": tuple(sorted(fingerprints)),
            "bounded_count": len(safe_ids) + len(fingerprints),
        },
        "finding_fingerprint",
    )
    return _build(
        PromotionIntegrityReport,
        {
            "report_id": report_id,
            "status": finding.status,
            "findings": (finding,),
            "finding_count": 1,
        },
        "report_fingerprint",
    )


def audit_promotion_request(request: KnowledgePromotionRequest) -> PromotionIntegrityReport:
    return _integrity_report(
        f"audit-{request.promotion_request_id}",
        (request.promotion_request_id, request.transaction_id),
        (request.request_fingerprint,),
        True,
        "promotion_request_valid",
    )


def audit_candidate_binding(binding: PromotionCandidateBinding) -> PromotionIntegrityReport:
    passed = all(
        report.status is VerifiedKnowledgeIntegrityStatus.PASSED
        for report in (
            binding.candidate_integrity_report,
            binding.lineage_integrity_report,
            binding.policy_status_integrity_report,
        )
    )
    return _integrity_report(
        f"audit-{binding.binding_id}",
        (binding.binding_id, binding.candidate_id),
        (binding.binding_fingerprint,),
        passed,
        "promotion_candidate_binding_valid" if passed else "promotion_candidate_integrity_invalid",
    )


def audit_approval_evidence(bundle: ApprovalEvidenceBundle) -> PromotionIntegrityReport:
    return _integrity_report(
        f"audit-{bundle.bundle_id}",
        (bundle.bundle_id,),
        (bundle.bundle_fingerprint,),
        bundle.separation_of_duties_passed,
        "approval_evidence_valid"
        if bundle.separation_of_duties_passed
        else "approval_separation_of_duties_failed",
    )


def audit_eligibility_snapshot(snapshot: PromotionEligibilitySnapshot) -> PromotionIntegrityReport:
    return _integrity_report(
        f"audit-{snapshot.snapshot_id}",
        (snapshot.snapshot_id, snapshot.candidate_id),
        (snapshot.snapshot_fingerprint,),
        snapshot.disposition is PromotionCandidateDisposition.ELIGIBLE_FOR_DRY_RUN,
        "promotion_candidate_confidence_non_amplification_passed",
    )


def audit_knowledge_identity_plan(plan: KnowledgeIdentityPlan) -> PromotionIntegrityReport:
    return _integrity_report(
        f"audit-{plan.identity_plan_id}",
        (plan.identity_plan_id, plan.knowledge_identity_id),
        (plan.identity_fingerprint,),
        not plan.persistent_identity_created,
        "knowledge_identity_derived",
    )


def audit_conflict_report(report: KnowledgeConflictReport) -> PromotionIntegrityReport:
    return _integrity_report(
        f"audit-{report.report_id}",
        (report.report_id,),
        (report.report_fingerprint,),
        True,
        "knowledge_identity_derived",
    )


def audit_version_plan(plan: KnowledgeVersionPlan) -> PromotionIntegrityReport:
    return _integrity_report(
        f"audit-{plan.version_plan_id}",
        (plan.version_plan_id, plan.knowledge_identity_id),
        (plan.version_plan_fingerprint,),
        plan.append_only
        and plan.historical_versions_preserved
        and not plan.persistent_version_created,
        "knowledge_history_preserved",
    )


def audit_memory_projection_plan(plan: MemoryProjectionPlan) -> PromotionIntegrityReport:
    passed = (
        not plan.persistent_write_authorized
        and not plan.cognitive_memory_write_authorized
        and not plan.belief_mutation_authorized
        and all(not record.memory_record_created for record in plan.records)
    )
    return _integrity_report(
        f"audit-{plan.projection_plan_id}",
        (plan.projection_plan_id,),
        (plan.plan_fingerprint,),
        passed,
        "memory_projection_write_disabled",
    )


def audit_rollback_plan(plan: PromotionRollbackPlan) -> PromotionIntegrityReport:
    return _integrity_report(
        f"audit-{plan.rollback_plan_id}",
        (plan.rollback_plan_id,),
        (plan.plan_fingerprint,),
        plan.valid,
        "promotion_rollback_valid" if plan.valid else "promotion_rollback_invalid",
    )


def audit_compensation_plan(plan: PromotionCompensationPlan) -> PromotionIntegrityReport:
    return _integrity_report(
        f"audit-{plan.compensation_plan_id}",
        (plan.compensation_plan_id,),
        (plan.plan_fingerprint,),
        plan.valid,
        "promotion_compensation_valid" if plan.valid else "promotion_compensation_invalid",
    )


class PromotionDiagnostics(StrictFrozenModel):
    diagnostics_id: str
    reason_codes: tuple[str, ...]
    safe_ids: tuple[str, ...]
    fingerprints: tuple[str, ...]
    diagnostics_fingerprint: str
    redacted: Literal[True] = True
    runtime_effect: Literal[False] = False

    @model_validator(mode="after")
    def validate_diagnostics(self) -> Self:
        expected = _model_fingerprint(self, {"diagnostics_fingerprint"})
        if self.diagnostics_fingerprint != expected:
            raise ValueError("diagnostics fingerprint mismatch")
        return self


class PromotionIncidentRecord(StrictFrozenModel):
    incident_id: str
    severity_code: str
    reason_codes: tuple[str, ...]
    safe_ids: tuple[str, ...]
    fingerprints: tuple[str, ...]
    created_at: datetime
    incident_fingerprint: str
    redacted: Literal[True] = True
    runtime_effect: Literal[False] = False

    @model_validator(mode="after")
    def validate_incident(self) -> Self:
        expected = _model_fingerprint(self, {"incident_fingerprint"})
        if self.incident_fingerprint != expected:
            raise ValueError("incident fingerprint mismatch")
        return self


class PromotionOperatorReviewItem(StrictFrozenModel):
    review_item_id: str
    transaction_id: str
    candidate_ids: tuple[str, ...]
    reason_codes: tuple[str, ...]
    expires_at: datetime
    operator_review_required: Literal[True] = True
    candidate_is_not_durable_knowledge: Literal[True] = True
    operator_approval_is_not_factual_proof: Literal[True] = True
    dry_run_is_not_persistence: Literal[True] = True
    projection_plan_is_not_memory_write: Literal[True] = True
    belief_projection_is_not_belief_creation: Literal[True] = True
    future_persistence_authorized: Literal[False] = False
    actual_knowledge_promotion_authorized: Literal[False] = False
    persistent_knowledge_write_authorized: Literal[False] = False
    cognitive_memory_write_authorized: Literal[False] = False
    belief_mutation_authorized: Literal[False] = False
    automatic_promotion_authorized: Literal[False] = False
    approval_created: Literal[False] = False
    implementation_authorization_created: Literal[False] = False
    review_fingerprint: str
    redacted: Literal[True] = True
    runtime_effect: Literal[False] = False

    @model_validator(mode="after")
    def validate_review(self) -> Self:
        expected = _model_fingerprint(self, {"review_fingerprint"})
        if self.review_fingerprint != expected:
            raise ValueError("operator review fingerprint mismatch")
        return self


class PromotionEvidenceBundle(StrictFrozenModel):
    schema_version: Literal["aion-glm-promotion-evidence/v1"] = PROMOTION_EVIDENCE_SCHEMA_VERSION
    evidence_bundle_id: str
    diagnostics: PromotionDiagnostics
    incidents: tuple[PromotionIncidentRecord, ...]
    operator_review_items: tuple[PromotionOperatorReviewItem, ...]
    evidence_fingerprint: str
    redacted: Literal[True] = True
    runtime_effect: Literal[False] = False

    @model_validator(mode="after")
    def validate_evidence(self) -> Self:
        expected = _model_fingerprint(self, {"evidence_fingerprint"})
        if self.evidence_fingerprint != expected:
            raise ValueError("promotion evidence fingerprint mismatch")
        return self


def build_operator_review_item(
    *,
    review_item_id: str,
    transaction_id: str,
    candidate_ids: tuple[str, ...],
    reason_codes: tuple[str, ...],
    created_at: datetime,
) -> PromotionOperatorReviewItem:
    return _build(
        PromotionOperatorReviewItem,
        {
            "review_item_id": review_item_id,
            "transaction_id": transaction_id,
            "candidate_ids": tuple(sorted(candidate_ids)),
            "reason_codes": reason_codes,
            "expires_at": created_at + timedelta(days=7),
        },
        "review_fingerprint",
    )


class PromotionTransactionPlan(StrictFrozenModel):
    schema_version: Literal["aion-glm-promotion-transaction-plan/v1"] = (
        PROMOTION_TRANSACTION_PLAN_SCHEMA_VERSION
    )
    transaction_id: str
    promotion_request: KnowledgePromotionRequest
    candidate_bindings: tuple[PromotionCandidateBinding, ...]
    eligibility_snapshots: tuple[PromotionEligibilitySnapshot, ...]
    approval_evidence_bundle: ApprovalEvidenceBundle
    knowledge_identity_plans: tuple[KnowledgeIdentityPlan, ...]
    conflict_report: KnowledgeConflictReport
    version_plans: tuple[KnowledgeVersionPlan, ...]
    memory_projection_plan: MemoryProjectionPlan
    rollback_plan: PromotionRollbackPlan
    compensation_plan: PromotionCompensationPlan
    resource_budget_decision: PromotionBudgetDecision
    operator_review_required: Literal[True] = True
    future_persistence_review_required: Literal[True] = True
    future_persistence_authorized: Literal[False] = False
    automatic_promotion: Literal[False] = False
    persistent_write_applied: Literal[False] = False
    cognitive_memory_written: Literal[False] = False
    belief_mutated: Literal[False] = False
    runtime_effect: Literal[False] = False
    transaction_plan_fingerprint: str

    @model_validator(mode="after")
    def validate_transaction_plan(self) -> Self:
        expected = _model_fingerprint(self, {"transaction_plan_fingerprint"})
        if self.transaction_plan_fingerprint != expected:
            raise ValueError("transaction plan fingerprint mismatch")
        return self


class PromotionTransactionResult(StrictFrozenModel):
    schema_version: Literal["aion-glm-promotion-transaction-result/v1"] = (
        PROMOTION_TRANSACTION_RESULT_SCHEMA_VERSION
    )
    transaction_id: str
    status: PromotionTransactionStatus
    candidate_dispositions: tuple[PromotionCandidateDisposition, ...]
    identity_dispositions: tuple[KnowledgeIdentityDisposition, ...]
    version_dispositions: tuple[KnowledgeVersionDisposition, ...]
    projection_statuses: tuple[MemoryProjectionStatus, ...]
    reason_codes: tuple[str, ...]
    integrity_report: PromotionIntegrityReport
    evidence_bundle: PromotionEvidenceBundle
    operator_review_items: tuple[PromotionOperatorReviewItem, ...]
    ready_for_future_persistence_review: bool
    future_persistence_authorized: Literal[False] = False
    actual_knowledge_promotion_applied: Literal[False] = False
    persistent_knowledge_writes: Literal[0] = 0
    persistent_verified_knowledge_writes: Literal[0] = 0
    cognitive_memory_writes: Literal[0] = 0
    semantic_memory_writes: Literal[0] = 0
    episodic_memory_writes: Literal[0] = 0
    procedural_memory_writes: Literal[0] = 0
    belief_creations: Literal[0] = 0
    belief_mutations: Literal[0] = 0
    automatic_promotions: Literal[0] = 0
    runtime_effect: Literal[False] = False
    result_fingerprint: str

    @model_validator(mode="after")
    def validate_result(self) -> Self:
        if self.status is PromotionTransactionStatus.DRY_RUN_PASSED:
            if not self.ready_for_future_persistence_review:
                raise ValueError("dry-run pass must be ready for future review")
        if self.future_persistence_authorized:
            raise ValueError("future persistence is never authorized by AION-222")
        expected = _model_fingerprint(self, {"result_fingerprint"})
        if self.result_fingerprint != expected:
            raise ValueError("transaction result fingerprint mismatch")
        return self


def audit_promotion_transaction_plan(plan: PromotionTransactionPlan) -> PromotionIntegrityReport:
    passed = (
        plan.resource_budget_decision.passed
        and not plan.future_persistence_authorized
        and not plan.persistent_write_applied
        and not plan.cognitive_memory_written
        and not plan.belief_mutated
        and not plan.runtime_effect
    )
    return _integrity_report(
        f"audit-{plan.transaction_id}",
        (plan.transaction_id,),
        (plan.transaction_plan_fingerprint,),
        passed,
        "promotion_transaction_integrity_passed"
        if passed
        else "promotion_transaction_integrity_failed",
    )


def audit_promotion_transaction_result(
    result: PromotionTransactionResult,
) -> PromotionIntegrityReport:
    zero_effect = (
        result.persistent_knowledge_writes == 0
        and result.persistent_verified_knowledge_writes == 0
        and result.cognitive_memory_writes == 0
        and result.semantic_memory_writes == 0
        and result.episodic_memory_writes == 0
        and result.procedural_memory_writes == 0
        and result.belief_creations == 0
        and result.belief_mutations == 0
        and result.automatic_promotions == 0
        and not result.runtime_effect
    )
    return _integrity_report(
        f"audit-result-{result.transaction_id}",
        (result.transaction_id,),
        (result.result_fingerprint,),
        zero_effect,
        "promotion_transaction_integrity_passed"
        if zero_effect
        else "promotion_transaction_integrity_failed",
    )


class ControlledKnowledgePromotionTransactionPlanner:
    """Pure dry-run transaction planner with no persistent side effects."""

    def validate_request(self, request: KnowledgePromotionRequest) -> PromotionIntegrityReport:
        return audit_promotion_request(request)

    def bind_candidates(
        self,
        request: KnowledgePromotionRequest,
        candidates: tuple[VerifiedKnowledgeCandidate, ...],
        *,
        memory_snapshot_id: str,
        memory_snapshot_fingerprint: str,
    ) -> tuple[PromotionCandidateBinding, ...]:
        from aion_brain.knowledge_intelligence.verified_knowledge_integrity import (
            audit_candidate_policy_status,
            audit_integrated_knowledge_lineage,
            audit_verified_knowledge_candidate,
        )

        return tuple(
            bind_promotion_candidate(
                request,
                candidate,
                candidate_integrity_report=audit_verified_knowledge_candidate(candidate),
                lineage_integrity_report=audit_integrated_knowledge_lineage(
                    candidate.integrated_lineage
                ),
                policy_status_integrity_report=audit_candidate_policy_status(candidate),
                memory_snapshot_id=memory_snapshot_id,
                memory_snapshot_fingerprint=memory_snapshot_fingerprint,
            )
            for candidate in sorted(candidates, key=lambda item: item.candidate_id)
        )

    def validate_approval_evidence(
        self,
        *,
        approval_requests: tuple[ApprovalRequest, ...],
        approval_decisions: tuple[ApprovalDecision, ...],
        request: KnowledgePromotionRequest,
        observed_at: datetime,
    ) -> ApprovalEvidenceBundle:
        decisions_by_request = {
            decision.approval_request_id: decision for decision in approval_decisions
        }
        records = tuple(
            project_existing_approval_evidence(
                approval_request,
                decisions_by_request[approval_request.approval_request_id],
                approval_evidence_id=f"approval-evidence-{index + 1:03d}",
                transaction_id=request.transaction_id,
                promotion_request_fingerprint=request.request_fingerprint,
                candidate_ids=request.candidate_ids,
                candidate_fingerprints=request.candidate_fingerprints,
                observed_at=observed_at,
            )
            for index, approval_request in enumerate(
                sorted(approval_requests, key=lambda item: item.approval_request_id)
            )
        )
        return build_approval_evidence_bundle(
            bundle_id=f"approval-bundle-{request.transaction_id}",
            evidence_records=records,
            risk_class=request.risk_class,
            requested_targets=request.requested_projection_targets,
        )

    def revalidate_candidates(
        self,
        bindings: tuple[PromotionCandidateBinding, ...],
        *,
        revalidated_at: datetime,
    ) -> tuple[PromotionEligibilitySnapshot, ...]:
        return tuple(
            revalidate_promotion_candidate(
                binding,
                revalidated_at=revalidated_at,
                valid_until=revalidated_at + timedelta(hours=1),
            )
            for binding in bindings
        )

    def derive_knowledge_identities(
        self,
        snapshots: tuple[PromotionEligibilitySnapshot, ...],
        bindings: tuple[PromotionCandidateBinding, ...],
        approval_bundle: ApprovalEvidenceBundle,
        existing_references: tuple[ExistingKnowledgeVersionReference, ...],
    ) -> tuple[KnowledgeIdentityPlan, ...]:
        bindings_by_candidate = {binding.candidate_id: binding for binding in bindings}
        return tuple(
            derive_knowledge_identity_plan(
                snapshot,
                lineage=bindings_by_candidate[snapshot.candidate_id].candidate.integrated_lineage,
                approval_bundle_fingerprint=approval_bundle.bundle_fingerprint,
                existing_references=existing_references,
            )
            for snapshot in snapshots
        )

    def detect_duplicates_and_conflicts(
        self,
        identity_plans: tuple[KnowledgeIdentityPlan, ...],
        *,
        existing_references: tuple[ExistingKnowledgeVersionReference, ...],
        snapshots: tuple[PromotionEligibilitySnapshot, ...],
    ) -> KnowledgeConflictReport:
        return detect_knowledge_duplicates_and_conflicts(
            identity_plans,
            existing_references=existing_references,
            unresolved_material_dissent=any(
                snapshot.unresolved_dissent_count > 0 for snapshot in snapshots
            ),
        )

    def plan_versions(
        self,
        *,
        request: KnowledgePromotionRequest,
        identity_plans: tuple[KnowledgeIdentityPlan, ...],
        snapshots: tuple[PromotionEligibilitySnapshot, ...],
        conflict_report: KnowledgeConflictReport,
        existing_references: tuple[ExistingKnowledgeVersionReference, ...],
    ) -> tuple[KnowledgeVersionPlan, ...]:
        snapshots_by_candidate = {snapshot.candidate_id: snapshot for snapshot in snapshots}
        return tuple(
            plan_knowledge_version(
                identity_plan=plan,
                snapshot=snapshots_by_candidate[plan.candidate_id],
                request_kind=request.request_kind,
                conflict_report=conflict_report,
                existing_references=existing_references,
                effective_from=request.requested_at,
                effective_to=None,
            )
            for plan in identity_plans
        )

    def plan_memory_projections(
        self,
        *,
        request: KnowledgePromotionRequest,
        version_plans: tuple[KnowledgeVersionPlan, ...],
        approval_bundle: ApprovalEvidenceBundle,
    ) -> MemoryProjectionPlan:
        return plan_memory_projections(
            request=request,
            version_plans=version_plans,
            approval_bundle=approval_bundle,
            source_reference_ids=("operator-supplied-planning-context",),
            valid_from=request.requested_at,
        )

    def plan_rollback(
        self,
        transaction_id: str,
        version_plans: tuple[KnowledgeVersionPlan, ...],
    ) -> PromotionRollbackPlan:
        return build_rollback_plan(transaction_id, version_plans)

    def plan_compensation(
        self,
        transaction_id: str,
        version_plans: tuple[KnowledgeVersionPlan, ...],
    ) -> PromotionCompensationPlan:
        return build_compensation_plan(transaction_id, version_plans)

    def run_dry_run(
        self,
        *,
        request: KnowledgePromotionRequest,
        candidates: tuple[VerifiedKnowledgeCandidate, ...],
        approval_requests: tuple[ApprovalRequest, ...],
        approval_decisions: tuple[ApprovalDecision, ...],
        existing_references: tuple[ExistingKnowledgeVersionReference, ...] = (),
        observed_at: datetime,
        memory_snapshot_id: str,
        memory_snapshot_fingerprint: str,
    ) -> PromotionTransactionResult:
        self.validate_request(request)
        bindings = self.bind_candidates(
            request,
            candidates,
            memory_snapshot_id=memory_snapshot_id,
            memory_snapshot_fingerprint=memory_snapshot_fingerprint,
        )
        usage = PromotionResourceUsage(
            candidates=len(bindings),
            approval_evidence_records=len(approval_requests),
        )
        budget_decision = evaluate_resource_budget(usage)
        snapshots = self.revalidate_candidates(bindings, revalidated_at=observed_at)
        approval_bundle = self.validate_approval_evidence(
            approval_requests=approval_requests,
            approval_decisions=approval_decisions,
            request=request,
            observed_at=observed_at,
        )
        identities = self.derive_knowledge_identities(
            snapshots,
            bindings,
            approval_bundle,
            existing_references,
        )
        conflicts = self.detect_duplicates_and_conflicts(
            identities,
            existing_references=existing_references,
            snapshots=snapshots,
        )
        versions = self.plan_versions(
            request=request,
            identity_plans=identities,
            snapshots=snapshots,
            conflict_report=conflicts,
            existing_references=existing_references,
        )
        projections = self.plan_memory_projections(
            request=request,
            version_plans=versions,
            approval_bundle=approval_bundle,
        )
        rollback = self.plan_rollback(request.transaction_id, versions)
        compensation = self.plan_compensation(request.transaction_id, versions)
        plan = _build(
            PromotionTransactionPlan,
            {
                "transaction_id": request.transaction_id,
                "promotion_request": request,
                "candidate_bindings": bindings,
                "eligibility_snapshots": snapshots,
                "approval_evidence_bundle": approval_bundle,
                "knowledge_identity_plans": identities,
                "conflict_report": conflicts,
                "version_plans": versions,
                "memory_projection_plan": projections,
                "rollback_plan": rollback,
                "compensation_plan": compensation,
                "resource_budget_decision": budget_decision,
            },
            "transaction_plan_fingerprint",
        )
        plan_integrity = audit_promotion_transaction_plan(plan)
        status = PromotionTransactionStatus.DRY_RUN_PASSED
        reasons: tuple[str, ...] = ("promotion_transaction_dry_run_passed",)
        if not budget_decision.passed:
            status = PromotionTransactionStatus.BLOCKED
            reasons = ("promotion_request_budget_exceeded",)
        elif any(
            audit_candidate_binding(binding).status is PromotionIntegrityStatus.FAILED
            for binding in bindings
        ):
            status = PromotionTransactionStatus.INTEGRITY_FAILED
            reasons = ("promotion_candidate_integrity_invalid",)
        elif any(
            snapshot.disposition is not PromotionCandidateDisposition.ELIGIBLE_FOR_DRY_RUN
            for snapshot in snapshots
        ):
            status = PromotionTransactionStatus.ABSTAINED
            reasons = ("promotion_candidate_revalidation_required",)
        elif not approval_bundle.separation_of_duties_passed:
            status = PromotionTransactionStatus.BLOCKED
            reasons = ("approval_separation_of_duties_failed",)
        elif all(
            disposition is KnowledgeVersionDisposition.NO_OP_DUPLICATE
            for disposition in (version.disposition for version in versions)
        ):
            status = PromotionTransactionStatus.DRY_RUN_NO_OP_DUPLICATE
            reasons = ("promotion_transaction_duplicate_no_op",)
        elif conflicts.material_hold:
            status = PromotionTransactionStatus.ABSTAINED
            reasons = ("promotion_transaction_abstained", "knowledge_direct_conflict")
        elif (
            not rollback.valid
            or not compensation.valid
            or any(
                record.projection_status is MemoryProjectionStatus.BLOCKED
                for record in projections.records
            )
        ):
            status = PromotionTransactionStatus.BLOCKED
            reasons = ("promotion_transaction_blocked",)
        review = build_operator_review_item(
            review_item_id=f"review-{request.transaction_id}",
            transaction_id=request.transaction_id,
            candidate_ids=request.candidate_ids,
            reason_codes=reasons,
            created_at=observed_at,
        )
        diagnostics = _build(
            PromotionDiagnostics,
            {
                "diagnostics_id": f"diagnostics-{request.transaction_id}",
                "reason_codes": reasons,
                "safe_ids": (request.transaction_id,),
                "fingerprints": (request.request_fingerprint, plan.transaction_plan_fingerprint),
            },
            "diagnostics_fingerprint",
        )
        evidence = _build(
            PromotionEvidenceBundle,
            {
                "evidence_bundle_id": f"evidence-{request.transaction_id}",
                "diagnostics": diagnostics,
                "incidents": (),
                "operator_review_items": (review,),
            },
            "evidence_fingerprint",
        )
        ready = status is PromotionTransactionStatus.DRY_RUN_PASSED
        return _build(
            PromotionTransactionResult,
            {
                "transaction_id": request.transaction_id,
                "status": status,
                "candidate_dispositions": tuple(snapshot.disposition for snapshot in snapshots),
                "identity_dispositions": tuple(plan.disposition for plan in identities),
                "version_dispositions": tuple(plan.disposition for plan in versions),
                "projection_statuses": tuple(
                    record.projection_status for record in projections.records
                ),
                "reason_codes": reasons,
                "integrity_report": plan_integrity,
                "evidence_bundle": evidence,
                "operator_review_items": (review,),
                "ready_for_future_persistence_review": ready,
            },
            "result_fingerprint",
        )

    def query(
        self,
        journal: InMemoryPromotionTransactionJournal,
        query: PromotionTransactionQuery,
    ) -> PromotionTransactionQueryResult:
        return journal.query(query)

    def audit(self, journal: InMemoryPromotionTransactionJournal) -> PromotionIntegrityReport:
        return journal.audit()

    def replay_fixture(self, path: Path, *, repository_root: Path) -> PromotionFixtureEnvelope:
        return ExplicitLocalPromotionFixtureReplay(repository_root=repository_root).replay_fixture(
            path
        )

    def reject_persistent_write(self) -> PersistentWriteOutcome:
        return PersistentWriteOutcome.PERSISTENT_WRITE_DISABLED


class PromotionTransactionJournalRecord(StrictFrozenModel):
    schema_version: Literal["aion-glm-promotion-transaction-journal/v1"] = (
        PROMOTION_TRANSACTION_JOURNAL_SCHEMA_VERSION
    )
    journal_record_id: str
    transaction_id: str
    result: PromotionTransactionResult
    transaction_fingerprint: str
    recorded_at: datetime
    read_only: Literal[True] = True
    redacted: Literal[True] = True
    persistent_write_applied: Literal[False] = False
    runtime_effect: Literal[False] = False
    journal_record_fingerprint: str

    @model_validator(mode="after")
    def validate_record(self) -> Self:
        if self.transaction_id != self.result.transaction_id:
            raise ValueError("journal transaction ID mismatch")
        if self.transaction_fingerprint != self.result.result_fingerprint:
            raise ValueError("journal transaction fingerprint mismatch")
        expected = _model_fingerprint(self, {"journal_record_fingerprint"})
        if self.journal_record_fingerprint != expected:
            raise ValueError("journal record fingerprint mismatch")
        return self


class PromotionTransactionQuery(StrictFrozenModel):
    schema_version: Literal["aion-glm-promotion-transaction-query/v1"] = (
        PROMOTION_TRANSACTION_QUERY_SCHEMA_VERSION
    )
    transaction_id: str | None = None
    promotion_request_id: str | None = None
    candidate_id: str | None = None
    candidate_identity_id: str | None = None
    knowledge_identity_id: str | None = None
    request_kind: PromotionRequestKind | None = None
    risk_class: PromotionRiskClass | None = None
    approval_status: ApprovalEvidenceStatus | None = None
    candidate_disposition: PromotionCandidateDisposition | None = None
    conflict_kind: KnowledgeConflictKind | None = None
    version_disposition: KnowledgeVersionDisposition | None = None
    projection_target: MemoryProjectionTarget | None = None
    transaction_status: PromotionTransactionStatus | None = None
    operator_review_required: bool | None = None
    ready_for_future_persistence_review: bool | None = None
    limit: int = Field(default=100, ge=1, le=MAXIMUM_QUERY_RESULTS)
    runtime_effect: Literal[False] = False


class PromotionTransactionQueryResult(StrictFrozenModel):
    schema_version: Literal["aion-glm-promotion-transaction-query-result/v1"] = (
        PROMOTION_TRANSACTION_QUERY_RESULT_SCHEMA_VERSION
    )
    query: PromotionTransactionQuery
    results: tuple[PromotionTransactionJournalRecord, ...]
    result_count: int = Field(ge=0, le=MAXIMUM_QUERY_RESULTS)
    exact_match_only: Literal[True] = True
    semantic_search_used: Literal[False] = False
    fuzzy_search_used: Literal[False] = False
    ranking_implies_truth: Literal[False] = False
    query_fingerprint: str
    runtime_effect: Literal[False] = False

    @model_validator(mode="after")
    def validate_query_result(self) -> Self:
        if self.result_count != len(self.results):
            raise ValueError("query result count mismatch")
        expected = _model_fingerprint(self, {"query_fingerprint"})
        if self.query_fingerprint != expected:
            raise ValueError("query result fingerprint mismatch")
        return self


class InMemoryPromotionTransactionJournal:
    """Copy-on-write transaction evidence journal; not a knowledge store."""

    def __init__(
        self,
        records: Iterable[PromotionTransactionJournalRecord] = (),
    ) -> None:
        ordered = tuple(sorted(records, key=lambda item: item.journal_record_id))
        if len(ordered) > MAXIMUM_IN_MEMORY_TRANSACTIONS:
            raise ValueError("in-memory transaction limit exceeded")
        by_id: dict[str, PromotionTransactionJournalRecord] = {}
        for record in ordered:
            existing = by_id.get(record.transaction_id)
            if existing and existing.transaction_fingerprint != record.transaction_fingerprint:
                raise ValueError("changed transaction replay rejected")
            by_id[record.transaction_id] = record
        self._records = ordered
        self._by_id = MappingProxyType(by_id)

    @property
    def records(self) -> tuple[PromotionTransactionJournalRecord, ...]:
        return self._records

    def with_transaction(
        self,
        record: PromotionTransactionJournalRecord,
    ) -> InMemoryPromotionTransactionJournal:
        existing = self._by_id.get(record.transaction_id)
        if existing:
            if existing.transaction_fingerprint != record.transaction_fingerprint:
                raise ValueError("changed transaction replay rejected")
            return self
        return InMemoryPromotionTransactionJournal((*self._records, record))

    def with_transactions(
        self,
        records: Iterable[PromotionTransactionJournalRecord],
    ) -> InMemoryPromotionTransactionJournal:
        journal = self
        for record in records:
            journal = journal.with_transaction(record)
        return journal

    def transaction_by_id(self, transaction_id: str) -> PromotionTransactionJournalRecord | None:
        return self._by_id.get(transaction_id)

    def transactions_by_candidate(
        self,
        candidate_id: str,
    ) -> tuple[PromotionTransactionJournalRecord, ...]:
        return tuple(
            record
            for record in self._records
            if candidate_id in json.dumps(record.result.model_dump(mode="json"), sort_keys=True)
        )

    def transactions_by_knowledge_identity(
        self,
        knowledge_identity_id: str,
    ) -> tuple[PromotionTransactionJournalRecord, ...]:
        return tuple(
            record
            for record in self._records
            if knowledge_identity_id in json.dumps(record.result.model_dump(mode="json"))
        )

    def query(self, query: PromotionTransactionQuery) -> PromotionTransactionQueryResult:
        results: list[PromotionTransactionJournalRecord] = []
        for record in self._records:
            result = record.result
            if query.transaction_id and result.transaction_id != query.transaction_id:
                continue
            if query.transaction_status and result.status is not query.transaction_status:
                continue
            if (
                query.candidate_disposition
                and query.candidate_disposition not in result.candidate_dispositions
            ):
                continue
            if (
                query.version_disposition
                and query.version_disposition not in result.version_dispositions
            ):
                continue
            if query.projection_target:
                target_text = query.projection_target.value
                if target_text not in json.dumps(result.model_dump(mode="json")):
                    continue
            if query.ready_for_future_persistence_review is not None:
                if (
                    result.ready_for_future_persistence_review
                    is not query.ready_for_future_persistence_review
                ):
                    continue
            results.append(record)
            if len(results) >= query.limit:
                break
        return _build(
            PromotionTransactionQueryResult,
            {
                "query": query,
                "results": tuple(results),
                "result_count": len(results),
            },
            "query_fingerprint",
        )

    def audit(self) -> PromotionIntegrityReport:
        return audit_transaction_journal(self)

    def replay_fixture(self, path: Path, *, repository_root: Path) -> PromotionFixtureEnvelope:
        return ExplicitLocalPromotionFixtureReplay(repository_root=repository_root).replay_fixture(
            path
        )

    def reject_persistent_write(self) -> PersistentWriteOutcome:
        return PersistentWriteOutcome.PERSISTENT_WRITE_DISABLED


def build_journal_record(
    *,
    journal_record_id: str,
    result: PromotionTransactionResult,
    recorded_at: datetime,
) -> PromotionTransactionJournalRecord:
    return _build(
        PromotionTransactionJournalRecord,
        {
            "journal_record_id": journal_record_id,
            "transaction_id": result.transaction_id,
            "result": result,
            "transaction_fingerprint": result.result_fingerprint,
            "recorded_at": recorded_at,
        },
        "journal_record_fingerprint",
    )


def audit_transaction_journal(
    journal: InMemoryPromotionTransactionJournal,
) -> PromotionIntegrityReport:
    return _integrity_report(
        "audit-transaction-journal",
        tuple(record.transaction_id for record in journal.records),
        tuple(record.journal_record_fingerprint for record in journal.records),
        True,
        "promotion_transaction_integrity_passed",
    )


class PromotionFixtureEnvelope(StrictFrozenModel):
    schema_version: Literal["aion-glm-promotion-fixture/v1"] = PROMOTION_FIXTURE_SCHEMA_VERSION
    fixture_id: str
    records: tuple[PromotionTransactionJournalRecord, ...]
    record_count: int = Field(ge=0, le=MAXIMUM_FIXTURE_RECORDS)
    fixture_fingerprint: str
    read_only: Literal[True] = True
    redacted: Literal[True] = True
    runtime_effect: Literal[False] = False

    @model_validator(mode="after")
    def validate_fixture(self) -> Self:
        if self.record_count != len(self.records):
            raise ValueError("fixture record count mismatch")
        expected = _model_fingerprint(self, {"fixture_fingerprint"})
        if self.fixture_fingerprint != expected:
            raise ValueError("fixture fingerprint mismatch")
        return self


def build_promotion_fixture_envelope(
    *,
    fixture_id: str,
    records: tuple[PromotionTransactionJournalRecord, ...],
) -> PromotionFixtureEnvelope:
    return _build(
        PromotionFixtureEnvelope,
        {
            "fixture_id": fixture_id,
            "records": records,
            "record_count": len(records),
        },
        "fixture_fingerprint",
    )


class ExplicitLocalPromotionFixtureReplay:
    """Read-only explicit local fixture replay for synthetic records."""

    def __init__(self, *, repository_root: Path) -> None:
        self.repository_root = repository_root.resolve()

    def replay_fixture(self, path: Path) -> PromotionFixtureEnvelope:
        text_path = str(path)
        if "://" in text_path or "$" in text_path or "~" in text_path:
            raise ValueError("fixture path must be explicit local absolute path")
        if not path.is_absolute():
            raise ValueError("fixture path must be absolute")
        if any(part.startswith(".") for part in path.parts if part not in {"/"}):
            raise ValueError("fixture path must not be hidden")
        if not path.exists():
            raise ValueError("fixture path missing")
        if path.is_symlink():
            raise ValueError("fixture path symlink rejected")
        if not path.is_file():
            raise ValueError("fixture path must be a regular file")
        resolved = path.resolve()
        if resolved == self.repository_root or self.repository_root in resolved.parents:
            raise ValueError("fixture path must be outside repository")
        if resolved.stat().st_size > MAXIMUM_FIXTURE_BYTES:
            raise ValueError("fixture exceeds byte limit")
        raw = resolved.read_text(encoding="utf-8")
        _reject_protected(raw, "fixture")
        payload = json.loads(raw)
        _reject_protected(payload, "fixture")
        envelope = PromotionFixtureEnvelope.model_validate(payload)
        if envelope.record_count > MAXIMUM_FIXTURE_RECORDS:
            raise ValueError("fixture record limit exceeded")
        return envelope


def reject_persistent_write() -> PersistentWriteOutcome:
    return PersistentWriteOutcome.PERSISTENT_WRITE_DISABLED


__all__ = [name for name in globals() if not name.startswith("_")]
