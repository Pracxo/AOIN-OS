"""Append-only source provenance registry contracts."""

from __future__ import annotations

import re
from collections.abc import Mapping
from datetime import datetime, timedelta
from typing import Any, Literal, Self

from pydantic import BaseModel, Field, field_validator, model_validator

from aion_brain.contracts.knowledge_research import (
    FROZEN_MODEL_CONFIG,
    CitationLocatorKind,
    LicencePolicyStatus,
    ResearchAdapterType,
    ResearchContentType,
    ResearchSourceClass,
    RobotsPolicyStatus,
    SourceLineageKind,
    ensure_utc,
    fingerprint_payload,
    reject_protected_material,
    validate_hex64,
    validate_safe_identifier,
)

PROGRAM_ID: Literal["AION-KNOWLEDGE-INTELLIGENCE-001"] = "AION-KNOWLEDGE-INTELLIGENCE-001"
AUTHORIZATION_TRANSACTION_ID: Literal["AION-206-KI-0002"] = "AION-206-KI-0002"
APPROVAL_RECORD_ID: Literal["AION-206-KI-0002"] = "AION-206-KI-0002"
IMPLEMENTATION_TASK: Literal["AION-207"] = "AION-207"
FORMAL_CLOSEOUT_TASK: Literal["AION-208"] = "AION-208"
AUTHORIZATION_SCOPE: Literal[
    "append-only-immutable-source-snapshot-provenance-lineage-citation-registry-core"
] = "append-only-immutable-source-snapshot-provenance-lineage-citation-registry-core"

SOURCE_REGISTRY_CONTRACT_SCHEMA_VERSION = "aion-knowledge-source-registry/v1"
SOURCE_REGISTRY_RECORD_ENVELOPE_SCHEMA_VERSION: Literal[
    "aion-knowledge-source-registry-record-envelope/v1"
] = "aion-knowledge-source-registry-record-envelope/v1"
SOURCE_REGISTRY_BATCH_SCHEMA_VERSION: Literal["aion-knowledge-source-registry-batch/v1"] = (
    "aion-knowledge-source-registry-batch/v1"
)
SOURCE_REGISTRY_STATE_SCHEMA_VERSION = "aion-knowledge-source-registry-state/v1"
SOURCE_REGISTRY_INDEX_SCHEMA_VERSION = "aion-knowledge-source-registry-index/v1"
SOURCE_REGISTRY_INTEGRITY_SCHEMA_VERSION = "aion-knowledge-source-registry-integrity/v1"
SOURCE_REGISTRY_QUERY_SCHEMA_VERSION = "aion-knowledge-source-registry-query/v1"
SOURCE_REGISTRY_EVIDENCE_SCHEMA_VERSION = "aion-knowledge-source-registry-evidence/v1"
SOURCE_REGISTRY_FIXTURE_SCHEMA_VERSION = "aion-knowledge-source-registry-fixture/v1"
SOURCE_REGISTRY_RESOURCE_BUDGET_SCHEMA_VERSION: Literal[
    "aion-knowledge-source-registry-resource-budget/v1"
] = "aion-knowledge-source-registry-resource-budget/v1"
SOURCE_REGISTRY_APPEND_DECISION_SCHEMA_VERSION: Literal[
    "aion-knowledge-source-registry-append-decision/v1"
] = "aion-knowledge-source-registry-append-decision/v1"
SOURCE_REGISTRY_REASON_CODE_REGISTRY_VERSION = "aion-knowledge-source-registry-reasons/v1"

MAXIMUM_REGISTRY_RECORDS_PER_PLAN = 100
MAXIMUM_RECORD_ENVELOPE_BYTES = 8192
MAXIMUM_METADATA_BYTES_PER_RECORD = 4096
MAXIMUM_LINEAGE_EDGES_PER_RECORD = 20
MAXIMUM_CITATION_REFERENCES_PER_RECORD = 20
MAXIMUM_REGISTRY_WRITE_BATCH = 0
MAXIMUM_PERSISTED_SOURCE_BODY_BYTES = 0
MAXIMUM_REPOSITORY_SOURCE_BODY_BYTES = 0
MAXIMUM_CLAIM_VERIFICATIONS = 0
MAXIMUM_KNOWLEDGE_PROMOTIONS = 0
MAXIMUM_BELIEF_MUTATIONS = 0
MAXIMUM_NETWORK_CALLS = 0
MAXIMUM_GIT_OPERATIONS = 0
MAXIMUM_RUNTIME_CREATED_PULL_REQUESTS = 0
MAXIMUM_APPROVALS_CREATED_BY_RUNTIME = 0
MAXIMUM_BACKGROUND_CRAWLS = 0
MAXIMUM_SEARCH_PROVIDER_CALLS = 0
MAXIMUM_CONNECTOR_CALLS = 0
MAXIMUM_MODEL_PROVIDER_CALLS = 0

