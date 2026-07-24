"""Immutable temporal claim-evidence graph contracts."""

from __future__ import annotations

import re
import unicodedata
from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Annotated, Any, Literal, Self

from pydantic import BaseModel, Field, field_validator, model_validator

from aion_brain.contracts.knowledge_research import (
    FROZEN_MODEL_CONFIG,
    ensure_utc,
    fingerprint_payload,
    reject_protected_material,
    stable_json,
    validate_hex64,
    validate_safe_identifier,
)

CLAIM_GRAPH_CONTRACT_SCHEMA_VERSION: Literal["aion-knowledge-claim-graph/v1"] = (
    "aion-knowledge-claim-graph/v1"
)
UNVERIFIED_CLAIM_ASSERTION_SCHEMA_VERSION: Literal[
    "aion-knowledge-unverified-claim-assertion/v1"
] = "aion-knowledge-unverified-claim-assertion/v1"
CLAIM_SCOPE_SCHEMA_VERSION: Literal["aion-knowledge-claim-scope/v1"] = (
    "aion-knowledge-claim-scope/v1"
)
CLAIM_EVIDENCE_BINDING_SCHEMA_VERSION: Literal[
    "aion-knowledge-claim-evidence-binding/v1"
] = "aion-knowledge-claim-evidence-binding/v1"
CLAIM_RELATION_EDGE_SCHEMA_VERSION: Literal["aion-knowledge-claim-relation-edge/v1"] = (
    "aion-knowledge-claim-relation-edge/v1"
)
STRUCTURAL_CONFLICT_CANDIDATE_SCHEMA_VERSION: Literal[
    "aion-knowledge-structural-conflict-candidate/v1"
] = "aion-knowledge-structural-conflict-candidate/v1"
CLAIM_GRAPH_RECORD_ENVELOPE_SCHEMA_VERSION: Literal[
    "aion-knowledge-claim-graph-record-envelope/v1"
] = "aion-knowledge-claim-graph-record-envelope/v1"
CLAIM_GRAPH_BATCH_SCHEMA_VERSION: Literal["aion-knowledge-claim-graph-batch/v1"] = (
    "aion-knowledge-claim-graph-batch/v1"
)
CLAIM_GRAPH_STATE_SCHEMA_VERSION: Literal["aion-knowledge-claim-graph-state/v1"] = (
    "aion-knowledge-claim-graph-state/v1"
)
CLAIM_GRAPH_INDEX_SCHEMA_VERSION: Literal["aion-knowledge-claim-graph-index/v1"] = (
    "aion-knowledge-claim-graph-index/v1"
)
CLAIM_GRAPH_INTEGRITY_SCHEMA_VERSION: Literal[
    "aion-knowledge-claim-graph-integrity/v1"
] = "aion-knowledge-claim-graph-integrity/v1"
CLAIM_GRAPH_QUERY_SCHEMA_VERSION: Literal["aion-knowledge-claim-graph-query/v1"] = (
    "aion-knowledge-claim-graph-query/v1"
)
CLAIM_GRAPH_FIXTURE_SCHEMA_VERSION: Literal["aion-knowledge-claim-graph-fixture/v1"] = (
    "aion-knowledge-claim-graph-fixture/v1"
)
CLAIM_GRAPH_EVIDENCE_SCHEMA_VERSION: Literal["aion-knowledge-claim-graph-evidence/v1"] = (
    "aion-knowledge-claim-graph-evidence/v1"
)
CLAIM_GRAPH_REASON_CODE_REGISTRY_VERSION: Literal[
    "aion-knowledge-claim-graph-reasons/v1"
] = "aion-knowledge-claim-graph-reasons/v1"

PROGRAM_ID: Literal["AION-KNOWLEDGE-INTELLIGENCE-001"] = "AION-KNOWLEDGE-INTELLIGENCE-001"
AUTHORIZATION_TRANSACTION_ID: Literal["AION-208-KI-0003"] = "AION-208-KI-0003"
APPROVAL_RECORD_ID: Literal["AION-208-KI-0003"] = "AION-208-KI-0003"
IMPLEMENTATION_TASK: Literal["AION-209"] = "AION-209"
FORMAL_CLOSEOUT_TASK: Literal["AION-210"] = "AION-210"
AUTHORIZATION_SCOPE: Literal[
    "append-only-immutable-temporal-claim-evidence-provenance-"
    "jurisdiction-version-contradiction-graph-core"
] = (
    "append-only-immutable-temporal-claim-evidence-provenance-"
    "jurisdiction-version-contradiction-graph-core"
)

MAXIMUM_CLAIM_NODES_PER_GRAPH = 1000
MAXIMUM_EVIDENCE_BINDINGS_PER_GRAPH = 5000
MAXIMUM_CLAIM_RELATION_EDGES_PER_GRAPH = 5000
MAXIMUM_SOURCE_REGISTRY_REFERENCES_PER_CLAIM = 50
MAXIMUM_CITATION_REFERENCES_PER_CLAIM = 50
MAXIMUM_LINEAGE_GROUPS_PER_CLAIM = 20
MAXIMUM_JURISDICTIONS_PER_CLAIM = 20
MAXIMUM_VERSIONS_PER_CLAIM = 20
MAXIMUM_TEMPORAL_INTERVALS_PER_CLAIM = 8
MAXIMUM_RELATION_EDGES_PER_CLAIM = 100
MAXIMUM_QUERY_RESULTS = 1000
MAXIMUM_FIXTURE_RECORDS = 2000
MAXIMUM_FIXTURE_BYTES = 2_097_152
MAXIMUM_CONCURRENT_READERS = 4
MAXIMUM_CONCURRENT_PROJECTIONS = 4
MAXIMUM_GRAPH_WRITE_BATCH = 0
MAXIMUM_SOURCE_BODY_BYTES = 0
MAXIMUM_AUTOMATIC_CLAIM_EXTRACTIONS = 0
MAXIMUM_CLAIM_VERIFICATIONS = 0
MAXIMUM_TRUTH_DECISIONS = 0
MAXIMUM_CONFIDENCE_CALCULATIONS = 0
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


class ClaimObjectType(StrEnum):
    """Supported explicit claim object value types."""

    TEXT = "text"
    IDENTIFIER = "identifier"
    BOOLEAN = "boolean"
    INTEGER = "integer"
    DECIMAL = "decimal"
    DATE = "date"
    DATETIME = "datetime"
    QUANTITY = "quantity"
    VERSION = "version"
    RANGE = "range"


class ClaimPolarity(StrEnum):
    """Explicit claim polarity."""

    POSITIVE = "positive"
    NEGATIVE = "negative"


class ClaimModality(StrEnum):
    """Operator-supplied claim modality."""

    ASSERTED = "asserted"
    REPORTED = "reported"
    POSSIBLE = "possible"
    PROBABLE = "probable"
    REQUIRED = "required"
    PERMITTED = "permitted"
    PROHIBITED = "prohibited"
    HYPOTHETICAL = "hypothetical"
    PROJECTED = "projected"


class ClaimPredicateCardinality(StrEnum):
    """Explicit predicate cardinality."""

    ONE = "one"
    MANY = "many"
    UNKNOWN = "unknown"


class EvidenceRole(StrEnum):
    """Evidence role without truth effect."""

    SUPPORTS = "supports"
    OPPOSES = "opposes"
    CONTEXT = "context"
    DUPLICATE = "duplicate"


class ClaimRelationType(StrEnum):
    """Claim relation types represented as assertions only."""

    EQUIVALENT_TO = "equivalent_to"
    REFINES = "refines"
    SUPERSEDES = "supersedes"
    CORRECTS = "corrects"
    RETRACTS = "retracts"
    STRUCTURAL_CONFLICT_CANDIDATE = "structural_conflict_candidate"


class ClaimRelationOrigin(StrEnum):
    """Origin of a relation edge."""

    OPERATOR_SUPPLIED = "operator_supplied"
    DERIVED_STRUCTURAL = "derived_structural"


class JurisdictionKind(StrEnum):
    """Explicit jurisdiction scope kind."""

    GLOBAL = "global"
    COUNTRY = "country"
    SUBDIVISION = "subdivision"
    SUPRANATIONAL = "supranational"
    ORGANIZATION_SPECIFIC = "organization_specific"


class VersionScheme(StrEnum):
    """Version comparison scheme."""

    OPAQUE_EXACT = "opaque_exact"
    NUMERIC_DOTTED_EXACT = "numeric_dotted_exact"
    NUMERIC_DOTTED_RANGE = "numeric_dotted_range"


class ClaimGraphRecordKind(StrEnum):
    """Append-only graph record kinds."""

    CLAIM_ASSERTION = "claim_assertion"
    EVIDENCE_BINDING = "evidence_binding"
    RELATION_EDGE = "relation_edge"
    STRUCTURAL_CONFLICT_CANDIDATE = "structural_conflict_candidate"
    OPERATOR_REVIEW_REFERENCE = "operator_review_reference"


class ClaimGraphAppendOutcome(StrEnum):
    """Simulated append and rejected-write outcomes."""

    VALIDATED = "validated"
    SIMULATED_APPEND = "simulated_append"
    IDEMPOTENT_REPLAY = "idempotent_replay"
    REJECTED_DUPLICATE_IDENTIFIER = "rejected_duplicate_identifier"
    REJECTED_CHANGED_PAYLOAD = "rejected_changed_payload"
    REJECTED_INTEGRITY = "rejected_integrity"
    REJECTED_BUDGET = "rejected_budget"
    PERSISTENT_WRITE_DISABLED = "persistent_write_disabled"


