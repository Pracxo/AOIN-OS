"""Deterministic verified-knowledge candidate memory contracts."""

from __future__ import annotations

import math
import re
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from enum import StrEnum
from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.knowledge_epistemic_assessment import (
    ConfidenceBand,
    ContradictionStatus,
    EpistemicAssessmentStatus,
    FreshnessStatus,
    ScopeApplicability,
)
from aion_brain.contracts.knowledge_research import (
    ensure_utc,
    fingerprint_payload,
    reject_protected_material,
    stable_json,
    validate_hex64,
    validate_safe_identifier,
)

VERIFIED_KNOWLEDGE_CONTRACT_SCHEMA_VERSION: Literal[
    "aion-knowledge-verified-memory/v1"
] = "aion-knowledge-verified-memory/v1"
INTEGRATED_KNOWLEDGE_LINEAGE_SCHEMA_VERSION: Literal[
    "aion-knowledge-integrated-lineage/v1"
] = "aion-knowledge-integrated-lineage/v1"
VERIFIED_KNOWLEDGE_CANDIDATE_SCHEMA_VERSION: Literal[
    "aion-knowledge-verified-candidate/v1"
] = (
    "aion-knowledge-verified-candidate/v1"
)
VERIFIED_KNOWLEDGE_ELIGIBILITY_SCHEMA_VERSION: Literal[
    "aion-knowledge-verified-candidate-eligibility/v1"
] = (
    "aion-knowledge-verified-candidate-eligibility/v1"
)
VERIFIED_KNOWLEDGE_VERSION_SCHEMA_VERSION: Literal[
    "aion-knowledge-verified-candidate-version/v1"
] = (
    "aion-knowledge-verified-candidate-version/v1"
)
VERIFIED_KNOWLEDGE_BATCH_SCHEMA_VERSION: Literal[
    "aion-knowledge-verified-candidate-batch/v1"
] = (
    "aion-knowledge-verified-candidate-batch/v1"
)
VERIFIED_KNOWLEDGE_MEMORY_SNAPSHOT_SCHEMA_VERSION: Literal[
    "aion-knowledge-verified-memory-snapshot/v1"
] = (
    "aion-knowledge-verified-memory-snapshot/v1"
)
VERIFIED_KNOWLEDGE_REVALIDATION_SCHEMA_VERSION: Literal[
    "aion-knowledge-verified-revalidation/v1"
] = (
    "aion-knowledge-verified-revalidation/v1"
)
VERIFIED_KNOWLEDGE_QUERY_SCHEMA_VERSION: Literal[
    "aion-knowledge-verified-query/v1"
] = "aion-knowledge-verified-query/v1"
VERIFIED_KNOWLEDGE_QUERY_RESULT_SCHEMA_VERSION: Literal[
    "aion-knowledge-verified-query-result/v1"
] = (
    "aion-knowledge-verified-query-result/v1"
)
VERIFIED_KNOWLEDGE_FIXTURE_SCHEMA_VERSION: Literal[
    "aion-knowledge-verified-fixture/v1"
] = "aion-knowledge-verified-fixture/v1"
ENGAGEMENT_SIGNAL_SCHEMA_VERSION: Literal[
    "aion-knowledge-engagement-signal/v1"
] = "aion-knowledge-engagement-signal/v1"
ENGAGEMENT_SIGNAL_BATCH_SCHEMA_VERSION: Literal[
    "aion-knowledge-engagement-signal-batch/v1"
] = (
    "aion-knowledge-engagement-signal-batch/v1"
)
ENGAGEMENT_LEARNING_CANDIDATE_SCHEMA_VERSION: Literal[
    "aion-knowledge-engagement-learning-candidate/v1"
] = (
    "aion-knowledge-engagement-learning-candidate/v1"
)
ENGAGEMENT_LEARNING_BATCH_SCHEMA_VERSION: Literal[
    "aion-knowledge-engagement-learning-batch/v1"
] = (
    "aion-knowledge-engagement-learning-batch/v1"
)
VERIFIED_KNOWLEDGE_INTEGRITY_SCHEMA_VERSION: Literal[
    "aion-knowledge-verified-integrity/v1"
] = (
    "aion-knowledge-verified-integrity/v1"
)
VERIFIED_KNOWLEDGE_EVIDENCE_SCHEMA_VERSION: Literal[
    "aion-knowledge-verified-evidence/v1"
] = "aion-knowledge-verified-evidence/v1"
VERIFIED_KNOWLEDGE_REASON_CODE_REGISTRY_VERSION: Literal[
    "aion-knowledge-verified-reasons/v1"
] = (
    "aion-knowledge-verified-reasons/v1"
)

PROGRAM_ID: Literal["AION-KNOWLEDGE-INTELLIGENCE-001"] = (
    "AION-KNOWLEDGE-INTELLIGENCE-001"
)
AUTHORIZATION_TRANSACTION_ID: Literal["AION-216-KI-0007"] = "AION-216-KI-0007"
APPROVAL_RECORD_ID: Literal["AION-216-KI-0007"] = "AION-216-KI-0007"
IMPLEMENTATION_TASK: Literal["AION-217"] = "AION-217"
FORMAL_CLOSEOUT_TASK: Literal["AION-218"] = "AION-218"
AUTHORIZATION_SCOPE: Literal[
    "deterministic-verified-knowledge-candidate-lineage-versioning-"
    "revalidation-operator-review-engagement-learning-abstention-core"
] = (
    "deterministic-verified-knowledge-candidate-lineage-versioning-"
    "revalidation-operator-review-engagement-learning-abstention-core"
)

VERIFIED_KNOWLEDGE_MEMORY_STATE: Literal[
    "implemented_deterministic_in_memory_candidate_versioning_engagement_learning_"
    "persistent_write_disabled"
] = (
    "implemented_deterministic_in_memory_candidate_versioning_engagement_learning_"
    "persistent_write_disabled"
)
ENGAGEMENT_LEARNING_CANDIDATE_PLANE_STATE: Literal[
    "implemented_deterministic_in_memory_non_factual_candidate_only"
] = "implemented_deterministic_in_memory_non_factual_candidate_only"

MAXIMUM_CANDIDATES_PER_BATCH: Literal[500] = 500
MAXIMUM_CANDIDATE_VERSIONS_PER_IDENTITY: Literal[100] = 100
MAXIMUM_LINEAGE_REFERENCES_PER_CANDIDATE: Literal[500] = 500
MAXIMUM_SOURCE_REGISTRY_REFERENCES_PER_CANDIDATE: Literal[100] = 100
MAXIMUM_CLAIM_REFERENCES_PER_CANDIDATE: Literal[20] = 20
MAXIMUM_ASSESSMENT_REFERENCES_PER_CANDIDATE: Literal[20] = 20
MAXIMUM_MESH_SYNTHESIS_REFERENCES_PER_CANDIDATE: Literal[20] = 20
MAXIMUM_TOOL_SESSION_REFERENCES_PER_CANDIDATE: Literal[20] = 20
MAXIMUM_REASON_CODES_PER_CANDIDATE: Literal[100] = 100
MAXIMUM_OPERATOR_REVIEW_ITEMS: Literal[500] = 500
MAXIMUM_MEMORY_SNAPSHOTS: Literal[100] = 100
MAXIMUM_QUERY_RESULTS: Literal[1000] = 1000
MAXIMUM_ENGAGEMENT_SIGNALS_PER_BATCH: Literal[1000] = 1000
MAXIMUM_ENGAGEMENT_LEARNING_CANDIDATES_PER_BATCH: Literal[500] = 500
MAXIMUM_FIXTURE_RECORDS: Literal[5000] = 5000
MAXIMUM_FIXTURE_BYTES: Literal[4194304] = 4_194_304
MAXIMUM_CONCURRENT_CANDIDATE_EVALUATIONS: Literal[4] = 4
MAXIMUM_PERSISTENT_VERIFIED_KNOWLEDGE_WRITE_BATCH: Literal[0] = 0
MAXIMUM_AUTOMATIC_KNOWLEDGE_PROMOTIONS: Literal[0] = 0
MAXIMUM_OPERATOR_APPROVAL_CREATIONS: Literal[0] = 0
MAXIMUM_COGNITIVE_MEMORY_WRITES: Literal[0] = 0
MAXIMUM_BELIEF_MUTATIONS: Literal[0] = 0
MAXIMUM_ENGAGEMENT_FACT_PROMOTIONS: Literal[0] = 0
MAXIMUM_ENGAGEMENT_CONFIDENCE_EFFECTS: Literal[0] = 0
MAXIMUM_PUBLIC_NETWORK_CALLS: Literal[0] = 0
MAXIMUM_DNS_RESOLUTIONS: Literal[0] = 0
MAXIMUM_SEARCH_PROVIDER_CALLS: Literal[0] = 0
MAXIMUM_CONNECTOR_CALLS: Literal[0] = 0
MAXIMUM_MODEL_PROVIDER_CALLS: Literal[0] = 0
MAXIMUM_ACTUAL_TOOL_EXECUTIONS: Literal[0] = 0
MAXIMUM_SHELL_COMMANDS: Literal[0] = 0
MAXIMUM_SUBPROCESS_EXECUTIONS: Literal[0] = 0
MAXIMUM_BROWSER_ACTIONS: Literal[0] = 0
MAXIMUM_FILESYSTEM_MUTATIONS: Literal[0] = 0
MAXIMUM_SOURCE_MUTATIONS: Literal[0] = 0
MAXIMUM_GIT_OPERATIONS: Literal[0] = 0
MAXIMUM_RUNTIME_CREATED_PULL_REQUESTS: Literal[0] = 0
MAXIMUM_APPROVALS_CREATED: Literal[0] = 0
MAXIMUM_DEPLOYMENTS: Literal[0] = 0
MAXIMUM_MODEL_WEIGHT_CHANGES: Literal[0] = 0

MODEL_CONFIG = ConfigDict(extra="forbid", hide_input_in_errors=True)
FROZEN_MODEL_CONFIG = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SUPPORT_CONFIDENCE_THRESHOLD = Decimal("0.850000")
REFUTATION_CONFIDENCE_THRESHOLD = Decimal("0.850000")

_REASON_CODE_RE = re.compile(r"^[a-z][a-z0-9_]{0,127}$")
_PROTECTED_KEY_MARKERS = (
    "source_body",
    "source_preview",
    "raw_prompt",
    "hidden_reasoning",
    "raw_user_message",
    "credential",
    "token",
    "cookie",
    "authorization_header",
    "private_key",
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
    "token",
    "cookie:",
    "authorization:",
    "private key",
    "personal data",
    "source patch",
    "raw diff",
    "diff --git",
    "@@",
    "sk-",
    "ghp_",
    "gho_",
)


class VerifiedKnowledgeError(ValueError):
    """Raised when verified-knowledge candidate input violates the boundary."""


class VerifiedKnowledgeCandidateKind(StrEnum):
    """Reviewable candidate posture, not factual truth."""

    SUPPORT_CANDIDATE = "support_candidate"
    REFUTATION_CANDIDATE = "refutation_candidate"


