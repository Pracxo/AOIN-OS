"""Deterministic epistemic evidence-assessment contracts."""

from __future__ import annotations

import math
import re
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from enum import StrEnum
from types import MappingProxyType
from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.knowledge_claim_graph import (
    EvidenceRole,
    ValidTimeInterval,
    VersionScope,
)
from aion_brain.contracts.knowledge_research import (
    FROZEN_MODEL_CONFIG,
    ResearchSourceClass,
    ensure_utc,
    fingerprint_payload,
    reject_protected_material,
    stable_json,
    validate_hex64,
    validate_safe_identifier,
)

EPISTEMIC_ASSESSMENT_CONTRACT_SCHEMA_VERSION: Literal["aion-knowledge-epistemic-assessment/v1"] = (
    "aion-knowledge-epistemic-assessment/v1"
)
EPISTEMIC_ASSESSMENT_REQUEST_SCHEMA_VERSION: Literal[
    "aion-knowledge-epistemic-assessment-request/v1"
] = "aion-knowledge-epistemic-assessment-request/v1"
EPISTEMIC_ASSESSMENT_POLICY_SCHEMA_VERSION: Literal[
    "aion-knowledge-epistemic-assessment-policy/v1"
] = "aion-knowledge-epistemic-assessment-policy/v1"
EVIDENCE_CONTRIBUTION_SCHEMA_VERSION: Literal["aion-knowledge-evidence-contribution/v1"] = (
    "aion-knowledge-evidence-contribution/v1"
)
ROLE_EVIDENCE_SCORE_SCHEMA_VERSION: Literal["aion-knowledge-role-evidence-score/v1"] = (
    "aion-knowledge-role-evidence-score/v1"
)
EPISTEMIC_SCORECARD_SCHEMA_VERSION: Literal["aion-knowledge-epistemic-scorecard/v1"] = (
    "aion-knowledge-epistemic-scorecard/v1"
)
CLAIM_EPISTEMIC_ASSESSMENT_SCHEMA_VERSION: Literal[
    "aion-knowledge-claim-epistemic-assessment/v1"
] = "aion-knowledge-claim-epistemic-assessment/v1"
EPISTEMIC_ASSESSMENT_BATCH_SCHEMA_VERSION: Literal[
    "aion-knowledge-epistemic-assessment-batch/v1"
] = "aion-knowledge-epistemic-assessment-batch/v1"
EPISTEMIC_ASSESSMENT_QUERY_SCHEMA_VERSION: Literal[
    "aion-knowledge-epistemic-assessment-query/v1"
] = "aion-knowledge-epistemic-assessment-query/v1"
EPISTEMIC_ASSESSMENT_INTEGRITY_SCHEMA_VERSION: Literal[
    "aion-knowledge-epistemic-assessment-integrity/v1"
] = "aion-knowledge-epistemic-assessment-integrity/v1"
EPISTEMIC_ASSESSMENT_FIXTURE_SCHEMA_VERSION: Literal[
    "aion-knowledge-epistemic-assessment-fixture/v1"
] = "aion-knowledge-epistemic-assessment-fixture/v1"
EPISTEMIC_ASSESSMENT_EVIDENCE_SCHEMA_VERSION: Literal[
    "aion-knowledge-epistemic-assessment-evidence/v1"
] = "aion-knowledge-epistemic-assessment-evidence/v1"
EPISTEMIC_REASON_CODE_REGISTRY_VERSION: Literal["aion-knowledge-epistemic-reasons/v1"] = (
    "aion-knowledge-epistemic-reasons/v1"
)
EPISTEMIC_SCORECARD_VERSION: Literal["aion-epistemic-scorecard/v1"] = "aion-epistemic-scorecard/v1"

PROGRAM_ID: Literal["AION-KNOWLEDGE-INTELLIGENCE-001"] = "AION-KNOWLEDGE-INTELLIGENCE-001"
AUTHORIZATION_TRANSACTION_ID: Literal["AION-210-KI-0004"] = "AION-210-KI-0004"
APPROVAL_RECORD_ID: Literal["AION-210-KI-0004"] = "AION-210-KI-0004"
IMPLEMENTATION_TASK: Literal["AION-211"] = "AION-211"
FORMAL_CLOSEOUT_TASK: Literal["AION-212"] = "AION-212"
AUTHORIZATION_SCOPE: Literal[
    "deterministic-evidence-corroboration-contradiction-freshness-source-independence-confidence-assessment-core"
] = (
    "deterministic-evidence-corroboration-contradiction-freshness-source-"
    "independence-confidence-assessment-core"
)

MAXIMUM_CLAIMS_PER_ASSESSMENT_BATCH = 500
MAXIMUM_EVIDENCE_BINDINGS_PER_CLAIM = 100
MAXIMUM_SOURCE_REGISTRY_REFERENCES_PER_CLAIM = 50
MAXIMUM_CITATION_REFERENCES_PER_CLAIM = 50
MAXIMUM_LINEAGE_GROUPS_PER_CLAIM = 20
MAXIMUM_RELATION_EDGES_PER_CLAIM = 100
MAXIMUM_REASON_CODES_PER_ASSESSMENT = 50
MAXIMUM_OPERATOR_REVIEW_ITEMS = 500
MAXIMUM_EPISTEMIC_ASSESSMENTS = 500
MAXIMUM_CONFIDENCE_CALCULATIONS = 500
MAXIMUM_BENCHMARK_CASES = 1000
MAXIMUM_QUERY_RESULTS = 1000
MAXIMUM_FIXTURE_RECORDS = 5000
MAXIMUM_FIXTURE_BYTES = 4_194_304
MAXIMUM_CONCURRENT_ASSESSMENTS = 4
MAXIMUM_PERSISTENT_ASSESSMENT_WRITE_BATCH = 0
MAXIMUM_SOURCE_BODY_BYTES = 0
MAXIMUM_AUTOMATIC_CLAIM_EXTRACTIONS = 0
MAXIMUM_ABSOLUTE_TRUTH_DECISIONS = 0
MAXIMUM_AUTOMATIC_CLAIM_ACCEPTANCES = 0
MAXIMUM_AUTOMATIC_CLAIM_REJECTIONS = 0
MAXIMUM_CONTRADICTION_RESOLUTIONS = 0
MAXIMUM_KNOWLEDGE_PROMOTIONS = 0
MAXIMUM_BELIEF_MUTATIONS = 0
MAXIMUM_NETWORK_CALLS = 0
MAXIMUM_SEARCH_PROVIDER_CALLS = 0
MAXIMUM_CONNECTOR_CALLS = 0
MAXIMUM_MODEL_PROVIDER_CALLS = 0
MAXIMUM_SOURCE_MUTATIONS = 0
MAXIMUM_GIT_OPERATIONS = 0
MAXIMUM_RUNTIME_CREATED_PULL_REQUESTS = 0
MAXIMUM_APPROVALS_CREATED = 0
MAXIMUM_DEPLOYMENTS = 0
MAXIMUM_MODEL_WEIGHT_CHANGES = 0

PROVIDER_MODEL_USAGE_ALIAS = "provider_" + "model_calls"

QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

LOCAL_FROZEN_MODEL_CONFIG = ConfigDict(
    extra="forbid",
    hide_input_in_errors=True,
    frozen=True,
    populate_by_name=True,
)


class EpistemicAssessmentStatus(StrEnum):
    """Evidence-posture status, never an absolute fact value."""

    SUPPORTED = "supported"
    CONTRADICTED = "contradicted"
    MIXED = "mixed"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    STALE = "stale"
    SUPERSEDED = "superseded"
    RETRACTED = "retracted"
    SCOPE_MISMATCH = "scope_mismatch"
    UNKNOWN = "unknown"


class ConfidenceBand(StrEnum):
    """Bounded confidence band."""

    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class FreshnessStatus(StrEnum):
    """Freshness posture for source metadata."""

    CURRENT = "current"
    AGEING = "ageing"
    STALE = "stale"
    SUPERSEDED = "superseded"
    RETRACTED = "retracted"
    UNKNOWN = "unknown"


class ScopeApplicability(StrEnum):
    """Explicit scope applicability."""

    APPLICABLE = "applicable"
    PARTIALLY_APPLICABLE = "partially_applicable"
    NOT_APPLICABLE = "not_applicable"
    INSUFFICIENT_SCOPE = "insufficient_scope"


class ContradictionStatus(StrEnum):
    """Structural conflict and opposition posture."""

    NONE_DETECTED = "none_detected"
    UNRESOLVED = "unresolved"
    MATERIAL = "material"
    SCOPE_SEPARATED = "scope_separated"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class EvidenceGroupDisposition(StrEnum):
    """Disposition for one independence group contribution."""

    COUNTED_SUPPORT = "counted_support"
    COUNTED_OPPOSITION = "counted_opposition"
    CONTEXT_ONLY = "context_only"
    DUPLICATE_SUPPRESSED = "duplicate_suppressed"
    MIRROR_SUPPRESSED = "mirror_suppressed"
    ROLE_AMBIGUOUS = "role_ambiguous"
    SCOPE_EXCLUDED = "scope_excluded"
    STALE_ONLY = "stale_only"
    UNRESOLVED_REFERENCE = "unresolved_reference"