SourceRegistryRecordKind = Literal[
    "source_snapshot_digest",
    "source_provenance",
    "citation_reference",
    "source_lineage",
    "deduplication_decision",
    "policy_decision",
    "operator_review_reference",
]

SOURCE_REGISTRY_REASON_CODES: tuple[str, ...] = (
    "source_registry_batch_valid",
    "source_registry_batch_invalid",
    "source_registry_record_valid",
    "source_registry_record_invalid",
    "source_registry_record_appended_in_memory",
    "source_registry_persistent_write_disabled",
    "source_registry_idempotent_replay",
    "source_registry_duplicate_identifier",
    "source_registry_changed_payload_rejected",
    "source_registry_sequence_valid",
    "source_registry_sequence_gap",
    "source_registry_sequence_duplicate",
    "source_registry_chain_valid",
    "source_registry_chain_broken",
    "source_registry_payload_fingerprint_valid",
    "source_registry_payload_fingerprint_mismatch",
    "source_registry_record_fingerprint_valid",
    "source_registry_record_fingerprint_mismatch",
    "source_registry_supersession_valid",
    "source_registry_supersession_missing",
    "source_registry_supersession_cycle",
    "source_registry_source_body_blocked",
    "source_registry_metadata_budget_satisfied",
    "source_registry_metadata_budget_exceeded",
    "source_registry_record_budget_satisfied",
    "source_registry_record_budget_exceeded",
    "source_registry_lineage_limit_satisfied",
    "source_registry_lineage_limit_exceeded",
    "source_registry_citation_limit_satisfied",
    "source_registry_citation_limit_exceeded",
    "source_registry_index_built",
    "source_registry_index_invalid",
    "source_registry_query_completed",
    "source_registry_query_limit_exceeded",
    "source_registry_fixture_replayed",
    "source_registry_fixture_rejected",
    "source_registry_claim_verification_blocked",
    "source_registry_knowledge_promotion_blocked",
    "source_registry_belief_mutation_blocked",
    "source_registry_network_fetch_blocked",
    "source_registry_runtime_disabled",
    "source_registry_operator_review_required",
    "source_registry_integrity_passed",
    "source_registry_integrity_failed",
)

_SOURCE_REGISTRY_REASON_CODES = frozenset(SOURCE_REGISTRY_REASON_CODES)
_UNSAFE_REASON_RE = re.compile(r"[/:\\\\]")


def validate_source_registry_reason_codes(values: tuple[str, ...]) -> tuple[str, ...]:
    """Validate immutable source-registry reason codes."""

    seen: set[str] = set()
    for code in values:
        if code not in _SOURCE_REGISTRY_REASON_CODES:
            raise ValueError("unknown source registry reason code")
        if code in seen:
            raise ValueError("duplicate source registry reason code")
        if _UNSAFE_REASON_RE.search(code):
            raise ValueError("source registry reason code must not embed URL, host, or path text")
        reject_protected_material(code, "source registry reason code")
        seen.add(code)
    return values


def source_registry_payload_fingerprint(payload: BaseModel | Mapping[str, object]) -> str:
    """Fingerprint one typed registry payload."""

    if isinstance(payload, BaseModel):
        return fingerprint_payload(payload.model_dump(mode="json"))
    return fingerprint_payload(_json_ready(dict(payload)))