class ClaimGraphIntegrityStatus(StrEnum):
    """Integrity audit status."""

    PASSED = "passed"
    FAILED = "failed"


CLAIM_GRAPH_REASON_CODES: tuple[str, ...] = (
    "claim_graph_batch_valid",
    "claim_graph_batch_invalid",
    "claim_graph_claim_valid",
    "claim_graph_claim_invalid",
    "claim_graph_identity_valid",
    "claim_graph_identity_collision",
    "claim_graph_scope_valid",
    "claim_graph_scope_insufficient",
    "claim_graph_temporal_overlap",
    "claim_graph_temporal_nonoverlap",
    "claim_graph_jurisdiction_overlap",
    "claim_graph_jurisdiction_mismatch",
    "claim_graph_version_overlap",
    "claim_graph_version_mismatch",
    "claim_graph_evidence_binding_valid",
    "claim_graph_evidence_binding_invalid",
    "claim_graph_source_reference_resolved",
    "claim_graph_source_reference_unresolved",
    "claim_graph_citation_reference_resolved",
    "claim_graph_citation_reference_unresolved",
    "claim_graph_lineage_group_propagated",
    "claim_graph_duplicate_independence_blocked",
    "claim_graph_relation_valid",
    "claim_graph_relation_invalid",
    "claim_graph_relation_cycle",
    "claim_graph_structural_conflict_candidate",
    "claim_graph_structural_conflict_not_established",
    "claim_graph_record_appended_in_memory",
    "claim_graph_persistent_write_disabled",
    "claim_graph_idempotent_replay",
    "claim_graph_duplicate_identifier",
    "claim_graph_changed_payload_rejected",
    "claim_graph_sequence_valid",
    "claim_graph_sequence_gap",
    "claim_graph_sequence_duplicate",
    "claim_graph_chain_valid",
    "claim_graph_chain_broken",
    "claim_graph_payload_fingerprint_valid",
    "claim_graph_payload_fingerprint_mismatch",
    "claim_graph_record_fingerprint_valid",
    "claim_graph_record_fingerprint_mismatch",
    "claim_graph_supersession_valid",
    "claim_graph_supersession_missing",
    "claim_graph_supersession_cycle",
    "claim_graph_index_built",
    "claim_graph_index_invalid",
    "claim_graph_query_completed",
    "claim_graph_query_limit_exceeded",
    "claim_graph_fixture_replayed",
    "claim_graph_fixture_rejected",
    "claim_graph_source_body_blocked",
    "claim_graph_automatic_extraction_blocked",
    "claim_graph_truth_decision_blocked",
    "claim_graph_confidence_calculation_blocked",
    "claim_graph_contradiction_resolution_blocked",
    "claim_graph_knowledge_promotion_blocked",
    "claim_graph_belief_mutation_blocked",
    "claim_graph_network_fetch_blocked",
    "claim_graph_runtime_disabled",
    "claim_graph_operator_review_required",
    "claim_graph_integrity_passed",
    "claim_graph_integrity_failed",
)
_CLAIM_GRAPH_REASON_CODE_SET = frozenset(CLAIM_GRAPH_REASON_CODES)
_UNSAFE_REASON_RE = re.compile(r"[/:\\\\]")
_URL_RE = re.compile(r"https?://", re.IGNORECASE)
_COMMAND_RE = re.compile(r"(^|\s)(curl|wget|bash|sh|zsh|python|node|git)\s", re.IGNORECASE)
_WHITESPACE_RE = re.compile(r"\s+")
_NUMERIC_DOTTED_RE = re.compile(r"^[0-9]+(?:[.][0-9]+){0,15}$")


def validate_claim_graph_reason_codes(values: tuple[str, ...]) -> tuple[str, ...]:
    """Validate stable, immutable claim-graph reason codes."""

    seen: set[str] = set()
    for code in values:
        if code not in _CLAIM_GRAPH_REASON_CODE_SET:
            raise ValueError("unknown claim graph reason code")
        if code in seen:
            raise ValueError("duplicate claim graph reason code")
        if _UNSAFE_REASON_RE.search(code):
            raise ValueError("claim graph reason code must not embed URL, host, or path text")
        reject_protected_material(code, "claim graph reason code")
        seen.add(code)
    return values


def normalize_claim_subject(value: str) -> str:
    """Normalize an operator-supplied canonical subject identifier."""

    normalized = unicodedata.normalize("NFKC", value.strip().lower())
    normalized = _WHITESPACE_RE.sub("-", normalized)
    return validate_safe_identifier(normalized, "claim subject")


def normalize_claim_predicate(value: str) -> str:
    """Normalize an operator-supplied canonical predicate identifier."""

    normalized = unicodedata.normalize("NFKC", value.strip().lower())
    normalized = _WHITESPACE_RE.sub("_", normalized)
    return validate_safe_identifier(normalized, "claim predicate")


def normalize_claim_statement(value: str) -> str:
    """Normalize a concise human-readable assertion without semantic rewriting."""

    normalized = _WHITESPACE_RE.sub(" ", unicodedata.normalize("NFKC", value).strip())
    _reject_sensitive_text(normalized, "claim statement")
    if len(normalized) < 1 or len(normalized) > 1024:
        raise ValueError("claim statement length is out of bounds")
    return normalized


def calculate_claim_identity_fingerprint(
    *,
    subject_id: str,
    predicate: str,
    object_value: ClaimObjectValue,
    polarity: ClaimPolarity | str,
    modality: ClaimModality | str,
    predicate_cardinality: ClaimPredicateCardinality | str,
    objects_mutually_exclusive: bool,
    scope: ClaimScope,
) -> str:
    """Fingerprint structured claim semantics without using transaction time."""

    payload = {
        "subject_id": normalize_claim_subject(subject_id),
        "predicate": normalize_claim_predicate(predicate),
        "object": _model_dump_json(object_value),
        "polarity": _enum_value(polarity),
        "modality": _enum_value(modality),
        "predicate_cardinality": _enum_value(predicate_cardinality),
        "objects_mutually_exclusive": objects_mutually_exclusive,
        "scope_fingerprint": scope.scope_fingerprint,
    }
    return fingerprint_payload(payload)


def calculate_claim_record_fingerprint(claim: UnverifiedClaimAssertion | dict[str, Any]) -> str:
    """Fingerprint the immutable claim assertion record including metadata."""

    payload = _model_dump_json(claim)
    payload.pop("claim_record_fingerprint", None)
    return fingerprint_payload(payload)


def claim_graph_payload_fingerprint(payload: ClaimGraphPayload | BaseModel | dict[str, Any]) -> str:
    """Fingerprint one graph payload."""

    return fingerprint_payload(_model_dump_json(payload))


def claim_graph_record_fingerprint(envelope: ClaimGraphRecordEnvelope | dict[str, Any]) -> str:
    """Fingerprint one graph envelope excluding the record fingerprint itself."""

    payload = _model_dump_json(envelope)
    payload.pop("record_fingerprint", None)
    return fingerprint_payload(payload)


def claim_object_value_fingerprint(
    *,
    kind: str,
    canonical_value: object,
    unit_id: str | None = None,
    scheme: str | None = None,
    lower_value: object | None = None,
    upper_value: object | None = None,
) -> str:
    """Fingerprint a typed claim object value deterministically."""

    payload = {
        "kind": kind,
        "canonical_value": _json_scalar(canonical_value),
        "unit_id": unit_id,
        "scheme": scheme,
        "lower_value": _json_scalar(lower_value),
        "upper_value": _json_scalar(upper_value),
    }
    return fingerprint_payload(payload)


class _ObjectValueBase(BaseModel):
    model_config = FROZEN_MODEL_CONFIG

    kind: str
    display_value: str = Field(min_length=1, max_length=256)
    object_fingerprint: str

    @field_validator("display_value")
    @classmethod
    def display_value_is_safe(cls, value: str) -> str:
        _reject_sensitive_text(value, "claim object display")
        return value

    @field_validator("object_fingerprint")
    @classmethod
    def object_fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "claim object fingerprint")


class TextClaimObjectValue(_ObjectValueBase):
    kind: Literal["text"] = "text"
    canonical_value: str = Field(min_length=1, max_length=512)

    @field_validator("canonical_value")
    @classmethod
    def canonical_text_is_safe(cls, value: str) -> str:
        normalized = _WHITESPACE_RE.sub(" ", unicodedata.normalize("NFKC", value).strip())
        _reject_sensitive_text(normalized, "claim object text")
        if _URL_RE.search(normalized) or "/" in normalized:
            raise ValueError("claim object text must not contain source content or URLs")
        return normalized

    @model_validator(mode="after")
    def fingerprint_matches(self) -> Self:
        _require_object_fingerprint(self, self.canonical_value)
        return self


class IdentifierClaimObjectValue(_ObjectValueBase):
    kind: Literal["identifier"] = "identifier"
    canonical_value: str

    @field_validator("canonical_value")
    @classmethod
    def canonical_identifier_is_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "claim object identifier")

    @model_validator(mode="after")
    def fingerprint_matches(self) -> Self:
        _require_object_fingerprint(self, self.canonical_value)
        return self


