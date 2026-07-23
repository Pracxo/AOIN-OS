"""Controlled Knowledge Intelligence research-acquisition contracts."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from typing import Any, Literal, Self
from urllib.parse import urlsplit, urlunsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

KNOWLEDGE_RESEARCH_CONTRACT_SCHEMA_VERSION = "aion-knowledge-research/v1"
RESEARCH_QUERY_SCHEMA_VERSION: Literal["aion-knowledge-research-query/v1"] = (
    "aion-knowledge-research-query/v1"
)
RESEARCH_PLAN_SCHEMA_VERSION: Literal["aion-knowledge-research-plan/v1"] = (
    "aion-knowledge-research-plan/v1"
)
SOURCE_CANDIDATE_SCHEMA_VERSION: Literal["aion-knowledge-source-candidate/v1"] = (
    "aion-knowledge-source-candidate/v1"
)
SOURCE_SNAPSHOT_SCHEMA_VERSION: Literal["aion-knowledge-source-snapshot/v1"] = (
    "aion-knowledge-source-snapshot/v1"
)
SOURCE_PROVENANCE_SCHEMA_VERSION: Literal["aion-knowledge-source-provenance/v1"] = (
    "aion-knowledge-source-provenance/v1"
)
SOURCE_LINEAGE_SCHEMA_VERSION: Literal["aion-knowledge-source-lineage/v1"] = (
    "aion-knowledge-source-lineage/v1"
)
CITATION_REFERENCE_SCHEMA_VERSION: Literal["aion-knowledge-citation-reference/v1"] = (
    "aion-knowledge-citation-reference/v1"
)
RESEARCH_EVIDENCE_SCHEMA_VERSION: Literal["aion-knowledge-research-evidence/v1"] = (
    "aion-knowledge-research-evidence/v1"
)
RESEARCH_DIAGNOSTICS_SCHEMA_VERSION: Literal[
    "aion-knowledge-research-diagnostics/v1"
] = "aion-knowledge-research-diagnostics/v1"
RESEARCH_INCIDENT_SCHEMA_VERSION: Literal["aion-knowledge-research-incident/v1"] = (
    "aion-knowledge-research-incident/v1"
)
RESEARCH_BUDGET_SCHEMA_VERSION = "aion-knowledge-research-budget/v1"
RESEARCH_REASON_CODE_REGISTRY_VERSION = "aion-knowledge-research-reasons/v1"

PROGRAM_ID: Literal["AION-KNOWLEDGE-INTELLIGENCE-001"] = "AION-KNOWLEDGE-INTELLIGENCE-001"
PARENT_PROGRAM_ID = "AION-COGNITIVE-ARCHITECTURE-001"
AUTHORIZATION_TRANSACTION_ID: Literal["AION-204-KI-0001"] = "AION-204-KI-0001"
APPROVAL_RECORD_ID: Literal["AION-204-KI-0001"] = "AION-204-KI-0001"
CANDIDATE_ID = "controlled-internet-research-acquisition-core"
WORKSTREAM = "knowledge-intelligence-research-acquisition"
IMPLEMENTATION_TASK: Literal["AION-205"] = "AION-205"
FORMAL_CLOSEOUT_TASK: Literal["AION-206"] = "AION-206"
AUTHORIZATION_SCOPE: Literal[
    "disabled-allowlisted-public-research-query-fetch-snapshot-provenance-core"
] = "disabled-allowlisted-public-research-query-fetch-snapshot-provenance-core"

MAXIMUM_QUERIES_PER_PLAN = 20
MAXIMUM_DOMAINS_PER_PLAN = 20
MAXIMUM_SOURCE_CANDIDATES_PER_PLAN = 100
MAXIMUM_FETCHES_PER_PLAN = 50
MAXIMUM_REDIRECTS_PER_FETCH = 3
MAXIMUM_CONCURRENCY = 4
MAXIMUM_TIMEOUT_SECONDS_PER_REQUEST = 20
MAXIMUM_WALL_CLOCK_SECONDS_PER_PLAN = 900
MAXIMUM_RESPONSE_BYTES_PER_SOURCE = 5_242_880
MAXIMUM_TOTAL_TRANSFER_BYTES_PER_PLAN = 52_428_800
MAXIMUM_SNAPSHOT_RECORDS_PER_PLAN = 100
MAXIMUM_SAFE_HEADERS_PER_SNAPSHOT = 32
MAXIMUM_CITATION_REFERENCES_PER_SNAPSHOT = 20
MAXIMUM_OPERATOR_REVIEW_ITEMS_PER_PLAN = 50

ResearchMethod = Literal["GET", "HEAD"]
ResearchSourceClass = Literal[
    "primary_authoritative",
    "official_standard",
    "official_government",
    "peer_reviewed",
    "vendor_primary",
    "institutional_primary",
    "reputable_secondary",
    "community_unverified",
    "unknown",
    "disallowed",
]
ResearchContentType = Literal[
    "text/html",
    "text/plain",
    "application/json",
    "application/pdf",
    "application/xml",
    "text/xml",
]
ResearchAdapterType = Literal[
    "disabled",
    "in_memory",
    "explicit_local_fixture",
    "operator_invoked_http",
]
ResearchSearchAdapterType = Literal["disabled", "in_memory"]
ResearchPlanState = Literal[
    "drafted",
    "validated",
    "acquisition_ready",
    "acquired",
    "review_pending",
    "failed",
    "archived",
]
ResearchPlanOutcome = Literal[
    "completed",
    "completed_with_rejections",
    "budget_blocked",
    "policy_blocked",
    "adapter_disabled",
    "source_unavailable",
    "content_rejected",
    "incident_recorded",
]
RobotsPolicyStatus = Literal["allowed", "disallowed", "unknown", "not_applicable"]
LicencePolicyStatus = Literal["permitted", "restricted", "unknown", "not_applicable"]
SourceLineageKind = Literal[
    "original",
    "redirect",
    "canonical_alias",
    "exact_duplicate",
    "suspected_mirror",
]
CitationLocatorKind = Literal[
    "full_source",
    "byte_range",
    "text_fingerprint",
    "page_number",
    "json_pointer",
    "xml_path",
]

RESEARCH_REASON_CODES: tuple[str, ...] = (
    "research_plan_valid",
    "research_plan_invalid",
    "research_query_valid",
    "research_query_invalid",
    "research_candidate_valid",
    "research_candidate_invalid",
    "research_domain_allowed",
    "research_domain_blocked",
    "research_scheme_allowed",
    "research_scheme_blocked",
    "research_destination_public",
    "research_destination_blocked",
    "research_dns_resolution_valid",
    "research_dns_resolution_blocked",
    "research_dns_rebinding_blocked",
    "research_redirect_allowed",
    "research_redirect_blocked",
    "research_redirect_limit_exceeded",
    "research_redirect_loop_detected",
    "research_method_allowed",
    "research_method_blocked",
    "research_content_type_allowed",
    "research_content_type_blocked",
    "research_character_encoding_valid",
    "research_character_encoding_invalid",
    "research_response_size_allowed",
    "research_response_size_exceeded",
    "research_total_transfer_allowed",
    "research_total_transfer_exceeded",
    "research_timeout_allowed",
    "research_timeout_exceeded",
    "research_concurrency_allowed",
    "research_concurrency_exceeded",
    "research_safe_headers_projected",
    "research_source_snapshotted",
    "research_source_snapshot_rejected",
    "research_provenance_recorded",
    "research_exact_url_duplicate",
    "research_exact_content_duplicate",
    "research_redirect_alias",
    "research_suspected_mirror",
    "research_independence_not_established",
    "research_citation_reference_created",
    "research_budget_satisfied",
    "research_budget_exceeded",
    "research_adapter_disabled",
    "research_search_adapter_disabled",
    "research_network_transport_unavailable",
    "research_private_network_blocked",
    "research_loopback_blocked",
    "research_link_local_blocked",
    "research_multicast_blocked",
    "research_reserved_address_blocked",
    "research_metadata_service_blocked",
    "research_robots_disallowed",
    "research_licence_restricted",
    "research_source_class_disallowed",
    "research_protected_material_blocked",
    "research_prompt_injection_untrusted",
    "research_operator_review_required",
    "research_claim_verification_not_performed",
    "research_knowledge_promotion_blocked",
    "research_belief_mutation_blocked",
    "research_background_crawl_blocked",
    "research_runtime_disabled",
    "research_plan_completed",
    "research_plan_completed_with_rejections",
    "research_plan_stopped_fail_closed",
)

MODEL_CONFIG = ConfigDict(extra="forbid", hide_input_in_errors=True)
FROZEN_MODEL_CONFIG = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
ALIASED_FROZEN_MODEL_CONFIG = ConfigDict(
    extra="forbid",
    hide_input_in_errors=True,
    frozen=True,
    populate_by_name=True,
)

_SAFE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._:-]{0,127}$")
_HEX64_RE = re.compile(r"^[a-f0-9]{64}$")
_COMMIT40_RE = re.compile(r"^[a-f0-9]{40}$")
_MALFORMED_PERCENT_RE = re.compile(r"%(?![0-9A-Fa-f]{2})")
_URL_RE = re.compile(r"https?://", re.IGNORECASE)
_SHELL_RE = re.compile(r"(^|\s)(curl|wget|bash|sh|zsh|python|node|git)\s", re.IGNORECASE)
_SECRET_KEY_PARTS = (
    "password",
    "credential",
    "authorization",
    "bearer",
    "access" "_token",
    "refresh" "_token",
    "session" "_token",
    "token",
    "cookie",
    "private" "_key",
    "signing" "_key",
    "raw" "_prompt",
    "hidden" "_reasoning",
    "chain" "_of_thought",
    "raw" "_user_message",
    "source" "_patch",
    "raw_diff",
)
_PROTECTED_VALUE_MARKERS = (
    "sk-",
    "ghp_",
    "gho_",
    "xoxb-",
    "bearer ",
    "authorization:",
    "cookie:",
    "-----begin private key-----",
    "chain-of-thought",
    "chain of thought",
    "hidden reasoning",
    "raw prompt",
    "developer prompt",
    "system prompt",
    "raw user message",
    "source patch",
    "raw diff",
    "unredacted personal data",
)


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""

    return datetime.now(UTC)


def ensure_utc(value: datetime, field_name: str = "timestamp") -> datetime:
    """Validate an aware UTC timestamp without coercing non-UTC inputs."""

    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware UTC")
    if value.utcoffset() != UTC.utcoffset(value):
        raise ValueError(f"{field_name} must use UTC")
    return value.astimezone(UTC)


def sha256_bytes(data: bytes) -> str:
    """Return a lower-case SHA-256 fingerprint."""

    return hashlib.sha256(data).hexdigest()


def stable_json(value: Any) -> str:
    """Serialize JSON-compatible data deterministically."""

    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def fingerprint_payload(value: Any) -> str:
    """Return a deterministic fingerprint for JSON-compatible data."""

    return sha256_bytes(stable_json(value).encode("utf-8"))


def validate_safe_identifier(value: str, field_name: str = "identifier") -> str:
    """Validate a bounded lowercase identifier."""

    if not _SAFE_ID_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a safe lowercase identifier")
    reject_protected_material(value, field_name)
    return value


def validate_hex64(value: str, field_name: str = "fingerprint") -> str:
    """Validate a 64-character lower-case hex fingerprint."""

    if not _HEX64_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a 64-character lowercase hex value")
    return value


def validate_commit_sha(value: str, field_name: str = "commit_sha") -> str:
    """Validate a 40-character lower-case commit SHA."""

    if not _COMMIT40_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a 40-character lowercase hex value")
    return value


def reject_protected_material(value: Any, field_name: str = "payload") -> None:
    """Reject protected material recursively without echoing the rejected value."""

    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key).lower()
            if any(part in key_text for part in _SECRET_KEY_PARTS):
                raise ValueError(f"{field_name} contains protected material")
            reject_protected_material(item, field_name)
    elif isinstance(value, (list, tuple, set, frozenset)):
        for item in value:
            reject_protected_material(item, field_name)
    elif isinstance(value, str):
        lowered = value.lower()
        if any(marker in lowered for marker in _PROTECTED_VALUE_MARKERS):
            raise ValueError(f"{field_name} contains protected material")


def validate_reason_codes(values: tuple[str, ...]) -> tuple[str, ...]:
    """Validate immutable ordered reason codes."""

    seen: set[str] = set()
    for code in values:
        if code not in RESEARCH_REASON_CODES:
            raise ValueError("unknown research reason code")
        if code in seen:
            raise ValueError("duplicate research reason code")
        if re.search(r"[/:\\\\]", code):
            raise ValueError("reason code must not embed URL, host, or path content")
        seen.add(code)
    return values


def _simple_canonical_url(url: str) -> str:
    if len(url) > 4096:
        raise ValueError("URL exceeds maximum length")
    if _MALFORMED_PERCENT_RE.search(url):
        raise ValueError("URL contains malformed percent encoding")
    split = urlsplit(url)
    if split.scheme.lower() not in {"http", "https"}:
        raise ValueError("URL scheme is not allowed")
    if split.username or split.password:
        raise ValueError("URL userinfo is rejected")
    if not split.hostname:
        raise ValueError("URL hostname is required")
    hostname = split.hostname.rstrip(".").encode("idna").decode("ascii").lower()
    port = split.port
    netloc = hostname
    if port is not None:
        netloc = f"{hostname}:{port}"
    path = split.path or "/"
    return urlunsplit((split.scheme.lower(), netloc, path, split.query, ""))


def research_query_fingerprint(payload: dict[str, Any]) -> str:
    return fingerprint_payload({"kind": RESEARCH_QUERY_SCHEMA_VERSION, **payload})


def source_candidate_fingerprint(payload: dict[str, Any]) -> str:
    return fingerprint_payload({"kind": SOURCE_CANDIDATE_SCHEMA_VERSION, **payload})


def research_plan_fingerprint(payload: dict[str, Any]) -> str:
    return fingerprint_payload({"kind": RESEARCH_PLAN_SCHEMA_VERSION, **payload})


class ResearchQuery(BaseModel):
    """Operator-supplied research question metadata."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-research-query/v1"] = RESEARCH_QUERY_SCHEMA_VERSION
    query_id: str = Field(min_length=1, max_length=128)
    research_question: str = Field(min_length=8, max_length=500)
    research_purpose: str = Field(min_length=1, max_length=300)
    language: str = Field(default="en", min_length=2, max_length=16)
    requested_source_classes: tuple[ResearchSourceClass, ...] = Field(min_length=1, max_length=10)
    requested_content_types: tuple[ResearchContentType, ...] = Field(min_length=1, max_length=6)
    domain_hints: tuple[str, ...] = Field(default_factory=tuple, max_length=20)
    created_at: datetime
    query_fingerprint: str
    operator_supplied: Literal[True] = True
    redacted: Literal[True] = True
    read_only: Literal[True] = True

    @field_validator("query_id")
    @classmethod
    def query_id_is_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "query_id")

    @field_validator("research_question", "research_purpose")
    @classmethod
    def text_is_safe(cls, value: str) -> str:
        reject_protected_material(value, "research text")
        if _URL_RE.search(value):
            raise ValueError("research question text must not contain URLs")
        if _SHELL_RE.search(value):
            raise ValueError("research question text must not contain executable commands")
        return value

    @field_validator("domain_hints")
    @classmethod
    def domain_hints_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if len(set(value)) != len(value):
            raise ValueError("duplicate domain hints are rejected")
        for domain in value:
            reject_protected_material(domain, "domain_hints")
            if domain in {"*", "*.*"}:
                raise ValueError("wildcard domain hints are rejected")
        return value

    @field_validator("requested_source_classes", "requested_content_types")
    @classmethod
    def tuple_values_are_unique(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if len(set(value)) != len(value):
            raise ValueError("duplicate values are rejected")
        if "disallowed" in value:
            raise ValueError("disallowed source class is rejected")
        return value

    @field_validator("created_at")
    @classmethod
    def created_at_is_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value, "created_at")

    @field_validator("query_fingerprint")
    @classmethod
    def fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "query_fingerprint")