class VerifiedKnowledgeEligibilityStatus(StrEnum):
    """Eligibility status for operator review only."""

    ELIGIBLE_FOR_OPERATOR_REVIEW = "eligible_for_operator_review"
    INELIGIBLE_INSUFFICIENT_EVIDENCE = "ineligible_insufficient_evidence"
    INELIGIBLE_LOW_CONFIDENCE = "ineligible_low_confidence"
    INELIGIBLE_INCOMPLETE_PROVENANCE = "ineligible_incomplete_provenance"
    INELIGIBLE_INCOMPLETE_CITATIONS = "ineligible_incomplete_citations"
    INELIGIBLE_STALE = "ineligible_stale"
    INELIGIBLE_RETRACTED = "ineligible_retracted"
    INELIGIBLE_SUPERSEDED = "ineligible_superseded"
    INELIGIBLE_SCOPE_MISMATCH = "ineligible_scope_mismatch"
    INELIGIBLE_UNRESOLVED_CONTRADICTION = "ineligible_unresolved_contradiction"
    INELIGIBLE_MATERIAL_DISSENT = "ineligible_material_dissent"
    INELIGIBLE_INTEGRITY_FAILURE = "ineligible_integrity_failure"
    REVALIDATION_REQUIRED = "revalidation_required"
    ABSTAINED = "abstained"


class VerifiedKnowledgeLifecycleStatus(StrEnum):
    """Candidate lifecycle, without approval or promotion semantics."""

    CANDIDATE = "candidate"
    OPERATOR_REVIEW_PENDING = "operator_review_pending"
    OPERATOR_REVIEW_REJECTED = "operator_review_rejected"
    SUPERSEDED = "superseded"
    RETRACTED = "retracted"
    EXPIRED = "expired"
    REVALIDATION_REQUIRED = "revalidation_required"
    ARCHIVED = "archived"


class VerifiedKnowledgeVersionReason(StrEnum):
    """Reason for creating an immutable candidate version."""

    INITIAL = "initial"
    EVIDENCE_ADDED = "evidence_added"
    EVIDENCE_REMOVED = "evidence_removed"
    ASSESSMENT_CHANGED = "assessment_changed"
    MESH_SYNTHESIS_CHANGED = "mesh_synthesis_changed"
    TOOL_EVIDENCE_CHANGED = "tool_evidence_changed"
    CORRECTION_RECORDED = "correction_recorded"
    RETRACTION_RECORDED = "retraction_recorded"
    SUPERSESSION_RECORDED = "supersession_recorded"
    SCOPE_CHANGED = "scope_changed"
    EXPIRY_REACHED = "expiry_reached"
    EXPLICIT_REVALIDATION = "explicit_revalidation"


class EngagementSignalKind(StrEnum):
    """Bounded engagement metadata kind; never factual evidence."""

    QUERY_REPEATED = "query_repeated"
    RESPONSE_ACCEPTED = "response_accepted"
    RESPONSE_REJECTED = "response_rejected"
    CORRECTION_SUBMITTED = "correction_submitted"
    CITATION_OPENED = "citation_opened"
    FOLLOW_UP_REQUESTED = "follow_up_requested"
    RETRIEVAL_SUCCEEDED = "retrieval_succeeded"
    RETRIEVAL_FAILED = "retrieval_failed"
    CLARIFICATION_REQUESTED = "clarification_requested"
    TASK_OUTCOME_REPORTED = "task_outcome_reported"


class EngagementLearningCandidateKind(StrEnum):
    """Engagement-learning candidate kind requiring operator review."""

    RESEARCH_GAP = "research_gap"
    CLARIFICATION_NEED = "clarification_need"
    RETRIEVAL_STRATEGY = "retrieval_strategy"
    SOURCE_SELECTION = "source_selection"
    DOMAIN_ROUTING = "domain_routing"
    VERIFICATION_RULE = "verification_rule"
    TOOL_MANIFEST_GAP = "tool_manifest_gap"
    RESPONSE_QUALITY = "response_quality"
    PREFERENCE_CANDIDATE = "preference_candidate"


class EngagementLearningLifecycleStatus(StrEnum):
    """Engagement-learning lifecycle without automatic application."""

    PROPOSED = "proposed"
    OPERATOR_REVIEW_PENDING = "operator_review_pending"
    OPERATOR_REVIEW_REJECTED = "operator_review_rejected"
    SUPERSEDED = "superseded"
    EXPIRED = "expired"
    ARCHIVED = "archived"


class VerifiedKnowledgeIntegrityStatus(StrEnum):
    """Integrity audit status."""

    PASSED = "passed"
    FAILED = "failed"


class VerifiedKnowledgePersistentWriteOutcome(StrEnum):
    """Fail-closed persistent-write outcome."""

    PERSISTENT_WRITE_DISABLED = "persistent_write_disabled"


class VerifiedKnowledgeRevalidationTrigger(StrEnum):
    """Explicit revalidation triggers."""

    EVIDENCE_ADDED = "evidence_added"
    EVIDENCE_REMOVED = "evidence_removed"
    CORRECTION_RECORDED = "correction_recorded"
    RETRACTION_RECORDED = "retraction_recorded"
    SUPERSESSION_RECORDED = "supersession_recorded"
    ASSESSMENT_CHANGED = "assessment_changed"
    MESH_SYNTHESIS_CHANGED = "mesh_synthesis_changed"
    TOOL_EVIDENCE_CHANGED = "tool_evidence_changed"
    SCOPE_CHANGED = "scope_changed"
    EXPIRY_REACHED = "expiry_reached"
    OPERATOR_REQUESTED = "operator_requested"


VERIFIED_KNOWLEDGE_REASON_CODES: tuple[str, ...] = (
    "verified_lineage_valid",
    "verified_lineage_invalid",
    "verified_lineage_reference_missing",
    "verified_lineage_fingerprint_mismatch",
    "verified_candidate_integrity_passed",
    "verified_candidate_integrity_failed",
    "verified_candidate_support_eligible",
    "verified_candidate_refutation_eligible",
    "verified_candidate_insufficient_evidence",
    "verified_candidate_low_confidence",
    "verified_candidate_incomplete_provenance",
    "verified_candidate_incomplete_citations",
    "verified_candidate_stale",
    "verified_candidate_retracted",
    "verified_candidate_superseded",
    "verified_candidate_scope_mismatch",
    "verified_candidate_unresolved_contradiction",
    "verified_candidate_material_dissent",
    "verified_candidate_upstream_abstention",
    "verified_candidate_revalidation_required",
    "verified_candidate_confidence_inherited",
    "verified_candidate_confidence_non_amplification_enforced",
    "verified_candidate_tool_output_not_fact",
    "verified_candidate_engagement_not_fact",
    "verified_candidate_version_created",
    "verified_candidate_version_idempotent_replay",
    "verified_candidate_version_collision",
    "verified_candidate_supersession_recorded",
    "verified_candidate_retraction_recorded",
    "verified_candidate_expiry_recorded",
    "verified_candidate_history_preserved",
    "verified_candidate_operator_review_required",
    "verified_candidate_automatic_promotion_blocked",
    "verified_candidate_cognitive_memory_write_blocked",
    "verified_candidate_belief_mutation_blocked",
    "verified_candidate_persistent_write_disabled",
    "verified_candidate_runtime_disabled",
    "engagement_signal_valid",
    "engagement_signal_invalid",
    "engagement_signal_idempotent_replay",
    "engagement_signal_identity_collision",
    "engagement_signal_non_factual",
    "engagement_signal_zero_confidence_effect",
    "engagement_signal_zero_source_independence_effect",
    "engagement_learning_candidate_proposed",
    "engagement_learning_candidate_version_created",
    "engagement_learning_candidate_operator_review_required",
    "engagement_learning_candidate_automatic_application_blocked",
    "engagement_learning_candidate_model_training_blocked",
    "verified_memory_integrity_passed",
    "verified_memory_integrity_failed",
)
_REASON_CODE_SET = frozenset(VERIFIED_KNOWLEDGE_REASON_CODES)


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""

    return datetime.now(UTC)


def reject_verified_knowledge_payload(value: Any, field_name: str = "payload") -> None:
    """Reject protected material recursively without echoing rejected content."""

    seen: set[int] = set()

    def visit(item: Any) -> None:
        item_id = id(item)
        if item_id in seen:
            raise ValueError(f"{field_name} contains protected material")
        if isinstance(item, (dict, list, tuple, set, frozenset)):
            seen.add(item_id)
        if isinstance(item, Mapping):
            for key, child in item.items():
                key_text = str(key).lower()
                if any(marker in key_text for marker in _PROTECTED_KEY_MARKERS):
                    raise ValueError(f"{field_name} contains protected material")
                visit(child)
        elif isinstance(item, (list, tuple, set, frozenset)):
            for child in item:
                visit(child)
        elif isinstance(item, str):
            lowered = item.lower()
            if any(marker in lowered for marker in _PROTECTED_VALUE_MARKERS):
                raise ValueError(f"{field_name} contains protected material")
            reject_protected_material(item, field_name)
        elif isinstance(item, BaseException):
            raise ValueError(f"{field_name} contains protected material")
        elif callable(item):
            raise ValueError(f"{field_name} contains protected material")

    visit(value)


def validate_verified_knowledge_reason_codes(values: tuple[str, ...]) -> tuple[str, ...]:
    """Validate immutable ordered verified-knowledge reason codes."""

    if len(values) > MAXIMUM_REASON_CODES_PER_CANDIDATE:
        raise ValueError("too many verified knowledge reason codes")
    seen: set[str] = set()
    for code in values:
        if code not in _REASON_CODE_SET:
            raise ValueError("unknown verified knowledge reason code")
        if code in seen:
            raise ValueError("duplicate verified knowledge reason code")
        if not _REASON_CODE_RE.fullmatch(code):
            raise ValueError("invalid verified knowledge reason code")
        seen.add(code)
    return values


def quantize_confidence(value: Decimal | int | str | float) -> Decimal:
    """Quantize a confidence or coverage value to six decimal places."""

    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("confidence value must be finite")
        value = str(value)
    try:
        decimal = Decimal(value)
    except (InvalidOperation, TypeError) as exc:
        raise ValueError("confidence value must be decimal-compatible") from exc
    if decimal.is_nan() or decimal.is_infinite():
        raise ValueError("confidence value must be finite")
    if decimal < ZERO or decimal > ONE:
        raise ValueError("confidence value must be between zero and one")
    return decimal.quantize(QUANT, rounding=ROUND_HALF_UP)


def verified_knowledge_fingerprint(payload: BaseModel | Mapping[str, object]) -> str:
    """Return a stable fingerprint for verified-knowledge JSON-compatible payloads."""

    if isinstance(payload, BaseModel):
        return fingerprint_payload(payload.model_dump(mode="json"))
    return fingerprint_payload(_json_ready(dict(payload)))


def candidate_identity_id(
    *,
    candidate_kind: VerifiedKnowledgeCandidateKind,
    claim_identity_fingerprint: str,
    target_valid_time_fingerprint: str,
    jurisdiction_scope_fingerprint: str,
    version_scope_fingerprint: str,
) -> str:
    """Derive a stable candidate identity from claim and scope identity."""

    for value in (
        claim_identity_fingerprint,
        target_valid_time_fingerprint,
        jurisdiction_scope_fingerprint,
        version_scope_fingerprint,
    ):
        validate_hex64(value, "candidate identity fingerprint input")
    digest = verified_knowledge_fingerprint(
        {
            "candidate_kind": candidate_kind.value,
            "claim_identity_fingerprint": claim_identity_fingerprint,
            "target_valid_time_fingerprint": target_valid_time_fingerprint,
            "jurisdiction_scope_fingerprint": jurisdiction_scope_fingerprint,
            "version_scope_fingerprint": version_scope_fingerprint,
        }
    )
    return f"candidate-identity-{digest[:48]}"


def _json_ready(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        encoded = ensure_utc(value).isoformat()
        return f"{encoded[:-6]}Z" if encoded.endswith("+00:00") else encoded
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, tuple | list):
        return [_json_ready(item) for item in value]
    return value


def _fingerprint_model(model: BaseModel, exclude: set[str]) -> str:
    payload = model.model_dump(mode="json", exclude=exclude)
    return verified_knowledge_fingerprint(payload)