class EpistemicAssessmentOutcome(StrEnum):
    """Batch outcome."""

    COMPLETED = "completed"
    COMPLETED_WITH_ABSTENTION = "completed_with_abstention"
    INTEGRITY_BLOCKED = "integrity_blocked"
    BUDGET_BLOCKED = "budget_blocked"
    FIXTURE_REJECTED = "fixture_rejected"
    PERSISTENT_WRITE_DISABLED = "persistent_write_disabled"


class EpistemicIntegrityStatus(StrEnum):
    """Assessment integrity audit status."""

    PASSED = "passed"
    FAILED = "failed"


EPISTEMIC_REASON_CODES: tuple[str, ...] = (
    "epistemic_assessment_request_valid",
    "epistemic_assessment_request_invalid",
    "epistemic_source_registry_integrity_valid",
    "epistemic_source_registry_integrity_failed",
    "epistemic_claim_graph_integrity_valid",
    "epistemic_claim_graph_integrity_failed",
    "epistemic_claim_found",
    "epistemic_claim_missing",
    "epistemic_evidence_reference_resolved",
    "epistemic_evidence_reference_unresolved",
    "epistemic_duplicate_evidence_suppressed",
    "epistemic_mirror_evidence_suppressed",
    "epistemic_role_ambiguous_group_suppressed",
    "epistemic_independent_support_counted",
    "epistemic_independent_opposition_counted",
    "epistemic_citation_coverage_complete",
    "epistemic_citation_coverage_incomplete",
    "epistemic_provenance_complete",
    "epistemic_provenance_incomplete",
    "epistemic_freshness_current",
    "epistemic_freshness_ageing",
    "epistemic_freshness_stale",
    "epistemic_freshness_unknown",
    "epistemic_valid_time_applicable",
    "epistemic_valid_time_not_applicable",
    "epistemic_valid_time_insufficient",
    "epistemic_jurisdiction_applicable",
    "epistemic_jurisdiction_not_applicable",
    "epistemic_jurisdiction_insufficient",
    "epistemic_version_applicable",
    "epistemic_version_not_applicable",
    "epistemic_version_insufficient",
    "epistemic_correction_relation_present",
    "epistemic_retraction_relation_present",
    "epistemic_supersession_relation_present",
    "epistemic_structural_conflict_none",
    "epistemic_structural_conflict_unresolved",
    "epistemic_structural_conflict_material",
    "epistemic_structural_conflict_scope_separated",
    "epistemic_status_supported",
    "epistemic_status_contradicted",
    "epistemic_status_mixed",
    "epistemic_status_insufficient_evidence",
    "epistemic_status_stale",
    "epistemic_status_superseded",
    "epistemic_status_retracted",
    "epistemic_status_scope_mismatch",
    "epistemic_status_unknown",
    "epistemic_hard_cap_integrity",
    "epistemic_hard_cap_retraction",
    "epistemic_hard_cap_supersession",
    "epistemic_hard_cap_scope_mismatch",
    "epistemic_hard_cap_insufficient_scope",
    "epistemic_hard_cap_material_opposition",
    "epistemic_hard_cap_zero_independence",
    "epistemic_hard_cap_one_independence",
    "epistemic_hard_cap_unverified_source_class",
    "epistemic_hard_cap_missing_citation",
    "epistemic_hard_cap_incomplete_provenance",
    "epistemic_hard_cap_stale_evidence",
    "epistemic_explicit_abstention_required",
    "epistemic_explicit_abstention_not_required",
    "epistemic_absolute_truth_oracle_blocked",
    "epistemic_automatic_claim_acceptance_blocked",
    "epistemic_automatic_claim_rejection_blocked",
    "epistemic_knowledge_promotion_blocked",
    "epistemic_belief_mutation_blocked",
    "epistemic_persistent_write_disabled",
    "epistemic_network_fetch_blocked",
    "epistemic_runtime_disabled",
    "epistemic_operator_review_required",
    "epistemic_integrity_passed",
    "epistemic_integrity_failed",
)

EPISTEMIC_REASON_CODE_REGISTRY = MappingProxyType(
    {code: index for index, code in enumerate(EPISTEMIC_REASON_CODES, start=1)}
)

SOURCE_QUALITY_METADATA_FACTORS: MappingProxyType[str, Decimal] = MappingProxyType(
    {
        "primary_authoritative": Decimal("1.00"),
        "official_standard": Decimal("1.00"),
        "official_government": Decimal("0.90"),
        "peer_reviewed": Decimal("0.85"),
        "vendor_primary": Decimal("0.70"),
        "institutional_primary": Decimal("0.70"),
        "reputable_secondary": Decimal("0.60"),
        "community_unverified": Decimal("0.35"),
        "unknown": Decimal("0.25"),
        "disallowed": Decimal("0.00"),
    }
)

ROLE_SCORE_WEIGHTS: MappingProxyType[str, Decimal] = MappingProxyType(
    {
        "reference_resolution": Decimal("0.10"),
        "evidence_coverage": Decimal("0.10"),
        "citation_coverage": Decimal("0.10"),
        "provenance_completeness": Decimal("0.10"),
        "source_independence": Decimal("0.25"),
        "source_quality_metadata": Decimal("0.10"),
        "valid_time_applicability": Decimal("0.08"),
        "jurisdiction_applicability": Decimal("0.06"),
        "version_applicability": Decimal("0.06"),
        "freshness": Decimal("0.05"),
    }
)

HARD_CAP_ORDER: tuple[str, ...] = (
    "broken_source_registry_or_graph_integrity",
    "applicable_retraction",
    "applicable_supersession_without_current_support",
    "scope_mismatch",
    "insufficient_explicit_scope",
    "unresolved_material_opposition",
    "zero_independent_evidence_groups",
    "one_independent_evidence_group",
    "only_unknown_or_community_unverified_evidence",
    "missing_citation_coverage",
    "incomplete_provenance",
    "stale_evidence",
)

_UNSAFE_REASON_RE = re.compile(r"[/:\\\\]")


def quantize_score(value: Decimal | int | str) -> Decimal:
    """Return a finite Decimal in [0, 1] quantized to six places."""

    score = value if isinstance(value, Decimal) else Decimal(str(value))
    if not score.is_finite():
        raise ValueError("score must be finite")
    if score < 0 or score > 1:
        raise ValueError("score must be within the closed unit interval")
    return score.quantize(QUANT, rounding=ROUND_HALF_UP)


def confidence_band_for(confidence: Decimal) -> ConfidenceBand:
    """Classify a quantized confidence value."""

    value = quantize_score(confidence)
    if value <= Decimal("0.200000"):
        return ConfidenceBand.VERY_LOW
    if value <= Decimal("0.400000"):
        return ConfidenceBand.LOW
    if value <= Decimal("0.650000"):
        return ConfidenceBand.MEDIUM
    if value <= Decimal("0.850000"):
        return ConfidenceBand.HIGH
    return ConfidenceBand.VERY_HIGH


def validate_epistemic_reason_codes(values: tuple[str, ...]) -> tuple[str, ...]:
    """Validate immutable ordered reason codes."""

    seen: set[str] = set()
    for code in values:
        if code not in EPISTEMIC_REASON_CODE_REGISTRY:
            raise ValueError("unknown epistemic reason code")
        if code in seen:
            raise ValueError("duplicate epistemic reason code")
        if _UNSAFE_REASON_RE.search(code):
            raise ValueError("epistemic reason code must not embed URL, host, or path text")
        reject_protected_material(code, "epistemic reason code")
        seen.add(code)
    return values


def fingerprint_model(model: BaseModel | dict[str, Any], field_name: str) -> str:
    """Fingerprint a model after excluding its fingerprint field."""

    payload = (
        model.model_dump(mode="json", by_alias=True)
        if isinstance(model, BaseModel)
        else dict(model)
    )
    payload.pop(field_name, None)
    return fingerprint_payload(_json_ready(payload))


def json_size(payload: object) -> int:
    """Return deterministic JSON byte size."""

    return len(stable_json(_json_ready(payload)).encode("utf-8"))


class EpistemicFreshnessPolicy(BaseModel):
    """Explicit freshness policy required by each assessment request."""

    model_config = FROZEN_MODEL_CONFIG

    policy_id: str
    current_max_age_seconds: int = Field(gt=0)
    stale_after_seconds: int = Field(gt=0)
    future_timestamp_tolerance_seconds: int = Field(ge=0, le=3600)
    policy_fingerprint: str

    @field_validator("policy_id")
    @classmethod
    def policy_id_is_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "freshness policy_id")

    @field_validator("policy_fingerprint")
    @classmethod
    def fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "freshness policy fingerprint")

    @model_validator(mode="after")
    def policy_is_explicit_and_fingerprinted(self) -> Self:
        if self.stale_after_seconds <= self.current_max_age_seconds:
            raise ValueError("stale_after_seconds must exceed current_max_age_seconds")
        if self.stale_after_seconds > 10 * 365 * 24 * 60 * 60:
            raise ValueError("stale window must not exceed ten years")
        if self.policy_fingerprint != epistemic_freshness_policy_fingerprint(self):
            raise ValueError("freshness policy fingerprint mismatch")
        return self