class RegisteredSourceSnapshotDigest(BaseModel):
    """Metadata-only digest reference for one immutable source snapshot."""

    model_config = FROZEN_MODEL_CONFIG

    snapshot_id: str
    snapshot_fingerprint: str
    content_sha256: str
    original_url_fingerprint: str
    canonical_url_fingerprint: str
    content_type: ResearchContentType
    content_length: int = Field(ge=0)
    source_class: ResearchSourceClass
    robots_policy_status: RobotsPolicyStatus
    licence_policy_status: LicencePolicyStatus
    publication_timestamp: datetime | None = None
    modification_timestamp: datetime | None = None
    retrieval_timestamp: datetime
    safe_headers_fingerprint: str
    redirect_chain_fingerprint: str
    source_body_present: Literal[False] = False
    source_body_bytes: Literal[0] = 0
    verified_fact: Literal[False] = False
    knowledge_promoted: Literal[False] = False
    belief_created: Literal[False] = False
    runtime_effect: Literal[False] = False

    @field_validator("snapshot_id")
    @classmethod
    def snapshot_id_is_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "snapshot_id")

    @field_validator(
        "snapshot_fingerprint",
        "content_sha256",
        "original_url_fingerprint",
        "canonical_url_fingerprint",
        "safe_headers_fingerprint",
        "redirect_chain_fingerprint",
    )
    @classmethod
    def hashes_are_hex(cls, value: str) -> str:
        return validate_hex64(value, "source snapshot digest fingerprint")

    @field_validator(
        "publication_timestamp",
        "modification_timestamp",
        "retrieval_timestamp",
    )
    @classmethod
    def timestamps_are_utc(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return ensure_utc(value, "source snapshot digest timestamp")


class RegisteredSourceProvenance(BaseModel):
    """Metadata-only provenance reference for one snapshot."""

    model_config = FROZEN_MODEL_CONFIG

    provenance_id: str
    provenance_fingerprint: str
    snapshot_id: str
    snapshot_fingerprint: str
    content_sha256: str
    canonical_url_fingerprint: str
    source_class: ResearchSourceClass
    declared_author: str | None = Field(default=None, max_length=200)
    declared_publisher: str | None = Field(default=None, max_length=200)
    declared_title: str | None = Field(default=None, max_length=300)
    declared_publication_timestamp: datetime | None = None
    declared_modification_timestamp: datetime | None = None
    retrieval_timestamp: datetime
    redirect_chain_fingerprint: str
    destination_validation_fingerprint: str
    safe_headers_fingerprint: str
    adapter_type: ResearchAdapterType
    source_claims_verified: Literal[False] = False
    runtime_effect: Literal[False] = False

    @field_validator("provenance_id", "snapshot_id")
    @classmethod
    def ids_are_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "source provenance identifier")

    @field_validator(
        "provenance_fingerprint",
        "snapshot_fingerprint",
        "content_sha256",
        "canonical_url_fingerprint",
        "redirect_chain_fingerprint",
        "destination_validation_fingerprint",
        "safe_headers_fingerprint",
    )
    @classmethod
    def hashes_are_hex(cls, value: str) -> str:
        return validate_hex64(value, "source provenance fingerprint")

    @field_validator("declared_author", "declared_publisher", "declared_title")
    @classmethod
    def declared_metadata_is_safe(cls, value: str | None) -> str | None:
        if value is not None:
            reject_protected_material(value, "source provenance declared metadata")
        return value

    @field_validator(
        "declared_publication_timestamp",
        "declared_modification_timestamp",
        "retrieval_timestamp",
    )
    @classmethod
    def timestamps_are_utc(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return ensure_utc(value, "source provenance timestamp")


class RegisteredCitationReference(BaseModel):
    """Metadata-only citation reference that never verifies the cited claim."""

    model_config = FROZEN_MODEL_CONFIG

    citation_id: str
    citation_fingerprint: str
    snapshot_id: str
    snapshot_fingerprint: str
    content_sha256: str
    canonical_url_fingerprint: str
    locator_kind: CitationLocatorKind
    locator_value: str = Field(min_length=1, max_length=256)
    retrieval_timestamp: datetime
    claim_verified: Literal[False] = False
    runtime_effect: Literal[False] = False

    @field_validator("citation_id", "snapshot_id")
    @classmethod
    def ids_are_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "citation reference identifier")

    @field_validator(
        "citation_fingerprint",
        "snapshot_fingerprint",
        "content_sha256",
        "canonical_url_fingerprint",
    )
    @classmethod
    def hashes_are_hex(cls, value: str) -> str:
        return validate_hex64(value, "citation reference fingerprint")

    @field_validator("locator_value")
    @classmethod
    def locator_is_safe(cls, value: str) -> str:
        reject_protected_material(value, "citation locator")
        return value

    @field_validator("retrieval_timestamp")
    @classmethod
    def retrieval_timestamp_is_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value, "citation retrieval_timestamp")