def _validate_safe_id(value: str, field_name: str) -> str:
    reject_verified_knowledge_payload(value, field_name)
    return validate_safe_identifier(value, field_name)


def _validate_safe_ids(values: tuple[str, ...], field_name: str) -> tuple[str, ...]:
    seen: set[str] = set()
    for value in values:
        _validate_safe_id(value, field_name)
        if value in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(value)
    return values


def _validate_hexes(values: tuple[str, ...], field_name: str) -> tuple[str, ...]:
    seen: set[str] = set()
    for value in values:
        validate_hex64(value, field_name)
        if value in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(value)
    return values


def _validate_utc_optional(value: datetime | None, field_name: str) -> datetime | None:
    if value is None:
        return None
    return ensure_utc(value, field_name)


def _values_are_sorted(values: tuple[str, ...], field_name: str) -> tuple[str, ...]:
    if values != tuple(sorted(values)):
        raise ValueError(f"{field_name} must use deterministic ordering")
    return values


class IntegratedKnowledgeLineage(BaseModel):
    """Complete upstream lineage for a reviewable verified-knowledge candidate."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal[
        "aion-knowledge-integrated-lineage/v1"
    ] = INTEGRATED_KNOWLEDGE_LINEAGE_SCHEMA_VERSION
    program_id: Literal["AION-KNOWLEDGE-INTELLIGENCE-001"] = PROGRAM_ID
    authorization_transaction_id: Literal["AION-216-KI-0007"] = (
        AUTHORIZATION_TRANSACTION_ID
    )
    lineage_id: str
    research_plan_id: str
    research_plan_fingerprint: str
    acquisition_result_fingerprint: str
    source_snapshot_ids: tuple[str, ...]
    source_snapshot_fingerprints: tuple[str, ...]
    source_provenance_ids: tuple[str, ...]
    source_provenance_fingerprints: tuple[str, ...]
    citation_reference_ids: tuple[str, ...]
    citation_reference_fingerprints: tuple[str, ...]
    source_registry_integrity_fingerprint: str
    claim_id: str
    claim_identity_fingerprint: str
    claim_version_id: str
    claim_graph_integrity_fingerprint: str
    assessment_id: str
    assessment_fingerprint: str
    assessment_status: EpistemicAssessmentStatus
    assessment_confidence: Decimal
    assessment_hard_cap: Decimal
    domain_mesh_session_id: str
    domain_mesh_session_fingerprint: str
    synthesis_id: str
    synthesis_fingerprint: str
    synthesis_confidence_cap: Decimal
    tool_verification_session_ids: tuple[str, ...] = ()
    tool_verification_session_fingerprints: tuple[str, ...] = ()
    attestation_chain_head_fingerprints: tuple[str, ...] = ()
    tool_evidence_confidence_caps: tuple[Decimal, ...] = ()
    source_independence_group_ids: tuple[str, ...]
    target_valid_time_fingerprint: str
    jurisdiction_scope_fingerprint: str
    version_scope_fingerprint: str
    lineage_reference_count: int = Field(ge=0, le=MAXIMUM_LINEAGE_REFERENCES_PER_CANDIDATE)
    lineage_fingerprint: str
    synthetic: bool = True
    read_only: Literal[True] = True
    redacted: Literal[True] = True
    runtime_effect: Literal[False] = False

    @field_validator(
        "lineage_id",
        "research_plan_id",
        "claim_id",
        "claim_version_id",
        "assessment_id",
        "domain_mesh_session_id",
        "synthesis_id",
    )
    @classmethod
    def ids_are_safe(cls, value: str) -> str:
        return _validate_safe_id(value, "integrated lineage id")

    @field_validator(
        "research_plan_fingerprint",
        "acquisition_result_fingerprint",
        "source_registry_integrity_fingerprint",
        "claim_identity_fingerprint",
        "claim_graph_integrity_fingerprint",
        "assessment_fingerprint",
        "domain_mesh_session_fingerprint",
        "synthesis_fingerprint",
        "target_valid_time_fingerprint",
        "jurisdiction_scope_fingerprint",
        "version_scope_fingerprint",
        "lineage_fingerprint",
    )
    @classmethod
    def hashes_are_hex(cls, value: str) -> str:
        return validate_hex64(value, "integrated lineage fingerprint")

    @field_validator(
        "source_snapshot_ids",
        "source_provenance_ids",
        "citation_reference_ids",
        "tool_verification_session_ids",
        "source_independence_group_ids",
    )
    @classmethod
    def tuples_are_safe_sorted(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return _values_are_sorted(_validate_safe_ids(value, "lineage reference"), "lineage")

    @field_validator(
        "source_snapshot_fingerprints",
        "source_provenance_fingerprints",
        "citation_reference_fingerprints",
        "tool_verification_session_fingerprints",
        "attestation_chain_head_fingerprints",
    )
    @classmethod
    def tuple_hashes_are_hex(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return _values_are_sorted(
            _validate_hexes(value, "integrated lineage tuple fingerprint"),
            "lineage fingerprints",
        )

    @field_validator(
        "assessment_confidence",
        "assessment_hard_cap",
        "synthesis_confidence_cap",
        mode="before",
    )
    @classmethod
    def scores_are_quantized(cls, value: Decimal | int | str | float) -> Decimal:
        return quantize_confidence(value)

    @field_validator("tool_evidence_confidence_caps", mode="before")
    @classmethod
    def tool_caps_are_quantized(cls, value: Any) -> tuple[Decimal, ...]:
        return tuple(quantize_confidence(item) for item in tuple(value or ()))

    @model_validator(mode="after")
    def validate_reference_integrity(self) -> Self:
        pairs = (
            (self.source_snapshot_ids, self.source_snapshot_fingerprints),
            (self.source_provenance_ids, self.source_provenance_fingerprints),
            (self.citation_reference_ids, self.citation_reference_fingerprints),
            (self.tool_verification_session_ids, self.tool_verification_session_fingerprints),
        )
        for ids, fingerprints in pairs:
            if len(ids) != len(fingerprints):
                raise ValueError("lineage reference fingerprint mismatch")
        source_registry_refs = (
            len(self.source_snapshot_ids)
            + len(self.source_provenance_ids)
            + len(self.citation_reference_ids)
        )
        if source_registry_refs > MAXIMUM_SOURCE_REGISTRY_REFERENCES_PER_CANDIDATE:
            raise ValueError("source registry reference limit exceeded")
        if len(self.tool_verification_session_ids) > MAXIMUM_TOOL_SESSION_REFERENCES_PER_CANDIDATE:
            raise ValueError("tool session reference limit exceeded")
        if len(self.tool_evidence_confidence_caps) != len(self.tool_verification_session_ids):
            raise ValueError("tool evidence cap reference mismatch")
        reference_count = (
            source_registry_refs
            + 1
            + 1
            + 1
            + len(self.tool_verification_session_ids)
            + len(self.attestation_chain_head_fingerprints)
            + len(self.source_independence_group_ids)
        )
        if self.lineage_reference_count != reference_count:
            raise ValueError("lineage reference count mismatch")
        expected = _fingerprint_model(self, {"lineage_fingerprint"})
        if self.lineage_fingerprint != expected:
            raise ValueError("lineage fingerprint mismatch")
        return self


class VerifiedKnowledgeCandidateEligibilityInput(BaseModel):
    """Explicit eligibility input; no integrity result silently defaults to true."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal[
        "aion-knowledge-verified-candidate-eligibility/v1"
    ] = VERIFIED_KNOWLEDGE_ELIGIBILITY_SCHEMA_VERSION
    candidate_kind: VerifiedKnowledgeCandidateKind
    integrated_lineage: IntegratedKnowledgeLineage
    source_registry_integrity_passed: bool
    claim_graph_integrity_passed: bool
    epistemic_assessment_integrity_passed: bool
    domain_mesh_integrity_passed: bool
    tool_verification_integrity_passed: bool
    assessment_status: EpistemicAssessmentStatus
    assessment_explicit_abstention: bool
    assessment_confidence: Decimal
    assessment_hard_cap: Decimal
    independent_support_count: int = Field(ge=0)
    independent_opposition_count: int = Field(ge=0)
    evidence_coverage: Decimal
    citation_coverage: Decimal
    provenance_completeness: Decimal
    freshness_status: FreshnessStatus
    scope_applicability_status: ScopeApplicability
    contradiction_status: ContradictionStatus
    retraction_applicable: bool
    supersession_applicable: bool
    current_evidence_after_supersession: bool
    unresolved_material_support_conflict: bool
    unresolved_material_opposition_conflict: bool
    required_mesh_roles_complete: bool
    unresolved_material_dissent: bool
    required_report_confidence_caps: tuple[Decimal, ...]
    synthesis_explicit_abstention: bool
    synthesis_confidence_cap: Decimal
    tool_verification_session_count: int = Field(
        ge=0,
        le=MAXIMUM_TOOL_SESSION_REFERENCES_PER_CANDIDATE,
    )
    tool_verification_statuses: tuple[str, ...] = ()
    tool_evidence_confidence_caps: tuple[Decimal, ...] = ()
    tool_attestation_chains_valid: bool
    actual_tool_executed: bool
    tool_output_used_as_fact: Literal[False] = False
    engagement_signal_count: int = Field(ge=0)
    engagement_used_as_fact: Literal[False] = False
    engagement_confidence_effect: Literal[False] = False

    @field_validator(
        "assessment_confidence",
        "assessment_hard_cap",
        "evidence_coverage",
        "citation_coverage",
        "provenance_completeness",
        "synthesis_confidence_cap",
        mode="before",
    )
    @classmethod
    def decimals_are_quantized(cls, value: Decimal | int | str | float) -> Decimal:
        return quantize_confidence(value)

    @field_validator(
        "required_report_confidence_caps",
        "tool_evidence_confidence_caps",
        mode="before",
    )
    @classmethod
    def caps_are_quantized(cls, value: Any) -> tuple[Decimal, ...]:
        return tuple(quantize_confidence(item) for item in tuple(value or ()))

    @field_validator("tool_verification_statuses")
    @classmethod
    def statuses_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return _validate_safe_ids(value, "tool verification status")

    @model_validator(mode="after")
    def validate_explicit_binding(self) -> Self:
        if self.assessment_status != self.integrated_lineage.assessment_status:
            raise ValueError("eligibility input assessment status mismatch")
        if self.assessment_confidence != self.integrated_lineage.assessment_confidence:
            raise ValueError("eligibility input assessment confidence mismatch")
        if self.assessment_hard_cap != self.integrated_lineage.assessment_hard_cap:
            raise ValueError("eligibility input assessment hard cap mismatch")
        if self.synthesis_confidence_cap != self.integrated_lineage.synthesis_confidence_cap:
            raise ValueError("eligibility input synthesis confidence cap mismatch")
        if self.tool_verification_session_count != len(
            self.integrated_lineage.tool_verification_session_ids
        ):
            raise ValueError("tool verification session count mismatch")
        if (
            self.tool_evidence_confidence_caps
            != self.integrated_lineage.tool_evidence_confidence_caps
        ):
            raise ValueError("tool evidence confidence cap mismatch")
        if self.engagement_signal_count > MAXIMUM_ENGAGEMENT_SIGNALS_PER_BATCH:
            raise ValueError("engagement signal count exceeds batch limit")
        return self