class BooleanClaimObjectValue(_ObjectValueBase):
    kind: Literal["boolean"] = "boolean"
    canonical_value: bool

    @model_validator(mode="after")
    def fingerprint_matches(self) -> Self:
        _require_object_fingerprint(self, self.canonical_value)
        return self


class IntegerClaimObjectValue(_ObjectValueBase):
    kind: Literal["integer"] = "integer"
    canonical_value: int = Field(ge=-(2**63), le=2**63 - 1)

    @model_validator(mode="after")
    def fingerprint_matches(self) -> Self:
        _require_object_fingerprint(self, self.canonical_value)
        return self


class DecimalClaimObjectValue(_ObjectValueBase):
    kind: Literal["decimal"] = "decimal"
    canonical_value: Decimal

    @field_validator("canonical_value")
    @classmethod
    def decimal_is_finite(cls, value: Decimal) -> Decimal:
        if not value.is_finite():
            raise ValueError("decimal claim object must be finite")
        return value.normalize()

    @model_validator(mode="after")
    def fingerprint_matches(self) -> Self:
        _require_object_fingerprint(self, self.canonical_value)
        return self


class DateClaimObjectValue(_ObjectValueBase):
    kind: Literal["date"] = "date"
    canonical_value: date

    @model_validator(mode="after")
    def fingerprint_matches(self) -> Self:
        _require_object_fingerprint(self, self.canonical_value.isoformat())
        return self


class DateTimeClaimObjectValue(_ObjectValueBase):
    kind: Literal["datetime"] = "datetime"
    canonical_value: datetime

    @field_validator("canonical_value")
    @classmethod
    def timestamp_is_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value, "claim object datetime")

    @model_validator(mode="after")
    def fingerprint_matches(self) -> Self:
        _require_object_fingerprint(self, self.canonical_value)
        return self


class QuantityClaimObjectValue(_ObjectValueBase):
    kind: Literal["quantity"] = "quantity"
    canonical_value: Decimal
    unit_id: str

    @field_validator("canonical_value")
    @classmethod
    def quantity_value_is_finite(cls, value: Decimal) -> Decimal:
        if not value.is_finite():
            raise ValueError("quantity claim object must be finite")
        return value.normalize()

    @field_validator("unit_id")
    @classmethod
    def unit_id_is_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "claim object unit_id")

    @model_validator(mode="after")
    def fingerprint_matches(self) -> Self:
        expected = claim_object_value_fingerprint(
            kind=self.kind,
            canonical_value=self.canonical_value,
            unit_id=self.unit_id,
        )
        if self.object_fingerprint != expected:
            raise ValueError("claim object fingerprint mismatch")
        return self


class VersionClaimObjectValue(_ObjectValueBase):
    kind: Literal["version"] = "version"
    canonical_value: str = Field(min_length=1, max_length=128)
    scheme: VersionScheme

    @field_validator("canonical_value")
    @classmethod
    def version_value_is_safe(cls, value: str) -> str:
        _reject_sensitive_text(value, "claim object version")
        if "/" in value or "://" in value:
            raise ValueError("claim object version must not contain URL or path text")
        return value

    @model_validator(mode="after")
    def version_shape_matches_scheme(self) -> Self:
        if self.scheme in {
            VersionScheme.NUMERIC_DOTTED_EXACT,
            VersionScheme.NUMERIC_DOTTED_RANGE,
        } and not _NUMERIC_DOTTED_RE.fullmatch(self.canonical_value):
            raise ValueError("numeric dotted versions require integer components")
        expected = claim_object_value_fingerprint(
            kind=self.kind,
            canonical_value=self.canonical_value,
            scheme=self.scheme,
        )
        if self.object_fingerprint != expected:
            raise ValueError("claim object fingerprint mismatch")
        return self


class RangeClaimObjectValue(_ObjectValueBase):
    kind: Literal["range"] = "range"
    canonical_value: str = Field(min_length=1, max_length=128)
    lower_value: Decimal
    upper_value: Decimal

    @field_validator("lower_value", "upper_value")
    @classmethod
    def range_bounds_are_finite(cls, value: Decimal) -> Decimal:
        if not value.is_finite():
            raise ValueError("range claim object bounds must be finite")
        return value.normalize()

    @model_validator(mode="after")
    def range_is_ordered_and_fingerprinted(self) -> Self:
        if self.lower_value > self.upper_value:
            raise ValueError("range claim object lower bound must not exceed upper bound")
        expected = claim_object_value_fingerprint(
            kind=self.kind,
            canonical_value=self.canonical_value,
            lower_value=self.lower_value,
            upper_value=self.upper_value,
        )
        if self.object_fingerprint != expected:
            raise ValueError("claim object fingerprint mismatch")
        return self


type ClaimObjectValue = Annotated[
    TextClaimObjectValue
    | IdentifierClaimObjectValue
    | BooleanClaimObjectValue
    | IntegerClaimObjectValue
    | DecimalClaimObjectValue
    | DateClaimObjectValue
    | DateTimeClaimObjectValue
    | QuantityClaimObjectValue
    | VersionClaimObjectValue
    | RangeClaimObjectValue,
    Field(discriminator="kind"),
]


class ValidTimeInterval(BaseModel):
    """Explicit valid-time interval, separate from transaction time."""

    model_config = FROZEN_MODEL_CONFIG

    interval_id: str
    start: datetime | None = None
    end: datetime | None = None
    start_inclusive: bool = True
    end_inclusive: bool = True
    interval_fingerprint: str

    @field_validator("interval_id")
    @classmethod
    def interval_id_is_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "valid time interval_id")

    @field_validator("start", "end")
    @classmethod
    def interval_bound_is_utc(cls, value: datetime | None) -> datetime | None:
        if value is not None:
            return ensure_utc(value, "valid time interval bound")
        return value

    @field_validator("interval_fingerprint")
    @classmethod
    def fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "valid time interval fingerprint")

    @model_validator(mode="after")
    def interval_is_valid(self) -> Self:
        if self.start is not None and self.end is not None:
            if self.start > self.end:
                raise ValueError("valid time interval start must not exceed end")
            if self.start == self.end and not (self.start_inclusive and self.end_inclusive):
                raise ValueError("zero-length interval requires inclusive boundaries")
        expected = fingerprint_payload(
            {
                "interval_id": self.interval_id,
                "start": _json_scalar(self.start),
                "end": _json_scalar(self.end),
                "start_inclusive": self.start_inclusive,
                "end_inclusive": self.end_inclusive,
            }
        )
        if self.interval_fingerprint != expected:
            raise ValueError("valid time interval fingerprint mismatch")
        return self


class JurisdictionScope(BaseModel):
    """Explicit jurisdiction scope without external lookup."""

    model_config = FROZEN_MODEL_CONFIG

    jurisdiction_id: str
    jurisdiction_kind: JurisdictionKind
    parent_jurisdiction_ids: tuple[str, ...] = Field(default_factory=tuple, max_length=20)
    scope_fingerprint: str

    @field_validator("jurisdiction_id")
    @classmethod
    def jurisdiction_id_is_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "jurisdiction_id")

    @field_validator("parent_jurisdiction_ids")
    @classmethod
    def parent_ids_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if len(set(value)) != len(value):
            raise ValueError("duplicate parent jurisdiction IDs rejected")
        for item in value:
            validate_safe_identifier(item, "parent_jurisdiction_id")
        return tuple(sorted(value))

    @field_validator("scope_fingerprint")
    @classmethod
    def scope_fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "jurisdiction scope fingerprint")

    @model_validator(mode="after")
    def jurisdiction_is_explicit(self) -> Self:
        if self.jurisdiction_kind == JurisdictionKind.GLOBAL and self.jurisdiction_id != "global":
            raise ValueError("global jurisdiction must use explicit global ID")
        payload = {
            "jurisdiction_id": self.jurisdiction_id,
            "jurisdiction_kind": self.jurisdiction_kind.value,
            "parent_jurisdiction_ids": self.parent_jurisdiction_ids,
        }
        if self.scope_fingerprint != fingerprint_payload(_model_dump_json(payload)):
            raise ValueError("jurisdiction scope fingerprint mismatch")
        return self