def epistemic_freshness_policy_fingerprint(
    policy: EpistemicFreshnessPolicy | dict[str, Any],
) -> str:
    return fingerprint_model(policy, "policy_fingerprint")


class EpistemicTargetScope(BaseModel):
    """Explicit assessment scope; missing dimensions are never global."""

    model_config = FROZEN_MODEL_CONFIG

    target_valid_time: ValidTimeInterval
    target_jurisdiction_ids: tuple[str, ...] = Field(min_length=1, max_length=20)
    target_version_scopes: tuple[VersionScope, ...] = Field(min_length=1, max_length=20)
    scope_fingerprint: str

    @field_validator("target_jurisdiction_ids")
    @classmethod
    def jurisdiction_ids_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if len(set(value)) != len(value):
            raise ValueError("duplicate target jurisdiction IDs rejected")
        return tuple(
            validate_safe_identifier(item, "target jurisdiction") for item in sorted(value)
        )

    @field_validator("scope_fingerprint")
    @classmethod
    def scope_fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "epistemic target scope fingerprint")

    @model_validator(mode="after")
    def scope_fingerprint_matches(self) -> Self:
        if self.scope_fingerprint != epistemic_target_scope_fingerprint(self):
            raise ValueError("epistemic target scope fingerprint mismatch")
        return self


def epistemic_target_scope_fingerprint(scope: EpistemicTargetScope | dict[str, Any]) -> str:
    return fingerprint_model(scope, "scope_fingerprint")


class EpistemicAssessmentRequest(BaseModel):
    """Operator-supplied read-only request containing claim IDs only."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-epistemic-assessment-request/v1"] = (
        EPISTEMIC_ASSESSMENT_REQUEST_SCHEMA_VERSION
    )
    program_id: Literal["AION-KNOWLEDGE-INTELLIGENCE-001"] = PROGRAM_ID
    authorization_transaction_id: Literal["AION-210-KI-0004"] = AUTHORIZATION_TRANSACTION_ID
    implementation_task: Literal["AION-211"] = IMPLEMENTATION_TASK
    formal_closeout_task: Literal["AION-212"] = FORMAL_CLOSEOUT_TASK
    authorization_scope: Literal[
        "deterministic-evidence-corroboration-contradiction-freshness-source-independence-confidence-assessment-core"
    ] = AUTHORIZATION_SCOPE
    request_id: str
    claim_ids: tuple[str, ...] = Field(
        min_length=1,
        max_length=MAXIMUM_CLAIMS_PER_ASSESSMENT_BATCH,
    )
    target_scope: EpistemicTargetScope
    freshness_policy: EpistemicFreshnessPolicy
    assessment_time: datetime
    operator_supplied: Literal[True] = True
    synthetic: Literal[True] = True
    read_only: Literal[True] = True
    redacted: Literal[True] = True
    absolute_truth_requested: Literal[False] = False
    automatic_acceptance_requested: Literal[False] = False
    knowledge_promotion_requested: Literal[False] = False
    belief_mutation_requested: Literal[False] = False
    persistent_write_requested: Literal[False] = False
    runtime_effect: Literal[False] = False

    @field_validator("request_id")
    @classmethod
    def request_id_is_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "epistemic assessment request_id")

    @field_validator("claim_ids")
    @classmethod
    def claim_ids_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if len(set(value)) != len(value):
            raise ValueError("duplicate claim IDs rejected")
        return tuple(sorted(validate_safe_identifier(item, "claim_id") for item in value))

    @field_validator("assessment_time")
    @classmethod
    def assessment_time_is_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value, "epistemic assessment_time")


class EvidenceContribution(BaseModel):
    """One resolved evidence binding contribution, without source or claim text."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-evidence-contribution/v1"] = (
        EVIDENCE_CONTRIBUTION_SCHEMA_VERSION
    )
    claim_id: str
    binding_id: str
    evidence_role: EvidenceRole
    independence_group_id: str
    source_registry_record_ids: tuple[str, ...] = Field(
        max_length=MAXIMUM_SOURCE_REGISTRY_REFERENCES_PER_CLAIM
    )
    citation_record_ids: tuple[str, ...] = Field(max_length=MAXIMUM_CITATION_REFERENCES_PER_CLAIM)
    provenance_record_ids: tuple[str, ...] = Field(
        max_length=MAXIMUM_SOURCE_REGISTRY_REFERENCES_PER_CLAIM
    )
    source_class: ResearchSourceClass
    source_quality_metadata_factor: Decimal
    reference_resolution_score: Decimal
    evidence_coverage_score: Decimal
    citation_coverage_score: Decimal
    provenance_completeness_score: Decimal
    freshness_status: FreshnessStatus
    freshness_factor: Decimal
    valid_time_applicability: ScopeApplicability
    valid_time_factor: Decimal
    jurisdiction_applicability: ScopeApplicability
    jurisdiction_factor: Decimal
    version_applicability: ScopeApplicability
    version_factor: Decimal
    disposition: EvidenceGroupDisposition
    duplicate_suppressed: bool
    mirror_suppressed: bool
    role_ambiguous: bool
    contribution_fingerprint: str
    claim_verified: Literal[False] = False
    truth_effect: Literal[False] = False
    confidence_effect_only: Literal[True] = True
    knowledge_effect: Literal[False] = False
    belief_effect: Literal[False] = False
    runtime_effect: Literal[False] = False

    @field_validator("claim_id", "binding_id", "independence_group_id")
    @classmethod
    def ids_are_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "evidence contribution identifier")

    @field_validator("source_registry_record_ids", "citation_record_ids", "provenance_record_ids")
    @classmethod
    def reference_ids_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if len(set(value)) != len(value):
            raise ValueError("duplicate evidence contribution references rejected")
        return tuple(sorted(validate_safe_identifier(item, "evidence reference") for item in value))

    @field_validator(
        "source_quality_metadata_factor",
        "reference_resolution_score",
        "evidence_coverage_score",
        "citation_coverage_score",
        "provenance_completeness_score",
        "freshness_factor",
        "valid_time_factor",
        "jurisdiction_factor",
        "version_factor",
    )
    @classmethod
    def decimal_scores_are_quantized(cls, value: Decimal) -> Decimal:
        return quantize_score(value)

    @field_validator("contribution_fingerprint")
    @classmethod
    def contribution_fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "evidence contribution fingerprint")

    @model_validator(mode="after")
    def contribution_is_valid(self) -> Self:
        if self.source_class == "disallowed":
            raise ValueError("disallowed evidence is rejected")
        expected = SOURCE_QUALITY_METADATA_FACTORS[self.source_class].quantize(QUANT)
        if self.source_quality_metadata_factor != expected:
            raise ValueError("source quality metadata factor mismatch")
        if self.contribution_fingerprint != evidence_contribution_fingerprint(self):
            raise ValueError("evidence contribution fingerprint mismatch")
        return self


def evidence_contribution_fingerprint(
    contribution: EvidenceContribution | dict[str, Any],
) -> str:
    return fingerprint_model(contribution, "contribution_fingerprint")