class VerifiedKnowledgeEligibilityDecision(BaseModel):
    """Eligibility decision for operator review; never approval or promotion."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal[
        "aion-knowledge-verified-candidate-eligibility/v1"
    ] = VERIFIED_KNOWLEDGE_ELIGIBILITY_SCHEMA_VERSION
    candidate_kind: VerifiedKnowledgeCandidateKind
    status: VerifiedKnowledgeEligibilityStatus
    eligible: bool
    candidate_confidence_cap: Decimal
    operator_review_required: Literal[True] = True
    automatic_promotion: Literal[False] = False
    verified_knowledge_created: Literal[False] = False
    cognitive_memory_written: Literal[False] = False
    belief_mutated: Literal[False] = False
    reason_codes: tuple[str, ...]
    decision_fingerprint: str
    runtime_effect: Literal[False] = False

    @field_validator("candidate_confidence_cap", mode="before")
    @classmethod
    def cap_is_quantized(cls, value: Decimal | int | str | float) -> Decimal:
        return quantize_confidence(value)

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_are_valid(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_verified_knowledge_reason_codes(value)

    @field_validator("decision_fingerprint")
    @classmethod
    def fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "decision fingerprint")

    @model_validator(mode="after")
    def fingerprint_matches(self) -> Self:
        expected = _fingerprint_model(self, {"decision_fingerprint"})
        if self.decision_fingerprint != expected:
            raise ValueError("eligibility decision fingerprint mismatch")
        return self


class VerifiedKnowledgeCandidate(BaseModel):
    """Immutable reviewable candidate; not factual truth."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal[
        "aion-knowledge-verified-candidate/v1"
    ] = VERIFIED_KNOWLEDGE_CANDIDATE_SCHEMA_VERSION
    candidate_id: str
    candidate_identity_id: str
    candidate_kind: VerifiedKnowledgeCandidateKind
    claim_id: str
    claim_identity_fingerprint: str
    integrated_lineage: IntegratedKnowledgeLineage
    eligibility_decision: VerifiedKnowledgeEligibilityDecision
    assessment_id: str
    assessment_status: EpistemicAssessmentStatus
    assessment_confidence: Decimal
    assessment_confidence_band: ConfidenceBand
    assessment_hard_cap: Decimal
    independent_support_count: int = Field(ge=0)
    independent_opposition_count: int = Field(ge=0)
    evidence_coverage: Decimal
    citation_coverage: Decimal
    provenance_completeness: Decimal
    freshness_status: FreshnessStatus
    scope_applicability_status: ScopeApplicability
    contradiction_status: ContradictionStatus
    mesh_session_id: str
    synthesis_id: str
    synthesis_fingerprint: str
    synthesis_confidence_cap: Decimal
    unresolved_dissent_ids: tuple[str, ...] = ()
    tool_verification_session_ids: tuple[str, ...] = ()
    attestation_chain_head_fingerprints: tuple[str, ...] = ()
    candidate_confidence_cap: Decimal
    lifecycle_status: VerifiedKnowledgeLifecycleStatus
    candidate_version: int = Field(ge=1, le=MAXIMUM_CANDIDATE_VERSIONS_PER_IDENTITY)
    supersedes_candidate_version_id: str | None = None
    created_at: datetime
    expires_at: datetime | None
    revalidation_due_at: datetime | None
    reason_codes: tuple[str, ...]
    candidate_fingerprint: str
    synthetic: bool = True
    read_only: Literal[True] = True
    redacted: Literal[True] = True
    operator_review_required: Literal[True] = True
    automatic_promotion: Literal[False] = False
    verified_knowledge_created: Literal[False] = False
    persistent_write_applied: Literal[False] = False
    cognitive_memory_written: Literal[False] = False
    belief_mutated: Literal[False] = False
    runtime_effect: Literal[False] = False

    @field_validator(
        "candidate_id",
        "candidate_identity_id",
        "claim_id",
        "assessment_id",
        "mesh_session_id",
        "synthesis_id",
    )
    @classmethod
    def ids_are_safe(cls, value: str) -> str:
        return _validate_safe_id(value, "verified knowledge candidate id")

    @field_validator(
        "claim_identity_fingerprint",
        "synthesis_fingerprint",
        "candidate_fingerprint",
    )
    @classmethod
    def hashes_are_hex(cls, value: str) -> str:
        return validate_hex64(value, "verified knowledge candidate fingerprint")

    @field_validator(
        "assessment_confidence",
        "assessment_hard_cap",
        "evidence_coverage",
        "citation_coverage",
        "provenance_completeness",
        "synthesis_confidence_cap",
        "candidate_confidence_cap",
        mode="before",
    )
    @classmethod
    def decimals_are_quantized(cls, value: Decimal | int | str | float) -> Decimal:
        return quantize_confidence(value)

    @field_validator("unresolved_dissent_ids", "tool_verification_session_ids")
    @classmethod
    def tuple_ids_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return _values_are_sorted(
            _validate_safe_ids(value, "candidate tuple id"),
            "candidate tuple ids",
        )

    @field_validator("attestation_chain_head_fingerprints")
    @classmethod
    def tuple_hashes_are_hex(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return _values_are_sorted(
            _validate_hexes(value, "candidate attestation fingerprint"),
            "candidate attestation fingerprints",
        )

    @field_validator("created_at")
    @classmethod
    def created_at_is_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value, "candidate created_at")

    @field_validator("expires_at", "revalidation_due_at")
    @classmethod
    def optional_times_are_utc(cls, value: datetime | None) -> datetime | None:
        return _validate_utc_optional(value, "candidate optional timestamp")

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_are_valid(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_verified_knowledge_reason_codes(value)

    @model_validator(mode="after")
    def validate_candidate_binding(self) -> Self:
        lineage = self.integrated_lineage
        expected_identity = candidate_identity_id(
            candidate_kind=self.candidate_kind,
            claim_identity_fingerprint=self.claim_identity_fingerprint,
            target_valid_time_fingerprint=lineage.target_valid_time_fingerprint,
            jurisdiction_scope_fingerprint=lineage.jurisdiction_scope_fingerprint,
            version_scope_fingerprint=lineage.version_scope_fingerprint,
        )
        if self.candidate_identity_id != expected_identity:
            raise ValueError("candidate identity mismatch")
        if self.claim_id != lineage.claim_id:
            raise ValueError("candidate claim mismatch")
        if self.claim_identity_fingerprint != lineage.claim_identity_fingerprint:
            raise ValueError("candidate claim identity mismatch")
        if self.assessment_id != lineage.assessment_id:
            raise ValueError("candidate assessment mismatch")
        if self.mesh_session_id != lineage.domain_mesh_session_id:
            raise ValueError("candidate mesh session mismatch")
        if self.synthesis_id != lineage.synthesis_id:
            raise ValueError("candidate synthesis mismatch")
        if self.synthesis_fingerprint != lineage.synthesis_fingerprint:
            raise ValueError("candidate synthesis fingerprint mismatch")
        if self.tool_verification_session_ids != lineage.tool_verification_session_ids:
            raise ValueError("candidate tool session mismatch")
        if self.attestation_chain_head_fingerprints != lineage.attestation_chain_head_fingerprints:
            raise ValueError("candidate attestation mismatch")
        if self.candidate_confidence_cap != self.eligibility_decision.candidate_confidence_cap:
            raise ValueError("candidate confidence cap mismatch")
        if self.candidate_confidence_cap > self.assessment_confidence:
            raise ValueError("candidate confidence amplification detected")
        expected = _fingerprint_model(self, {"candidate_fingerprint"})
        if self.candidate_fingerprint != expected:
            raise ValueError("candidate fingerprint mismatch")
        return self


class VerifiedKnowledgeCandidateVersion(BaseModel):
    """Immutable candidate version record."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal[
        "aion-knowledge-verified-candidate-version/v1"
    ] = VERIFIED_KNOWLEDGE_VERSION_SCHEMA_VERSION
    candidate_version_id: str
    candidate_identity_id: str
    candidate_id: str
    version_number: int = Field(ge=1, le=MAXIMUM_CANDIDATE_VERSIONS_PER_IDENTITY)
    version_reason: VerifiedKnowledgeVersionReason
    candidate: VerifiedKnowledgeCandidate
    previous_candidate_version_id: str | None = None
    supersedes_candidate_version_id: str | None = None
    created_at: datetime
    version_fingerprint: str
    persistent_write_applied: Literal[False] = False
    cognitive_memory_written: Literal[False] = False
    belief_mutated: Literal[False] = False
    runtime_effect: Literal[False] = False

    @field_validator(
        "candidate_version_id",
        "candidate_identity_id",
        "candidate_id",
        "previous_candidate_version_id",
        "supersedes_candidate_version_id",
    )
    @classmethod
    def ids_are_safe(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _validate_safe_id(value, "candidate version id")

    @field_validator("created_at")
    @classmethod
    def created_at_is_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value, "candidate version created_at")

    @field_validator("version_fingerprint")
    @classmethod
    def fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "candidate version fingerprint")

    @model_validator(mode="after")
    def validate_version_binding(self) -> Self:
        if self.candidate_identity_id != self.candidate.candidate_identity_id:
            raise ValueError("candidate version identity mismatch")
        if self.candidate_id != self.candidate.candidate_id:
            raise ValueError("candidate version candidate mismatch")
        if self.version_number != self.candidate.candidate_version:
            raise ValueError("candidate version number mismatch")
        expected = _fingerprint_model(self, {"version_fingerprint"})
        if self.version_fingerprint != expected:
            raise ValueError("candidate version fingerprint mismatch")
        return self


class VerifiedKnowledgeCandidateHistory(BaseModel):
    """Append-only candidate history for one candidate identity."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal[
        "aion-knowledge-verified-candidate-version/v1"
    ] = VERIFIED_KNOWLEDGE_VERSION_SCHEMA_VERSION
    candidate_identity_id: str
    versions: tuple[VerifiedKnowledgeCandidateVersion, ...]
    latest_candidate_version_id: str
    version_count: int = Field(ge=0, le=MAXIMUM_CANDIDATE_VERSIONS_PER_IDENTITY)
    history_fingerprint: str
    persistent_write_applied: Literal[False] = False
    runtime_effect: Literal[False] = False

    @field_validator("candidate_identity_id", "latest_candidate_version_id")
    @classmethod
    def ids_are_safe(cls, value: str) -> str:
        return _validate_safe_id(value, "candidate history id")

    @field_validator("history_fingerprint")
    @classmethod
    def fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "candidate history fingerprint")

    @model_validator(mode="after")
    def validate_history(self) -> Self:
        if self.version_count != len(self.versions):
            raise ValueError("candidate history count mismatch")
        expected_numbers = tuple(range(1, len(self.versions) + 1))
        actual_numbers = tuple(version.version_number for version in self.versions)
        if actual_numbers != expected_numbers:
            raise ValueError("candidate history versions must be contiguous")
        if any(
            version.candidate_identity_id != self.candidate_identity_id
            for version in self.versions
        ):
            raise ValueError("candidate history identity mismatch")
        if (
            self.versions
            and self.latest_candidate_version_id != self.versions[-1].candidate_version_id
        ):
            raise ValueError("candidate history latest version mismatch")
        expected = _fingerprint_model(self, {"history_fingerprint"})
        if self.history_fingerprint != expected:
            raise ValueError("candidate history fingerprint mismatch")
        return self