class VersionScope(BaseModel):
    """Explicit product, document, standard, software, or dataset version scope."""

    model_config = FROZEN_MODEL_CONFIG

    target_id: str
    scheme: VersionScheme
    exact_version: str | None = Field(default=None, max_length=128)
    lower_bound: str | None = Field(default=None, max_length=128)
    upper_bound: str | None = Field(default=None, max_length=128)
    lower_inclusive: bool = True
    upper_inclusive: bool = True
    scope_fingerprint: str

    @field_validator("target_id")
    @classmethod
    def target_id_is_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "version target_id")

    @field_validator("exact_version", "lower_bound", "upper_bound")
    @classmethod
    def versions_are_safe(cls, value: str | None) -> str | None:
        if value is None:
            return None
        _reject_sensitive_text(value, "version scope")
        if "/" in value or "://" in value:
            raise ValueError("version scope must not contain URL or path text")
        return value

    @field_validator("scope_fingerprint")
    @classmethod
    def scope_fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "version scope fingerprint")

    @model_validator(mode="after")
    def version_scope_is_valid(self) -> Self:
        if self.scheme == VersionScheme.OPAQUE_EXACT:
            if (
                self.exact_version is None
                or self.lower_bound is not None
                or self.upper_bound is not None
            ):
                raise ValueError("opaque version scope supports exact version only")
        elif self.scheme == VersionScheme.NUMERIC_DOTTED_EXACT:
            if (
                self.exact_version is None
                or self.lower_bound is not None
                or self.upper_bound is not None
            ):
                raise ValueError("numeric dotted exact scope requires exact version only")
            _parse_numeric_dotted(self.exact_version)
        else:
            if self.exact_version is not None:
                raise ValueError("numeric dotted range must not also set exact version")
            if self.lower_bound is None and self.upper_bound is None:
                raise ValueError("numeric dotted range requires at least one bound")
            lower = _parse_numeric_dotted(self.lower_bound) if self.lower_bound else None
            upper = _parse_numeric_dotted(self.upper_bound) if self.upper_bound else None
            if lower is not None and upper is not None:
                if _compare_versions(lower, upper) > 0:
                    raise ValueError("version lower bound must not exceed upper bound")
                if lower == upper and not (self.lower_inclusive and self.upper_inclusive):
                    raise ValueError("equal version range bounds require inclusive boundaries")
        payload = {
            "target_id": self.target_id,
            "scheme": self.scheme.value,
            "exact_version": self.exact_version,
            "lower_bound": self.lower_bound,
            "upper_bound": self.upper_bound,
            "lower_inclusive": self.lower_inclusive,
            "upper_inclusive": self.upper_inclusive,
        }
        if self.scope_fingerprint != fingerprint_payload(_model_dump_json(payload)):
            raise ValueError("version scope fingerprint mismatch")
        return self


class ClaimScope(BaseModel):
    """Explicit claim scope; empty collections mean unspecified, not global."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-claim-scope/v1"] = CLAIM_SCOPE_SCHEMA_VERSION
    jurisdiction_scopes: tuple[JurisdictionScope, ...] = Field(
        default_factory=tuple,
        max_length=MAXIMUM_JURISDICTIONS_PER_CLAIM,
    )
    version_scopes: tuple[VersionScope, ...] = Field(
        default_factory=tuple,
        max_length=MAXIMUM_VERSIONS_PER_CLAIM,
    )
    valid_time_intervals: tuple[ValidTimeInterval, ...] = Field(
        default_factory=tuple,
        max_length=MAXIMUM_TEMPORAL_INTERVALS_PER_CLAIM,
    )
    scope_fingerprint: str

    @field_validator("scope_fingerprint")
    @classmethod
    def scope_fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "claim scope fingerprint")

    @model_validator(mode="after")
    def scope_is_deterministic(self) -> Self:
        _reject_duplicate_ids([scope.jurisdiction_id for scope in self.jurisdiction_scopes])
        _reject_duplicate_ids([scope.target_id for scope in self.version_scopes])
        _reject_duplicate_ids([interval.interval_id for interval in self.valid_time_intervals])
        for left_index, left in enumerate(self.valid_time_intervals):
            for right in self.valid_time_intervals[left_index + 1 :]:
                if _intervals_overlap_bool(left, right):
                    raise ValueError("overlapping valid-time intervals are rejected")
        expected = claim_scope_fingerprint(
            jurisdiction_scopes=self.jurisdiction_scopes,
            version_scopes=self.version_scopes,
            valid_time_intervals=self.valid_time_intervals,
        )
        if self.scope_fingerprint != expected:
            raise ValueError("claim scope fingerprint mismatch")
        return self


def valid_time_interval_fingerprint(
    *,
    interval_id: str,
    start: datetime | None,
    end: datetime | None,
    start_inclusive: bool = True,
    end_inclusive: bool = True,
) -> str:
    """Fingerprint a valid-time interval payload."""

    return fingerprint_payload(
        {
            "interval_id": interval_id,
            "start": _json_scalar(start),
            "end": _json_scalar(end),
            "start_inclusive": start_inclusive,
            "end_inclusive": end_inclusive,
        }
    )


def jurisdiction_scope_fingerprint(
    *,
    jurisdiction_id: str,
    jurisdiction_kind: JurisdictionKind | str,
    parent_jurisdiction_ids: tuple[str, ...] = (),
) -> str:
    """Fingerprint a jurisdiction scope payload."""

    return fingerprint_payload(
        {
            "jurisdiction_id": jurisdiction_id,
            "jurisdiction_kind": _enum_value(jurisdiction_kind),
            "parent_jurisdiction_ids": tuple(sorted(parent_jurisdiction_ids)),
        }
    )


def version_scope_fingerprint(
    *,
    target_id: str,
    scheme: VersionScheme | str,
    exact_version: str | None = None,
    lower_bound: str | None = None,
    upper_bound: str | None = None,
    lower_inclusive: bool = True,
    upper_inclusive: bool = True,
) -> str:
    """Fingerprint a version scope payload."""

    return fingerprint_payload(
        {
            "target_id": target_id,
            "scheme": _enum_value(scheme),
            "exact_version": exact_version,
            "lower_bound": lower_bound,
            "upper_bound": upper_bound,
            "lower_inclusive": lower_inclusive,
            "upper_inclusive": upper_inclusive,
        }
    )


def claim_scope_fingerprint(
    *,
    jurisdiction_scopes: tuple[JurisdictionScope, ...] = (),
    version_scopes: tuple[VersionScope, ...] = (),
    valid_time_intervals: tuple[ValidTimeInterval, ...] = (),
) -> str:
    """Fingerprint explicit scope by child fingerprints."""

    return fingerprint_payload(
        {
            "schema_version": CLAIM_SCOPE_SCHEMA_VERSION,
            "jurisdiction_scopes": sorted(scope.scope_fingerprint for scope in jurisdiction_scopes),
            "version_scopes": sorted(scope.scope_fingerprint for scope in version_scopes),
            "valid_time_intervals": sorted(
                interval.interval_fingerprint for interval in valid_time_intervals
            ),
        }
    )


class UnverifiedClaimAssertion(BaseModel):
    """Structured claim assertion that always remains unverified."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-unverified-claim-assertion/v1"] = (
        UNVERIFIED_CLAIM_ASSERTION_SCHEMA_VERSION
    )
    claim_id: str
    claim_statement: str = Field(min_length=1, max_length=1024)
    subject_id: str
    predicate: str
    object_value: ClaimObjectValue
    polarity: ClaimPolarity
    modality: ClaimModality
    predicate_cardinality: ClaimPredicateCardinality
    objects_mutually_exclusive: bool
    language: str = Field(min_length=2, max_length=16)
    scope: ClaimScope
    transaction_time: datetime
    claim_identity_fingerprint: str
    claim_record_fingerprint: str
    operator_supplied: Literal[True] = True
    unverified: Literal[True] = True
    verified: Literal[False] = False
    truth_value_assigned: Literal[False] = False
    epistemic_confidence_assigned: Literal[False] = False
    knowledge_promoted: Literal[False] = False
    belief_created: Literal[False] = False
    belief_mutated: Literal[False] = False
    runtime_effect: Literal[False] = False

    @field_validator("claim_id")
    @classmethod
    def claim_id_is_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "claim_id")

    @field_validator("claim_statement")
    @classmethod
    def claim_statement_is_safe(cls, value: str) -> str:
        return normalize_claim_statement(value)

    @field_validator("subject_id")
    @classmethod
    def subject_id_is_safe(cls, value: str) -> str:
        return normalize_claim_subject(value)

    @field_validator("predicate")
    @classmethod
    def predicate_is_safe(cls, value: str) -> str:
        return normalize_claim_predicate(value)

    @field_validator("transaction_time")
    @classmethod
    def transaction_time_is_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value, "claim transaction_time")

    @field_validator("claim_identity_fingerprint", "claim_record_fingerprint")
    @classmethod
    def fingerprints_are_hex(cls, value: str) -> str:
        return validate_hex64(value, "claim fingerprint")

    @model_validator(mode="after")
    def claim_fingerprints_match(self) -> Self:
        identity = calculate_claim_identity_fingerprint(
            subject_id=self.subject_id,
            predicate=self.predicate,
            object_value=self.object_value,
            polarity=self.polarity,
            modality=self.modality,
            predicate_cardinality=self.predicate_cardinality,
            objects_mutually_exclusive=self.objects_mutually_exclusive,
            scope=self.scope,
        )
        if self.claim_identity_fingerprint != identity:
            raise ValueError("claim identity fingerprint mismatch")
        if self.claim_record_fingerprint != calculate_claim_record_fingerprint(self):
            raise ValueError("claim record fingerprint mismatch")
        return self