class RegisteredSourceLineage(BaseModel):
    """Metadata-only lineage edge for one source snapshot."""

    model_config = FROZEN_MODEL_CONFIG

    lineage_id: str
    lineage_fingerprint: str
    snapshot_id: str
    canonical_source_snapshot_id: str
    lineage_kind: SourceLineageKind
    content_sha256: str
    canonical_url_fingerprint: str
    independence_group_id: str
    created_at: datetime
    independent_corroboration_established: Literal[False] = False
    runtime_effect: Literal[False] = False

    @field_validator("lineage_id", "snapshot_id", "canonical_source_snapshot_id")
    @classmethod
    def ids_are_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "source lineage identifier")

    @field_validator("independence_group_id")
    @classmethod
    def group_id_is_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "independence_group_id")

    @field_validator("lineage_fingerprint", "content_sha256", "canonical_url_fingerprint")
    @classmethod
    def hashes_are_hex(cls, value: str) -> str:
        return validate_hex64(value, "source lineage fingerprint")

    @field_validator("created_at")
    @classmethod
    def created_at_is_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value, "source lineage created_at")


class RegisteredDeduplicationDecision(BaseModel):
    """Metadata-only exact deduplication decision, not a truth decision."""

    model_config = FROZEN_MODEL_CONFIG

    decision_id: str
    decision_fingerprint: str
    snapshot_id: str
    exact_url_duplicate: bool
    canonical_url_duplicate: bool
    exact_content_duplicate: bool
    redirect_alias: bool
    suspected_mirror: bool
    independence_group_id: str
    independent_source_count: int = Field(ge=0)
    reason_codes: tuple[str, ...]
    created_at: datetime
    claim_corroboration_established: Literal[False] = False
    runtime_effect: Literal[False] = False

    @field_validator("decision_id", "snapshot_id", "independence_group_id")
    @classmethod
    def ids_are_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "deduplication identifier")

    @field_validator("decision_fingerprint")
    @classmethod
    def fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "deduplication fingerprint")

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_source_registry_reason_codes(value)

    @field_validator("created_at")
    @classmethod
    def created_at_is_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value, "deduplication created_at")


class RegisteredPolicyDecision(BaseModel):
    """Metadata-only source policy decision with no runtime or truth effect."""

    model_config = FROZEN_MODEL_CONFIG

    policy_decision_id: str
    policy_decision_fingerprint: str
    snapshot_id: str
    snapshot_fingerprint: str
    source_class: ResearchSourceClass
    robots_policy_status: RobotsPolicyStatus
    licence_policy_status: LicencePolicyStatus
    reason_codes: tuple[str, ...]
    created_at: datetime
    claim_verified: Literal[False] = False
    knowledge_promoted: Literal[False] = False
    belief_mutated: Literal[False] = False
    runtime_effect: Literal[False] = False

    @field_validator("policy_decision_id", "snapshot_id")
    @classmethod
    def ids_are_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "source registry policy decision identifier")

    @field_validator("policy_decision_fingerprint", "snapshot_fingerprint")
    @classmethod
    def fingerprints_are_hex(cls, value: str) -> str:
        return validate_hex64(value, "source registry policy decision fingerprint")

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_source_registry_reason_codes(value)

    @field_validator("created_at")
    @classmethod
    def created_at_is_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value, "source registry policy decision created_at")