class VerifiedKnowledgeRevalidationRequest(BaseModel):
    """Explicit operator-invoked revalidation request."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal[
        "aion-knowledge-verified-revalidation/v1"
    ] = VERIFIED_KNOWLEDGE_REVALIDATION_SCHEMA_VERSION
    request_id: str
    candidate_version_id: str
    triggers: tuple[VerifiedKnowledgeRevalidationTrigger, ...]
    requested_at: datetime
    operator_invoked: Literal[True] = True
    scheduler_invoked: Literal[False] = False
    background_worker_invoked: Literal[False] = False
    persistent_write_applied: Literal[False] = False
    approval_created: Literal[False] = False
    knowledge_created: Literal[False] = False
    cognitive_memory_written: Literal[False] = False
    belief_mutated: Literal[False] = False
    runtime_effect: Literal[False] = False

    @field_validator("request_id", "candidate_version_id")
    @classmethod
    def ids_are_safe(cls, value: str) -> str:
        return _validate_safe_id(value, "revalidation id")

    @field_validator("requested_at")
    @classmethod
    def requested_at_is_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value, "revalidation requested_at")

    @model_validator(mode="after")
    def validate_triggers(self) -> Self:
        if not self.triggers:
            raise ValueError("revalidation requires explicit trigger")
        if len(set(self.triggers)) != len(self.triggers):
            raise ValueError("revalidation trigger duplicate")
        return self


class VerifiedKnowledgeRevalidationResult(BaseModel):
    """Revalidation result that preserves prior version and creates no knowledge."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal[
        "aion-knowledge-verified-revalidation/v1"
    ] = VERIFIED_KNOWLEDGE_REVALIDATION_SCHEMA_VERSION
    request: VerifiedKnowledgeRevalidationRequest
    prior_candidate_version: VerifiedKnowledgeCandidateVersion
    new_candidate_version: VerifiedKnowledgeCandidateVersion
    eligibility_decision: VerifiedKnowledgeEligibilityDecision
    lineage_revalidated: bool
    confidence_recomputed_from_scratch: Literal[True] = True
    carry_forward_blocked: bool
    approval_created: Literal[False] = False
    verified_knowledge_created: Literal[False] = False
    persistent_write_applied: Literal[False] = False
    cognitive_memory_written: Literal[False] = False
    belief_mutated: Literal[False] = False
    result_fingerprint: str
    runtime_effect: Literal[False] = False

    @field_validator("result_fingerprint")
    @classmethod
    def fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "revalidation result fingerprint")

    @model_validator(mode="after")
    def validate_result(self) -> Self:
        if self.new_candidate_version.version_number < self.prior_candidate_version.version_number:
            raise ValueError("revalidation version cannot go backward")
        expected = _fingerprint_model(self, {"result_fingerprint"})
        if self.result_fingerprint != expected:
            raise ValueError("revalidation result fingerprint mismatch")
        return self


class VerifiedKnowledgeCandidateBatch(BaseModel):
    """Bounded deterministic candidate batch."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal[
        "aion-knowledge-verified-candidate-batch/v1"
    ] = VERIFIED_KNOWLEDGE_BATCH_SCHEMA_VERSION
    batch_id: str
    candidates: tuple[VerifiedKnowledgeCandidate, ...]
    candidate_count: int = Field(ge=0, le=MAXIMUM_CANDIDATES_PER_BATCH)
    batch_fingerprint: str
    persistent_write_applied: Literal[False] = False
    runtime_effect: Literal[False] = False

    @field_validator("batch_id")
    @classmethod
    def batch_id_is_safe(cls, value: str) -> str:
        return _validate_safe_id(value, "candidate batch id")

    @field_validator("batch_fingerprint")
    @classmethod
    def fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "candidate batch fingerprint")

    @model_validator(mode="after")
    def validate_batch(self) -> Self:
        ids = tuple(candidate.candidate_id for candidate in self.candidates)
        if self.candidate_count != len(ids):
            raise ValueError("candidate batch count mismatch")
        if len(set(ids)) != len(ids):
            raise ValueError("candidate batch duplicate candidate")
        if ids != tuple(sorted(ids)):
            raise ValueError("candidate batch must be deterministically ordered")
        expected = _fingerprint_model(self, {"batch_fingerprint"})
        if self.batch_fingerprint != expected:
            raise ValueError("candidate batch fingerprint mismatch")
        return self


class VerifiedKnowledgeCandidateMemorySnapshot(BaseModel):
    """Deterministic immutable memory snapshot; not persistence."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal[
        "aion-knowledge-verified-memory-snapshot/v1"
    ] = VERIFIED_KNOWLEDGE_MEMORY_SNAPSHOT_SCHEMA_VERSION
    snapshot_id: str
    authorization_transaction_id: Literal["AION-216-KI-0007"] = (
        AUTHORIZATION_TRANSACTION_ID
    )
    candidate_ids: tuple[str, ...]
    candidate_identity_ids: tuple[str, ...]
    latest_version_ids: tuple[str, ...]
    candidate_count: int = Field(ge=0)
    eligible_candidate_count: int = Field(ge=0)
    ineligible_candidate_count: int = Field(ge=0)
    revalidation_required_count: int = Field(ge=0)
    support_candidate_count: int = Field(ge=0)
    refutation_candidate_count: int = Field(ge=0)
    created_at: datetime
    snapshot_fingerprint: str
    synthetic: bool = True
    read_only: Literal[True] = True
    redacted: Literal[True] = True
    persistent_write_applied: Literal[False] = False
    runtime_effect: Literal[False] = False

    @field_validator("snapshot_id")
    @classmethod
    def snapshot_id_is_safe(cls, value: str) -> str:
        return _validate_safe_id(value, "memory snapshot id")

    @field_validator("candidate_ids", "candidate_identity_ids", "latest_version_ids")
    @classmethod
    def ids_are_safe_sorted(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return _values_are_sorted(
            _validate_safe_ids(value, "memory snapshot id"),
            "memory snapshot ids",
        )

    @field_validator("created_at")
    @classmethod
    def created_at_is_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value, "memory snapshot created_at")

    @field_validator("snapshot_fingerprint")
    @classmethod
    def fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "memory snapshot fingerprint")

    @model_validator(mode="after")
    def validate_snapshot(self) -> Self:
        if self.candidate_count != len(self.candidate_ids):
            raise ValueError("memory snapshot candidate count mismatch")
        if len(self.candidate_identity_ids) != self.candidate_count:
            raise ValueError("memory snapshot identity count mismatch")
        if len(self.latest_version_ids) != self.candidate_count:
            raise ValueError("memory snapshot version count mismatch")
        counted = self.eligible_candidate_count + self.ineligible_candidate_count
        if counted != self.candidate_count:
            raise ValueError("memory snapshot eligibility count mismatch")
        expected = _fingerprint_model(self, {"snapshot_fingerprint"})
        if self.snapshot_fingerprint != expected:
            raise ValueError("memory snapshot fingerprint mismatch")
        return self


class VerifiedKnowledgeCandidateQuery(BaseModel):
    """Bounded exact query; no search or engagement ranking."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal[
        "aion-knowledge-verified-query/v1"
    ] = VERIFIED_KNOWLEDGE_QUERY_SCHEMA_VERSION
    candidate_id: str | None = None
    candidate_identity_id: str | None = None
    candidate_kind: VerifiedKnowledgeCandidateKind | None = None
    claim_id: str | None = None
    assessment_id: str | None = None
    mesh_session_id: str | None = None
    synthesis_id: str | None = None
    tool_verification_session_id: str | None = None
    eligibility_status: VerifiedKnowledgeEligibilityStatus | None = None
    lifecycle_status: VerifiedKnowledgeLifecycleStatus | None = None
    operator_review_required: bool | None = None
    revalidation_due: bool | None = None
    expired: bool | None = None
    minimum_version: int | None = Field(default=None, ge=1)
    maximum_version: int | None = Field(default=None, ge=1)
    limit: int = Field(default=MAXIMUM_QUERY_RESULTS, ge=1, le=MAXIMUM_QUERY_RESULTS)

    @field_validator(
        "candidate_id",
        "candidate_identity_id",
        "claim_id",
        "assessment_id",
        "mesh_session_id",
        "synthesis_id",
        "tool_verification_session_id",
    )
    @classmethod
    def optional_ids_are_safe(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _validate_safe_id(value, "query id")

    @model_validator(mode="after")
    def validate_version_range(self) -> Self:
        if (
            self.minimum_version is not None
            and self.maximum_version is not None
            and self.minimum_version > self.maximum_version
        ):
            raise ValueError("query version range invalid")
        return self


class VerifiedKnowledgeCandidateQueryResult(BaseModel):
    """Deterministic exact query result."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal[
        "aion-knowledge-verified-query-result/v1"
    ] = VERIFIED_KNOWLEDGE_QUERY_RESULT_SCHEMA_VERSION
    query: VerifiedKnowledgeCandidateQuery
    candidates: tuple[VerifiedKnowledgeCandidate, ...]
    result_count: int = Field(ge=0, le=MAXIMUM_QUERY_RESULTS)
    query_result_fingerprint: str
    semantic_search_used: Literal[False] = False
    engagement_ranking_used: Literal[False] = False
    popularity_ranking_used: Literal[False] = False
    runtime_effect: Literal[False] = False

    @field_validator("query_result_fingerprint")
    @classmethod
    def fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "query result fingerprint")

    @model_validator(mode="after")
    def validate_query_result(self) -> Self:
        ids = tuple(candidate.candidate_id for candidate in self.candidates)
        if self.result_count != len(ids):
            raise ValueError("query result count mismatch")
        if ids != tuple(sorted(ids)):
            raise ValueError("query result order must be deterministic")
        expected = _fingerprint_model(self, {"query_result_fingerprint"})
        if self.query_result_fingerprint != expected:
            raise ValueError("query result fingerprint mismatch")
        return self


class VerifiedKnowledgeFixtureEnvelope(BaseModel):
    """Explicit synthetic local fixture envelope."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal[
        "aion-knowledge-verified-fixture/v1"
    ] = VERIFIED_KNOWLEDGE_FIXTURE_SCHEMA_VERSION
    fixture_id: str
    fixture_records: tuple[Mapping[str, object], ...]
    fixture_record_count: int = Field(ge=0, le=MAXIMUM_FIXTURE_RECORDS)
    fixture_fingerprint: str
    synthetic: Literal[True] = True
    read_only: Literal[True] = True
    redacted: Literal[True] = True
    runtime_effect: Literal[False] = False

    @field_validator("fixture_id")
    @classmethod
    def fixture_id_is_safe(cls, value: str) -> str:
        return _validate_safe_id(value, "fixture id")

    @field_validator("fixture_records")
    @classmethod
    def fixture_records_are_safe(
        cls, value: tuple[Mapping[str, object], ...]
    ) -> tuple[Mapping[str, object], ...]:
        reject_verified_knowledge_payload(value, "fixture records")
        return value

    @field_validator("fixture_fingerprint")
    @classmethod
    def fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "fixture fingerprint")

    @model_validator(mode="after")
    def validate_fixture(self) -> Self:
        if self.fixture_record_count != len(self.fixture_records):
            raise ValueError("fixture record count mismatch")
        expected = _fingerprint_model(self, {"fixture_fingerprint"})
        if self.fixture_fingerprint != expected:
            raise ValueError("fixture fingerprint mismatch")
        return self


class EngagementSignalMetadata(BaseModel):
    """Bounded engagement metadata with no factual effect."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal[
        "aion-knowledge-engagement-signal/v1"
    ] = ENGAGEMENT_SIGNAL_SCHEMA_VERSION
    signal_id: str
    signal_kind: EngagementSignalKind
    session_fingerprint: str
    response_fingerprint: str
    subject_fingerprint: str
    bounded_outcome_code: str
    metadata_codes: tuple[str, ...] = ()
    occurred_at: datetime
    signal_fingerprint: str
    factual_effect: Literal[False] = False
    confidence_effect: Literal[False] = False
    source_independence_effect: Literal[False] = False
    citation_coverage_effect: Literal[False] = False
    provenance_effect: Literal[False] = False
    contradiction_resolution_effect: Literal[False] = False
    freshness_effect: Literal[False] = False
    knowledge_effect: Literal[False] = False
    cognitive_memory_effect: Literal[False] = False
    belief_effect: Literal[False] = False
    model_weight_effect: Literal[False] = False
    runtime_effect: Literal[False] = False

    @field_validator("signal_id", "bounded_outcome_code")
    @classmethod
    def ids_are_safe(cls, value: str) -> str:
        return _validate_safe_id(value, "engagement signal id")

    @field_validator("metadata_codes")
    @classmethod
    def metadata_codes_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return _values_are_sorted(
            _validate_safe_ids(value, "engagement metadata code"),
            "engagement metadata codes",
        )

    @field_validator(
        "session_fingerprint",
        "response_fingerprint",
        "subject_fingerprint",
        "signal_fingerprint",
    )
    @classmethod
    def hashes_are_hex(cls, value: str) -> str:
        return validate_hex64(value, "engagement signal fingerprint")

    @field_validator("occurred_at")
    @classmethod
    def occurred_at_is_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value, "engagement occurred_at")

    @model_validator(mode="after")
    def validate_signal(self) -> Self:
        expected = _fingerprint_model(self, {"signal_fingerprint"})
        if self.signal_fingerprint != expected:
            raise ValueError("engagement signal fingerprint mismatch")
        return self