class SourceCandidate(BaseModel):
    """One explicit source candidate for controlled acquisition."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-source-candidate/v1"] = (
        SOURCE_CANDIDATE_SCHEMA_VERSION
    )
    candidate_id: str = Field(min_length=1, max_length=128)
    query_ids: tuple[str, ...] = Field(min_length=1, max_length=20)
    original_url: str = Field(min_length=12, max_length=4096)
    source_class: ResearchSourceClass
    expected_content_types: tuple[ResearchContentType, ...] = Field(min_length=1, max_length=6)
    robots_policy_status: RobotsPolicyStatus
    licence_policy_status: LicencePolicyStatus
    operator_supplied: bool = True
    search_adapter_type: ResearchSearchAdapterType = "disabled"
    created_at: datetime
    candidate_fingerprint: str
    redacted: Literal[True] = True
    read_only: Literal[True] = True

    @field_validator("candidate_id")
    @classmethod
    def candidate_id_is_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "candidate_id")

    @field_validator("query_ids")
    @classmethod
    def query_ids_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if len(set(value)) != len(value):
            raise ValueError("duplicate query IDs are rejected")
        for query_id in value:
            validate_safe_identifier(query_id, "query_id")
        return value

    @field_validator("original_url")
    @classmethod
    def original_url_is_safe(cls, value: str) -> str:
        reject_protected_material(value, "original_url")
        return _simple_canonical_url(value)

    @field_validator("source_class")
    @classmethod
    def source_class_is_allowed(cls, value: ResearchSourceClass) -> ResearchSourceClass:
        if value == "disallowed":
            raise ValueError("disallowed source class is rejected")
        return value

    @field_validator("expected_content_types")
    @classmethod
    def content_types_are_unique(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if len(set(value)) != len(value):
            raise ValueError("duplicate content types are rejected")
        return value

    @field_validator("created_at")
    @classmethod
    def source_created_at_is_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value, "created_at")

    @field_validator("candidate_fingerprint")
    @classmethod
    def candidate_fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "candidate_fingerprint")


class ResearchPlan(BaseModel):
    """Bounded operator-invoked acquisition plan."""

    model_config = ALIASED_FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-research-plan/v1"] = RESEARCH_PLAN_SCHEMA_VERSION
    plan_id: str = Field(min_length=1, max_length=128)
    program_id: Literal["AION-KNOWLEDGE-INTELLIGENCE-001"] = PROGRAM_ID
    authorization_transaction_id: Literal["AION-204-KI-0001"] = AUTHORIZATION_TRANSACTION_ID
    approval_record_id: Literal["AION-204-KI-0001"] = APPROVAL_RECORD_ID
    implementation_task: Literal["AION-205"] = IMPLEMENTATION_TASK
    formal_closeout_task: Literal["AION-206"] = FORMAL_CLOSEOUT_TASK
    authz_scope: Literal[
        "disabled-allowlisted-public-research-query-fetch-snapshot-provenance-core"
    ] = Field(
        default=AUTHORIZATION_SCOPE,
        alias="authorization_scope",
        serialization_alias="authorization_scope",
    )
    queries: tuple[ResearchQuery, ...] = Field(min_length=1, max_length=20)
    explicit_domain_allowlist: tuple[str, ...] = Field(min_length=0, max_length=20)
    explicit_source_candidates: tuple[SourceCandidate, ...] = Field(default_factory=tuple)
    allowed_methods: tuple[ResearchMethod, ...] = Field(default=("GET", "HEAD"), min_length=1)
    allowed_content_types: tuple[ResearchContentType, ...] = Field(min_length=1, max_length=6)
    research_adapter_type: ResearchAdapterType = "disabled"
    search_adapter_type: ResearchSearchAdapterType = "disabled"
    resource_budget_fingerprint: str
    operator_invoked: Literal[True] = True
    background_execution: Literal[False] = False
    research_runtime_enabled: Literal[False] = False
    network_access_enabled: Literal[False] = False
    knowledge_promotion_enabled: Literal[False] = False
    cognitive_belief_mutation_enabled: Literal[False] = False
    created_at: datetime
    expires_at: datetime
    plan_fingerprint: str
    redacted: Literal[True] = True
    read_only: Literal[True] = True

    @field_validator("plan_id")
    @classmethod
    def plan_id_is_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "plan_id")

    @field_validator("explicit_domain_allowlist")
    @classmethod
    def domains_are_unique(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if len(set(value)) != len(value):
            raise ValueError("duplicate allowlist domains are rejected")
        for domain in value:
            reject_protected_material(domain, "explicit_domain_allowlist")
            if domain in {"*", "*.*"}:
                raise ValueError("universal wildcard is rejected")
        return value

    @field_validator("explicit_source_candidates")
    @classmethod
    def candidates_are_bounded(
        cls, value: tuple[SourceCandidate, ...]
    ) -> tuple[SourceCandidate, ...]:
        if len(value) > MAXIMUM_SOURCE_CANDIDATES_PER_PLAN:
            raise ValueError("too many source candidates")
        return value

    @field_validator("allowed_methods")
    @classmethod
    def methods_are_read_only(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if set(value) - {"GET", "HEAD"}:
            raise ValueError("only GET and HEAD are allowed")
        if len(set(value)) != len(value):
            raise ValueError("duplicate methods are rejected")
        return value

    @field_validator("allowed_content_types")
    @classmethod
    def allowed_content_types_are_unique(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if len(set(value)) != len(value):
            raise ValueError("duplicate content types are rejected")
        return value

    @field_validator("created_at", "expires_at")
    @classmethod
    def plan_timestamps_are_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value, "plan timestamp")

    @field_validator("resource_budget_fingerprint", "plan_fingerprint")
    @classmethod
    def plan_fingerprints_are_hex(cls, value: str) -> str:
        return validate_hex64(value, "plan fingerprint")

    @model_validator(mode="after")
    def plan_invariants_hold(self) -> Self:
        query_ids = [query.query_id for query in self.queries]
        if len(set(query_ids)) != len(query_ids):
            raise ValueError("duplicate query IDs are rejected")
        candidate_ids = [candidate.candidate_id for candidate in self.explicit_source_candidates]
        if len(set(candidate_ids)) != len(candidate_ids):
            raise ValueError("duplicate candidate IDs are rejected")
        candidate_urls = [
            _simple_canonical_url(candidate.original_url)
            for candidate in self.explicit_source_candidates
        ]
        if len(set(candidate_urls)) != len(candidate_urls):
            raise ValueError("duplicate canonical URLs are rejected")
        if (
            self.research_adapter_type == "operator_invoked_http"
            and not self.explicit_domain_allowlist
        ):
            raise ValueError("HTTP policy adapter requires an explicit domain allowlist")
        if self.expires_at <= self.created_at:
            raise ValueError("expires_at must be after created_at")
        if (self.expires_at - self.created_at).total_seconds() > 86_400:
            raise ValueError("plan expiry must be within 24 hours")
        return self


class ResearchFetchRequest(BaseModel):
    """Internal immutable request passed to fetch adapters."""

    model_config = FROZEN_MODEL_CONFIG

    request_id: str
    candidate_id: str
    method: ResearchMethod
    canonical_url: str
    validated_destination: dict[str, Any]
    safe_request_headers: dict[str, str]
    timeout_seconds: int = Field(ge=1, le=20)
    maximum_response_bytes: int = Field(ge=1, le=MAXIMUM_RESPONSE_BYTES_PER_SOURCE)
    maximum_redirects: int = Field(ge=0, le=MAXIMUM_REDIRECTS_PER_FETCH)
    created_at: datetime
    fingerprint: str

    @field_validator("request_id", "candidate_id")
    @classmethod
    def fetch_ids_are_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "fetch identifier")

    @field_validator("canonical_url")
    @classmethod
    def request_url_is_canonical(cls, value: str) -> str:
        return _simple_canonical_url(value)

    @field_validator("safe_request_headers")
    @classmethod
    def request_headers_are_safe(cls, value: dict[str, str]) -> dict[str, str]:
        allowed = {"User-Agent", "Accept", "Accept-Language", "Accept-Encoding"}
        for key, item in value.items():
            if key not in allowed:
                raise ValueError("unsafe request header is rejected")
            if "\r" in key or "\n" in key or "\r" in item or "\n" in item:
                raise ValueError("header newline injection is rejected")
            reject_protected_material(item, "safe_request_headers")
        if value.get("Accept-Encoding") != "identity":
            raise ValueError("Accept-Encoding must be identity")
        return value

    @field_validator("created_at")
    @classmethod
    def fetch_created_at_is_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value, "created_at")

    @field_validator("fingerprint")
    @classmethod
    def fetch_fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "fetch fingerprint")


class ResearchFetchResponse(BaseModel):
    """Internal immutable response returned by fetch adapters."""

    model_config = FROZEN_MODEL_CONFIG

    request_id: str
    status_code: int = Field(ge=100, le=599)
    response_url: str
    peer_address: str
    safe_response_headers: dict[str, str] = Field(max_length=MAXIMUM_SAFE_HEADERS_PER_SNAPSHOT)
    content_type: ResearchContentType
    character_encoding: str | None = Field(default=None, max_length=32)
    body: bytes = Field(repr=False)
    body_length: int = Field(ge=0, le=MAXIMUM_RESPONSE_BYTES_PER_SOURCE)
    retrieved_at: datetime
    fingerprint: str

    @field_validator("request_id")
    @classmethod
    def response_request_id_is_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "request_id")

    @field_validator("response_url")
    @classmethod
    def response_url_is_canonical(cls, value: str) -> str:
        return _simple_canonical_url(value)

    @field_validator("safe_response_headers")
    @classmethod
    def response_headers_are_safe(cls, value: dict[str, str]) -> dict[str, str]:
        for key, item in value.items():
            lowered = key.lower()
            if lowered in {"set-cookie", "www-authenticate", "proxy-authenticate", "authorization"}:
                raise ValueError("unsafe response header is rejected")
            if "\r" in key or "\n" in key or "\r" in item or "\n" in item:
                raise ValueError("header newline injection is rejected")
            reject_protected_material(item, "safe_response_headers")
        return value

    @field_validator("retrieved_at")
    @classmethod
    def retrieved_at_is_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value, "retrieved_at")

    @field_validator("fingerprint")
    @classmethod
    def response_fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "response fingerprint")

    @model_validator(mode="after")
    def body_length_matches(self) -> Self:
        if len(self.body) != self.body_length:
            raise ValueError("body length must match measured bytes")
        return self


class CitationReference(BaseModel):
    """A bounded reference to source evidence that does not verify a claim."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-citation-reference/v1"] = (
        CITATION_REFERENCE_SCHEMA_VERSION
    )
    citation_id: str
    snapshot_id: str
    content_sha256: str
    canonical_url_fingerprint: str
    locator_kind: CitationLocatorKind
    locator_value: str = Field(min_length=1, max_length=256)
    retrieval_timestamp: datetime
    citation_fingerprint: str
    read_only: Literal[True] = True
    redacted: Literal[True] = True
    claim_verified: Literal[False] = False

    @field_validator("citation_id", "snapshot_id")
    @classmethod
    def citation_ids_are_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "citation identifier")

    @field_validator("content_sha256", "canonical_url_fingerprint", "citation_fingerprint")
    @classmethod
    def citation_hashes_are_hex(cls, value: str) -> str:
        return validate_hex64(value, "citation fingerprint")

    @field_validator("locator_value")
    @classmethod
    def locator_is_safe(cls, value: str) -> str:
        reject_protected_material(value, "locator_value")
        return value

    @field_validator("retrieval_timestamp")
    @classmethod
    def retrieval_timestamp_is_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value, "retrieval_timestamp")

    @model_validator(mode="after")
    def locator_shape_is_valid(self) -> Self:
        if self.locator_kind == "page_number" and int(self.locator_value) < 1:
            raise ValueError("page number must be positive")
        if self.locator_kind == "json_pointer" and not self.locator_value.startswith("/"):
            raise ValueError("JSON Pointer must start with /")
        if self.locator_kind == "xml_path" and len(self.locator_value.split("/")) > 16:
            raise ValueError("XML path is too deep")
        if self.locator_kind == "byte_range":
            parts = self.locator_value.split(":")
            if len(parts) != 2 or int(parts[0]) < 0 or int(parts[1]) < int(parts[0]):
                raise ValueError("byte range is invalid")
        return self