class RegisteredOperatorReviewReference(BaseModel):
    """Operator-review reference that cannot become an approval record."""

    model_config = FROZEN_MODEL_CONFIG

    review_item_id: str
    plan_id: str
    source_snapshot_ids: tuple[str, ...]
    evidence_bundle_fingerprint: str
    operator_review_required: Literal[True] = True
    claim_verification_required: Literal[True] = True
    persistent_write_authorization_required: Literal[True] = True
    knowledge_promotion_authorized: Literal[False] = False
    belief_mutation_authorized: Literal[False] = False
    approval_created: Literal[False] = False
    implementation_authorization_created: Literal[False] = False
    created_at: datetime
    expires_at: datetime
    runtime_effect: Literal[False] = False

    @field_validator("review_item_id", "plan_id")
    @classmethod
    def ids_are_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "operator review identifier")

    @field_validator("source_snapshot_ids")
    @classmethod
    def snapshot_ids_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if len(set(value)) != len(value):
            raise ValueError("duplicate source snapshot IDs are rejected")
        for item in value:
            validate_safe_identifier(item, "source_snapshot_id")
        return value

    @field_validator("evidence_bundle_fingerprint")
    @classmethod
    def fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "operator review evidence fingerprint")

    @field_validator("created_at", "expires_at")
    @classmethod
    def timestamps_are_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value, "operator review timestamp")

    @model_validator(mode="after")
    def expiry_is_bounded(self) -> Self:
        if self.expires_at <= self.created_at:
            raise ValueError("operator review expiry must be after creation")
        if self.expires_at - self.created_at > timedelta(days=7):
            raise ValueError("operator review expiry must be within seven days")
        return self


SourceRegistryPayload = (
    RegisteredSourceSnapshotDigest
    | RegisteredSourceProvenance
    | RegisteredCitationReference
    | RegisteredSourceLineage
    | RegisteredDeduplicationDecision
    | RegisteredPolicyDecision
    | RegisteredOperatorReviewReference
)


class SourceRegistryRecordEnvelope(BaseModel):
    """Append-only envelope around one typed source-registry payload."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-source-registry-record-envelope/v1"] = (
        SOURCE_REGISTRY_RECORD_ENVELOPE_SCHEMA_VERSION
    )
    record_id: str
    record_kind: SourceRegistryRecordKind
    sequence_number: int = Field(ge=1)
    record_version: int = Field(ge=1)
    supersedes_record_id: str | None = None
    program_id: Literal["AION-KNOWLEDGE-INTELLIGENCE-001"] = PROGRAM_ID
    authorization_transaction_id: Literal["AION-206-KI-0002"] = AUTHORIZATION_TRANSACTION_ID
    implementation_task: Literal["AION-207"] = IMPLEMENTATION_TASK
    formal_closeout_task: Literal["AION-208"] = FORMAL_CLOSEOUT_TASK
    authorization_scope: Literal[
        "append-only-immutable-source-snapshot-provenance-lineage-citation-registry-core"
    ] = AUTHORIZATION_SCOPE
    payload: SourceRegistryPayload
    payload_fingerprint: str
    previous_record_fingerprint: str | None = None
    created_at: datetime
    record_fingerprint: str
    synthetic: Literal[True] = True
    read_only: Literal[True] = True
    redacted: Literal[True] = True
    append_only: Literal[True] = True
    source_body_present: Literal[False] = False
    source_body_bytes: Literal[0] = 0
    claim_verified: Literal[False] = False
    knowledge_promoted: Literal[False] = False
    belief_created: Literal[False] = False
    belief_mutated: Literal[False] = False
    persistent_write_applied: Literal[False] = False
    runtime_effect: Literal[False] = False

    @field_validator("record_id")
    @classmethod
    def record_id_is_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "record_id")

    @field_validator("supersedes_record_id")
    @classmethod
    def supersedes_record_id_is_safe(cls, value: str | None) -> str | None:
        if value is not None:
            return validate_safe_identifier(value, "supersedes_record_id")
        return value

    @field_validator("payload_fingerprint", "previous_record_fingerprint", "record_fingerprint")
    @classmethod
    def fingerprints_are_hex(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return validate_hex64(value, "source registry envelope fingerprint")

    @field_validator("created_at")
    @classmethod
    def created_at_is_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value, "source registry record created_at")

    @model_validator(mode="after")
    def envelope_invariants_hold(self) -> Self:
        if self.payload_fingerprint != source_registry_payload_fingerprint(self.payload):
            raise ValueError("payload fingerprint mismatch")
        if self.record_version == 1 and self.supersedes_record_id is not None:
            raise ValueError("initial record must not supersede another record")
        if self.record_version > 1 and self.supersedes_record_id is None:
            raise ValueError("correction records must reference a superseded record")
        if self.supersedes_record_id == self.record_id:
            raise ValueError("record cannot supersede itself")
        if self.record_kind != _payload_record_kind(self.payload):
            raise ValueError("record kind does not match typed payload")
        return self


class SourceRegistryResourceBudget(BaseModel):
    """AION-206 source-registry resource budget with persistent writes at zero."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-source-registry-resource-budget/v1"] = (
        SOURCE_REGISTRY_RESOURCE_BUDGET_SCHEMA_VERSION
    )
    maximum_registry_records_per_plan: Literal[100] = 100
    maximum_record_envelope_bytes: Literal[8192] = 8192
    maximum_metadata_bytes_per_record: Literal[4096] = 4096
    maximum_lineage_edges_per_record: Literal[20] = 20
    maximum_citation_references_per_record: Literal[20] = 20
    maximum_registry_write_batch: Literal[0] = 0
    maximum_persisted_source_body_bytes: Literal[0] = 0
    maximum_repository_source_body_bytes: Literal[0] = 0
    maximum_claim_verifications: Literal[0] = 0
    maximum_knowledge_promotions: Literal[0] = 0
    maximum_belief_mutations: Literal[0] = 0
    maximum_network_calls: Literal[0] = 0
    maximum_git_operations: Literal[0] = 0
    maximum_runtime_created_pull_requests: Literal[0] = 0
    maximum_approvals_created_by_runtime: Literal[0] = 0
    maximum_background_crawls: Literal[0] = 0
    maximum_search_provider_calls: Literal[0] = 0
    maximum_connector_calls: Literal[0] = 0
    maximum_model_provider_calls: Literal[0] = 0