class RoleEvidenceScore(BaseModel):
    """Transparent weighted score for one evidence role."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-role-evidence-score/v1"] = (
        ROLE_EVIDENCE_SCORE_SCHEMA_VERSION
    )
    claim_id: str
    role: Literal["support", "opposition"]
    reference_resolution: Decimal
    evidence_coverage: Decimal
    citation_coverage: Decimal
    provenance_completeness: Decimal
    source_independence: Decimal
    source_quality_metadata: Decimal
    valid_time_applicability: Decimal
    jurisdiction_applicability: Decimal
    version_applicability: Decimal
    freshness: Decimal
    independent_group_count: int = Field(ge=0)
    declared_group_count: int = Field(ge=0)
    representative_binding_ids: tuple[str, ...] = ()
    raw_role_score: Decimal
    reason_codes: tuple[str, ...]
    score_fingerprint: str
    runtime_effect: Literal[False] = False

    @field_validator("claim_id")
    @classmethod
    def claim_id_is_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "role score claim_id")

    @field_validator("representative_binding_ids")
    @classmethod
    def representative_ids_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if len(set(value)) != len(value):
            raise ValueError("duplicate representative binding IDs rejected")
        return tuple(validate_safe_identifier(item, "representative binding") for item in value)

    @field_validator(
        "reference_resolution",
        "evidence_coverage",
        "citation_coverage",
        "provenance_completeness",
        "source_independence",
        "source_quality_metadata",
        "valid_time_applicability",
        "jurisdiction_applicability",
        "version_applicability",
        "freshness",
        "raw_role_score",
    )
    @classmethod
    def role_score_decimal_is_quantized(cls, value: Decimal) -> Decimal:
        return quantize_score(value)

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_epistemic_reason_codes(value)

    @field_validator("score_fingerprint")
    @classmethod
    def score_fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "role evidence score fingerprint")

    @model_validator(mode="after")
    def score_is_weighted_and_fingerprinted(self) -> Self:
        if sum(ROLE_SCORE_WEIGHTS.values(), Decimal("0.00")) != Decimal("1.00"):
            raise ValueError("role score weights must sum exactly to one")
        expected_score = sum(
            (
                self.reference_resolution * ROLE_SCORE_WEIGHTS["reference_resolution"],
                self.evidence_coverage * ROLE_SCORE_WEIGHTS["evidence_coverage"],
                self.citation_coverage * ROLE_SCORE_WEIGHTS["citation_coverage"],
                self.provenance_completeness * ROLE_SCORE_WEIGHTS["provenance_completeness"],
                self.source_independence * ROLE_SCORE_WEIGHTS["source_independence"],
                self.source_quality_metadata * ROLE_SCORE_WEIGHTS["source_quality_metadata"],
                self.valid_time_applicability * ROLE_SCORE_WEIGHTS["valid_time_applicability"],
                self.jurisdiction_applicability * ROLE_SCORE_WEIGHTS["jurisdiction_applicability"],
                self.version_applicability * ROLE_SCORE_WEIGHTS["version_applicability"],
                self.freshness * ROLE_SCORE_WEIGHTS["freshness"],
            ),
            Decimal("0.00"),
        )
        if self.raw_role_score != quantize_score(expected_score):
            raise ValueError("raw role score mismatch")
        if self.score_fingerprint != role_evidence_score_fingerprint(self):
            raise ValueError("role evidence score fingerprint mismatch")
        return self


def role_evidence_score_fingerprint(score: RoleEvidenceScore | dict[str, Any]) -> str:
    return fingerprint_model(score, "score_fingerprint")


class EpistemicScorecardPolicy(BaseModel):
    """Versioned deterministic scorecard policy."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-epistemic-assessment-policy/v1"] = (
        EPISTEMIC_ASSESSMENT_POLICY_SCHEMA_VERSION
    )
    scorecard_version: Literal["aion-epistemic-scorecard/v1"] = EPISTEMIC_SCORECARD_VERSION
    weights: dict[str, Decimal]
    hard_cap_order: tuple[str, ...] = HARD_CAP_ORDER
    minimum_independent_support_groups: Literal[2] = 2
    minimum_independent_opposition_groups: Literal[2] = 2
    supported_raw_score_threshold: Decimal = Decimal("0.550000")
    contradicted_raw_score_threshold: Decimal = Decimal("0.550000")
    mixed_raw_score_threshold: Decimal = Decimal("0.350000")
    dominance_margin: Decimal = Decimal("0.200000")
    abstention_confidence_threshold: Decimal = Decimal("0.700000")
    policy_fingerprint: str

    @field_validator(
        "supported_raw_score_threshold",
        "contradicted_raw_score_threshold",
        "mixed_raw_score_threshold",
        "dominance_margin",
        "abstention_confidence_threshold",
    )
    @classmethod
    def threshold_is_quantized(cls, value: Decimal) -> Decimal:
        return quantize_score(value)

    @field_validator("weights")
    @classmethod
    def weights_are_exact(cls, value: dict[str, Decimal]) -> dict[str, Decimal]:
        expected = dict(ROLE_SCORE_WEIGHTS)
        if set(value) != set(expected):
            raise ValueError("scorecard weights must use exact dimensions")
        quantized = {key: quantize_score(item) for key, item in value.items()}
        if quantized != {key: item.quantize(QUANT) for key, item in expected.items()}:
            raise ValueError("scorecard weights must match versioned specification")
        if sum(value.values(), Decimal("0.00")) != Decimal("1.00"):
            raise ValueError("scorecard weights must sum exactly to one")
        return quantized

    @field_validator("hard_cap_order")
    @classmethod
    def hard_cap_order_is_exact(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if value != HARD_CAP_ORDER:
            raise ValueError("hard cap order mismatch")
        return value

    @field_validator("policy_fingerprint")
    @classmethod
    def policy_fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "epistemic scorecard policy fingerprint")

    @model_validator(mode="after")
    def policy_fingerprint_matches(self) -> Self:
        if self.policy_fingerprint != epistemic_scorecard_policy_fingerprint(self):
            raise ValueError("epistemic scorecard policy fingerprint mismatch")
        return self


def default_scorecard_policy_payload() -> dict[str, Any]:
    payload = {
        "schema_version": EPISTEMIC_ASSESSMENT_POLICY_SCHEMA_VERSION,
        "scorecard_version": EPISTEMIC_SCORECARD_VERSION,
        "weights": {key: value for key, value in ROLE_SCORE_WEIGHTS.items()},
        "hard_cap_order": HARD_CAP_ORDER,
        "minimum_independent_support_groups": 2,
        "minimum_independent_opposition_groups": 2,
        "supported_raw_score_threshold": Decimal("0.550000"),
        "contradicted_raw_score_threshold": Decimal("0.550000"),
        "mixed_raw_score_threshold": Decimal("0.350000"),
        "dominance_margin": Decimal("0.200000"),
        "abstention_confidence_threshold": Decimal("0.700000"),
    }
    return {**payload, "policy_fingerprint": fingerprint_payload(_json_ready(payload))}


def default_scorecard_policy() -> EpistemicScorecardPolicy:
    """Return the exact AION-211 v1 scorecard policy."""

    return EpistemicScorecardPolicy.model_validate(default_scorecard_policy_payload())


def epistemic_scorecard_policy_fingerprint(
    policy: EpistemicScorecardPolicy | dict[str, Any],
) -> str:
    return fingerprint_model(policy, "policy_fingerprint")


class EpistemicHardCapApplication(BaseModel):
    """One deterministic hard-cap application record."""

    model_config = FROZEN_MODEL_CONFIG

    cap_id: str
    reason_code: str
    pre_cap_confidence: Decimal
    post_cap_confidence: Decimal
    forced_status: EpistemicAssessmentStatus | None = None
    applied: bool
    cap_fingerprint: str

    @field_validator("cap_id")
    @classmethod
    def cap_id_is_safe(cls, value: str) -> str:
        if value not in HARD_CAP_ORDER:
            raise ValueError("unknown hard cap ID")
        return value

    @field_validator("reason_code")
    @classmethod
    def reason_code_is_known(cls, value: str) -> str:
        return validate_epistemic_reason_codes((value,))[0]

    @field_validator("pre_cap_confidence", "post_cap_confidence")
    @classmethod
    def cap_confidence_is_quantized(cls, value: Decimal) -> Decimal:
        return quantize_score(value)

    @field_validator("cap_fingerprint")
    @classmethod
    def cap_fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "hard cap fingerprint")

    @model_validator(mode="after")
    def cap_is_safe(self) -> Self:
        if self.post_cap_confidence > self.pre_cap_confidence:
            raise ValueError("hard cap must not increase confidence")
        if self.cap_fingerprint != hard_cap_fingerprint(self):
            raise ValueError("hard cap fingerprint mismatch")
        return self


def hard_cap_fingerprint(cap: EpistemicHardCapApplication | dict[str, Any]) -> str:
    return fingerprint_model(cap, "cap_fingerprint")