class ClaimEvidenceBinding(BaseModel):
    """Binding from an unverified claim to source-registry evidence records."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-claim-evidence-binding/v1"] = (
        CLAIM_EVIDENCE_BINDING_SCHEMA_VERSION
    )
    binding_id: str
    claim_id: str
    source_registry_record_ids: tuple[str, ...] = Field(
        min_length=1,
        max_length=MAXIMUM_SOURCE_REGISTRY_REFERENCES_PER_CLAIM,
    )
    source_snapshot_record_ids: tuple[str, ...] = Field(default_factory=tuple, max_length=50)
    source_provenance_record_ids: tuple[str, ...] = Field(default_factory=tuple, max_length=50)
    citation_record_ids: tuple[str, ...] = Field(
        default_factory=tuple,
        max_length=MAXIMUM_CITATION_REFERENCES_PER_CLAIM,
    )
    lineage_record_ids: tuple[str, ...] = Field(default_factory=tuple, max_length=50)
    lineage_group_ids: tuple[str, ...] = Field(
        default_factory=tuple,
        max_length=MAXIMUM_LINEAGE_GROUPS_PER_CLAIM,
    )
    evidence_role: EvidenceRole
    created_at: datetime
    binding_fingerprint: str
    source_records_resolved: Literal[True] = True
    verified_support: Literal[False] = False
    truth_effect: Literal[False] = False
    confidence_effect: Literal[False] = False
    knowledge_effect: Literal[False] = False
    belief_effect: Literal[False] = False
    runtime_effect: Literal[False] = False

    @field_validator(
        "binding_id",
        "claim_id",
    )
    @classmethod
    def identifiers_are_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "claim evidence binding identifier")

    @field_validator(
        "source_registry_record_ids",
        "source_snapshot_record_ids",
        "source_provenance_record_ids",
        "citation_record_ids",
        "lineage_record_ids",
        "lineage_group_ids",
    )
    @classmethod
    def reference_ids_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if len(set(value)) != len(value):
            raise ValueError("duplicate evidence references rejected")
        for item in value:
            validate_safe_identifier(item, "claim evidence reference")
        return tuple(sorted(value))

    @field_validator("created_at")
    @classmethod
    def created_at_is_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value, "claim evidence binding timestamp")

    @field_validator("binding_fingerprint")
    @classmethod
    def binding_fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "claim evidence binding fingerprint")

    @model_validator(mode="after")
    def binding_fingerprint_matches(self) -> Self:
        if self.binding_fingerprint != claim_evidence_binding_fingerprint(self):
            raise ValueError("claim evidence binding fingerprint mismatch")
        return self


def claim_evidence_binding_fingerprint(binding: ClaimEvidenceBinding | dict[str, Any]) -> str:
    """Fingerprint a claim evidence binding."""

    payload = _model_dump_json(binding)
    payload.pop("binding_fingerprint", None)
    return fingerprint_payload(payload)


class ClaimRelationEdge(BaseModel):
    """Claim-to-claim relation edge with no truth effect."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-claim-relation-edge/v1"] = (
        CLAIM_RELATION_EDGE_SCHEMA_VERSION
    )
    relation_id: str
    source_claim_id: str
    target_claim_id: str
    relation_type: ClaimRelationType
    relation_origin: ClaimRelationOrigin
    effective_time: datetime | None = None
    operator_supplied: bool
    derived_structural: bool
    relation_verified: Literal[False] = False
    truth_effect: Literal[False] = False
    knowledge_effect: Literal[False] = False
    belief_effect: Literal[False] = False
    created_at: datetime
    relation_fingerprint: str
    runtime_effect: Literal[False] = False

    @field_validator("relation_id", "source_claim_id", "target_claim_id")
    @classmethod
    def identifiers_are_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "claim relation identifier")

    @field_validator("effective_time", "created_at")
    @classmethod
    def timestamps_are_utc(cls, value: datetime | None) -> datetime | None:
        if value is not None:
            return ensure_utc(value, "claim relation timestamp")
        return value

    @field_validator("relation_fingerprint")
    @classmethod
    def relation_fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "claim relation fingerprint")

    @model_validator(mode="after")
    def relation_is_valid(self) -> Self:
        if self.source_claim_id == self.target_claim_id:
            raise ValueError("claim relation self-relations are rejected")
        if (
            self.relation_type
            in {
                ClaimRelationType.EQUIVALENT_TO,
                ClaimRelationType.STRUCTURAL_CONFLICT_CANDIDATE,
            }
            and self.source_claim_id > self.target_claim_id
        ):
            raise ValueError("symmetric claim relations must use canonical endpoint order")
        if (
            self.relation_origin == ClaimRelationOrigin.OPERATOR_SUPPLIED
            and not self.operator_supplied
        ):
            raise ValueError("operator-supplied relation origin requires operator_supplied")
        if (
            self.relation_origin == ClaimRelationOrigin.DERIVED_STRUCTURAL
            and not self.derived_structural
        ):
            raise ValueError("derived structural relation origin requires derived_structural")
        if self.relation_fingerprint != claim_relation_fingerprint(self):
            raise ValueError("claim relation fingerprint mismatch")
        return self


def claim_relation_fingerprint(relation: ClaimRelationEdge | dict[str, Any]) -> str:
    """Fingerprint a claim relation edge."""

    payload = _model_dump_json(relation)
    payload.pop("relation_fingerprint", None)
    return fingerprint_payload(payload)


class StructuralConflictCandidate(BaseModel):
    """Conservative structural conflict candidate without resolution."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-structural-conflict-candidate/v1"] = (
        STRUCTURAL_CONFLICT_CANDIDATE_SCHEMA_VERSION
    )
    candidate_id: str
    left_claim_id: str
    right_claim_id: str
    shared_subject_id: str
    shared_predicate: str
    temporal_overlap: bool
    jurisdiction_overlap: bool
    version_overlap: bool
    object_conflict: bool
    polarity_conflict: bool
    scope_sufficient: bool
    reason_codes: tuple[str, ...]
    created_at: datetime
    candidate_fingerprint: str
    structural_conflict_candidate: Literal[True] = True
    contradiction_resolved: Literal[False] = False
    left_claim_true: Literal[False] = False
    right_claim_true: Literal[False] = False
    left_claim_false: Literal[False] = False
    right_claim_false: Literal[False] = False
    runtime_effect: Literal[False] = False

    @field_validator("candidate_id", "left_claim_id", "right_claim_id", "shared_subject_id")
    @classmethod
    def identifiers_are_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "structural conflict identifier")

    @field_validator("shared_predicate")
    @classmethod
    def predicate_is_safe(cls, value: str) -> str:
        return normalize_claim_predicate(value)

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_claim_graph_reason_codes(value)

    @field_validator("created_at")
    @classmethod
    def created_at_is_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value, "structural conflict candidate timestamp")

    @field_validator("candidate_fingerprint")
    @classmethod
    def candidate_fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "structural conflict candidate fingerprint")

    @model_validator(mode="after")
    def candidate_is_valid(self) -> Self:
        if self.left_claim_id == self.right_claim_id:
            raise ValueError("structural conflict candidate requires distinct claims")
        if self.left_claim_id > self.right_claim_id:
            raise ValueError("structural conflict candidate endpoints must be canonical")
        if not self.scope_sufficient:
            raise ValueError("structural conflict candidate requires sufficient overlapping scope")
        if not (self.object_conflict or self.polarity_conflict):
            raise ValueError("structural conflict candidate requires object or polarity conflict")
        if self.candidate_fingerprint != structural_conflict_candidate_fingerprint(self):
            raise ValueError("structural conflict candidate fingerprint mismatch")
        return self


def structural_conflict_candidate_fingerprint(
    candidate: StructuralConflictCandidate | dict[str, Any],
) -> str:
    """Fingerprint a structural conflict candidate."""

    payload = _model_dump_json(candidate)
    payload.pop("candidate_fingerprint", None)
    return fingerprint_payload(payload)


class ClaimGraphOperatorReviewReference(BaseModel):
    """Envelope payload reference to redacted operator review evidence."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-claim-graph-evidence/v1"] = (
        CLAIM_GRAPH_EVIDENCE_SCHEMA_VERSION
    )
    review_item_id: str
    evidence_bundle_fingerprint: str
    created_at: datetime
    reference_fingerprint: str
    operator_review_required: Literal[True] = True
    claim_verification_required: Literal[True] = True
    truth_engine_authorization_required: Literal[True] = True
    persistent_graph_write_authorization_required: Literal[True] = True
    knowledge_promotion_authorized: Literal[False] = False
    belief_mutation_authorized: Literal[False] = False
    runtime_effect: Literal[False] = False

    @field_validator("review_item_id")
    @classmethod
    def review_item_id_is_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "claim graph review item")

    @field_validator("evidence_bundle_fingerprint", "reference_fingerprint")
    @classmethod
    def fingerprints_are_hex(cls, value: str) -> str:
        return validate_hex64(value, "claim graph review reference fingerprint")

    @field_validator("created_at")
    @classmethod
    def created_at_is_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value, "claim graph review reference timestamp")

    @model_validator(mode="after")
    def reference_fingerprint_matches(self) -> Self:
        payload = self.model_dump(mode="json")
        payload.pop("reference_fingerprint", None)
        if self.reference_fingerprint != fingerprint_payload(payload):
            raise ValueError("claim graph review reference fingerprint mismatch")
        return self


type ClaimGraphPayload = Annotated[
    UnverifiedClaimAssertion
    | ClaimEvidenceBinding
    | ClaimRelationEdge
    | StructuralConflictCandidate
    | ClaimGraphOperatorReviewReference,
    Field(discriminator="schema_version"),
]