class SourceRegistryResourceUsage(BaseModel):
    """Measured source-registry resource usage for one proposed operation."""

    model_config = FROZEN_MODEL_CONFIG

    registry_record_count: int = Field(default=0, ge=0)
    largest_record_envelope_bytes: int = Field(default=0, ge=0)
    largest_metadata_bytes_per_record: int = Field(default=0, ge=0)
    maximum_lineage_references_per_record: int = Field(default=0, ge=0)
    maximum_citation_references_per_record: int = Field(default=0, ge=0)
    persistent_write_batch: int = Field(default=0, ge=0)
    persisted_source_body_bytes: int = Field(default=0, ge=0)
    repository_source_body_bytes: int = Field(default=0, ge=0)
    claim_verifications: int = Field(default=0, ge=0)
    knowledge_promotions: int = Field(default=0, ge=0)
    belief_mutations: int = Field(default=0, ge=0)
    network_calls: int = Field(default=0, ge=0)
    git_operations: int = Field(default=0, ge=0)
    runtime_created_pull_requests: int = Field(default=0, ge=0)
    approvals_created_by_runtime: int = Field(default=0, ge=0)
    background_crawls: int = Field(default=0, ge=0)
    search_provider_calls: int = Field(default=0, ge=0)
    connector_calls: int = Field(default=0, ge=0)
    model_provider_calls: int = Field(default=0, ge=0)


class SourceRegistryBudgetDecision(BaseModel):
    """Budget decision for proposed registry work."""

    model_config = FROZEN_MODEL_CONFIG

    within_budget: bool
    usage: SourceRegistryResourceUsage
    budget: SourceRegistryResourceBudget
    reason_codes: tuple[str, ...]
    persistent_write_allowed: Literal[False] = False
    operator_review_required: Literal[True] = True
    fingerprint: str
    runtime_effect: Literal[False] = False

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_source_registry_reason_codes(value)

    @field_validator("fingerprint")
    @classmethod
    def fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "source registry budget fingerprint")