class EpistemicScorecard(BaseModel):
    """Transparent scorecard result before claim-assessment wrapping."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-epistemic-scorecard/v1"] = (
        EPISTEMIC_SCORECARD_SCHEMA_VERSION
    )
    claim_id: str
    policy_fingerprint: str
    scorecard_version: Literal["aion-epistemic-scorecard/v1"] = EPISTEMIC_SCORECARD_VERSION
    support_score: RoleEvidenceScore
    opposition_score: RoleEvidenceScore
    status: EpistemicAssessmentStatus
    contradiction_status: ContradictionStatus
    freshness_status: FreshnessStatus
    scope_applicability: ScopeApplicability
    confidence: Decimal
    confidence_band: ConfidenceBand
    explicit_abstention: bool
    hard_caps: tuple[EpistemicHardCapApplication, ...]
    reason_codes: tuple[str, ...] = Field(max_length=MAXIMUM_REASON_CODES_PER_ASSESSMENT)
    scorecard_fingerprint: str
    absolute_truth_claimed: Literal[False] = False
    claim_accepted: Literal[False] = False
    claim_rejected: Literal[False] = False
    knowledge_promoted: Literal[False] = False
    belief_mutated: Literal[False] = False
    persistent_write_applied: Literal[False] = False
    runtime_effect: Literal[False] = False

    @field_validator("claim_id")
    @classmethod
    def scorecard_claim_id_is_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "epistemic scorecard claim_id")

    @field_validator("policy_fingerprint", "scorecard_fingerprint")
    @classmethod
    def scorecard_fingerprints_are_hex(cls, value: str) -> str:
        return validate_hex64(value, "epistemic scorecard fingerprint")

    @field_validator("confidence")
    @classmethod
    def scorecard_confidence_is_quantized(cls, value: Decimal) -> Decimal:
        return quantize_score(value)

    @field_validator("reason_codes")
    @classmethod
    def scorecard_reason_codes_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_epistemic_reason_codes(value)

    @model_validator(mode="after")
    def scorecard_is_consistent(self) -> Self:
        if self.support_score.claim_id != self.claim_id:
            raise ValueError("support score claim_id mismatch")
        if self.opposition_score.claim_id != self.claim_id:
            raise ValueError("opposition score claim_id mismatch")
        if self.confidence_band != confidence_band_for(self.confidence):
            raise ValueError("scorecard confidence band mismatch")
        if self.scorecard_fingerprint != epistemic_scorecard_fingerprint(self):
            raise ValueError("epistemic scorecard fingerprint mismatch")
        return self


def epistemic_scorecard_fingerprint(scorecard: EpistemicScorecard | dict[str, Any]) -> str:
    return fingerprint_model(scorecard, "scorecard_fingerprint")


class ClaimEpistemicAssessment(BaseModel):
    """Immutable redacted assessment for one unverified claim."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-claim-epistemic-assessment/v1"] = (
        CLAIM_EPISTEMIC_ASSESSMENT_SCHEMA_VERSION
    )
    assessment_id: str
    request_id: str
    claim_id: str
    claim_identity_fingerprint: str
    source_registry_integrity_fingerprint: str
    claim_graph_integrity_fingerprint: str
    assessment_policy_fingerprint: str
    scorecard_version: Literal["aion-epistemic-scorecard/v1"] = EPISTEMIC_SCORECARD_VERSION
    status: EpistemicAssessmentStatus
    confidence: Decimal
    confidence_band: ConfidenceBand
    explicit_abstention: bool
    independent_support_count: int = Field(ge=0)
    independent_opposition_count: int = Field(ge=0)
    duplicate_suppressed_count: int = Field(ge=0)
    mirror_suppressed_count: int = Field(ge=0)
    ambiguous_group_count: int = Field(ge=0)
    reference_resolution: Decimal
    evidence_coverage: Decimal
    citation_coverage: Decimal
    provenance_completeness: Decimal
    support_score: Decimal
    opposition_score: Decimal
    freshness_status: FreshnessStatus
    scope_applicability: ScopeApplicability
    contradiction_status: ContradictionStatus
    applicable_correction_relation_ids: tuple[str, ...] = ()
    applicable_retraction_relation_ids: tuple[str, ...] = ()
    applicable_supersession_relation_ids: tuple[str, ...] = ()
    structural_conflict_candidate_ids: tuple[str, ...] = ()
    hard_caps: tuple[EpistemicHardCapApplication, ...]
    reason_codes: tuple[str, ...] = Field(max_length=MAXIMUM_REASON_CODES_PER_ASSESSMENT)
    assessment_time: datetime
    assessment_fingerprint: str
    unverified_source_inputs: Literal[True] = True
    absolute_truth_claimed: Literal[False] = False
    claim_accepted: Literal[False] = False
    claim_rejected: Literal[False] = False
    contradiction_resolved: Literal[False] = False
    knowledge_promoted: Literal[False] = False
    belief_created: Literal[False] = False
    belief_mutated: Literal[False] = False
    persistent_write_applied: Literal[False] = False
    runtime_effect: Literal[False] = False

    @field_validator("assessment_id", "request_id", "claim_id")
    @classmethod
    def ids_are_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "claim epistemic assessment identifier")

    @field_validator(
        "claim_identity_fingerprint",
        "source_registry_integrity_fingerprint",
        "claim_graph_integrity_fingerprint",
        "assessment_policy_fingerprint",
        "assessment_fingerprint",
    )
    @classmethod
    def fingerprints_are_hex(cls, value: str) -> str:
        return validate_hex64(value, "claim epistemic assessment fingerprint")

    @field_validator(
        "reference_resolution",
        "evidence_coverage",
        "citation_coverage",
        "provenance_completeness",
        "support_score",
        "opposition_score",
        "confidence",
    )
    @classmethod
    def assessment_scores_are_quantized(cls, value: Decimal) -> Decimal:
        return quantize_score(value)

    @field_validator(
        "applicable_correction_relation_ids",
        "applicable_retraction_relation_ids",
        "applicable_supersession_relation_ids",
        "structural_conflict_candidate_ids",
    )
    @classmethod
    def related_ids_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if len(set(value)) != len(value):
            raise ValueError("duplicate assessment relation IDs rejected")
        return tuple(
            sorted(validate_safe_identifier(item, "assessment relation") for item in value)
        )

    @field_validator("reason_codes")
    @classmethod
    def assessment_reason_codes_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_epistemic_reason_codes(value)

    @field_validator("assessment_time")
    @classmethod
    def assessment_time_is_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value, "claim epistemic assessment timestamp")

    @model_validator(mode="after")
    def assessment_is_consistent(self) -> Self:
        if self.confidence_band != confidence_band_for(self.confidence):
            raise ValueError("confidence band mismatch")
        if self.assessment_fingerprint != claim_epistemic_assessment_fingerprint(self):
            raise ValueError("claim epistemic assessment fingerprint mismatch")
        return self


def claim_epistemic_assessment_fingerprint(
    assessment: ClaimEpistemicAssessment | dict[str, Any],
) -> str:
    return fingerprint_model(assessment, "assessment_fingerprint")


class EpistemicOperatorReviewItem(BaseModel):
    """Redacted human review requirement; evidence, not approval."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-epistemic-assessment-evidence/v1"] = (
        EPISTEMIC_ASSESSMENT_EVIDENCE_SCHEMA_VERSION
    )
    review_item_id: str
    assessment_ids: tuple[str, ...] = Field(max_length=MAXIMUM_OPERATOR_REVIEW_ITEMS)
    reason_codes: tuple[str, ...]
    created_at: datetime
    expires_at: datetime
    review_fingerprint: str
    operator_review_required: Literal[True] = True
    human_fact_review_required: Literal[True] = True
    knowledge_promotion_authorized: Literal[False] = False
    belief_mutation_authorized: Literal[False] = False
    persistent_assessment_write_authorized: Literal[False] = False
    automatic_claim_acceptance_authorized: Literal[False] = False
    automatic_claim_rejection_authorized: Literal[False] = False
    approval_created: Literal[False] = False
    implementation_authorization_created: Literal[False] = False
    runtime_effect: Literal[False] = False

    @field_validator("review_item_id")
    @classmethod
    def review_id_is_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "epistemic review item")

    @field_validator("assessment_ids")
    @classmethod
    def assessment_ids_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if len(set(value)) != len(value):
            raise ValueError("duplicate review assessment IDs rejected")
        return tuple(validate_safe_identifier(item, "review assessment") for item in value)

    @field_validator("reason_codes")
    @classmethod
    def review_reason_codes_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_epistemic_reason_codes(value)

    @field_validator("created_at", "expires_at")
    @classmethod
    def review_timestamps_are_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value, "epistemic review timestamp")

    @field_validator("review_fingerprint")
    @classmethod
    def review_fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "epistemic review fingerprint")

    @model_validator(mode="after")
    def review_is_bounded(self) -> Self:
        if self.expires_at <= self.created_at:
            raise ValueError("review expiry must be after creation")
        if (self.expires_at - self.created_at).total_seconds() > 7 * 24 * 60 * 60:
            raise ValueError("review expiry must be within seven days")
        if self.review_fingerprint != operator_review_fingerprint(self):
            raise ValueError("epistemic review fingerprint mismatch")
        return self


def operator_review_fingerprint(item: EpistemicOperatorReviewItem | dict[str, Any]) -> str:
    return fingerprint_model(item, "review_fingerprint")


class EpistemicAssessmentBatch(BaseModel):
    """Immutable in-memory assessment batch."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-epistemic-assessment-batch/v1"] = (
        EPISTEMIC_ASSESSMENT_BATCH_SCHEMA_VERSION
    )
    batch_id: str
    request: EpistemicAssessmentRequest
    assessments: tuple[ClaimEpistemicAssessment, ...] = Field(
        max_length=MAXIMUM_EPISTEMIC_ASSESSMENTS
    )
    assessment_count: int = Field(ge=0, le=MAXIMUM_EPISTEMIC_ASSESSMENTS)
    outcome: EpistemicAssessmentOutcome
    integrity_status: EpistemicIntegrityStatus
    operator_review_items: tuple[EpistemicOperatorReviewItem, ...] = Field(
        default_factory=tuple,
        max_length=MAXIMUM_OPERATOR_REVIEW_ITEMS,
    )
    created_at: datetime
    batch_fingerprint: str
    synthetic: Literal[True] = True
    read_only: Literal[True] = True
    redacted: Literal[True] = True
    persistent_write_applied: Literal[False] = False
    runtime_effect: Literal[False] = False

    @field_validator("batch_id")
    @classmethod
    def batch_id_is_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "epistemic assessment batch_id")

    @field_validator("created_at")
    @classmethod
    def created_at_is_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value, "epistemic batch timestamp")

    @field_validator("batch_fingerprint")
    @classmethod
    def batch_fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "epistemic batch fingerprint")

    @model_validator(mode="after")
    def batch_is_consistent(self) -> Self:
        if self.assessment_count != len(self.assessments):
            raise ValueError("assessment_count must match assessments")
        if tuple(item.claim_id for item in self.assessments) != self.request.claim_ids:
            raise ValueError("assessment order must match request claim order")
        if len({item.assessment_id for item in self.assessments}) != len(self.assessments):
            raise ValueError("assessment IDs must be unique")
        if self.batch_fingerprint != epistemic_assessment_batch_fingerprint(self):
            raise ValueError("epistemic assessment batch fingerprint mismatch")
        return self