class EngagementSignalBatch(BaseModel):
    """Deterministic bounded engagement-signal batch."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal[
        "aion-knowledge-engagement-signal-batch/v1"
    ] = ENGAGEMENT_SIGNAL_BATCH_SCHEMA_VERSION
    batch_id: str
    signals: tuple[EngagementSignalMetadata, ...]
    signal_count: int = Field(ge=0, le=MAXIMUM_ENGAGEMENT_SIGNALS_PER_BATCH)
    batch_fingerprint: str
    factual_effect: Literal[False] = False
    confidence_effect: Literal[False] = False
    runtime_effect: Literal[False] = False

    @field_validator("batch_id")
    @classmethod
    def batch_id_is_safe(cls, value: str) -> str:
        return _validate_safe_id(value, "engagement signal batch id")

    @field_validator("batch_fingerprint")
    @classmethod
    def fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "engagement batch fingerprint")

    @model_validator(mode="after")
    def validate_batch(self) -> Self:
        ids = tuple(signal.signal_id for signal in self.signals)
        if self.signal_count != len(ids):
            raise ValueError("engagement signal count mismatch")
        if ids != tuple(sorted(ids)):
            raise ValueError("engagement signals must be deterministically ordered")
        if len(set(ids)) != len(ids):
            raise ValueError("engagement signal duplicate")
        expected = _fingerprint_model(self, {"batch_fingerprint"})
        if self.batch_fingerprint != expected:
            raise ValueError("engagement signal batch fingerprint mismatch")
        return self


class EngagementLearningCandidate(BaseModel):
    """Non-factual engagement-learning candidate requiring operator review."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal[
        "aion-knowledge-engagement-learning-candidate/v1"
    ] = ENGAGEMENT_LEARNING_CANDIDATE_SCHEMA_VERSION
    learning_candidate_id: str
    candidate_kind: EngagementLearningCandidateKind
    signal_ids: tuple[str, ...]
    signal_fingerprints: tuple[str, ...]
    target_component_code: str
    target_policy_code: str
    reason_codes: tuple[str, ...]
    lifecycle_status: EngagementLearningLifecycleStatus
    candidate_version: int = Field(ge=1, le=MAXIMUM_CANDIDATE_VERSIONS_PER_IDENTITY)
    supersedes_candidate_id: str | None = None
    created_at: datetime
    expires_at: datetime | None
    operator_review_required: Literal[True] = True
    automatic_application: Literal[False] = False
    factual_effect: Literal[False] = False
    confidence_effect: Literal[False] = False
    knowledge_effect: Literal[False] = False
    cognitive_memory_effect: Literal[False] = False
    belief_effect: Literal[False] = False
    model_weight_effect: Literal[False] = False
    runtime_effect: Literal[False] = False
    candidate_fingerprint: str

    @field_validator(
        "learning_candidate_id",
        "target_component_code",
        "target_policy_code",
        "supersedes_candidate_id",
    )
    @classmethod
    def ids_are_safe(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _validate_safe_id(value, "engagement learning id")

    @field_validator("signal_ids")
    @classmethod
    def signal_ids_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return _values_are_sorted(
            _validate_safe_ids(value, "engagement learning signal id"),
            "engagement learning signal ids",
        )

    @field_validator("signal_fingerprints")
    @classmethod
    def signal_fingerprints_are_hex(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return _values_are_sorted(
            _validate_hexes(value, "engagement learning signal fingerprint"),
            "engagement learning signal fingerprints",
        )

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_are_valid(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_verified_knowledge_reason_codes(value)

    @field_validator("created_at")
    @classmethod
    def created_at_is_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value, "engagement learning created_at")

    @field_validator("expires_at")
    @classmethod
    def expires_at_is_utc(cls, value: datetime | None) -> datetime | None:
        return _validate_utc_optional(value, "engagement learning expires_at")

    @field_validator("candidate_fingerprint")
    @classmethod
    def fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "engagement learning fingerprint")

    @model_validator(mode="after")
    def validate_learning_candidate(self) -> Self:
        if len(self.signal_ids) != len(self.signal_fingerprints):
            raise ValueError("engagement learning signal fingerprint mismatch")
        expected = _fingerprint_model(self, {"candidate_fingerprint"})
        if self.candidate_fingerprint != expected:
            raise ValueError("engagement learning candidate fingerprint mismatch")
        return self


class EngagementLearningCandidateBatch(BaseModel):
    """Bounded deterministic engagement-learning candidate batch."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal[
        "aion-knowledge-engagement-learning-batch/v1"
    ] = ENGAGEMENT_LEARNING_BATCH_SCHEMA_VERSION
    batch_id: str
    candidates: tuple[EngagementLearningCandidate, ...]
    candidate_count: int = Field(
        ge=0, le=MAXIMUM_ENGAGEMENT_LEARNING_CANDIDATES_PER_BATCH
    )
    batch_fingerprint: str
    automatic_application: Literal[False] = False
    model_weight_effect: Literal[False] = False
    runtime_effect: Literal[False] = False

    @field_validator("batch_id")
    @classmethod
    def batch_id_is_safe(cls, value: str) -> str:
        return _validate_safe_id(value, "engagement learning batch id")

    @field_validator("batch_fingerprint")
    @classmethod
    def fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "engagement learning batch fingerprint")

    @model_validator(mode="after")
    def validate_batch(self) -> Self:
        ids = tuple(candidate.learning_candidate_id for candidate in self.candidates)
        if self.candidate_count != len(ids):
            raise ValueError("engagement learning candidate count mismatch")
        if ids != tuple(sorted(ids)):
            raise ValueError("engagement learning order must be deterministic")
        if len(set(ids)) != len(ids):
            raise ValueError("engagement learning duplicate candidate")
        expected = _fingerprint_model(self, {"batch_fingerprint"})
        if self.batch_fingerprint != expected:
            raise ValueError("engagement learning batch fingerprint mismatch")
        return self


class VerifiedKnowledgeResourceBudget(BaseModel):
    """Exact AION-216-KI-0007 resource budget."""

    model_config = FROZEN_MODEL_CONFIG

    maximum_candidates_per_batch: Literal[500] = MAXIMUM_CANDIDATES_PER_BATCH
    maximum_candidate_versions_per_identity: Literal[100] = (
        MAXIMUM_CANDIDATE_VERSIONS_PER_IDENTITY
    )
    maximum_lineage_references_per_candidate: Literal[500] = (
        MAXIMUM_LINEAGE_REFERENCES_PER_CANDIDATE
    )
    maximum_source_registry_references_per_candidate: Literal[100] = (
        MAXIMUM_SOURCE_REGISTRY_REFERENCES_PER_CANDIDATE
    )
    maximum_claim_references_per_candidate: Literal[20] = (
        MAXIMUM_CLAIM_REFERENCES_PER_CANDIDATE
    )
    maximum_assessment_references_per_candidate: Literal[20] = (
        MAXIMUM_ASSESSMENT_REFERENCES_PER_CANDIDATE
    )
    maximum_mesh_synthesis_references_per_candidate: Literal[20] = (
        MAXIMUM_MESH_SYNTHESIS_REFERENCES_PER_CANDIDATE
    )
    maximum_tool_session_references_per_candidate: Literal[20] = (
        MAXIMUM_TOOL_SESSION_REFERENCES_PER_CANDIDATE
    )
    maximum_reason_codes_per_candidate: Literal[100] = (
        MAXIMUM_REASON_CODES_PER_CANDIDATE
    )
    maximum_operator_review_items: Literal[500] = MAXIMUM_OPERATOR_REVIEW_ITEMS
    maximum_memory_snapshots: Literal[100] = MAXIMUM_MEMORY_SNAPSHOTS
    maximum_query_results: Literal[1000] = MAXIMUM_QUERY_RESULTS
    maximum_engagement_signals_per_batch: Literal[1000] = (
        MAXIMUM_ENGAGEMENT_SIGNALS_PER_BATCH
    )
    maximum_engagement_learning_candidates_per_batch: Literal[500] = (
        MAXIMUM_ENGAGEMENT_LEARNING_CANDIDATES_PER_BATCH
    )
    maximum_fixture_records: Literal[5000] = MAXIMUM_FIXTURE_RECORDS
    maximum_fixture_bytes: Literal[4194304] = MAXIMUM_FIXTURE_BYTES
    maximum_concurrent_candidate_evaluations: Literal[4] = (
        MAXIMUM_CONCURRENT_CANDIDATE_EVALUATIONS
    )
    maximum_persistent_verified_knowledge_write_batch: Literal[0] = (
        MAXIMUM_PERSISTENT_VERIFIED_KNOWLEDGE_WRITE_BATCH
    )
    maximum_automatic_knowledge_promotions: Literal[0] = (
        MAXIMUM_AUTOMATIC_KNOWLEDGE_PROMOTIONS
    )
    maximum_operator_approval_creations: Literal[0] = (
        MAXIMUM_OPERATOR_APPROVAL_CREATIONS
    )
    maximum_cognitive_memory_writes: Literal[0] = MAXIMUM_COGNITIVE_MEMORY_WRITES
    maximum_belief_mutations: Literal[0] = MAXIMUM_BELIEF_MUTATIONS
    maximum_engagement_fact_promotions: Literal[0] = MAXIMUM_ENGAGEMENT_FACT_PROMOTIONS
    maximum_engagement_confidence_effects: Literal[0] = (
        MAXIMUM_ENGAGEMENT_CONFIDENCE_EFFECTS
    )
    maximum_public_network_calls: Literal[0] = MAXIMUM_PUBLIC_NETWORK_CALLS
    maximum_dns_resolutions: Literal[0] = MAXIMUM_DNS_RESOLUTIONS
    maximum_search_provider_calls: Literal[0] = MAXIMUM_SEARCH_PROVIDER_CALLS
    maximum_connector_calls: Literal[0] = MAXIMUM_CONNECTOR_CALLS
    maximum_model_provider_calls: Literal[0] = MAXIMUM_MODEL_PROVIDER_CALLS
    maximum_actual_tool_executions: Literal[0] = MAXIMUM_ACTUAL_TOOL_EXECUTIONS
    maximum_shell_commands: Literal[0] = MAXIMUM_SHELL_COMMANDS
    maximum_subprocess_executions: Literal[0] = MAXIMUM_SUBPROCESS_EXECUTIONS
    maximum_browser_actions: Literal[0] = MAXIMUM_BROWSER_ACTIONS
    maximum_filesystem_mutations: Literal[0] = MAXIMUM_FILESYSTEM_MUTATIONS
    maximum_source_mutations: Literal[0] = MAXIMUM_SOURCE_MUTATIONS
    maximum_git_operations: Literal[0] = MAXIMUM_GIT_OPERATIONS
    maximum_runtime_created_pull_requests: Literal[0] = (
        MAXIMUM_RUNTIME_CREATED_PULL_REQUESTS
    )
    maximum_approvals_created: Literal[0] = MAXIMUM_APPROVALS_CREATED
    maximum_deployments: Literal[0] = MAXIMUM_DEPLOYMENTS
    maximum_model_weight_changes: Literal[0] = MAXIMUM_MODEL_WEIGHT_CHANGES


class VerifiedKnowledgeResourceUsage(BaseModel):
    """Resource usage for fail-closed budget decisions."""

    model_config = FROZEN_MODEL_CONFIG

    candidates: int = Field(default=0, ge=0)
    candidate_versions_per_identity: int = Field(default=0, ge=0)
    lineage_references_per_candidate: int = Field(default=0, ge=0)
    source_registry_references_per_candidate: int = Field(default=0, ge=0)
    claim_references_per_candidate: int = Field(default=0, ge=0)
    assessment_references_per_candidate: int = Field(default=0, ge=0)
    mesh_synthesis_references_per_candidate: int = Field(default=0, ge=0)
    tool_session_references_per_candidate: int = Field(default=0, ge=0)
    reason_codes_per_candidate: int = Field(default=0, ge=0)
    operator_review_items: int = Field(default=0, ge=0)
    memory_snapshots: int = Field(default=0, ge=0)
    query_results: int = Field(default=0, ge=0)
    engagement_signals_per_batch: int = Field(default=0, ge=0)
    engagement_learning_candidates_per_batch: int = Field(default=0, ge=0)
    fixture_records: int = Field(default=0, ge=0)
    fixture_bytes: int = Field(default=0, ge=0)
    concurrent_candidate_evaluations: int = Field(default=0, ge=0)
    persistent_verified_knowledge_write_batch: int = Field(default=0, ge=0)
    automatic_knowledge_promotions: int = Field(default=0, ge=0)
    operator_approval_creations: int = Field(default=0, ge=0)
    cognitive_memory_writes: int = Field(default=0, ge=0)
    belief_mutations: int = Field(default=0, ge=0)
    engagement_fact_promotions: int = Field(default=0, ge=0)
    engagement_confidence_effects: int = Field(default=0, ge=0)
    public_network_calls: int = Field(default=0, ge=0)
    dns_resolutions: int = Field(default=0, ge=0)
    search_provider_calls: int = Field(default=0, ge=0)
    connector_calls: int = Field(default=0, ge=0)
    model_provider_calls: int = Field(default=0, ge=0)
    actual_tool_executions: int = Field(default=0, ge=0)
    shell_commands: int = Field(default=0, ge=0)
    subprocess_executions: int = Field(default=0, ge=0)
    browser_actions: int = Field(default=0, ge=0)
    filesystem_mutations: int = Field(default=0, ge=0)
    source_mutations: int = Field(default=0, ge=0)
    git_operations: int = Field(default=0, ge=0)
    runtime_created_pull_requests: int = Field(default=0, ge=0)
    approvals_created: int = Field(default=0, ge=0)
    deployments: int = Field(default=0, ge=0)
    model_weight_changes: int = Field(default=0, ge=0)


class VerifiedKnowledgeBudgetDecision(BaseModel):
    """Budget decision that fails closed on any exceeded counter."""

    model_config = FROZEN_MODEL_CONFIG

    budget: VerifiedKnowledgeResourceBudget
    usage: VerifiedKnowledgeResourceUsage
    within_budget: bool
    failed_counters: tuple[str, ...]
    reason_codes: tuple[str, ...]
    decision_fingerprint: str
    runtime_effect: Literal[False] = False

    @field_validator("failed_counters")
    @classmethod
    def failed_counters_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return _values_are_sorted(
            _validate_safe_ids(value, "budget failed counter"),
            "budget failed counters",
        )

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_are_valid(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_verified_knowledge_reason_codes(value)

    @field_validator("decision_fingerprint")
    @classmethod
    def fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "budget decision fingerprint")

    @model_validator(mode="after")
    def validate_decision(self) -> Self:
        if self.within_budget == bool(self.failed_counters):
            raise ValueError("budget decision state mismatch")
        expected = _fingerprint_model(self, {"decision_fingerprint"})
        if self.decision_fingerprint != expected:
            raise ValueError("budget decision fingerprint mismatch")
        return self


class VerifiedKnowledgeIntegrityFinding(BaseModel):
    """Redacted integrity finding."""

    model_config = FROZEN_MODEL_CONFIG

    finding_id: str
    status: VerifiedKnowledgeIntegrityStatus
    reason_codes: tuple[str, ...]
    safe_ids: tuple[str, ...] = ()
    fingerprints: tuple[str, ...] = ()
    bounded_count: int = Field(default=0, ge=0)
    redacted_summary: str = "redacted verified knowledge integrity finding"
    runtime_effect: Literal[False] = False

    @field_validator("finding_id")
    @classmethod
    def finding_id_is_safe(cls, value: str) -> str:
        return _validate_safe_id(value, "integrity finding id")

    @field_validator("safe_ids")
    @classmethod
    def safe_ids_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return _values_are_sorted(_validate_safe_ids(value, "integrity safe id"), "safe ids")

    @field_validator("fingerprints")
    @classmethod
    def fingerprints_are_hex(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return _values_are_sorted(
            _validate_hexes(value, "integrity fingerprint"),
            "integrity fingerprints",
        )

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_are_valid(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_verified_knowledge_reason_codes(value)

    @field_validator("redacted_summary")
    @classmethod
    def summary_is_safe(cls, value: str) -> str:
        reject_verified_knowledge_payload(value, "integrity summary")
        return value


class VerifiedKnowledgeIntegrityReport(BaseModel):
    """Redacted integrity report."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal[
        "aion-knowledge-verified-integrity/v1"
    ] = VERIFIED_KNOWLEDGE_INTEGRITY_SCHEMA_VERSION
    report_id: str
    status: VerifiedKnowledgeIntegrityStatus
    findings: tuple[VerifiedKnowledgeIntegrityFinding, ...]
    finding_count: int = Field(ge=0)
    report_fingerprint: str
    read_only: Literal[True] = True
    redacted: Literal[True] = True
    persistent_write_applied: Literal[False] = False
    runtime_effect: Literal[False] = False

    @field_validator("report_id")
    @classmethod
    def report_id_is_safe(cls, value: str) -> str:
        return _validate_safe_id(value, "integrity report id")

    @field_validator("report_fingerprint")
    @classmethod
    def fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "integrity report fingerprint")

    @model_validator(mode="after")
    def validate_report(self) -> Self:
        ids = tuple(finding.finding_id for finding in self.findings)
        if self.finding_count != len(ids):
            raise ValueError("integrity finding count mismatch")
        if ids != tuple(sorted(ids)):
            raise ValueError("integrity findings must be sorted")
        expected = _fingerprint_model(self, {"report_fingerprint"})
        if self.report_fingerprint != expected:
            raise ValueError("integrity report fingerprint mismatch")
        return self