class SourceRegistryProposedBatch(BaseModel):
    """Immutable proposed source-registry batch; no persistent write is applied."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-source-registry-batch/v1"] = (
        SOURCE_REGISTRY_BATCH_SCHEMA_VERSION
    )
    program_id: Literal["AION-KNOWLEDGE-INTELLIGENCE-001"] = PROGRAM_ID
    authorization_transaction_id: Literal["AION-206-KI-0002"] = AUTHORIZATION_TRANSACTION_ID
    implementation_task: Literal["AION-207"] = IMPLEMENTATION_TASK
    formal_closeout_task: Literal["AION-208"] = FORMAL_CLOSEOUT_TASK
    authorization_scope: Literal[
        "append-only-immutable-source-snapshot-provenance-lineage-citation-registry-core"
    ] = AUTHORIZATION_SCOPE
    plan_id: str
    evidence_bundle_fingerprint: str
    records: tuple[SourceRegistryRecordEnvelope, ...]
    record_count: int = Field(ge=0)
    budget_decision: SourceRegistryBudgetDecision
    operator_review_required: Literal[True] = True
    persistent_write_applied: Literal[False] = False
    append_only: Literal[True] = True
    created_at: datetime
    batch_fingerprint: str
    runtime_effect: Literal[False] = False

    @field_validator("plan_id")
    @classmethod
    def plan_id_is_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "source registry plan_id")

    @field_validator("evidence_bundle_fingerprint", "batch_fingerprint")
    @classmethod
    def fingerprints_are_hex(cls, value: str) -> str:
        return validate_hex64(value, "source registry batch fingerprint")

    @field_validator("created_at")
    @classmethod
    def created_at_is_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value, "source registry batch created_at")

    @model_validator(mode="after")
    def batch_invariants_hold(self) -> Self:
        if self.record_count != len(self.records):
            raise ValueError("record_count must match proposed records")
        if not self.budget_decision.within_budget:
            raise ValueError("invalid source registry batch exceeds budget")
        return self


class SourceRegistryAppendDecision(BaseModel):
    """Decision from a simulated append or rejected persistent-write request."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-source-registry-append-decision/v1"] = (
        SOURCE_REGISTRY_APPEND_DECISION_SCHEMA_VERSION
    )
    append_allowed: bool
    persistent_write_requested: bool
    persistent_write_applied: Literal[False] = False
    appended_record_count: int = Field(ge=0)
    idempotent_replay_count: int = Field(default=0, ge=0)
    operator_review_required: Literal[True] = True
    persistent_write_authorization_required: Literal[True] = True
    reason_codes: tuple[str, ...]
    created_at: datetime
    fingerprint: str
    runtime_effect: Literal[False] = False

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_source_registry_reason_codes(value)

    @field_validator("created_at")
    @classmethod
    def created_at_is_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value, "source registry append decision timestamp")

    @field_validator("fingerprint")
    @classmethod
    def fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "source registry append decision fingerprint")


def evaluate_source_registry_budget(
    usage: SourceRegistryResourceUsage,
    budget: SourceRegistryResourceBudget | None = None,
) -> SourceRegistryBudgetDecision:
    """Evaluate source-registry usage against the AION-206 zero-write budget."""

    current_budget = budget or SourceRegistryResourceBudget()
    violations: list[str] = []
    if usage.registry_record_count > current_budget.maximum_registry_records_per_plan:
        violations.append("source_registry_record_budget_exceeded")
    else:
        violations.append("source_registry_record_budget_satisfied")
    if usage.largest_record_envelope_bytes > current_budget.maximum_record_envelope_bytes:
        violations.append("source_registry_record_budget_exceeded")
    if usage.largest_metadata_bytes_per_record > current_budget.maximum_metadata_bytes_per_record:
        violations.append("source_registry_metadata_budget_exceeded")
    else:
        violations.append("source_registry_metadata_budget_satisfied")
    if usage.maximum_lineage_references_per_record > (
        current_budget.maximum_lineage_edges_per_record
    ):
        violations.append("source_registry_lineage_limit_exceeded")
    else:
        violations.append("source_registry_lineage_limit_satisfied")
    if usage.maximum_citation_references_per_record > (
        current_budget.maximum_citation_references_per_record
    ):
        violations.append("source_registry_citation_limit_exceeded")
    else:
        violations.append("source_registry_citation_limit_satisfied")

    zero_limited = (
        (usage.persistent_write_batch, "source_registry_persistent_write_disabled"),
        (usage.persisted_source_body_bytes, "source_registry_source_body_blocked"),
        (usage.repository_source_body_bytes, "source_registry_source_body_blocked"),
        (usage.claim_verifications, "source_registry_claim_verification_blocked"),
        (usage.knowledge_promotions, "source_registry_knowledge_promotion_blocked"),
        (usage.belief_mutations, "source_registry_belief_mutation_blocked"),
        (usage.network_calls, "source_registry_network_fetch_blocked"),
        (usage.git_operations, "source_registry_runtime_disabled"),
        (usage.runtime_created_pull_requests, "source_registry_runtime_disabled"),
        (usage.approvals_created_by_runtime, "source_registry_runtime_disabled"),
        (usage.background_crawls, "source_registry_network_fetch_blocked"),
        (usage.search_provider_calls, "source_registry_network_fetch_blocked"),
        (usage.connector_calls, "source_registry_runtime_disabled"),
        (usage.model_provider_calls, "source_registry_runtime_disabled"),
    )
    for count, reason in zero_limited:
        if count > 0:
            violations.append(reason)

    unique_reasons = tuple(dict.fromkeys(violations))
    blocking_reasons = {
        reason
        for reason in unique_reasons
        if reason.endswith("_exceeded") or reason.endswith("_blocked")
    }
    if any(count > 0 for count, _reason in zero_limited):
        blocking_reasons.add("source_registry_persistent_write_disabled")
    within_budget = not blocking_reasons
    if within_budget:
        reason_codes = ("source_registry_batch_valid", *unique_reasons)
    else:
        reason_codes = ("source_registry_batch_invalid", *unique_reasons)
    payload = {
        "within_budget": within_budget,
        "usage": usage.model_dump(mode="json"),
        "budget": current_budget.model_dump(mode="json"),
        "reason_codes": reason_codes,
    }
    return SourceRegistryBudgetDecision(
        within_budget=within_budget,
        usage=usage,
        budget=current_budget,
        reason_codes=reason_codes,
        fingerprint=fingerprint_payload(payload),
    )