def epistemic_assessment_batch_fingerprint(
    batch: EpistemicAssessmentBatch | dict[str, Any],
) -> str:
    return fingerprint_model(batch, "batch_fingerprint")


class EpistemicAssessmentQuery(BaseModel):
    """Bounded exact query over an in-memory batch."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-epistemic-assessment-query/v1"] = (
        EPISTEMIC_ASSESSMENT_QUERY_SCHEMA_VERSION
    )
    assessment_id: str | None = None
    claim_id: str | None = None
    status: EpistemicAssessmentStatus | None = None
    confidence_band: ConfidenceBand | None = None
    freshness_status: FreshnessStatus | None = None
    scope_applicability: ScopeApplicability | None = None
    contradiction_status: ContradictionStatus | None = None
    explicit_abstention: bool | None = None
    limit: int = Field(default=MAXIMUM_QUERY_RESULTS, ge=1, le=MAXIMUM_QUERY_RESULTS)

    @field_validator("assessment_id", "claim_id")
    @classmethod
    def query_ids_are_safe(cls, value: str | None) -> str | None:
        if value is not None:
            return validate_safe_identifier(value, "epistemic query identifier")
        return value


class EpistemicAssessmentQueryResult(BaseModel):
    """Deterministic exact query result."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-epistemic-assessment-query/v1"] = (
        EPISTEMIC_ASSESSMENT_QUERY_SCHEMA_VERSION
    )
    query: EpistemicAssessmentQuery
    results: tuple[ClaimEpistemicAssessment, ...] = Field(max_length=MAXIMUM_QUERY_RESULTS)
    result_count: int = Field(ge=0, le=MAXIMUM_QUERY_RESULTS)
    truncated: bool
    query_fingerprint: str
    runtime_effect: Literal[False] = False

    @field_validator("query_fingerprint")
    @classmethod
    def query_fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "epistemic query result fingerprint")

    @model_validator(mode="after")
    def query_result_is_consistent(self) -> Self:
        if self.result_count != len(self.results):
            raise ValueError("result_count must match query results")
        if self.query_fingerprint != epistemic_query_result_fingerprint(self):
            raise ValueError("epistemic query result fingerprint mismatch")
        return self


def epistemic_query_result_fingerprint(
    result: EpistemicAssessmentQueryResult | dict[str, Any],
) -> str:
    return fingerprint_model(result, "query_fingerprint")


class EpistemicResourceBudget(BaseModel):
    """AION-210-KI-0004 resource budget with persistent writes at zero."""

    model_config = LOCAL_FROZEN_MODEL_CONFIG

    maximum_claims_per_assessment_batch: Literal[500] = 500
    maximum_evidence_bindings_per_claim: Literal[100] = 100
    maximum_source_registry_references_per_claim: Literal[50] = 50
    maximum_citation_references_per_claim: Literal[50] = 50
    maximum_lineage_groups_per_claim: Literal[20] = 20
    maximum_relation_edges_per_claim: Literal[100] = 100
    maximum_reason_codes_per_assessment: Literal[50] = 50
    maximum_operator_review_items: Literal[500] = 500
    maximum_epistemic_assessments: Literal[500] = 500
    maximum_confidence_calculations: Literal[500] = 500
    maximum_benchmark_cases: Literal[1000] = 1000
    maximum_query_results: Literal[1000] = 1000
    maximum_fixture_records: Literal[5000] = 5000
    maximum_fixture_bytes: Literal[4194304] = 4_194_304
    maximum_concurrent_assessments: Literal[4] = 4
    maximum_persistent_assessment_write_batch: Literal[0] = 0
    maximum_source_body_bytes: Literal[0] = 0
    maximum_automatic_claim_extractions: Literal[0] = 0
    maximum_absolute_truth_decisions: Literal[0] = 0
    maximum_automatic_claim_acceptances: Literal[0] = 0
    maximum_automatic_claim_rejections: Literal[0] = 0
    maximum_contradiction_resolutions: Literal[0] = 0
    maximum_knowledge_promotions: Literal[0] = 0
    maximum_belief_mutations: Literal[0] = 0
    maximum_network_calls: Literal[0] = 0
    maximum_search_provider_calls: Literal[0] = 0
    maximum_connector_calls: Literal[0] = 0
    maximum_provider_model_calls: Literal[0] = 0
    maximum_source_mutations: Literal[0] = 0
    maximum_git_operations: Literal[0] = 0
    maximum_runtime_created_pull_requests: Literal[0] = 0
    maximum_approvals_created: Literal[0] = 0
    maximum_deployments: Literal[0] = 0
    maximum_model_weight_changes: Literal[0] = 0


class EpistemicResourceUsage(BaseModel):
    """Measured assessment usage."""

    model_config = LOCAL_FROZEN_MODEL_CONFIG

    claims_per_assessment_batch: int = Field(default=0, ge=0)
    evidence_bindings_per_claim: int = Field(default=0, ge=0)
    source_registry_references_per_claim: int = Field(default=0, ge=0)
    citation_references_per_claim: int = Field(default=0, ge=0)
    lineage_groups_per_claim: int = Field(default=0, ge=0)
    relation_edges_per_claim: int = Field(default=0, ge=0)
    reason_codes_per_assessment: int = Field(default=0, ge=0)
    operator_review_items: int = Field(default=0, ge=0)
    epistemic_assessments: int = Field(default=0, ge=0)
    confidence_calculations: int = Field(default=0, ge=0)
    benchmark_cases: int = Field(default=0, ge=0)
    query_results: int = Field(default=0, ge=0)
    fixture_records: int = Field(default=0, ge=0)
    fixture_bytes: int = Field(default=0, ge=0)
    concurrent_assessments: int = Field(default=0, ge=0)
    persistent_assessment_write_batch: int = Field(default=0, ge=0)
    source_body_bytes: int = Field(default=0, ge=0)
    automatic_claim_extractions: int = Field(default=0, ge=0)
    absolute_truth_decisions: int = Field(default=0, ge=0)
    automatic_claim_acceptances: int = Field(default=0, ge=0)
    automatic_claim_rejections: int = Field(default=0, ge=0)
    contradiction_resolutions: int = Field(default=0, ge=0)
    knowledge_promotions: int = Field(default=0, ge=0)
    belief_mutations: int = Field(default=0, ge=0)
    network_calls: int = Field(default=0, ge=0)
    search_provider_calls: int = Field(default=0, ge=0)
    connector_calls: int = Field(default=0, ge=0)
    provider_model_calls: int = Field(
        default=0,
        ge=0,
        alias="provider_model_calls",
    )
    source_mutations: int = Field(default=0, ge=0)
    git_operations: int = Field(default=0, ge=0)
    runtime_created_pull_requests: int = Field(default=0, ge=0)
    approvals_created: int = Field(default=0, ge=0)
    deployments: int = Field(default=0, ge=0)
    model_weight_changes: int = Field(default=0, ge=0)


class EpistemicBudgetDecision(BaseModel):
    """Budget decision for assessment work."""

    model_config = FROZEN_MODEL_CONFIG

    within_budget: bool
    usage: EpistemicResourceUsage
    budget: EpistemicResourceBudget
    reason_codes: tuple[str, ...]
    persistent_write_allowed: Literal[False] = False
    operator_review_required: Literal[True] = True
    decision_fingerprint: str
    runtime_effect: Literal[False] = False

    @field_validator("reason_codes")
    @classmethod
    def budget_reason_codes_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_epistemic_reason_codes(value)

    @field_validator("decision_fingerprint")
    @classmethod
    def decision_fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "epistemic budget decision fingerprint")

    @model_validator(mode="after")
    def decision_fingerprint_matches(self) -> Self:
        if self.decision_fingerprint != epistemic_budget_decision_fingerprint(self):
            raise ValueError("epistemic budget decision fingerprint mismatch")
        return self


def epistemic_budget_decision_fingerprint(
    decision: EpistemicBudgetDecision | dict[str, Any],
) -> str:
    return fingerprint_model(decision, "decision_fingerprint")