class VerifiedKnowledgeDiagnostics(BaseModel):
    """Redacted diagnostics for operator review."""

    model_config = FROZEN_MODEL_CONFIG

    diagnostics_id: str
    reason_codes: tuple[str, ...]
    safe_ids: tuple[str, ...] = ()
    redacted_summary: str
    diagnostics_fingerprint: str
    redacted: Literal[True] = True
    runtime_effect: Literal[False] = False

    @field_validator("diagnostics_id")
    @classmethod
    def diagnostics_id_is_safe(cls, value: str) -> str:
        return _validate_safe_id(value, "diagnostics id")

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_are_valid(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_verified_knowledge_reason_codes(value)

    @field_validator("safe_ids")
    @classmethod
    def safe_ids_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return _values_are_sorted(
            _validate_safe_ids(value, "diagnostics safe id"),
            "diagnostics safe ids",
        )

    @field_validator("redacted_summary")
    @classmethod
    def summary_is_safe(cls, value: str) -> str:
        reject_verified_knowledge_payload(value, "diagnostics summary")
        return value

    @field_validator("diagnostics_fingerprint")
    @classmethod
    def fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "diagnostics fingerprint")

    @model_validator(mode="after")
    def fingerprint_matches(self) -> Self:
        expected = _fingerprint_model(self, {"diagnostics_fingerprint"})
        if self.diagnostics_fingerprint != expected:
            raise ValueError("diagnostics fingerprint mismatch")
        return self


class VerifiedKnowledgeIncidentRecord(BaseModel):
    """Redacted candidate incident record."""

    model_config = FROZEN_MODEL_CONFIG

    incident_id: str
    severity_code: str
    reason_codes: tuple[str, ...]
    candidate_ids: tuple[str, ...] = ()
    created_at: datetime
    incident_fingerprint: str
    redacted: Literal[True] = True
    runtime_effect: Literal[False] = False

    @field_validator("incident_id", "severity_code")
    @classmethod
    def ids_are_safe(cls, value: str) -> str:
        return _validate_safe_id(value, "incident id")

    @field_validator("candidate_ids")
    @classmethod
    def candidate_ids_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return _values_are_sorted(
            _validate_safe_ids(value, "incident candidate id"),
            "incident candidate ids",
        )

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_are_valid(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_verified_knowledge_reason_codes(value)

    @field_validator("created_at")
    @classmethod
    def created_at_is_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value, "incident created_at")

    @field_validator("incident_fingerprint")
    @classmethod
    def fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "incident fingerprint")

    @model_validator(mode="after")
    def fingerprint_matches(self) -> Self:
        expected = _fingerprint_model(self, {"incident_fingerprint"})
        if self.incident_fingerprint != expected:
            raise ValueError("incident fingerprint mismatch")
        return self