__all__ = [
    "APPROVAL_RECORD_ID",
    "AUTHORIZATION_SCOPE",
    "AUTHORIZATION_TRANSACTION_ID",
    "CANDIDATE_ID",
    "CITATION_REFERENCE_SCHEMA_VERSION",
    "CitationLocatorKind",
    "CitationReference",
    "FORMAL_CLOSEOUT_TASK",
    "FROZEN_MODEL_CONFIG",
    "IMPLEMENTATION_TASK",
    "KNOWLEDGE_RESEARCH_CONTRACT_SCHEMA_VERSION",
    "MAXIMUM_CITATION_REFERENCES_PER_SNAPSHOT",
    "MAXIMUM_CONCURRENCY",
    "MAXIMUM_DOMAINS_PER_PLAN",
    "MAXIMUM_FETCHES_PER_PLAN",
    "MAXIMUM_OPERATOR_REVIEW_ITEMS_PER_PLAN",
    "MAXIMUM_QUERIES_PER_PLAN",
    "MAXIMUM_REDIRECTS_PER_FETCH",
    "MAXIMUM_RESPONSE_BYTES_PER_SOURCE",
    "MAXIMUM_SAFE_HEADERS_PER_SNAPSHOT",
    "MAXIMUM_SNAPSHOT_RECORDS_PER_PLAN",
    "MAXIMUM_SOURCE_CANDIDATES_PER_PLAN",
    "MAXIMUM_TIMEOUT_SECONDS_PER_REQUEST",
    "MAXIMUM_TOTAL_TRANSFER_BYTES_PER_PLAN",
    "MAXIMUM_WALL_CLOCK_SECONDS_PER_PLAN",
    "MODEL_CONFIG",
    "PROGRAM_ID",
    "RESEARCH_BUDGET_SCHEMA_VERSION",
    "RESEARCH_DIAGNOSTICS_SCHEMA_VERSION",
    "RESEARCH_EVIDENCE_SCHEMA_VERSION",
    "RESEARCH_INCIDENT_SCHEMA_VERSION",
    "RESEARCH_PLAN_SCHEMA_VERSION",
    "RESEARCH_QUERY_SCHEMA_VERSION",
    "RESEARCH_REASON_CODE_REGISTRY_VERSION",
    "RESEARCH_REASON_CODES",
    "SOURCE_CANDIDATE_SCHEMA_VERSION",
    "SOURCE_LINEAGE_SCHEMA_VERSION",
    "SOURCE_PROVENANCE_SCHEMA_VERSION",
    "SOURCE_SNAPSHOT_SCHEMA_VERSION",
    "WORKSTREAM",
    "LicencePolicyStatus",
    "ResearchAdapterType",
    "ResearchContentType",
    "ResearchFetchRequest",
    "ResearchFetchResponse",
    "ResearchMethod",
    "ResearchPlan",
    "ResearchPlanOutcome",
    "ResearchPlanState",
    "ResearchQuery",
    "ResearchSearchAdapterType",
    "ResearchSourceClass",
    "RobotsPolicyStatus",
    "SourceCandidate",
    "SourceLineageKind",
    "ensure_utc",
    "fingerprint_payload",
    "reject_protected_material",
    "research_plan_fingerprint",
    "research_query_fingerprint",
    "sha256_bytes",
    "source_candidate_fingerprint",
    "stable_json",
    "utc_now",
    "validate_commit_sha",
    "validate_hex64",
    "validate_reason_codes",
    "validate_safe_identifier",
]