class EpistemicAssessmentFixtureEnvelope(BaseModel):
    """Explicit local synthetic fixture containing source and graph records."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-epistemic-assessment-fixture/v1"] = (
        EPISTEMIC_ASSESSMENT_FIXTURE_SCHEMA_VERSION
    )
    program_id: Literal["AION-KNOWLEDGE-INTELLIGENCE-001"] = PROGRAM_ID
    authorization_transaction_id: Literal["AION-210-KI-0004"] = AUTHORIZATION_TRANSACTION_ID
    implementation_task: Literal["AION-211"] = IMPLEMENTATION_TASK
    formal_closeout_task: Literal["AION-212"] = FORMAL_CLOSEOUT_TASK
    authorization_scope: Literal[
        "deterministic-evidence-corroboration-contradiction-freshness-source-independence-confidence-assessment-core"
    ] = AUTHORIZATION_SCOPE
    request: EpistemicAssessmentRequest
    source_registry_records: tuple[Any, ...] = Field(max_length=MAXIMUM_FIXTURE_RECORDS)
    claim_graph_records: tuple[Any, ...] = Field(max_length=MAXIMUM_FIXTURE_RECORDS)
    synthetic: Literal[True] = True
    read_only: Literal[True] = True
    redacted: Literal[True] = True
    persistent_write_applied: Literal[False] = False
    runtime_effect: Literal[False] = False
    fixture_fingerprint: str

    @field_validator("fixture_fingerprint")
    @classmethod
    def fixture_fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "epistemic fixture fingerprint")

    @model_validator(mode="after")
    def fixture_is_fingerprinted(self) -> Self:
        if self.fixture_fingerprint != epistemic_fixture_fingerprint(self):
            raise ValueError("epistemic fixture fingerprint mismatch")
        return self


def epistemic_fixture_fingerprint(
    fixture: EpistemicAssessmentFixtureEnvelope | dict[str, Any],
) -> str:
    return fingerprint_model(fixture, "fixture_fingerprint")


class EpistemicIntegrityFinding(BaseModel):
    """Redacted assessment integrity finding."""

    model_config = FROZEN_MODEL_CONFIG

    finding_id: str
    severity: Literal["low", "medium", "high", "critical"]
    reason_codes: tuple[str, ...]
    assessment_id: str | None = None
    claim_id: str | None = None
    bounded_count: int | None = Field(default=None, ge=0)
    redacted_summary: str = Field(max_length=240)
    runtime_effect: Literal[False] = False

    @field_validator("finding_id", "assessment_id", "claim_id")
    @classmethod
    def finding_ids_are_safe(cls, value: str | None) -> str | None:
        if value is not None:
            return validate_safe_identifier(value, "epistemic integrity identifier")
        return value

    @field_validator("reason_codes")
    @classmethod
    def finding_reason_codes_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_epistemic_reason_codes(value)

    @field_validator("redacted_summary")
    @classmethod
    def finding_summary_is_safe(cls, value: str) -> str:
        _reject_leaky_text(value, "epistemic integrity summary")
        return value


class EpistemicAssessmentIntegrityReport(BaseModel):
    """Integrity audit report for a redacted assessment batch."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-epistemic-assessment-integrity/v1"] = (
        EPISTEMIC_ASSESSMENT_INTEGRITY_SCHEMA_VERSION
    )
    status: EpistemicIntegrityStatus
    assessment_count: int = Field(ge=0)
    validated_assessment_count: int = Field(ge=0)
    findings: tuple[EpistemicIntegrityFinding, ...]
    reason_codes: tuple[str, ...]
    audit_timestamp: datetime
    report_fingerprint: str
    runtime_effect: Literal[False] = False

    @field_validator("reason_codes")
    @classmethod
    def report_reason_codes_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_epistemic_reason_codes(value)

    @field_validator("audit_timestamp")
    @classmethod
    def audit_timestamp_is_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value, "epistemic integrity audit timestamp")

    @field_validator("report_fingerprint")
    @classmethod
    def report_fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "epistemic integrity report fingerprint")

    @model_validator(mode="after")
    def report_fingerprint_matches(self) -> Self:
        if self.report_fingerprint != epistemic_integrity_report_fingerprint(self):
            raise ValueError("epistemic integrity report fingerprint mismatch")
        return self


def epistemic_integrity_report_fingerprint(
    report: EpistemicAssessmentIntegrityReport | dict[str, Any],
) -> str:
    return fingerprint_model(report, "report_fingerprint")


class EpistemicIncidentRecord(BaseModel):
    """Redacted epistemic incident record."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-epistemic-assessment-evidence/v1"] = (
        EPISTEMIC_ASSESSMENT_EVIDENCE_SCHEMA_VERSION
    )
    incident_id: str
    reason_codes: tuple[str, ...]
    severity: Literal["low", "medium", "high"]
    redacted_summary: str = Field(max_length=240)
    created_at: datetime
    incident_fingerprint: str
    runtime_effect: Literal[False] = False

    @field_validator("incident_id")
    @classmethod
    def incident_id_is_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "epistemic incident")

    @field_validator("reason_codes")
    @classmethod
    def incident_reason_codes_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_epistemic_reason_codes(value)

    @field_validator("redacted_summary")
    @classmethod
    def incident_summary_is_safe(cls, value: str) -> str:
        _reject_leaky_text(value, "epistemic incident summary")
        return value

    @field_validator("created_at")
    @classmethod
    def incident_timestamp_is_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value, "epistemic incident timestamp")

    @field_validator("incident_fingerprint")
    @classmethod
    def incident_fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "epistemic incident fingerprint")

    @model_validator(mode="after")
    def incident_fingerprint_matches(self) -> Self:
        if self.incident_fingerprint != epistemic_incident_fingerprint(self):
            raise ValueError("epistemic incident fingerprint mismatch")
        return self


def epistemic_incident_fingerprint(incident: EpistemicIncidentRecord | dict[str, Any]) -> str:
    return fingerprint_model(incident, "incident_fingerprint")


class EpistemicDiagnostics(BaseModel):
    """Redacted diagnostics with counts and safe statuses only."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-epistemic-assessment-evidence/v1"] = (
        EPISTEMIC_ASSESSMENT_EVIDENCE_SCHEMA_VERSION
    )
    batch_id: str
    status_counts: dict[EpistemicAssessmentStatus, int]
    confidence_band_counts: dict[ConfidenceBand, int]
    abstention_count: int = Field(ge=0)
    integrity_status: EpistemicIntegrityStatus
    reason_codes: tuple[str, ...]
    diagnostics_fingerprint: str
    read_only: Literal[True] = True
    redacted: Literal[True] = True
    runtime_effect: Literal[False] = False

    @field_validator("batch_id")
    @classmethod
    def diagnostics_batch_id_is_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "epistemic diagnostics batch_id")

    @field_validator("reason_codes")
    @classmethod
    def diagnostics_reason_codes_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_epistemic_reason_codes(value)

    @field_validator("diagnostics_fingerprint")
    @classmethod
    def diagnostics_fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "epistemic diagnostics fingerprint")

    @model_validator(mode="after")
    def diagnostics_fingerprint_matches(self) -> Self:
        if self.diagnostics_fingerprint != epistemic_diagnostics_fingerprint(self):
            raise ValueError("epistemic diagnostics fingerprint mismatch")
        return self


def epistemic_diagnostics_fingerprint(diagnostics: EpistemicDiagnostics | dict[str, Any]) -> str:
    return fingerprint_model(diagnostics, "diagnostics_fingerprint")