def _payload_record_kind(payload: SourceRegistryPayload) -> SourceRegistryRecordKind:
    if isinstance(payload, RegisteredSourceSnapshotDigest):
        return "source_snapshot_digest"
    if isinstance(payload, RegisteredSourceProvenance):
        return "source_provenance"
    if isinstance(payload, RegisteredCitationReference):
        return "citation_reference"
    if isinstance(payload, RegisteredSourceLineage):
        return "source_lineage"
    if isinstance(payload, RegisteredDeduplicationDecision):
        return "deduplication_decision"
    if isinstance(payload, RegisteredPolicyDecision):
        return "policy_decision"
    return "operator_review_reference"


def _json_ready(value: object) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, datetime):
        text = value.isoformat()
        if text.endswith("+00:00"):
            return f"{text[:-6]}Z"
        return text
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value


__all__ = [
    "APPROVAL_RECORD_ID",
    "AUTHORIZATION_SCOPE",
    "AUTHORIZATION_TRANSACTION_ID",
    "FORMAL_CLOSEOUT_TASK",
    "IMPLEMENTATION_TASK",
    "MAXIMUM_REGISTRY_WRITE_BATCH",
    "PROGRAM_ID",
    "SOURCE_REGISTRY_BATCH_SCHEMA_VERSION",
    "SOURCE_REGISTRY_CONTRACT_SCHEMA_VERSION",
    "SOURCE_REGISTRY_EVIDENCE_SCHEMA_VERSION",
    "SOURCE_REGISTRY_FIXTURE_SCHEMA_VERSION",
    "SOURCE_REGISTRY_INDEX_SCHEMA_VERSION",
    "SOURCE_REGISTRY_INTEGRITY_SCHEMA_VERSION",
    "SOURCE_REGISTRY_QUERY_SCHEMA_VERSION",
    "SOURCE_REGISTRY_RECORD_ENVELOPE_SCHEMA_VERSION",
    "SOURCE_REGISTRY_REASON_CODES",
    "SOURCE_REGISTRY_REASON_CODE_REGISTRY_VERSION",
    "SOURCE_REGISTRY_STATE_SCHEMA_VERSION",
    "RegisteredCitationReference",
    "RegisteredDeduplicationDecision",
    "RegisteredOperatorReviewReference",
    "RegisteredPolicyDecision",
    "RegisteredSourceLineage",
    "RegisteredSourceProvenance",
    "RegisteredSourceSnapshotDigest",
    "SourceRegistryAppendDecision",
    "SourceRegistryBudgetDecision",
    "SourceRegistryPayload",
    "SourceRegistryProposedBatch",
    "SourceRegistryRecordEnvelope",
    "SourceRegistryRecordKind",
    "SourceRegistryResourceBudget",
    "SourceRegistryResourceUsage",
    "evaluate_source_registry_budget",
    "source_registry_payload_fingerprint",
    "validate_source_registry_reason_codes",
]