class ClaimGraphRecordEnvelope(BaseModel):
    """Immutable append-only claim-graph record envelope."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-claim-graph-record-envelope/v1"] = (
        CLAIM_GRAPH_RECORD_ENVELOPE_SCHEMA_VERSION
    )
    record_id: str
    record_kind: ClaimGraphRecordKind
    sequence_number: int = Field(ge=1)
    record_version: int = Field(ge=1)
    supersedes_record_id: str | None = None
    program_id: Literal["AION-KNOWLEDGE-INTELLIGENCE-001"] = PROGRAM_ID
    authorization_transaction_id: Literal["AION-208-KI-0003"] = AUTHORIZATION_TRANSACTION_ID
    implementation_task: Literal["AION-209"] = IMPLEMENTATION_TASK
    payload: ClaimGraphPayload
    payload_fingerprint: str
    previous_record_fingerprint: str | None = None
    created_at: datetime
    record_fingerprint: str
    synthetic: Literal[True] = True
    read_only: Literal[True] = True
    redacted: Literal[True] = True
    append_only: Literal[True] = True
    unverified: Literal[True] = True
    truth_value_assigned: Literal[False] = False
    epistemic_confidence_assigned: Literal[False] = False
    knowledge_promoted: Literal[False] = False
    belief_created: Literal[False] = False
    belief_mutated: Literal[False] = False
    persistent_write_applied: Literal[False] = False
    source_body_present: Literal[False] = False
    source_body_bytes: Literal[0] = 0
    runtime_effect: Literal[False] = False

    @field_validator("record_id", "supersedes_record_id")
    @classmethod
    def identifiers_are_safe(cls, value: str | None) -> str | None:
        if value is not None:
            return validate_safe_identifier(value, "claim graph record identifier")
        return value

    @field_validator("payload_fingerprint", "previous_record_fingerprint", "record_fingerprint")
    @classmethod
    def fingerprints_are_hex(cls, value: str | None) -> str | None:
        if value is not None:
            return validate_hex64(value, "claim graph record fingerprint")
        return value

    @field_validator("created_at")
    @classmethod
    def created_at_is_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value, "claim graph record timestamp")

    @model_validator(mode="after")
    def envelope_invariants_hold(self) -> Self:
        if self.payload_fingerprint != claim_graph_payload_fingerprint(self.payload):
            raise ValueError("claim graph payload fingerprint mismatch")
        if self.record_kind != _payload_record_kind(self.payload):
            raise ValueError("claim graph record kind does not match payload")
        if self.record_version == 1 and self.supersedes_record_id is not None:
            raise ValueError("initial claim graph record must not supersede another record")
        if self.record_version > 1 and self.supersedes_record_id is None:
            raise ValueError("claim graph correction record must reference superseded record")
        if self.supersedes_record_id == self.record_id:
            raise ValueError("claim graph record cannot supersede itself")
        if self.record_fingerprint != claim_graph_record_fingerprint(self):
            raise ValueError("claim graph record fingerprint mismatch")
        return self


class ClaimGraphResourceBudget(BaseModel):
    """AION-208-KI-0003 claim-graph resource budget with write batch at zero."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-claim-graph-batch/v1"] = (
        CLAIM_GRAPH_BATCH_SCHEMA_VERSION
    )
    maximum_claim_nodes_per_graph: Literal[1000] = 1000
    maximum_evidence_bindings_per_graph: Literal[5000] = 5000
    maximum_claim_relation_edges_per_graph: Literal[5000] = 5000
    maximum_source_registry_references_per_claim: Literal[50] = 50
    maximum_citation_references_per_claim: Literal[50] = 50
    maximum_lineage_groups_per_claim: Literal[20] = 20
    maximum_jurisdictions_per_claim: Literal[20] = 20
    maximum_versions_per_claim: Literal[20] = 20
    maximum_temporal_intervals_per_claim: Literal[8] = 8
    maximum_relation_edges_per_claim: Literal[100] = 100
    maximum_query_results: Literal[1000] = 1000
    maximum_fixture_records: Literal[2000] = 2000
    maximum_fixture_bytes: Literal[2097152] = 2_097_152
    maximum_concurrent_readers: Literal[4] = 4
    maximum_concurrent_projections: Literal[4] = 4
    maximum_graph_write_batch: Literal[0] = 0
    maximum_source_body_bytes: Literal[0] = 0
    maximum_automatic_claim_extractions: Literal[0] = 0
    maximum_claim_verifications: Literal[0] = 0
    maximum_truth_decisions: Literal[0] = 0
    maximum_confidence_calculations: Literal[0] = 0
    maximum_knowledge_promotions: Literal[0] = 0
    maximum_belief_mutations: Literal[0] = 0
    maximum_network_calls: Literal[0] = 0
    maximum_search_provider_calls: Literal[0] = 0
    maximum_connector_calls: Literal[0] = 0
    maximum_model_provider_calls: Literal[0] = 0
    maximum_source_mutations: Literal[0] = 0
    maximum_git_operations: Literal[0] = 0
    maximum_runtime_created_pull_requests: Literal[0] = 0
    maximum_approvals_created: Literal[0] = 0
    maximum_deployments: Literal[0] = 0
    maximum_model_weight_changes: Literal[0] = 0


class ClaimGraphResourceUsage(BaseModel):
    """Measured claim-graph usage for one proposed operation."""

    model_config = FROZEN_MODEL_CONFIG

    claim_nodes: int = Field(default=0, ge=0)
    evidence_bindings: int = Field(default=0, ge=0)
    claim_relation_edges: int = Field(default=0, ge=0)
    maximum_source_registry_references_per_claim: int = Field(default=0, ge=0)
    maximum_citation_references_per_claim: int = Field(default=0, ge=0)
    maximum_lineage_groups_per_claim: int = Field(default=0, ge=0)
    maximum_jurisdictions_per_claim: int = Field(default=0, ge=0)
    maximum_versions_per_claim: int = Field(default=0, ge=0)
    maximum_temporal_intervals_per_claim: int = Field(default=0, ge=0)
    maximum_relation_edges_per_claim: int = Field(default=0, ge=0)
    query_results: int = Field(default=0, ge=0)
    fixture_records: int = Field(default=0, ge=0)
    fixture_bytes: int = Field(default=0, ge=0)
    concurrent_readers: int = Field(default=0, ge=0)
    concurrent_projections: int = Field(default=0, ge=0)
    graph_write_batch: int = Field(default=0, ge=0)
    source_body_bytes: int = Field(default=0, ge=0)
    automatic_claim_extractions: int = Field(default=0, ge=0)
    claim_verifications: int = Field(default=0, ge=0)
    truth_decisions: int = Field(default=0, ge=0)
    confidence_calculations: int = Field(default=0, ge=0)
    knowledge_promotions: int = Field(default=0, ge=0)
    belief_mutations: int = Field(default=0, ge=0)
    network_calls: int = Field(default=0, ge=0)
    search_provider_calls: int = Field(default=0, ge=0)
    connector_calls: int = Field(default=0, ge=0)
    model_provider_calls: int = Field(default=0, ge=0)
    source_mutations: int = Field(default=0, ge=0)
    git_operations: int = Field(default=0, ge=0)
    runtime_created_pull_requests: int = Field(default=0, ge=0)
    approvals_created: int = Field(default=0, ge=0)
    deployments: int = Field(default=0, ge=0)
    model_weight_changes: int = Field(default=0, ge=0)


class ClaimGraphBudgetDecision(BaseModel):
    """Budget decision for claim-graph work."""

    model_config = FROZEN_MODEL_CONFIG

    within_budget: bool
    usage: ClaimGraphResourceUsage
    budget: ClaimGraphResourceBudget
    reason_codes: tuple[str, ...]
    persistent_write_allowed: Literal[False] = False
    operator_review_required: Literal[True] = True
    fingerprint: str
    runtime_effect: Literal[False] = False

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_claim_graph_reason_codes(value)

    @field_validator("fingerprint")
    @classmethod
    def fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "claim graph budget fingerprint")

    @model_validator(mode="after")
    def fingerprint_matches(self) -> Self:
        payload = {
            "within_budget": self.within_budget,
            "usage": self.usage.model_dump(mode="json"),
            "budget": self.budget.model_dump(mode="json"),
            "reason_codes": self.reason_codes,
        }
        if self.fingerprint != fingerprint_payload(payload):
            raise ValueError("claim graph budget fingerprint mismatch")
        return self