class EpistemicAssessmentEvidenceBundle(BaseModel):
    """Safe evidence bundle for operator review."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-epistemic-assessment-evidence/v1"] = (
        EPISTEMIC_ASSESSMENT_EVIDENCE_SCHEMA_VERSION
    )
    batch_id: str
    assessment_ids: tuple[str, ...]
    confidence_bands: tuple[ConfidenceBand, ...]
    statuses: tuple[EpistemicAssessmentStatus, ...]
    hard_cap_ids: tuple[str, ...]
    reason_codes: tuple[str, ...]
    integrity_status: EpistemicIntegrityStatus
    authorization_transaction_id: Literal["AION-210-KI-0004"] = AUTHORIZATION_TRANSACTION_ID
    implementation_task: Literal["AION-211"] = IMPLEMENTATION_TASK
    formal_closeout_task: Literal["AION-212"] = FORMAL_CLOSEOUT_TASK
    epistemic_truth_engine_runtime_enabled: Literal[False] = False
    persistent_assessment_write_enabled: Literal[False] = False
    runtime_effect: Literal[False] = False
    evidence_fingerprint: str

    @field_validator("batch_id")
    @classmethod
    def bundle_batch_id_is_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "epistemic evidence batch_id")

    @field_validator("assessment_ids")
    @classmethod
    def bundle_assessment_ids_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if len(set(value)) != len(value):
            raise ValueError("duplicate evidence assessment IDs rejected")
        return tuple(
            validate_safe_identifier(item, "epistemic evidence assessment") for item in value
        )

    @field_validator("hard_cap_ids")
    @classmethod
    def bundle_cap_ids_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for cap_id in value:
            if cap_id not in HARD_CAP_ORDER:
                raise ValueError("unknown hard cap ID")
        return tuple(value)

    @field_validator("reason_codes")
    @classmethod
    def bundle_reason_codes_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_epistemic_reason_codes(value)

    @field_validator("evidence_fingerprint")
    @classmethod
    def evidence_fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "epistemic evidence bundle fingerprint")

    @model_validator(mode="after")
    def bundle_fingerprint_matches(self) -> Self:
        if self.evidence_fingerprint != epistemic_evidence_bundle_fingerprint(self):
            raise ValueError("epistemic evidence bundle fingerprint mismatch")
        return self


def epistemic_evidence_bundle_fingerprint(
    bundle: EpistemicAssessmentEvidenceBundle | dict[str, Any],
) -> str:
    return fingerprint_model(bundle, "evidence_fingerprint")


def evaluate_epistemic_budget(
    usage: EpistemicResourceUsage,
    budget: EpistemicResourceBudget | None = None,
) -> EpistemicBudgetDecision:
    """Evaluate usage against the exact AION-210-KI-0004 budget."""

    current_budget = budget or EpistemicResourceBudget()
    violations: list[str] = []
    checks = (
        (usage.claims_per_assessment_batch, current_budget.maximum_claims_per_assessment_batch),
        (usage.evidence_bindings_per_claim, current_budget.maximum_evidence_bindings_per_claim),
        (
            usage.source_registry_references_per_claim,
            current_budget.maximum_source_registry_references_per_claim,
        ),
        (usage.citation_references_per_claim, current_budget.maximum_citation_references_per_claim),
        (usage.lineage_groups_per_claim, current_budget.maximum_lineage_groups_per_claim),
        (usage.relation_edges_per_claim, current_budget.maximum_relation_edges_per_claim),
        (usage.reason_codes_per_assessment, current_budget.maximum_reason_codes_per_assessment),
        (usage.operator_review_items, current_budget.maximum_operator_review_items),
        (usage.epistemic_assessments, current_budget.maximum_epistemic_assessments),
        (usage.confidence_calculations, current_budget.maximum_confidence_calculations),
        (usage.benchmark_cases, current_budget.maximum_benchmark_cases),
        (usage.query_results, current_budget.maximum_query_results),
        (usage.fixture_records, current_budget.maximum_fixture_records),
        (usage.fixture_bytes, current_budget.maximum_fixture_bytes),
        (usage.concurrent_assessments, current_budget.maximum_concurrent_assessments),
    )
    if any(used > limit for used, limit in checks):
        violations.append("epistemic_assessment_request_invalid")
    forbidden = {
        "persistent_assessment_write_batch": usage.persistent_assessment_write_batch,
        "source_body_bytes": usage.source_body_bytes,
        "automatic_claim_extractions": usage.automatic_claim_extractions,
        "absolute_truth_decisions": usage.absolute_truth_decisions,
        "automatic_claim_acceptances": usage.automatic_claim_acceptances,
        "automatic_claim_rejections": usage.automatic_claim_rejections,
        "contradiction_resolutions": usage.contradiction_resolutions,
        "knowledge_promotions": usage.knowledge_promotions,
        "belief_mutations": usage.belief_mutations,
        "network_calls": usage.network_calls,
        "search_provider_calls": usage.search_provider_calls,
        "connector_calls": usage.connector_calls,
        "provider_model_calls": usage.provider_model_calls,
        "source_mutations": usage.source_mutations,
        "git_operations": usage.git_operations,
        "runtime_created_pull_requests": usage.runtime_created_pull_requests,
        "approvals_created": usage.approvals_created,
        "deployments": usage.deployments,
        "model_weight_changes": usage.model_weight_changes,
    }
    if any(value > 0 for value in forbidden.values()):
        violations.extend(
            (
                "epistemic_persistent_write_disabled",
                "epistemic_absolute_truth_oracle_blocked",
                "epistemic_automatic_claim_acceptance_blocked",
                "epistemic_automatic_claim_rejection_blocked",
                "epistemic_knowledge_promotion_blocked",
                "epistemic_belief_mutation_blocked",
                "epistemic_network_fetch_blocked",
                "epistemic_runtime_disabled",
            )
        )
    reason_codes = tuple(dict.fromkeys(violations or ["epistemic_assessment_request_valid"]))
    payload = {
        "within_budget": not violations,
        "usage": usage.model_dump(mode="json", by_alias=True),
        "budget": current_budget.model_dump(mode="json", by_alias=True),
        "reason_codes": reason_codes,
        "persistent_write_allowed": False,
        "operator_review_required": True,
        "runtime_effect": False,
    }
    return EpistemicBudgetDecision(
        within_budget=not violations,
        usage=usage,
        budget=current_budget,
        reason_codes=reason_codes,
        decision_fingerprint=fingerprint_payload(_json_ready(payload)),
    )


def _reject_leaky_text(value: str, field_name: str) -> None:
    reject_protected_material(value, field_name)
    lowered = value.lower()
    prohibited = (
        "http://",
        "https://",
        "?",
        "traceback",
        "exception",
        "claim statement",
        "source preview",
        "source body",
        "raw url",
        "object display",
    )
    if any(marker in lowered for marker in prohibited):
        raise ValueError(f"{field_name} must remain redacted")


def _json_ready(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return _json_ready(value.model_dump(mode="json", by_alias=True))
    if isinstance(value, Decimal):
        return format(quantize_score(value), "f")
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, datetime):
        text = value.isoformat()
        return f"{text[:-6]}Z" if text.endswith("+00:00") else text
    if isinstance(value, MappingProxyType):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in sorted(value.items())}
    if isinstance(value, (tuple, list)):
        return [_json_ready(item) for item in value]
    if isinstance(value, set | frozenset):
        return sorted(_json_ready(item) for item in value)
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("non-finite value rejected")
        return value
    return value


__all__ = [
    "APPROVAL_RECORD_ID",
    "AUTHORIZATION_SCOPE",
    "AUTHORIZATION_TRANSACTION_ID",
    "CLAIM_EPISTEMIC_ASSESSMENT_SCHEMA_VERSION",
    "EPISTEMIC_ASSESSMENT_BATCH_SCHEMA_VERSION",
    "EPISTEMIC_ASSESSMENT_CONTRACT_SCHEMA_VERSION",
    "EPISTEMIC_ASSESSMENT_EVIDENCE_SCHEMA_VERSION",
    "EPISTEMIC_ASSESSMENT_FIXTURE_SCHEMA_VERSION",
    "EPISTEMIC_ASSESSMENT_INTEGRITY_SCHEMA_VERSION",
    "EPISTEMIC_ASSESSMENT_POLICY_SCHEMA_VERSION",
    "EPISTEMIC_ASSESSMENT_QUERY_SCHEMA_VERSION",
    "EPISTEMIC_ASSESSMENT_REQUEST_SCHEMA_VERSION",
    "EPISTEMIC_REASON_CODE_REGISTRY_VERSION",
    "EPISTEMIC_SCORECARD_SCHEMA_VERSION",
    "EPISTEMIC_SCORECARD_VERSION",
    "FORMAL_CLOSEOUT_TASK",
    "IMPLEMENTATION_TASK",
    "MAXIMUM_PERSISTENT_ASSESSMENT_WRITE_BATCH",
    "PROGRAM_ID",
    "ROLE_SCORE_WEIGHTS",
    "SOURCE_QUALITY_METADATA_FACTORS",
    "ClaimEpistemicAssessment",
    "ConfidenceBand",
    "ContradictionStatus",
    "EpistemicAssessmentBatch",
    "EpistemicAssessmentEvidenceBundle",
    "EpistemicAssessmentFixtureEnvelope",
    "EpistemicAssessmentIntegrityReport",
    "EpistemicAssessmentOutcome",
    "EpistemicAssessmentQuery",
    "EpistemicAssessmentQueryResult",
    "EpistemicAssessmentRequest",
    "EpistemicAssessmentStatus",
    "EpistemicBudgetDecision",
    "EpistemicDiagnostics",
    "EpistemicFreshnessPolicy",
    "EpistemicHardCapApplication",
    "EpistemicIncidentRecord",
    "EpistemicIntegrityFinding",
    "EpistemicIntegrityStatus",
    "EpistemicOperatorReviewItem",
    "EpistemicResourceBudget",
    "EpistemicResourceUsage",
    "EpistemicScorecard",
    "EpistemicScorecardPolicy",
    "EpistemicTargetScope",
    "EvidenceContribution",
    "EvidenceGroupDisposition",
    "FreshnessStatus",
    "HARD_CAP_ORDER",
    "ROLE_EVIDENCE_SCORE_SCHEMA_VERSION",
    "RoleEvidenceScore",
    "ScopeApplicability",
    "claim_epistemic_assessment_fingerprint",
    "confidence_band_for",
    "default_scorecard_policy",
    "default_scorecard_policy_payload",
    "epistemic_assessment_batch_fingerprint",
    "epistemic_budget_decision_fingerprint",
    "epistemic_diagnostics_fingerprint",
    "epistemic_evidence_bundle_fingerprint",
    "epistemic_fixture_fingerprint",
    "epistemic_freshness_policy_fingerprint",
    "epistemic_incident_fingerprint",
    "epistemic_integrity_report_fingerprint",
    "epistemic_query_result_fingerprint",
    "epistemic_scorecard_fingerprint",
    "epistemic_scorecard_policy_fingerprint",
    "epistemic_target_scope_fingerprint",
    "evaluate_epistemic_budget",
    "evidence_contribution_fingerprint",
    "hard_cap_fingerprint",
    "json_size",
    "operator_review_fingerprint",
    "quantize_score",
    "role_evidence_score_fingerprint",
    "validate_epistemic_reason_codes",
]