class VerifiedKnowledgeEvidenceBundle(BaseModel):
    """Redacted evidence bundle with safe IDs and fingerprints only."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal[
        "aion-knowledge-verified-evidence/v1"
    ] = VERIFIED_KNOWLEDGE_EVIDENCE_SCHEMA_VERSION
    evidence_bundle_id: str
    candidate_ids: tuple[str, ...]
    candidate_kinds: tuple[VerifiedKnowledgeCandidateKind, ...]
    eligibility_statuses: tuple[VerifiedKnowledgeEligibilityStatus, ...]
    lifecycle_statuses: tuple[VerifiedKnowledgeLifecycleStatus, ...]
    confidence_caps: tuple[Decimal, ...]
    coverage_values: tuple[Decimal, ...]
    freshness_statuses: tuple[FreshnessStatus, ...]
    scope_statuses: tuple[ScopeApplicability, ...]
    contradiction_statuses: tuple[ContradictionStatus, ...]
    dissent_counts: tuple[int, ...]
    version_numbers: tuple[int, ...]
    lineage_counts: tuple[int, ...]
    engagement_signal_kinds: tuple[EngagementSignalKind, ...] = ()
    learning_candidate_kinds: tuple[EngagementLearningCandidateKind, ...] = ()
    integrity_status: VerifiedKnowledgeIntegrityStatus
    authorization_lineage: tuple[str, ...]
    disabled_state_flags: tuple[str, ...]
    evidence_fingerprint: str
    redacted: Literal[True] = True
    runtime_effect: Literal[False] = False

    @field_validator("evidence_bundle_id")
    @classmethod
    def evidence_bundle_id_is_safe(cls, value: str) -> str:
        return _validate_safe_id(value, "evidence bundle id")

    @field_validator("candidate_ids", "authorization_lineage", "disabled_state_flags")
    @classmethod
    def tuple_ids_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return _values_are_sorted(_validate_safe_ids(value, "evidence tuple id"), "evidence ids")

    @field_validator("confidence_caps", "coverage_values", mode="before")
    @classmethod
    def decimals_are_quantized(cls, value: Any) -> tuple[Decimal, ...]:
        return tuple(quantize_confidence(item) for item in tuple(value or ()))

    @field_validator("evidence_fingerprint")
    @classmethod
    def fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "evidence bundle fingerprint")

    @model_validator(mode="after")
    def validate_evidence_bundle(self) -> Self:
        candidate_count = len(self.candidate_ids)
        parallel_fields = (
            self.candidate_kinds,
            self.eligibility_statuses,
            self.lifecycle_statuses,
            self.confidence_caps,
            self.coverage_values,
            self.freshness_statuses,
            self.scope_statuses,
            self.contradiction_statuses,
            self.dissent_counts,
            self.version_numbers,
            self.lineage_counts,
        )
        if any(len(values) != candidate_count for values in parallel_fields):
            raise ValueError("evidence bundle candidate field count mismatch")
        expected = _fingerprint_model(self, {"evidence_fingerprint"})
        if self.evidence_fingerprint != expected:
            raise ValueError("evidence bundle fingerprint mismatch")
        return self


class VerifiedKnowledgeOperatorReviewItem(BaseModel):
    """Operator-review item that cannot create approval or knowledge."""

    model_config = FROZEN_MODEL_CONFIG

    review_item_id: str
    candidate_id: str
    eligibility_status: VerifiedKnowledgeEligibilityStatus
    lifecycle_status: VerifiedKnowledgeLifecycleStatus
    reason_codes: tuple[str, ...]
    created_at: datetime
    expires_at: datetime
    operator_review_required: Literal[True] = True
    candidate_is_not_factual_truth: Literal[True] = True
    candidate_approval_authorized: Literal[False] = False
    automatic_promotion_authorized: Literal[False] = False
    verified_knowledge_creation_authorized: Literal[False] = False
    cognitive_memory_write_authorized: Literal[False] = False
    belief_mutation_authorized: Literal[False] = False
    engagement_policy_update_authorized: Literal[False] = False
    model_training_authorized: Literal[False] = False
    persistent_write_authorized: Literal[False] = False
    public_network_authorized: Literal[False] = False
    approval_created: Literal[False] = False
    implementation_authorization_created: Literal[False] = False
    review_fingerprint: str
    runtime_effect: Literal[False] = False

    @field_validator("review_item_id", "candidate_id")
    @classmethod
    def ids_are_safe(cls, value: str) -> str:
        return _validate_safe_id(value, "operator review id")

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_are_valid(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_verified_knowledge_reason_codes(value)

    @field_validator("created_at", "expires_at")
    @classmethod
    def timestamps_are_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value, "operator review timestamp")

    @field_validator("review_fingerprint")
    @classmethod
    def fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "operator review fingerprint")

    @model_validator(mode="after")
    def validate_review_item(self) -> Self:
        if self.expires_at <= self.created_at:
            raise ValueError("operator review expiry must be after creation")
        if self.expires_at - self.created_at > timedelta(days=7):
            raise ValueError("operator review expiry exceeds seven days")
        expected = _fingerprint_model(self, {"review_fingerprint"})
        if self.review_fingerprint != expected:
            raise ValueError("operator review fingerprint mismatch")
        return self


def evaluate_verified_knowledge_budget(
    usage: VerifiedKnowledgeResourceUsage,
    budget: VerifiedKnowledgeResourceBudget | None = None,
) -> VerifiedKnowledgeBudgetDecision:
    """Evaluate exact resource limits and fail closed on any exceeded counter."""

    active_budget = budget or VerifiedKnowledgeResourceBudget()
    mapping = {
        "candidates": "maximum_candidates_per_batch",
        "candidate_versions_per_identity": "maximum_candidate_versions_per_identity",
        "lineage_references_per_candidate": "maximum_lineage_references_per_candidate",
        "source_registry_references_per_candidate": (
            "maximum_source_registry_references_per_candidate"
        ),
        "claim_references_per_candidate": "maximum_claim_references_per_candidate",
        "assessment_references_per_candidate": "maximum_assessment_references_per_candidate",
        "mesh_synthesis_references_per_candidate": (
            "maximum_mesh_synthesis_references_per_candidate"
        ),
        "tool_session_references_per_candidate": (
            "maximum_tool_session_references_per_candidate"
        ),
        "reason_codes_per_candidate": "maximum_reason_codes_per_candidate",
        "operator_review_items": "maximum_operator_review_items",
        "memory_snapshots": "maximum_memory_snapshots",
        "query_results": "maximum_query_results",
        "engagement_signals_per_batch": "maximum_engagement_signals_per_batch",
        "engagement_learning_candidates_per_batch": (
            "maximum_engagement_learning_candidates_per_batch"
        ),
        "fixture_records": "maximum_fixture_records",
        "fixture_bytes": "maximum_fixture_bytes",
        "concurrent_candidate_evaluations": "maximum_concurrent_candidate_evaluations",
        "persistent_verified_knowledge_write_batch": (
            "maximum_persistent_verified_knowledge_write_batch"
        ),
        "automatic_knowledge_promotions": "maximum_automatic_knowledge_promotions",
        "operator_approval_creations": "maximum_operator_approval_creations",
        "cognitive_memory_writes": "maximum_cognitive_memory_writes",
        "belief_mutations": "maximum_belief_mutations",
        "engagement_fact_promotions": "maximum_engagement_fact_promotions",
        "engagement_confidence_effects": "maximum_engagement_confidence_effects",
        "public_network_calls": "maximum_public_network_calls",
        "dns_resolutions": "maximum_dns_resolutions",
        "search_provider_calls": "maximum_search_provider_calls",
        "connector_calls": "maximum_connector_calls",
        "model_provider_calls": "maximum_model_provider_calls",
        "actual_tool_executions": "maximum_actual_tool_executions",
        "shell_commands": "maximum_shell_commands",
        "subprocess_executions": "maximum_subprocess_executions",
        "browser_actions": "maximum_browser_actions",
        "filesystem_mutations": "maximum_filesystem_mutations",
        "source_mutations": "maximum_source_mutations",
        "git_operations": "maximum_git_operations",
        "runtime_created_pull_requests": "maximum_runtime_created_pull_requests",
        "approvals_created": "maximum_approvals_created",
        "deployments": "maximum_deployments",
        "model_weight_changes": "maximum_model_weight_changes",
    }
    failed = tuple(
        sorted(
            usage_key
            for usage_key, limit_key in mapping.items()
            if getattr(usage, usage_key) > getattr(active_budget, limit_key)
        )
    )
    reason_codes = (
        ("verified_memory_integrity_failed",)
        if failed
        else ("verified_memory_integrity_passed",)
    )
    payload = {
        "budget": active_budget,
        "usage": usage,
        "within_budget": not failed,
        "failed_counters": failed,
        "reason_codes": reason_codes,
        "runtime_effect": False,
    }
    return VerifiedKnowledgeBudgetDecision.model_validate(
        {**payload, "decision_fingerprint": verified_knowledge_fingerprint(payload)}
    )


__all__ = [
    "APPROVAL_RECORD_ID",
    "AUTHORIZATION_SCOPE",
    "AUTHORIZATION_TRANSACTION_ID",
    "ENGAGEMENT_LEARNING_BATCH_SCHEMA_VERSION",
    "ENGAGEMENT_LEARNING_CANDIDATE_PLANE_STATE",
    "ENGAGEMENT_LEARNING_CANDIDATE_SCHEMA_VERSION",
    "ENGAGEMENT_SIGNAL_BATCH_SCHEMA_VERSION",
    "ENGAGEMENT_SIGNAL_SCHEMA_VERSION",
    "FORMAL_CLOSEOUT_TASK",
    "IMPLEMENTATION_TASK",
    "INTEGRATED_KNOWLEDGE_LINEAGE_SCHEMA_VERSION",
    "PROGRAM_ID",
    "VERIFIED_KNOWLEDGE_BATCH_SCHEMA_VERSION",
    "VERIFIED_KNOWLEDGE_CANDIDATE_SCHEMA_VERSION",
    "VERIFIED_KNOWLEDGE_CONTRACT_SCHEMA_VERSION",
    "VERIFIED_KNOWLEDGE_ELIGIBILITY_SCHEMA_VERSION",
    "VERIFIED_KNOWLEDGE_EVIDENCE_SCHEMA_VERSION",
    "VERIFIED_KNOWLEDGE_FIXTURE_SCHEMA_VERSION",
    "VERIFIED_KNOWLEDGE_INTEGRITY_SCHEMA_VERSION",
    "VERIFIED_KNOWLEDGE_MEMORY_SNAPSHOT_SCHEMA_VERSION",
    "VERIFIED_KNOWLEDGE_QUERY_RESULT_SCHEMA_VERSION",
    "VERIFIED_KNOWLEDGE_QUERY_SCHEMA_VERSION",
    "VERIFIED_KNOWLEDGE_REASON_CODE_REGISTRY_VERSION",
    "VERIFIED_KNOWLEDGE_REVALIDATION_SCHEMA_VERSION",
    "VERIFIED_KNOWLEDGE_VERSION_SCHEMA_VERSION",
    "VERIFIED_KNOWLEDGE_MEMORY_STATE",
    "EngagementLearningCandidate",
    "EngagementLearningCandidateBatch",
    "EngagementLearningCandidateKind",
    "EngagementLearningLifecycleStatus",
    "EngagementSignalBatch",
    "EngagementSignalKind",
    "EngagementSignalMetadata",
    "IntegratedKnowledgeLineage",
    "VerifiedKnowledgeBudgetDecision",
    "VerifiedKnowledgeCandidate",
    "VerifiedKnowledgeCandidateBatch",
    "VerifiedKnowledgeCandidateEligibilityInput",
    "VerifiedKnowledgeCandidateHistory",
    "VerifiedKnowledgeCandidateKind",
    "VerifiedKnowledgeCandidateMemorySnapshot",
    "VerifiedKnowledgeCandidateQuery",
    "VerifiedKnowledgeCandidateQueryResult",
    "VerifiedKnowledgeCandidateVersion",
    "VerifiedKnowledgeDiagnostics",
    "VerifiedKnowledgeEligibilityDecision",
    "VerifiedKnowledgeEligibilityStatus",
    "VerifiedKnowledgeError",
    "VerifiedKnowledgeEvidenceBundle",
    "VerifiedKnowledgeFixtureEnvelope",
    "VerifiedKnowledgeIncidentRecord",
    "VerifiedKnowledgeIntegrityFinding",
    "VerifiedKnowledgeIntegrityReport",
    "VerifiedKnowledgeIntegrityStatus",
    "VerifiedKnowledgeLifecycleStatus",
    "VerifiedKnowledgeOperatorReviewItem",
    "VerifiedKnowledgePersistentWriteOutcome",
    "VerifiedKnowledgeResourceBudget",
    "VerifiedKnowledgeResourceUsage",
    "VerifiedKnowledgeRevalidationRequest",
    "VerifiedKnowledgeRevalidationResult",
    "VerifiedKnowledgeRevalidationTrigger",
    "VerifiedKnowledgeVersionReason",
    "candidate_identity_id",
    "evaluate_verified_knowledge_budget",
    "quantize_confidence",
    "reject_verified_knowledge_payload",
    "stable_json",
    "utc_now",
    "validate_verified_knowledge_reason_codes",
    "verified_knowledge_fingerprint",
]