class ClaimGraphProposedBatch(BaseModel):
    """Immutable proposed claim-graph batch; no persistent write is applied."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-claim-graph-batch/v1"] = (
        CLAIM_GRAPH_BATCH_SCHEMA_VERSION
    )
    program_id: Literal["AION-KNOWLEDGE-INTELLIGENCE-001"] = PROGRAM_ID
    authorization_transaction_id: Literal["AION-208-KI-0003"] = AUTHORIZATION_TRANSACTION_ID
    implementation_task: Literal["AION-209"] = IMPLEMENTATION_TASK
    formal_closeout_task: Literal["AION-210"] = FORMAL_CLOSEOUT_TASK
    authorization_scope: Literal[
        "append-only-immutable-temporal-claim-evidence-provenance-jurisdiction-version-contradiction-graph-core"
    ] = AUTHORIZATION_SCOPE
    graph_id: str
    records: tuple[ClaimGraphRecordEnvelope, ...]
    record_count: int = Field(ge=0)
    claim_count: int = Field(ge=0)
    evidence_binding_count: int = Field(ge=0)
    relation_count: int = Field(ge=0)
    structural_conflict_candidate_count: int = Field(ge=0)
    budget_decision: ClaimGraphBudgetDecision
    operator_review_required: Literal[True] = True
    persistent_write_applied: Literal[False] = False
    append_only: Literal[True] = True
    created_at: datetime
    batch_fingerprint: str
    runtime_effect: Literal[False] = False

    @field_validator("graph_id")
    @classmethod
    def graph_id_is_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "claim graph_id")

    @field_validator("created_at")
    @classmethod
    def created_at_is_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value, "claim graph batch timestamp")

    @field_validator("batch_fingerprint")
    @classmethod
    def batch_fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "claim graph batch fingerprint")

    @model_validator(mode="after")
    def batch_invariants_hold(self) -> Self:
        if self.record_count != len(self.records):
            raise ValueError("claim graph record_count must match records")
        if self.claim_count != sum(
            record.record_kind == ClaimGraphRecordKind.CLAIM_ASSERTION for record in self.records
        ):
            raise ValueError("claim graph claim_count must match records")
        if self.evidence_binding_count != sum(
            record.record_kind == ClaimGraphRecordKind.EVIDENCE_BINDING for record in self.records
        ):
            raise ValueError("claim graph evidence_binding_count must match records")
        if self.relation_count != sum(
            record.record_kind == ClaimGraphRecordKind.RELATION_EDGE for record in self.records
        ):
            raise ValueError("claim graph relation_count must match records")
        if self.structural_conflict_candidate_count != sum(
            record.record_kind == ClaimGraphRecordKind.STRUCTURAL_CONFLICT_CANDIDATE
            for record in self.records
        ):
            raise ValueError("claim graph conflict count must match records")
        if not self.budget_decision.within_budget:
            raise ValueError("invalid claim graph batch exceeds budget")
        if self.batch_fingerprint != claim_graph_batch_fingerprint(self):
            raise ValueError("claim graph batch fingerprint mismatch")
        return self


class ClaimGraphAppendDecision(BaseModel):
    """Decision from simulated append or rejected persistent write."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-claim-graph-batch/v1"] = (
        CLAIM_GRAPH_BATCH_SCHEMA_VERSION
    )
    append_allowed: bool
    append_outcome: ClaimGraphAppendOutcome
    persistent_write_requested: bool
    persistent_write_applied: Literal[False] = False
    appended_record_count: int = Field(ge=0)
    idempotent_replay_count: int = Field(default=0, ge=0)
    operator_review_required: Literal[True] = True
    persistent_graph_write_authorization_required: Literal[True] = True
    reason_codes: tuple[str, ...]
    created_at: datetime
    fingerprint: str
    runtime_effect: Literal[False] = False

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_claim_graph_reason_codes(value)

    @field_validator("created_at")
    @classmethod
    def created_at_is_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value, "claim graph append decision timestamp")

    @field_validator("fingerprint")
    @classmethod
    def fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "claim graph append decision fingerprint")

    @model_validator(mode="after")
    def fingerprint_matches(self) -> Self:
        if self.fingerprint != claim_graph_append_decision_fingerprint(self):
            raise ValueError("claim graph append decision fingerprint mismatch")
        return self


class ClaimGraphState(BaseModel):
    """Immutable in-memory claim-graph state summary."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-claim-graph-state/v1"] = (
        CLAIM_GRAPH_STATE_SCHEMA_VERSION
    )
    program_id: Literal["AION-KNOWLEDGE-INTELLIGENCE-001"] = PROGRAM_ID
    authorization_transaction_id: Literal["AION-208-KI-0003"] = AUTHORIZATION_TRANSACTION_ID
    implementation_task: Literal["AION-209"] = IMPLEMENTATION_TASK
    formal_closeout_task: Literal["AION-210"] = FORMAL_CLOSEOUT_TASK
    authorization_scope: Literal[
        "append-only-immutable-temporal-claim-evidence-provenance-jurisdiction-version-contradiction-graph-core"
    ] = AUTHORIZATION_SCOPE
    graph_id: str
    record_count: int = Field(ge=0)
    claim_count: int = Field(ge=0)
    evidence_binding_count: int = Field(ge=0)
    relation_count: int = Field(ge=0)
    structural_conflict_candidate_count: int = Field(ge=0)
    chain_head_fingerprint: str | None
    state_fingerprint: str
    read_only: Literal[True] = True
    redacted: Literal[True] = True
    unverified: Literal[True] = True
    truth_value_assigned: Literal[False] = False
    epistemic_confidence_assigned: Literal[False] = False
    persistent_write_applied: Literal[False] = False
    runtime_effect: Literal[False] = False

    @field_validator("graph_id")
    @classmethod
    def graph_id_is_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "claim graph state graph_id")

    @field_validator("chain_head_fingerprint", "state_fingerprint")
    @classmethod
    def fingerprints_are_hex(cls, value: str | None) -> str | None:
        if value is not None:
            return validate_hex64(value, "claim graph state fingerprint")
        return value


def evaluate_claim_graph_budget(
    usage: ClaimGraphResourceUsage,
    budget: ClaimGraphResourceBudget | None = None,
) -> ClaimGraphBudgetDecision:
    """Evaluate claim-graph usage against the AION-208-KI-0003 zero-write budget."""

    current_budget = budget or ClaimGraphResourceBudget()
    reasons: list[str] = []
    _append_limit_reason(
        reasons,
        usage.claim_nodes,
        current_budget.maximum_claim_nodes_per_graph,
        "claim_graph_claim_valid",
        "claim_graph_claim_invalid",
    )
    _append_limit_reason(
        reasons,
        usage.evidence_bindings,
        current_budget.maximum_evidence_bindings_per_graph,
        "claim_graph_evidence_binding_valid",
        "claim_graph_evidence_binding_invalid",
    )
    _append_limit_reason(
        reasons,
        usage.claim_relation_edges,
        current_budget.maximum_claim_relation_edges_per_graph,
        "claim_graph_relation_valid",
        "claim_graph_relation_invalid",
    )
    limit_checks = (
        (
            usage.maximum_source_registry_references_per_claim,
            current_budget.maximum_source_registry_references_per_claim,
            "claim_graph_source_reference_unresolved",
        ),
        (
            usage.maximum_citation_references_per_claim,
            current_budget.maximum_citation_references_per_claim,
            "claim_graph_citation_reference_unresolved",
        ),
        (
            usage.maximum_lineage_groups_per_claim,
            current_budget.maximum_lineage_groups_per_claim,
            "claim_graph_duplicate_independence_blocked",
        ),
        (
            usage.maximum_jurisdictions_per_claim,
            current_budget.maximum_jurisdictions_per_claim,
            "claim_graph_scope_insufficient",
        ),
        (
            usage.maximum_versions_per_claim,
            current_budget.maximum_versions_per_claim,
            "claim_graph_scope_insufficient",
        ),
        (
            usage.maximum_temporal_intervals_per_claim,
            current_budget.maximum_temporal_intervals_per_claim,
            "claim_graph_scope_insufficient",
        ),
        (
            usage.maximum_relation_edges_per_claim,
            current_budget.maximum_relation_edges_per_claim,
            "claim_graph_relation_invalid",
        ),
        (
            usage.query_results,
            current_budget.maximum_query_results,
            "claim_graph_query_limit_exceeded",
        ),
        (
            usage.fixture_records,
            current_budget.maximum_fixture_records,
            "claim_graph_fixture_rejected",
        ),
        (
            usage.fixture_bytes,
            current_budget.maximum_fixture_bytes,
            "claim_graph_fixture_rejected",
        ),
        (
            usage.concurrent_readers,
            current_budget.maximum_concurrent_readers,
            "claim_graph_runtime_disabled",
        ),
        (
            usage.concurrent_projections,
            current_budget.maximum_concurrent_projections,
            "claim_graph_runtime_disabled",
        ),
    )
    for actual, limit, reason in limit_checks:
        if actual > limit:
            reasons.append(reason)
    zero_limited = (
        (usage.graph_write_batch, "claim_graph_persistent_write_disabled"),
        (usage.source_body_bytes, "claim_graph_source_body_blocked"),
        (usage.automatic_claim_extractions, "claim_graph_automatic_extraction_blocked"),
        (usage.claim_verifications, "claim_graph_truth_decision_blocked"),
        (usage.truth_decisions, "claim_graph_truth_decision_blocked"),
        (usage.confidence_calculations, "claim_graph_confidence_calculation_blocked"),
        (usage.knowledge_promotions, "claim_graph_knowledge_promotion_blocked"),
        (usage.belief_mutations, "claim_graph_belief_mutation_blocked"),
        (usage.network_calls, "claim_graph_network_fetch_blocked"),
        (usage.search_provider_calls, "claim_graph_network_fetch_blocked"),
        (usage.connector_calls, "claim_graph_runtime_disabled"),
        (usage.model_provider_calls, "claim_graph_runtime_disabled"),
        (usage.source_mutations, "claim_graph_runtime_disabled"),
        (usage.git_operations, "claim_graph_runtime_disabled"),
        (usage.runtime_created_pull_requests, "claim_graph_runtime_disabled"),
        (usage.approvals_created, "claim_graph_runtime_disabled"),
        (usage.deployments, "claim_graph_runtime_disabled"),
        (usage.model_weight_changes, "claim_graph_runtime_disabled"),
    )
    for count, reason in zero_limited:
        if count > 0:
            reasons.append(reason)
    unique_reasons = tuple(dict.fromkeys(reasons))
    blocking_reasons = {
        reason
        for reason in unique_reasons
        if reason.endswith("_invalid")
        or reason.endswith("_blocked")
        or reason.endswith("_disabled")
        or reason.endswith("_unresolved")
        or reason.endswith("_rejected")
        or reason.endswith("_exceeded")
        or reason == "claim_graph_scope_insufficient"
    }
    within_budget = not blocking_reasons
    reason_codes = (
        ("claim_graph_batch_valid", *unique_reasons)
        if within_budget
        else ("claim_graph_batch_invalid", *unique_reasons)
    )
    payload = {
        "within_budget": within_budget,
        "usage": usage.model_dump(mode="json"),
        "budget": current_budget.model_dump(mode="json"),
        "reason_codes": reason_codes,
    }
    return ClaimGraphBudgetDecision(
        within_budget=within_budget,
        usage=usage,
        budget=current_budget,
        reason_codes=reason_codes,
        fingerprint=fingerprint_payload(payload),
    )


def claim_graph_batch_fingerprint(batch: ClaimGraphProposedBatch | dict[str, Any]) -> str:
    """Fingerprint a proposed claim-graph batch."""

    payload = _model_dump_json(batch)
    payload.pop("batch_fingerprint", None)
    return fingerprint_payload(payload)


def claim_graph_append_decision_fingerprint(
    decision: ClaimGraphAppendDecision | dict[str, Any],
) -> str:
    """Fingerprint a claim-graph append decision."""

    payload = _model_dump_json(decision)
    payload.pop("fingerprint", None)
    return fingerprint_payload(payload)


def _payload_record_kind(payload: ClaimGraphPayload) -> ClaimGraphRecordKind:
    if isinstance(payload, UnverifiedClaimAssertion):
        return ClaimGraphRecordKind.CLAIM_ASSERTION
    if isinstance(payload, ClaimEvidenceBinding):
        return ClaimGraphRecordKind.EVIDENCE_BINDING
    if isinstance(payload, ClaimRelationEdge):
        return ClaimGraphRecordKind.RELATION_EDGE
    if isinstance(payload, StructuralConflictCandidate):
        return ClaimGraphRecordKind.STRUCTURAL_CONFLICT_CANDIDATE
    return ClaimGraphRecordKind.OPERATOR_REVIEW_REFERENCE


def _append_limit_reason(
    reasons: list[str],
    actual: int,
    limit: int,
    ok_reason: str,
    fail_reason: str,
) -> None:
    reasons.append(ok_reason if actual <= limit else fail_reason)


def _require_object_fingerprint(value: _ObjectValueBase, canonical_value: object) -> None:
    expected = claim_object_value_fingerprint(
        kind=str(value.kind),
        canonical_value=canonical_value,
    )
    if value.object_fingerprint != expected:
        raise ValueError("claim object fingerprint mismatch")


def _reject_sensitive_text(value: str, field_name: str) -> None:
    reject_protected_material(value, field_name)
    if _COMMAND_RE.search(value):
        raise ValueError(f"{field_name} must not contain executable command text")
    lowered = value.lower()
    for marker in (
        "authorization header",
        "source preview",
        "source body",
        "source quotation",
        "raw prompt",
        "hidden reasoning",
        "raw user message",
        "raw diff",
    ):
        if marker in lowered:
            raise ValueError(f"{field_name} contains protected material")


def _reject_duplicate_ids(values: list[str]) -> None:
    if len(values) != len(set(values)):
        raise ValueError("duplicate scoped identifiers rejected")


def _parse_numeric_dotted(value: str | None) -> tuple[int, ...]:
    if value is None or not _NUMERIC_DOTTED_RE.fullmatch(value):
        raise ValueError("numeric dotted version requires integer components")
    return tuple(int(part) for part in value.split("."))


def _compare_versions(left: tuple[int, ...], right: tuple[int, ...]) -> int:
    width = max(len(left), len(right))
    padded_left = left + (0,) * (width - len(left))
    padded_right = right + (0,) * (width - len(right))
    return (padded_left > padded_right) - (padded_left < padded_right)


def _intervals_overlap_bool(left: ValidTimeInterval, right: ValidTimeInterval) -> bool:
    left_start = left.start
    left_end = left.end
    right_start = right.start
    right_end = right.end
    if left_end is not None and right_start is not None:
        if left_end < right_start:
            return False
        if left_end == right_start and not (left.end_inclusive and right.start_inclusive):
            return False
    if right_end is not None and left_start is not None:
        if right_end < left_start:
            return False
        if right_end == left_start and not (right.end_inclusive and left.start_inclusive):
            return False
    return True


def _json_scalar(value: object) -> object:
    if isinstance(value, datetime):
        return _json_datetime(value)
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value.normalize())
    if isinstance(value, StrEnum):
        return value.value
    return value


def _enum_value(value: object) -> object:
    if isinstance(value, StrEnum):
        return value.value
    return value


def _model_dump_json(value: object) -> dict[str, Any]:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    raise TypeError("claim graph payload must be a model or mapping")


def _json_ready(value: object) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, datetime):
        return _json_datetime(value)
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value.normalize())
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value


def _json_datetime(value: datetime) -> str:
    text = value.isoformat()
    if text.endswith("+00:00"):
        return f"{text[:-6]}Z"
    return text


def json_size(value: object) -> int:
    """Return deterministic JSON byte size for budget checks."""

    return len(stable_json(_json_ready(value)).encode("utf-8"))


__all__ = [
    "APPROVAL_RECORD_ID",
    "AUTHORIZATION_SCOPE",
    "AUTHORIZATION_TRANSACTION_ID",
    "CLAIM_EVIDENCE_BINDING_SCHEMA_VERSION",
    "CLAIM_GRAPH_BATCH_SCHEMA_VERSION",
    "CLAIM_GRAPH_CONTRACT_SCHEMA_VERSION",
    "CLAIM_GRAPH_EVIDENCE_SCHEMA_VERSION",
    "CLAIM_GRAPH_FIXTURE_SCHEMA_VERSION",
    "CLAIM_GRAPH_INDEX_SCHEMA_VERSION",
    "CLAIM_GRAPH_INTEGRITY_SCHEMA_VERSION",
    "CLAIM_GRAPH_QUERY_SCHEMA_VERSION",
    "CLAIM_GRAPH_REASON_CODES",
    "CLAIM_GRAPH_RECORD_ENVELOPE_SCHEMA_VERSION",
    "CLAIM_GRAPH_STATE_SCHEMA_VERSION",
    "CLAIM_RELATION_EDGE_SCHEMA_VERSION",
    "CLAIM_SCOPE_SCHEMA_VERSION",
    "FORMAL_CLOSEOUT_TASK",
    "IMPLEMENTATION_TASK",
    "MAXIMUM_GRAPH_WRITE_BATCH",
    "PROGRAM_ID",
    "STRUCTURAL_CONFLICT_CANDIDATE_SCHEMA_VERSION",
    "UNVERIFIED_CLAIM_ASSERTION_SCHEMA_VERSION",
    "BooleanClaimObjectValue",
    "ClaimEvidenceBinding",
    "ClaimGraphAppendDecision",
    "ClaimGraphAppendOutcome",
    "ClaimGraphBudgetDecision",
    "ClaimGraphIntegrityStatus",
    "ClaimGraphOperatorReviewReference",
    "ClaimGraphPayload",
    "ClaimGraphProposedBatch",
    "ClaimGraphRecordEnvelope",
    "ClaimGraphRecordKind",
    "ClaimGraphResourceBudget",
    "ClaimGraphResourceUsage",
    "ClaimGraphState",
    "ClaimModality",
    "ClaimObjectType",
    "ClaimObjectValue",
    "ClaimPolarity",
    "ClaimPredicateCardinality",
    "ClaimRelationEdge",
    "ClaimRelationOrigin",
    "ClaimRelationType",
    "ClaimScope",
    "DateClaimObjectValue",
    "DateTimeClaimObjectValue",
    "DecimalClaimObjectValue",
    "EvidenceRole",
    "IdentifierClaimObjectValue",
    "IntegerClaimObjectValue",
    "JurisdictionKind",
    "JurisdictionScope",
    "QuantityClaimObjectValue",
    "RangeClaimObjectValue",
    "StructuralConflictCandidate",
    "TextClaimObjectValue",
    "UnverifiedClaimAssertion",
    "ValidTimeInterval",
    "VersionClaimObjectValue",
    "VersionScheme",
    "VersionScope",
    "calculate_claim_identity_fingerprint",
    "calculate_claim_record_fingerprint",
    "claim_evidence_binding_fingerprint",
    "claim_graph_append_decision_fingerprint",
    "claim_graph_batch_fingerprint",
    "claim_graph_payload_fingerprint",
    "claim_graph_record_fingerprint",
    "claim_object_value_fingerprint",
    "claim_relation_fingerprint",
    "claim_scope_fingerprint",
    "evaluate_claim_graph_budget",
    "jurisdiction_scope_fingerprint",
    "json_size",
    "normalize_claim_predicate",
    "normalize_claim_statement",
    "normalize_claim_subject",
    "structural_conflict_candidate_fingerprint",
    "valid_time_interval_fingerprint",
    "validate_claim_graph_reason_codes",
    "version_scope_fingerprint",
]
