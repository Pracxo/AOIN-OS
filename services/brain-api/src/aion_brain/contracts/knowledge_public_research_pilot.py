"""AION-219 controlled public research pilot contracts."""

from __future__ import annotations

import ipaddress
import re
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any, Literal, Self
from urllib.parse import parse_qsl, urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.knowledge_research import (
    ensure_utc,
    fingerprint_payload,
    reject_protected_material,
    sha256_bytes,
    stable_json,
    validate_hex64,
)

PUBLIC_RESEARCH_PILOT_CONTRACT_SCHEMA_VERSION: Literal[
    "aion-public-research-pilot/v1"
] = "aion-public-research-pilot/v1"
PUBLIC_RESEARCH_PILOT_AUTHORIZATION_SCHEMA_VERSION: Literal[
    "aion-public-research-pilot-authorization/v1"
] = (
    "aion-public-research-pilot-authorization/v1"
)
PUBLIC_RESEARCH_PILOT_PLAN_SCHEMA_VERSION: Literal[
    "aion-public-research-pilot-plan/v1"
] = "aion-public-research-pilot-plan/v1"
PUBLIC_RESEARCH_SOURCE_CANDIDATE_SCHEMA_VERSION: Literal[
    "aion-public-research-pilot-source-candidate/v1"
] = (
    "aion-public-research-pilot-source-candidate/v1"
)
PUBLIC_RESEARCH_CLAIM_SPECIFICATION_SCHEMA_VERSION: Literal[
    "aion-public-research-pilot-claim-specification/v1"
] = (
    "aion-public-research-pilot-claim-specification/v1"
)
PUBLIC_RESEARCH_DNS_RESOLUTION_SCHEMA_VERSION: Literal[
    "aion-public-research-dns-resolution/v1"
] = "aion-public-research-dns-resolution/v1"
PUBLIC_RESEARCH_REDIRECT_HOP_SCHEMA_VERSION: Literal[
    "aion-public-research-redirect-hop/v1"
] = "aion-public-research-redirect-hop/v1"
PUBLIC_RESEARCH_HTTP_EXCHANGE_SCHEMA_VERSION: Literal[
    "aion-public-research-http-exchange/v1"
] = "aion-public-research-http-exchange/v1"
PUBLIC_RESEARCH_PIPELINE_TRACE_SCHEMA_VERSION: Literal[
    "aion-public-research-pipeline-trace/v1"
] = "aion-public-research-pipeline-trace/v1"
PUBLIC_RESEARCH_PILOT_SESSION_SCHEMA_VERSION: Literal[
    "aion-public-research-pilot-session/v1"
] = "aion-public-research-pilot-session/v1"
PUBLIC_RESEARCH_PILOT_RESULT_SCHEMA_VERSION: Literal[
    "aion-public-research-pilot-result/v1"
] = "aion-public-research-pilot-result/v1"
PUBLIC_RESEARCH_PILOT_BUDGET_SCHEMA_VERSION: Literal[
    "aion-public-research-pilot-budget/v1"
] = "aion-public-research-pilot-budget/v1"
PUBLIC_RESEARCH_PILOT_INTEGRITY_SCHEMA_VERSION: Literal[
    "aion-public-research-pilot-integrity/v1"
] = "aion-public-research-pilot-integrity/v1"
PUBLIC_RESEARCH_PILOT_EVIDENCE_SCHEMA_VERSION: Literal[
    "aion-public-research-pilot-evidence/v1"
] = "aion-public-research-pilot-evidence/v1"
PUBLIC_RESEARCH_PILOT_REASON_CODE_REGISTRY_VERSION: Literal[
    "aion-public-research-pilot-reasons/v1"
] = (
    "aion-public-research-pilot-reasons/v1"
)

PROGRAM_ID: Literal["AION-KNOWLEDGE-INTELLIGENCE-001"] = (
    "AION-KNOWLEDGE-INTELLIGENCE-001"
)
AUTHORIZATION_TRANSACTION_ID: Literal["AION-218-KI-0008"] = "AION-218-KI-0008"
APPROVAL_RECORD_ID: Literal["AION-218-KI-0008"] = "AION-218-KI-0008"
IMPLEMENTATION_TASK: Literal["AION-219"] = "AION-219"
FORMAL_CLOSEOUT_TASK: Literal["AION-220"] = "AION-220"
AUTHORIZATION_SCOPE: Literal[
    "operator-invoked-allowlisted-public-https-fetch-dns-pinning-integrated-research-verified-candidate-pilot-operator-review-abstention-core"
] = (
    "operator-invoked-allowlisted-public-https-fetch-dns-pinning-integrated-research-"
    "verified-candidate-pilot-operator-review-abstention-core"
)

PUBLIC_RESEARCH_USER_AGENT = "AION-PublicResearchPilot/1.0"
LIVE_CONFIRMATION_TEXT = "CONTROLLED_PUBLIC_RESEARCH_PILOT"

PUBLIC_RESEARCH_RESOURCE_LIMITS: dict[str, int] = {
    "maximum_pilot_sessions": 5,
    "maximum_plans_per_session": 5,
    "maximum_queries_per_plan": 20,
    "maximum_domains_per_plan": 20,
    "maximum_explicit_source_candidates_per_plan": 50,
    "maximum_source_fetches_per_plan": 25,
    "maximum_robots_fetches_per_plan": 20,
    "maximum_public_https_requests_per_plan": 50,
    "maximum_dns_resolutions_per_plan": 100,
    "maximum_redirects_per_fetch": 3,
    "maximum_concurrency": 4,
    "maximum_timeout_seconds_per_request": 20,
    "maximum_wall_clock_seconds_per_plan": 900,
    "maximum_response_bytes_per_source": 5_242_880,
    "maximum_total_transfer_bytes_per_plan": 52_428_800,
    "maximum_snapshots_per_plan": 100,
    "maximum_safe_headers_per_snapshot": 32,
    "maximum_citation_references_per_snapshot": 20,
    "maximum_query_parameters_per_url": 10,
    "maximum_url_length": 4096,
    "maximum_explicit_claim_specs_per_session": 50,
    "maximum_candidate_evaluations_per_session": 100,
    "maximum_candidate_versions_per_identity": 100,
    "maximum_operator_review_items_per_session": 100,
    "maximum_pilot_report_bytes": 10_485_760,
    "maximum_source_body_retention_seconds": 300,
    "maximum_operator_pilot_report_writes": 1,
    "maximum_search_provider_calls": 0,
    "maximum_connector_calls": 0,
    "maximum_model_provider_calls": 0,
    "maximum_actual_tool_executions": 0,
    "maximum_shell_commands": 0,
    "maximum_subprocess_executions": 0,
    "maximum_browser_actions": 0,
    "maximum_runtime_filesystem_mutations": 0,
    "maximum_persistent_source_body_writes": 0,
    "maximum_persistent_source_registry_writes": 0,
    "maximum_persistent_claim_graph_writes": 0,
    "maximum_persistent_assessment_writes": 0,
    "maximum_persistent_expert_mesh_writes": 0,
    "maximum_persistent_tool_state_writes": 0,
    "maximum_persistent_verified_knowledge_writes": 0,
    "maximum_automatic_knowledge_promotions": 0,
    "maximum_cognitive_memory_writes": 0,
    "maximum_belief_mutations": 0,
    "maximum_engagement_fact_promotions": 0,
    "maximum_engagement_confidence_effects": 0,
    "maximum_source_mutations": 0,
    "maximum_git_operations": 0,
    "maximum_runtime_created_pull_requests": 0,
    "maximum_approvals_created": 0,
    "maximum_deployments": 0,
    "maximum_model_weight_changes": 0,
}
PUBLIC_RESEARCH_PILOT_RESOURCE_LIMITS = PUBLIC_RESEARCH_RESOURCE_LIMITS

MODEL_CONFIG = ConfigDict(extra="forbid", hide_input_in_errors=True)
FROZEN_MODEL_CONFIG = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)

_SAFE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._:-]{0,127}$")
_DOMAIN_RE = re.compile(
    r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?"
    r"(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+$"
)
_MALFORMED_PERCENT_RE = re.compile(r"%(?![0-9A-Fa-f]{2})")
_AMBIGUOUS_IPV4_RE = re.compile(
    r"^(0x[0-9a-fA-F]+|0[0-7]+|\d+)([.](0x[0-9a-fA-F]+|0[0-7]+|\d+))*$"
)
_CRLF_RE = re.compile(r"[\r\n]")
_PROHIBITED_TEXT_MARKERS = (
    "cookie:",
    "authorization:",
    "proxy-authorization:",
    "bearer ",
    "sk-",
    "ghp_",
    "gho_",
    "-----begin private key-----",
)
APPROVED_SOURCE_CLASSES: tuple[str, ...] = (
    "primary_authoritative",
    "official_standard",
    "official_government",
    "peer_reviewed",
    "vendor_primary",
    "institutional_primary",
    "reputable_secondary",
)
APPROVED_LICENCE_STATUSES: tuple[str, ...] = ("permitted", "not_applicable")
APPROVED_METHODS: tuple[str, ...] = ("GET", "HEAD")
APPROVED_CONTENT_TYPES: tuple[str, ...] = (
    "text/html",
    "text/plain",
    "application/json",
    "application/xml",
    "text/xml",
)
APPROVED_ENCODINGS: tuple[str, ...] = (
    "utf-8",
    "utf-8-sig",
    "us-ascii",
    "iso-8859-1",
    "windows-1252",
)


class PublicResearchPilotMode(StrEnum):
    """Execution mode for one pilot session."""

    DETERMINISTIC_SIMULATION = "deterministic_simulation"
    OPERATOR_INVOKED_LIVE = "operator_invoked_live"


class PublicResearchPilotStatus(StrEnum):
    """Lifecycle state for a public research pilot."""

    DRAFTED = "drafted"
    VALIDATED = "validated"
    RUNNING = "running"
    COMPLETED = "completed"
    COMPLETED_WITH_REJECTIONS = "completed_with_rejections"
    ABSTAINED = "abstained"
    BLOCKED = "blocked"
    KILLED = "killed"
    FAILED = "failed"


class PublicResearchKillSwitchState(StrEnum):
    """Per-session kill-switch state."""

    ARMED = "armed"
    AVAILABLE_NOT_TRIGGERED = "available_not_triggered"
    TRIGGERED = "triggered"


class PublicResearchDnsStatus(StrEnum):
    """DNS validation outcome."""

    RESOLVED_AND_PINNED = "resolved_and_pinned"
    REJECTED_PRIVATE = "rejected_private"
    REJECTED_LOOPBACK = "rejected_loopback"
    REJECTED_LINK_LOCAL = "rejected_link_local"
    REJECTED_MULTICAST = "rejected_multicast"
    REJECTED_RESERVED = "rejected_reserved"
    REJECTED_METADATA = "rejected_metadata"
    REJECTED_UNSPECIFIED = "rejected_unspecified"
    REJECTED_DOCUMENTATION = "rejected_documentation"
    REJECTED_AMBIGUOUS = "rejected_ambiguous"
    REJECTED_TOO_MANY_ADDRESSES = "rejected_too_many_addresses"
    RESOLUTION_FAILED = "resolution_failed"
    BUDGET_BLOCKED = "budget_blocked"
    KILLED = "killed"


class PublicResearchHttpOutcome(StrEnum):
    """HTTP exchange outcome."""

    COMPLETED = "completed"
    REDIRECTED = "redirected"
    REJECTED_SCHEME = "rejected_scheme"
    REJECTED_METHOD = "rejected_method"
    REJECTED_DOMAIN = "rejected_domain"
    REJECTED_DESTINATION = "rejected_destination"
    REJECTED_PEER = "rejected_peer"
    REJECTED_TLS = "rejected_tls"
    REJECTED_HEADERS = "rejected_headers"
    REJECTED_CONTENT_LENGTH = "rejected_content_length"
    REJECTED_CONTENT_ENCODING = "rejected_content_encoding"
    REJECTED_CONTENT_TYPE = "rejected_content_type"
    REJECTED_CHARACTER_ENCODING = "rejected_character_encoding"
    REJECTED_RESPONSE_SIZE = "rejected_response_size"
    REJECTED_REDIRECT = "rejected_redirect"
    TIMEOUT = "timeout"
    KILLED = "killed"
    FAILED = "failed"


class PublicResearchCandidateOutcome(StrEnum):
    """Candidate evidence disposition."""

    ELIGIBLE_FOR_OPERATOR_REVIEW = "eligible_for_operator_review"
    INELIGIBLE_FOR_OPERATOR_REVIEW = "ineligible_for_operator_review"
    ABSTAINED = "abstained"
    PIPELINE_BLOCKED = "pipeline_blocked"


def utc_now() -> datetime:
    """Return an aware UTC timestamp."""

    return datetime.now(UTC)


def public_research_fingerprint(payload: Any) -> str:
    """Return a deterministic public-research fingerprint."""

    return fingerprint_payload(payload)


def validate_safe_identifier(value: str, field_name: str = "identifier") -> str:
    """Validate a bounded lowercase identifier without echoing sensitive input."""

    if not _SAFE_ID_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a safe lowercase identifier")
    reject_protected_material(value, field_name)
    return value


def validate_domain_name(value: str, field_name: str = "domain") -> str:
    """Normalize and validate an exact public DNS name."""

    reject_protected_material(value, field_name)
    if value in {"*", "*.*"} or value.startswith("*."):
        raise ValueError(f"{field_name} must be an exact domain")
    try:
        normalized = value.rstrip(".").encode("idna").decode("ascii").lower()
    except UnicodeError as exc:
        raise ValueError(f"{field_name} must be IDNA-normalizable") from exc
    if not _DOMAIN_RE.fullmatch(normalized):
        raise ValueError(f"{field_name} must be a fully-qualified DNS name")
    try:
        ipaddress.ip_address(normalized)
    except ValueError:
        return normalized
    raise ValueError(f"{field_name} must not be an IP literal")


def validate_public_research_url(value: str) -> str:
    """Validate an explicit HTTPS URL without credentials or path traversal."""

    reject_protected_material(value, "public research URL")
    if len(value) > PUBLIC_RESEARCH_RESOURCE_LIMITS["maximum_url_length"]:
        raise ValueError("URL exceeds maximum length")
    if _CRLF_RE.search(value) or "\\" in value:
        raise ValueError("URL contains prohibited characters")
    if _MALFORMED_PERCENT_RE.search(value):
        raise ValueError("URL contains malformed percent encoding")
    split = urlsplit(value)
    if split.scheme.lower() != "https":
        raise ValueError("public research URL must use HTTPS")
    if split.username or split.password:
        raise ValueError("URL userinfo is rejected")
    if not split.hostname:
        raise ValueError("URL hostname is required")
    hostname = validate_domain_name(split.hostname, "URL hostname")
    if _AMBIGUOUS_IPV4_RE.fullmatch(hostname):
        raise ValueError("ambiguous IP encoding is rejected")
    if split.path and any(part == ".." for part in split.path.split("/")):
        raise ValueError("path traversal is rejected")
    if len(parse_qsl(split.query, keep_blank_values=True)) > PUBLIC_RESEARCH_RESOURCE_LIMITS[
        "maximum_query_parameters_per_url"
    ]:
        raise ValueError("too many query parameters")
    return value


def reject_prohibited_text(value: str, field_name: str) -> str:
    """Reject obvious credential, token, prompt, and command markers."""

    reject_protected_material(value, field_name)
    lowered = value.lower()
    if any(marker in lowered for marker in _PROHIBITED_TEXT_MARKERS):
        raise ValueError(f"{field_name} contains protected material")
    if _CRLF_RE.search(value):
        raise ValueError(f"{field_name} must not contain CRLF")
    return value


def _tuple_unique(values: tuple[str, ...], field_name: str) -> tuple[str, ...]:
    if len(set(values)) != len(values):
        raise ValueError(f"{field_name} must not contain duplicates")
    return tuple(values)


def _sorted_tuple_unique(values: tuple[str, ...], field_name: str) -> tuple[str, ...]:
    return tuple(sorted(_tuple_unique(values, field_name)))


class PublicResearchPilotResourceBudget(BaseModel):
    """Authorized hard resource limits for AION-219."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-public-research-pilot-budget/v1"] = (
        PUBLIC_RESEARCH_PILOT_BUDGET_SCHEMA_VERSION
    )
    maximum_pilot_sessions: int = 5
    maximum_plans_per_session: int = 5
    maximum_queries_per_plan: int = 20
    maximum_domains_per_plan: int = 20
    maximum_explicit_source_candidates_per_plan: int = 50
    maximum_source_fetches_per_plan: int = 25
    maximum_robots_fetches_per_plan: int = 20
    maximum_public_https_requests_per_plan: int = 50
    maximum_dns_resolutions_per_plan: int = 100
    maximum_redirects_per_fetch: int = 3
    maximum_concurrency: int = 4
    maximum_timeout_seconds_per_request: int = 20
    maximum_wall_clock_seconds_per_plan: int = 900
    maximum_response_bytes_per_source: int = 5_242_880
    maximum_total_transfer_bytes_per_plan: int = 52_428_800
    maximum_snapshots_per_plan: int = 100
    maximum_safe_headers_per_snapshot: int = 32
    maximum_citation_references_per_snapshot: int = 20
    maximum_query_parameters_per_url: int = 10
    maximum_url_length: int = 4096
    maximum_explicit_claim_specs_per_session: int = 50
    maximum_candidate_evaluations_per_session: int = 100
    maximum_candidate_versions_per_identity: int = 100
    maximum_operator_review_items_per_session: int = 100
    maximum_pilot_report_bytes: int = 10_485_760
    maximum_source_body_retention_seconds: int = 300
    maximum_operator_pilot_report_writes: int = 1
    maximum_search_provider_calls: int = 0
    maximum_connector_calls: int = 0
    maximum_model_provider_calls: int = 0
    maximum_actual_tool_executions: int = 0
    maximum_shell_commands: int = 0
    maximum_subprocess_executions: int = 0
    maximum_browser_actions: int = 0
    maximum_runtime_filesystem_mutations: int = 0
    maximum_persistent_source_body_writes: int = 0
    maximum_persistent_source_registry_writes: int = 0
    maximum_persistent_claim_graph_writes: int = 0
    maximum_persistent_assessment_writes: int = 0
    maximum_persistent_expert_mesh_writes: int = 0
    maximum_persistent_tool_state_writes: int = 0
    maximum_persistent_verified_knowledge_writes: int = 0
    maximum_automatic_knowledge_promotions: int = 0
    maximum_cognitive_memory_writes: int = 0
    maximum_belief_mutations: int = 0
    maximum_engagement_fact_promotions: int = 0
    maximum_engagement_confidence_effects: int = 0
    maximum_source_mutations: int = 0
    maximum_git_operations: int = 0
    maximum_runtime_created_pull_requests: int = 0
    maximum_approvals_created: int = 0
    maximum_deployments: int = 0
    maximum_model_weight_changes: int = 0

    @model_validator(mode="after")
    def exact_authorized_limits(self) -> Self:
        actual = self.model_dump(mode="json", exclude={"schema_version"})
        if actual != PUBLIC_RESEARCH_RESOURCE_LIMITS:
            raise ValueError("AION-218-KI-0008 resource limits changed")
        return self


class PublicResearchPilotResourceUsage(BaseModel):
    """Per-session and per-plan bounded usage counters."""

    model_config = FROZEN_MODEL_CONFIG

    pilot_sessions: int = 1
    plans: int = 1
    source_candidates: int = 0
    source_fetches: int = 0
    robots_fetches: int = 0
    public_https_requests: int = 0
    dns_resolutions: int = 0
    redirects: int = 0
    maximum_response_bytes_for_any_source: int = 0
    total_transfer_bytes: int = 0
    snapshots: int = 0
    safe_headers_for_any_snapshot: int = 0
    citation_references_for_any_snapshot: int = 0
    claim_specifications: int = 0
    candidate_evaluations: int = 0
    candidate_versions_for_any_identity: int = 0
    operator_review_items: int = 0
    report_bytes: int = 0
    report_writes: int = 0
    elapsed_wall_clock_seconds: int = 0
    search_provider_calls: int = 0
    connector_calls: int = 0
    model_provider_calls: int = 0
    actual_tool_executions: int = 0
    shell_commands: int = 0
    subprocess_executions: int = 0
    browser_actions: int = 0
    runtime_filesystem_mutations: int = 0
    persistent_source_body_writes: int = 0
    persistent_source_registry_writes: int = 0
    persistent_claim_graph_writes: int = 0
    persistent_assessment_writes: int = 0
    persistent_expert_mesh_writes: int = 0
    persistent_tool_state_writes: int = 0
    persistent_verified_knowledge_writes: int = 0
    automatic_knowledge_promotions: int = 0
    cognitive_memory_writes: int = 0
    belief_mutations: int = 0

    @field_validator("*")
    @classmethod
    def counts_are_non_negative(cls, value: int) -> int:
        if value < 0:
            raise ValueError("usage counters must be non-negative")
        return value


class PublicResearchPilotBudgetDecision(BaseModel):
    """Fail-closed budget evaluation."""

    model_config = FROZEN_MODEL_CONFIG

    within_budget: bool
    reason_codes: tuple[str, ...]
    usage: PublicResearchPilotResourceUsage
    budget: PublicResearchPilotResourceBudget
    fingerprint: str

    @field_validator("reason_codes")
    @classmethod
    def reasons_are_safe(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return _sorted_tuple_unique(values, "budget reason_codes")

    @field_validator("fingerprint")
    @classmethod
    def fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "budget fingerprint")


class PublicResearchPilotAuthorizationEnvelope(BaseModel):
    """Per-session explicit operator authorization envelope."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-public-research-pilot-authorization/v1"] = (
        PUBLIC_RESEARCH_PILOT_AUTHORIZATION_SCHEMA_VERSION
    )
    authorization_transaction_id: Literal["AION-218-KI-0008"]
    approval_record_id: Literal["AION-218-KI-0008"]
    pilot_session_id: str
    plan_ids: tuple[str, ...] = Field(min_length=1, max_length=5)
    operator_invoked: Literal[True] = True
    operator_identity_fingerprint: str
    live_network_access_approved: bool
    confirmation_fingerprint: str
    created_at: datetime
    expires_at: datetime
    maximum_pilot_sessions: Literal[5] = 5
    authorization_scope: Literal[
        "operator-invoked-allowlisted-public-https-fetch-dns-pinning-integrated-research-verified-candidate-pilot-operator-review-abstention-core"
    ] = AUTHORIZATION_SCOPE
    background_execution: Literal[False] = False
    scheduled_execution: Literal[False] = False
    crawler_enabled: Literal[False] = False
    search_provider_enabled: Literal[False] = False
    connector_enabled: Literal[False] = False
    model_provider_enabled: Literal[False] = False
    browser_enabled: Literal[False] = False
    automatic_promotion: Literal[False] = False
    persistent_write_authorized: Literal[False] = False
    cognitive_memory_write_authorized: Literal[False] = False
    belief_mutation_authorized: Literal[False] = False
    approval_created: Literal[False] = False
    authorization_envelope_fingerprint: str

    @field_validator("pilot_session_id")
    @classmethod
    def session_id_is_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "pilot_session_id")

    @field_validator("plan_ids")
    @classmethod
    def plan_ids_are_safe(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return _sorted_tuple_unique(
            tuple(validate_safe_identifier(value, "plan_id") for value in values),
            "plan_ids",
        )

    @field_validator(
        "operator_identity_fingerprint",
        "confirmation_fingerprint",
        "authorization_envelope_fingerprint",
    )
    @classmethod
    def hashes_are_hex(cls, value: str) -> str:
        return validate_hex64(value, "authorization envelope fingerprint")

    @field_validator("created_at", "expires_at")
    @classmethod
    def timestamps_are_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value, "authorization envelope timestamp")

    @model_validator(mode="after")
    def envelope_is_exact_and_non_reusable(self) -> Self:
        if self.expires_at <= self.created_at:
            raise ValueError("authorization envelope expires before creation")
        if self.expires_at - self.created_at > timedelta(hours=1):
            raise ValueError("authorization envelope must expire within one hour")
        expected_confirmation = public_research_fingerprint(
            {
                "confirmation": LIVE_CONFIRMATION_TEXT,
                "pilot_session_id": self.pilot_session_id,
                "authorization_transaction_id": AUTHORIZATION_TRANSACTION_ID,
            }
        )
        if self.confirmation_fingerprint != expected_confirmation:
            raise ValueError("operator confirmation fingerprint mismatch")
        expected = _model_fingerprint(self, "authorization_envelope_fingerprint")
        if self.authorization_envelope_fingerprint != expected:
            raise ValueError("authorization envelope fingerprint mismatch")
        return self


class PublicResearchPilotSourceCandidate(BaseModel):
    """One explicit HTTPS source candidate supplied by the operator."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-public-research-pilot-source-candidate/v1"] = (
        PUBLIC_RESEARCH_SOURCE_CANDIDATE_SCHEMA_VERSION
    )
    source_candidate_id: str
    query_ids: tuple[str, ...] = Field(min_length=1, max_length=20)
    original_url: str = Field(min_length=12, max_length=4096)
    canonical_url_fingerprint: str
    explicit_operator_supplied: Literal[True] = True
    domain: str
    source_class: Literal[
        "primary_authoritative",
        "official_standard",
        "official_government",
        "peer_reviewed",
        "vendor_primary",
        "institutional_primary",
        "reputable_secondary",
    ]
    source_control_group_id: str
    robots_policy_expectation: str = Field(min_length=1, max_length=80)
    licence_policy_status: Literal["permitted", "not_applicable"]
    expected_content_types: tuple[str, ...] = Field(min_length=1, max_length=6)
    method: Literal["GET", "HEAD"] = "GET"
    domain_allowlisted: bool
    credential_free: Literal[True] = True
    cookie_free: Literal[True] = True
    authorization_header_free: Literal[True] = True
    client_certificate_free: Literal[True] = True
    ip_literal_url: Literal[False] = False
    scheme: Literal["https"] = "https"
    read_only: Literal[True] = True
    redacted: Literal[True] = True
    candidate_fingerprint: str

    @field_validator("source_candidate_id", "source_control_group_id")
    @classmethod
    def candidate_ids_are_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "source candidate identifier")

    @field_validator("query_ids")
    @classmethod
    def query_ids_are_safe(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return _sorted_tuple_unique(
            tuple(validate_safe_identifier(value, "query_id") for value in values),
            "query_ids",
        )

    @field_validator("original_url")
    @classmethod
    def original_url_is_safe(cls, value: str) -> str:
        return validate_public_research_url(value)

    @field_validator("canonical_url_fingerprint", "candidate_fingerprint")
    @classmethod
    def fingerprints_are_hex(cls, value: str) -> str:
        return validate_hex64(value, "source candidate fingerprint")

    @field_validator("domain")
    @classmethod
    def domain_is_safe(cls, value: str) -> str:
        return validate_domain_name(value, "source candidate domain")

    @field_validator("expected_content_types")
    @classmethod
    def content_types_are_allowed(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        values = _sorted_tuple_unique(values, "expected_content_types")
        if set(values) - set(APPROVED_CONTENT_TYPES):
            raise ValueError("unsupported content type is rejected")
        return values

    @model_validator(mode="after")
    def candidate_is_bound_to_url(self) -> Self:
        split = urlsplit(self.original_url)
        if validate_domain_name(split.hostname or "", "candidate URL domain") != self.domain:
            raise ValueError("source candidate domain must match URL hostname")
        expected_url_fp = public_research_fingerprint({"canonical_url": self.original_url})
        if self.canonical_url_fingerprint != expected_url_fp:
            raise ValueError("canonical URL fingerprint mismatch")
        expected = _model_fingerprint(self, "candidate_fingerprint")
        if self.candidate_fingerprint != expected:
            raise ValueError("source candidate fingerprint mismatch")
        if not self.domain_allowlisted:
            raise ValueError("source candidate must be domain allowlisted")
        return self


class PublicResearchClaimSpecification(BaseModel):
    """Explicit operator-supplied claim specification."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-public-research-pilot-claim-specification/v1"] = (
        PUBLIC_RESEARCH_CLAIM_SPECIFICATION_SCHEMA_VERSION
    )
    claim_specification_id: str
    claim_id: str
    operator_supplied_claim_text: str = Field(min_length=8, max_length=1024)
    claim_text_fingerprint: str
    claim_kind: str = Field(min_length=1, max_length=80)
    evidence_bindings: tuple[str, ...] = Field(min_length=1, max_length=50)
    evidence_direction_by_source: dict[str, Literal["supports", "opposes", "contextual"]]
    target_valid_time: datetime
    jurisdiction: str = Field(min_length=1, max_length=80)
    version_scope: str = Field(min_length=1, max_length=80)
    domain_codes: tuple[str, ...] = Field(min_length=1, max_length=20)
    risk_class: Literal["low", "medium", "high"]
    explicit_operator_supplied: Literal[True] = True
    automatic_claim_extraction_enabled: Literal[False] = False
    automatic_claim_acceptance_enabled: Literal[False] = False
    automatic_claim_rejection_enabled: Literal[False] = False
    read_only: Literal[True] = True
    redacted: Literal[True] = True
    specification_fingerprint: str

    @field_validator("claim_specification_id", "claim_id")
    @classmethod
    def claim_ids_are_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "claim specification identifier")

    @field_validator("operator_supplied_claim_text")
    @classmethod
    def claim_text_is_safe(cls, value: str) -> str:
        return reject_prohibited_text(value, "claim text")

    @field_validator("claim_text_fingerprint", "specification_fingerprint")
    @classmethod
    def fingerprints_are_hex(cls, value: str) -> str:
        return validate_hex64(value, "claim specification fingerprint")

    @field_validator("evidence_bindings", "domain_codes")
    @classmethod
    def tuples_are_safe(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return _sorted_tuple_unique(
            tuple(
                validate_safe_identifier(value, "claim specification reference")
                for value in values
            ),
            "claim specification tuple",
        )

    @field_validator("evidence_direction_by_source")
    @classmethod
    def directions_are_explicit(
        cls,
        values: dict[str, Literal["supports", "opposes", "contextual"]],
    ) -> dict[str, Literal["supports", "opposes", "contextual"]]:
        return {
            validate_safe_identifier(key, "evidence direction key"): value
            for key, value in sorted(values.items())
        }

    @field_validator("target_valid_time")
    @classmethod
    def target_time_is_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value, "target_valid_time")

    @model_validator(mode="after")
    def specification_is_explicit(self) -> Self:
        if set(self.evidence_bindings) - set(self.evidence_direction_by_source):
            raise ValueError("every evidence binding must have an explicit direction")
        expected_claim = public_research_fingerprint(
            {
                "claim_id": self.claim_id,
                "operator_supplied_claim_text": self.operator_supplied_claim_text,
            }
        )
        if self.claim_text_fingerprint != expected_claim:
            raise ValueError("claim text fingerprint mismatch")
        expected = _model_fingerprint(self, "specification_fingerprint")
        if self.specification_fingerprint != expected:
            raise ValueError("claim specification fingerprint mismatch")
        return self


class PublicResearchPilotPlan(BaseModel):
    """One bounded public research plan."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-public-research-pilot-plan/v1"] = (
        PUBLIC_RESEARCH_PILOT_PLAN_SCHEMA_VERSION
    )
    pilot_plan_id: str
    authorization_transaction_id: Literal["AION-218-KI-0008"]
    mode: PublicResearchPilotMode
    research_plan: str = Field(min_length=8, max_length=1000)
    explicit_source_candidates: tuple[PublicResearchPilotSourceCandidate, ...] = Field(
        min_length=1,
        max_length=50,
    )
    explicit_claim_specifications: tuple[PublicResearchClaimSpecification, ...] = Field(
        min_length=1,
        max_length=50,
    )
    explicit_domain_allowlist: tuple[str, ...] = Field(min_length=1, max_length=20)
    allowed_methods: tuple[Literal["GET", "HEAD"], ...] = Field(
        default=("GET", "HEAD"),
        min_length=1,
        max_length=2,
    )
    allowed_content_types: tuple[str, ...] = Field(min_length=1, max_length=6)
    resource_budget: PublicResearchPilotResourceBudget = Field(
        default_factory=PublicResearchPilotResourceBudget
    )
    operator_invoked: Literal[True] = True
    background_execution: Literal[False] = False
    automatic_claim_extraction_enabled: Literal[False] = False
    search_provider_integration_enabled: Literal[False] = False
    connector_integration_enabled: Literal[False] = False
    model_provider_integration_enabled: Literal[False] = False
    browser_automation_enabled: Literal[False] = False
    automatic_promotion: Literal[False] = False
    persistent_write_applied: Literal[False] = False
    cognitive_memory_written: Literal[False] = False
    belief_mutated: Literal[False] = False
    created_at: datetime
    expires_at: datetime
    plan_fingerprint: str
    read_only: Literal[True] = True
    redacted: Literal[True] = True

    @field_validator("pilot_plan_id")
    @classmethod
    def plan_id_is_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "pilot_plan_id")

    @field_validator("research_plan")
    @classmethod
    def research_plan_is_safe(cls, value: str) -> str:
        return reject_prohibited_text(value, "research plan")

    @field_validator("explicit_domain_allowlist")
    @classmethod
    def allowlist_is_exact(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return _sorted_tuple_unique(
            tuple(validate_domain_name(value, "domain allowlist") for value in values),
            "domain allowlist",
        )

    @field_validator("allowed_methods")
    @classmethod
    def methods_are_safe(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if set(values) - set(APPROVED_METHODS):
            raise ValueError("only GET and HEAD are allowed")
        return _sorted_tuple_unique(values, "allowed_methods")

    @field_validator("allowed_content_types")
    @classmethod
    def content_types_are_safe(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        values = _sorted_tuple_unique(values, "allowed_content_types")
        if set(values) - set(APPROVED_CONTENT_TYPES):
            raise ValueError("unsupported content type is rejected")
        return values

    @field_validator("created_at", "expires_at")
    @classmethod
    def timestamps_are_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value, "public research plan timestamp")

    @field_validator("plan_fingerprint")
    @classmethod
    def fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "plan_fingerprint")

    @model_validator(mode="after")
    def plan_is_explicit_and_bounded(self) -> Self:
        if self.expires_at <= self.created_at:
            raise ValueError("plan expires before creation")
        elapsed = (self.expires_at - self.created_at).total_seconds()
        if elapsed > self.resource_budget.maximum_wall_clock_seconds_per_plan:
            raise ValueError("plan expiry exceeds wall-clock budget")
        allowlist = set(self.explicit_domain_allowlist)
        for candidate in self.explicit_source_candidates:
            if candidate.domain not in allowlist:
                raise ValueError("source candidate domain is not allowlisted")
            if candidate.method not in self.allowed_methods:
                raise ValueError("source candidate method is not allowed")
        expected = _model_fingerprint(self, "plan_fingerprint")
        if self.plan_fingerprint != expected:
            raise ValueError("pilot plan fingerprint mismatch")
        return self


class PublicResearchDnsResolution(BaseModel):
    """Redacted DNS resolution evidence with address fingerprints only."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-public-research-dns-resolution/v1"] = (
        PUBLIC_RESEARCH_DNS_RESOLUTION_SCHEMA_VERSION
    )
    resolution_id: str
    hostname: str
    port: int = Field(ge=1, le=65535)
    status: PublicResearchDnsStatus
    address_family_counts: dict[str, int]
    address_fingerprints: tuple[str, ...]
    host_fingerprint: str
    resolved_at: datetime
    validation_result: str
    resolution_fingerprint: str
    raw_address_logged: Literal[False] = False
    redacted: Literal[True] = True

    @field_validator("resolution_id")
    @classmethod
    def resolution_id_is_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "resolution_id")

    @field_validator("hostname")
    @classmethod
    def hostname_is_safe(cls, value: str) -> str:
        return validate_domain_name(value, "resolution hostname")

    @field_validator("address_fingerprints")
    @classmethod
    def address_hashes_are_safe(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return _sorted_tuple_unique(
            tuple(validate_hex64(value, "address fingerprint") for value in values),
            "address fingerprints",
        )

    @field_validator("host_fingerprint", "resolution_fingerprint")
    @classmethod
    def hashes_are_hex(cls, value: str) -> str:
        return validate_hex64(value, "DNS fingerprint")

    @field_validator("resolved_at")
    @classmethod
    def resolved_at_is_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value, "resolved_at")


class PublicResearchPinnedDestination(BaseModel):
    """Ephemeral pinned destination used by a single connection attempt."""

    model_config = FROZEN_MODEL_CONFIG

    hostname: str
    port: int = Field(ge=1, le=65535)
    address_family_by_address: dict[str, Literal["IPv4", "IPv6"]] = Field(repr=False)
    address_fingerprints_by_address: dict[str, str] = Field(repr=False)
    resolution: PublicResearchDnsResolution
    pinned_destination_fingerprint: str

    @field_validator("hostname")
    @classmethod
    def hostname_is_safe(cls, value: str) -> str:
        return validate_domain_name(value, "pinned hostname")

    @field_validator("pinned_destination_fingerprint")
    @classmethod
    def fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "pinned destination fingerprint")

    @model_validator(mode="after")
    def pinned_set_matches_resolution(self) -> Self:
        fingerprints = tuple(sorted(self.address_fingerprints_by_address.values()))
        if fingerprints != self.resolution.address_fingerprints:
            raise ValueError("pinned address set does not match DNS evidence")
        return self


PublicResearchDnsEvidence = PublicResearchDnsResolution


class PublicResearchRedirectHop(BaseModel):
    """Redacted redirect-hop evidence."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-public-research-redirect-hop/v1"] = (
        PUBLIC_RESEARCH_REDIRECT_HOP_SCHEMA_VERSION
    )
    redirect_id: str
    from_url_fingerprint: str
    to_url_fingerprint: str
    status_code: Literal[301, 302, 303, 307, 308]
    destination_resolution_fingerprint: str
    peer_address_fingerprint: str | None = None
    redirect_fingerprint: str
    redacted: Literal[True] = True

    @field_validator("redirect_id")
    @classmethod
    def redirect_id_is_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "redirect_id")

    @field_validator(
        "from_url_fingerprint",
        "to_url_fingerprint",
        "destination_resolution_fingerprint",
        "peer_address_fingerprint",
        "redirect_fingerprint",
    )
    @classmethod
    def hashes_are_hex(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return validate_hex64(value, "redirect fingerprint")


class PublicResearchHttpExchangeMetadata(BaseModel):
    """Committed redacted HTTP exchange evidence."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-public-research-http-exchange/v1"] = (
        PUBLIC_RESEARCH_HTTP_EXCHANGE_SCHEMA_VERSION
    )
    exchange_id: str
    request_id: str
    method: Literal["GET", "HEAD"]
    canonical_url_fingerprint: str
    hostname_fingerprint: str
    destination_resolution_fingerprint: str
    peer_address_fingerprint: str
    tls_protocol_version: str
    certificate_subject_fingerprint: str
    certificate_issuer_fingerprint: str
    status_code: int = Field(ge=100, le=599)
    safe_response_header_fingerprint: str
    content_type: str
    character_encoding: str | None = None
    body_length: int = Field(ge=0)
    body_sha256: str
    redirect_count: int = Field(ge=0, le=3)
    started_at: datetime
    completed_at: datetime
    outcome: PublicResearchHttpOutcome
    exchange_fingerprint: str
    source_body_committed: Literal[False] = False
    raw_headers_committed: Literal[False] = False
    cookies_committed: Literal[False] = False
    credentials_committed: Literal[False] = False
    redacted: Literal[True] = True

    @field_validator("exchange_id", "request_id")
    @classmethod
    def ids_are_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "HTTP exchange identifier")

    @field_validator(
        "canonical_url_fingerprint",
        "hostname_fingerprint",
        "destination_resolution_fingerprint",
        "peer_address_fingerprint",
        "certificate_subject_fingerprint",
        "certificate_issuer_fingerprint",
        "safe_response_header_fingerprint",
        "body_sha256",
        "exchange_fingerprint",
    )
    @classmethod
    def hashes_are_hex(cls, value: str) -> str:
        return validate_hex64(value, "HTTP exchange fingerprint")

    @field_validator("started_at", "completed_at")
    @classmethod
    def timestamps_are_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value, "HTTP exchange timestamp")

    @model_validator(mode="after")
    def response_metadata_is_safe(self) -> Self:
        if self.completed_at < self.started_at:
            raise ValueError("HTTP exchange completed before it started")
        if self.method == "HEAD" and self.body_length != 0:
            raise ValueError("HEAD response must not retain a body")
        if self.content_type not in APPROVED_CONTENT_TYPES:
            raise ValueError("unsupported content type")
        if (
            self.character_encoding is not None
            and self.character_encoding.lower() not in APPROVED_ENCODINGS
        ):
            raise ValueError("unsupported character encoding")
        return self


class PublicResearchPipelineTrace(BaseModel):
    """Redacted complete Knowledge Intelligence pipeline trace."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-public-research-pipeline-trace/v1"] = (
        PUBLIC_RESEARCH_PIPELINE_TRACE_SCHEMA_VERSION
    )
    trace_id: str
    composed_planes: tuple[str, ...]
    research_acquisition_result_fingerprint: str | None
    source_registry_integrity_fingerprint: str | None
    claim_graph_integrity_fingerprint: str | None
    assessment_fingerprints: tuple[str, ...] = ()
    domain_mesh_session_fingerprints: tuple[str, ...] = ()
    synthesis_fingerprints: tuple[str, ...] = ()
    tool_verification_session_fingerprints: tuple[str, ...] = ()
    verified_candidate_fingerprints: tuple[str, ...] = ()
    candidate_memory_snapshot_fingerprint: str | None = None
    source_body_purged: bool
    operator_review_required: Literal[True] = True
    automatic_promotion: Literal[False] = False
    persistent_write_applied: Literal[False] = False
    cognitive_memory_written: Literal[False] = False
    belief_mutated: Literal[False] = False
    runtime_effect: Literal[False] = False
    trace_fingerprint: str

    @field_validator("trace_id")
    @classmethod
    def trace_id_is_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "pipeline trace id")

    @field_validator(
        "research_acquisition_result_fingerprint",
        "source_registry_integrity_fingerprint",
        "claim_graph_integrity_fingerprint",
        "candidate_memory_snapshot_fingerprint",
        "trace_fingerprint",
    )
    @classmethod
    def optional_hashes_are_hex(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return validate_hex64(value, "pipeline trace fingerprint")

    @field_validator(
        "assessment_fingerprints",
        "domain_mesh_session_fingerprints",
        "synthesis_fingerprints",
        "tool_verification_session_fingerprints",
        "verified_candidate_fingerprints",
    )
    @classmethod
    def tuple_hashes_are_safe(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return _sorted_tuple_unique(
            tuple(validate_hex64(value, "pipeline trace tuple fingerprint") for value in values),
            "pipeline trace fingerprints",
        )


class PublicResearchPilotIntegrityFinding(BaseModel):
    """One redacted integrity audit finding."""

    model_config = FROZEN_MODEL_CONFIG

    finding_id: str
    passed: bool
    reason_code: str
    redacted_summary: str = Field(max_length=240)
    fingerprint: str

    @field_validator("finding_id", "reason_code")
    @classmethod
    def finding_ids_are_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "integrity finding")

    @field_validator("fingerprint")
    @classmethod
    def fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "integrity finding fingerprint")


class PublicResearchPilotIntegrityReport(BaseModel):
    """Redacted integrity report for one public research pilot."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-public-research-pilot-integrity/v1"] = (
        PUBLIC_RESEARCH_PILOT_INTEGRITY_SCHEMA_VERSION
    )
    report_id: str
    passed: bool
    findings: tuple[PublicResearchPilotIntegrityFinding, ...]
    finding_count: int = Field(ge=0)
    report_fingerprint: str
    redacted: Literal[True] = True
    runtime_effect: Literal[False] = False

    @field_validator("report_id")
    @classmethod
    def report_id_is_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "integrity report id")

    @field_validator("report_fingerprint")
    @classmethod
    def fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "integrity report fingerprint")

    @model_validator(mode="after")
    def finding_count_matches(self) -> Self:
        if self.finding_count != len(self.findings):
            raise ValueError("integrity finding count mismatch")
        return self


class PublicResearchPilotIncident(BaseModel):
    """Redacted fail-closed incident."""

    model_config = FROZEN_MODEL_CONFIG

    incident_id: str
    reason_code: str
    redacted_summary: str = Field(max_length=240)
    created_at: datetime
    fingerprint: str
    source_body_committed: Literal[False] = False
    redacted: Literal[True] = True

    @field_validator("incident_id", "reason_code")
    @classmethod
    def ids_are_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "incident identifier")

    @field_validator("redacted_summary")
    @classmethod
    def summary_is_safe(cls, value: str) -> str:
        return reject_prohibited_text(value, "incident summary")

    @field_validator("created_at")
    @classmethod
    def created_at_is_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value, "incident timestamp")

    @field_validator("fingerprint")
    @classmethod
    def fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "incident fingerprint")


class PublicResearchPilotDiagnostics(BaseModel):
    """Bounded redacted diagnostics for one pilot run."""

    model_config = FROZEN_MODEL_CONFIG

    diagnostics_id: str
    reason_codes: tuple[str, ...]
    bounded_counts: dict[str, int]
    incident_ids: tuple[str, ...] = ()
    created_at: datetime
    fingerprint: str
    redacted: Literal[True] = True
    runtime_effect: Literal[False] = False

    @field_validator("diagnostics_id")
    @classmethod
    def diagnostics_id_is_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "diagnostics id")

    @field_validator("reason_codes", "incident_ids")
    @classmethod
    def tuples_are_safe(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return _sorted_tuple_unique(
            tuple(validate_safe_identifier(value, "diagnostics tuple") for value in values),
            "diagnostics tuple",
        )

    @field_validator("bounded_counts")
    @classmethod
    def bounded_counts_are_safe(cls, value: dict[str, int]) -> dict[str, int]:
        for key, count in value.items():
            validate_safe_identifier(key, "diagnostics count")
            if count < 0:
                raise ValueError("diagnostics counts must be non-negative")
        return dict(sorted(value.items()))

    @field_validator("created_at")
    @classmethod
    def created_at_is_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value, "diagnostics timestamp")

    @field_validator("fingerprint")
    @classmethod
    def fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "diagnostics fingerprint")


class PublicResearchPilotOperatorReviewItem(BaseModel):
    """Operator review item for candidate evidence."""

    model_config = FROZEN_MODEL_CONFIG

    review_item_id: str
    candidate_ids: tuple[str, ...]
    candidate_eligibility_statuses: tuple[PublicResearchCandidateOutcome, ...]
    operator_review_required: Literal[True] = True
    candidate_is_not_factual_truth: Literal[True] = True
    candidate_approval_authorized: Literal[False] = False
    automatic_promotion_authorized: Literal[False] = False
    cognitive_memory_write_authorized: Literal[False] = False
    belief_mutation_authorized: Literal[False] = False
    persistent_write_authorized: Literal[False] = False
    background_research_authorized: Literal[False] = False
    search_provider_authorized: Literal[False] = False
    connector_authorized: Literal[False] = False
    model_provider_authorized: Literal[False] = False
    browser_authorized: Literal[False] = False
    approval_created: Literal[False] = False
    implementation_authorization_created: Literal[False] = False
    fingerprint: str

    @field_validator("review_item_id")
    @classmethod
    def review_id_is_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "operator review id")

    @field_validator("candidate_ids")
    @classmethod
    def candidate_ids_are_safe(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return _sorted_tuple_unique(
            tuple(validate_safe_identifier(value, "candidate id") for value in values),
            "candidate ids",
        )

    @field_validator("fingerprint")
    @classmethod
    def fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "operator review fingerprint")


class PublicResearchPilotEvidenceBundle(BaseModel):
    """Redacted evidence bundle for operator review."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-public-research-pilot-evidence/v1"] = (
        PUBLIC_RESEARCH_PILOT_EVIDENCE_SCHEMA_VERSION
    )
    evidence_bundle_id: str
    dns_resolution_fingerprints: tuple[str, ...] = ()
    http_exchange_fingerprints: tuple[str, ...] = ()
    redirect_hop_fingerprints: tuple[str, ...] = ()
    robots_policy_fingerprints: tuple[str, ...] = ()
    source_snapshot_fingerprints: tuple[str, ...] = ()
    source_provenance_fingerprints: tuple[str, ...] = ()
    citation_fingerprints: tuple[str, ...] = ()
    verified_candidate_fingerprints: tuple[str, ...] = ()
    incidents: tuple[PublicResearchPilotIncident, ...] = ()
    operator_review_items: tuple[PublicResearchPilotOperatorReviewItem, ...] = ()
    source_bodies_retained: Literal[0] = 0
    source_bodies_persisted: Literal[0] = 0
    automatic_promotions: Literal[0] = 0
    cognitive_memory_writes: Literal[0] = 0
    belief_mutations: Literal[0] = 0
    persistent_verified_knowledge_writes: Literal[0] = 0
    bundle_fingerprint: str
    redacted: Literal[True] = True
    runtime_effect: Literal[False] = False

    @field_validator("evidence_bundle_id")
    @classmethod
    def bundle_id_is_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "evidence bundle id")

    @field_validator(
        "dns_resolution_fingerprints",
        "http_exchange_fingerprints",
        "redirect_hop_fingerprints",
        "robots_policy_fingerprints",
        "source_snapshot_fingerprints",
        "source_provenance_fingerprints",
        "citation_fingerprints",
        "verified_candidate_fingerprints",
    )
    @classmethod
    def tuple_hashes_are_safe(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return _sorted_tuple_unique(
            tuple(validate_hex64(value, "evidence fingerprint") for value in values),
            "evidence fingerprints",
        )

    @field_validator("bundle_fingerprint")
    @classmethod
    def bundle_fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "evidence bundle fingerprint")


class PublicResearchPilotSession(BaseModel):
    """Final immutable public research pilot session record."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-public-research-pilot-session/v1"] = (
        PUBLIC_RESEARCH_PILOT_SESSION_SCHEMA_VERSION
    )
    pilot_session_id: str
    authorization_transaction_id: Literal["AION-218-KI-0008"]
    mode: PublicResearchPilotMode
    status: PublicResearchPilotStatus
    plan_fingerprints: tuple[str, ...]
    explicit_source_candidate_fingerprints: tuple[str, ...]
    explicit_claim_specification_fingerprints: tuple[str, ...]
    domain_allowlist_fingerprint: str
    dns_resolution_fingerprints: tuple[str, ...]
    http_exchange_fingerprints: tuple[str, ...]
    redirect_hop_fingerprints: tuple[str, ...]
    robots_policy_fingerprints: tuple[str, ...]
    source_snapshot_fingerprints: tuple[str, ...]
    source_provenance_fingerprints: tuple[str, ...]
    citation_fingerprints: tuple[str, ...]
    source_registry_integrity_fingerprint: str | None
    claim_graph_integrity_fingerprint: str | None
    assessment_fingerprints: tuple[str, ...]
    domain_mesh_session_fingerprints: tuple[str, ...]
    synthesis_fingerprints: tuple[str, ...]
    tool_verification_session_fingerprints: tuple[str, ...]
    verified_candidate_fingerprints: tuple[str, ...]
    candidate_eligibility_statuses: tuple[PublicResearchCandidateOutcome, ...]
    candidate_memory_snapshot_fingerprint: str | None
    operator_review_item_ids: tuple[str, ...]
    incident_ids: tuple[str, ...]
    budget_decision: PublicResearchPilotBudgetDecision
    kill_switch_state: PublicResearchKillSwitchState
    source_body_purged_count: int = Field(ge=0)
    public_https_request_count: int = Field(ge=0)
    dns_resolution_count: int = Field(ge=0)
    robots_request_count: int = Field(ge=0)
    external_read_performed: bool
    created_at: datetime
    session_fingerprint: str
    operator_invoked: Literal[True] = True
    background_execution: Literal[False] = False
    automatic_promotion: Literal[False] = False
    persistent_write_applied: Literal[False] = False
    cognitive_memory_written: Literal[False] = False
    belief_mutated: Literal[False] = False
    production_runtime_enabled: Literal[False] = False
    runtime_effect: Literal[False] = False

    @field_validator("pilot_session_id")
    @classmethod
    def session_id_is_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "pilot session id")

    @field_validator("created_at")
    @classmethod
    def created_at_is_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value, "pilot session timestamp")

    @field_validator("session_fingerprint", "domain_allowlist_fingerprint")
    @classmethod
    def fingerprints_are_hex(cls, value: str) -> str:
        return validate_hex64(value, "session fingerprint")

    @model_validator(mode="after")
    def mode_external_read_matches(self) -> Self:
        if (
            self.mode is PublicResearchPilotMode.DETERMINISTIC_SIMULATION
            and self.external_read_performed
        ):
            raise ValueError("simulation mode must not record external reads")
        if (
            self.mode is PublicResearchPilotMode.OPERATOR_INVOKED_LIVE
            and not self.external_read_performed
            and self.status
            not in {
                PublicResearchPilotStatus.BLOCKED,
                PublicResearchPilotStatus.KILLED,
                PublicResearchPilotStatus.FAILED,
            }
        ):
            raise ValueError("live mode must record external read effect")
        return self


class PublicResearchPilotResult(BaseModel):
    """Final redacted pilot result."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-public-research-pilot-result/v1"] = (
        PUBLIC_RESEARCH_PILOT_RESULT_SCHEMA_VERSION
    )
    pilot_session_id: str
    status: PublicResearchPilotStatus
    mode: PublicResearchPilotMode
    session: PublicResearchPilotSession
    pipeline_trace: PublicResearchPipelineTrace
    integrity_report: PublicResearchPilotIntegrityReport
    evidence_bundle: PublicResearchPilotEvidenceBundle
    candidate_count: int = Field(ge=0)
    candidate_eligibility_statuses: tuple[PublicResearchCandidateOutcome, ...]
    operator_review_required: Literal[True] = True
    external_read_performed: bool
    automatic_promotion: Literal[False] = False
    cognitive_memory_written: Literal[False] = False
    belief_mutated: Literal[False] = False
    persistent_write_applied: Literal[False] = False
    runtime_effect: Literal[False] = False
    result_fingerprint: str

    @field_validator("pilot_session_id")
    @classmethod
    def session_id_is_safe(cls, value: str) -> str:
        return validate_safe_identifier(value, "result session id")

    @field_validator("result_fingerprint")
    @classmethod
    def result_fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "result fingerprint")


def budget_decision_for_usage(
    usage: PublicResearchPilotResourceUsage,
    budget: PublicResearchPilotResourceBudget | None = None,
) -> PublicResearchPilotBudgetDecision:
    """Evaluate AION-219 hard budget limits."""

    resolved_budget = budget or PublicResearchPilotResourceBudget()
    checks = {
        "pilot_sessions": usage.pilot_sessions <= resolved_budget.maximum_pilot_sessions,
        "plans": usage.plans <= resolved_budget.maximum_plans_per_session,
        "source_candidates": (
            usage.source_candidates
            <= resolved_budget.maximum_explicit_source_candidates_per_plan
        ),
        "source_fetches": usage.source_fetches <= resolved_budget.maximum_source_fetches_per_plan,
        "robots_fetches": usage.robots_fetches <= resolved_budget.maximum_robots_fetches_per_plan,
        "public_https_requests": (
            usage.public_https_requests
            <= resolved_budget.maximum_public_https_requests_per_plan
        ),
        "dns_resolutions": (
            usage.dns_resolutions <= resolved_budget.maximum_dns_resolutions_per_plan
        ),
        "redirects": usage.redirects <= resolved_budget.maximum_redirects_per_fetch,
        "response_bytes": (
            usage.maximum_response_bytes_for_any_source
            <= resolved_budget.maximum_response_bytes_per_source
        ),
        "total_transfer_bytes": (
            usage.total_transfer_bytes <= resolved_budget.maximum_total_transfer_bytes_per_plan
        ),
        "snapshots": usage.snapshots <= resolved_budget.maximum_snapshots_per_plan,
        "claim_specifications": (
            usage.claim_specifications
            <= resolved_budget.maximum_explicit_claim_specs_per_session
        ),
        "candidate_evaluations": (
            usage.candidate_evaluations
            <= resolved_budget.maximum_candidate_evaluations_per_session
        ),
        "operator_review_items": (
            usage.operator_review_items
            <= resolved_budget.maximum_operator_review_items_per_session
        ),
        "elapsed_wall_clock_seconds": (
            usage.elapsed_wall_clock_seconds
            <= resolved_budget.maximum_wall_clock_seconds_per_plan
        ),
    }
    zero_limits = {
        "search_provider_calls": usage.search_provider_calls,
        "connector_calls": usage.connector_calls,
        "model_provider_calls": usage.model_provider_calls,
        "actual_tool_executions": usage.actual_tool_executions,
        "shell_commands": usage.shell_commands,
        "subprocess_executions": usage.subprocess_executions,
        "browser_actions": usage.browser_actions,
        "runtime_filesystem_mutations": usage.runtime_filesystem_mutations,
        "persistent_source_body_writes": usage.persistent_source_body_writes,
        "persistent_verified_knowledge_writes": usage.persistent_verified_knowledge_writes,
        "automatic_knowledge_promotions": usage.automatic_knowledge_promotions,
        "cognitive_memory_writes": usage.cognitive_memory_writes,
        "belief_mutations": usage.belief_mutations,
    }
    checks.update({key: count == 0 for key, count in zero_limits.items()})
    failed = tuple(sorted(key for key, passed in checks.items() if not passed))
    reasons = ("public_research_budget_satisfied",) if not failed else failed
    payload = {
        "within_budget": not failed,
        "reason_codes": reasons,
        "usage": usage.model_dump(mode="json"),
        "budget": resolved_budget.model_dump(mode="json"),
    }
    return PublicResearchPilotBudgetDecision(
        within_budget=not failed,
        reason_codes=reasons,
        usage=usage,
        budget=resolved_budget,
        fingerprint=public_research_fingerprint(payload),
    )


def confirmation_fingerprint(pilot_session_id: str) -> str:
    """Build the exact live pilot confirmation fingerprint."""

    validate_safe_identifier(pilot_session_id, "pilot_session_id")
    return public_research_fingerprint(
        {
            "authorization_transaction_id": AUTHORIZATION_TRANSACTION_ID,
            "confirmation": LIVE_CONFIRMATION_TEXT,
            "pilot_session_id": pilot_session_id,
        }
    )


def body_digest(body: bytes) -> str:
    """Return a SHA-256 digest for a source body without retaining the body."""

    return sha256_bytes(body)


def deterministic_json_bytes(value: Any) -> bytes:
    """Return deterministic UTF-8 JSON bytes."""

    return stable_json(value).encode("utf-8")


def _model_fingerprint(model: BaseModel, fingerprint_field: str) -> str:
    payload = model.model_dump(mode="json", exclude={fingerprint_field})
    return public_research_fingerprint(payload)


def _build_fingerprinted_model(
    model_type: type[BaseModel],
    payload: dict[str, Any],
    fingerprint_field: str,
) -> BaseModel:
    data: dict[str, Any] = {**payload, fingerprint_field: "0" * 64}
    placeholder = model_type.model_construct(_fields_set=set(data), **data)
    fingerprint = _model_fingerprint(placeholder, fingerprint_field)
    return model_type.model_validate({**payload, fingerprint_field: fingerprint})


def build_public_research_authorization_envelope(
    *,
    pilot_session_id: str,
    plan_ids: tuple[str, ...],
    operator_identity_fingerprint: str,
    live_network_access_approved: bool,
    created_at: datetime,
    expires_at: datetime,
) -> PublicResearchPilotAuthorizationEnvelope:
    """Build a self-fingerprinted AION-218-KI-0008 invocation envelope."""

    payload = {
        "authorization_transaction_id": AUTHORIZATION_TRANSACTION_ID,
        "approval_record_id": APPROVAL_RECORD_ID,
        "pilot_session_id": pilot_session_id,
        "plan_ids": tuple(plan_ids),
        "operator_identity_fingerprint": operator_identity_fingerprint,
        "live_network_access_approved": live_network_access_approved,
        "confirmation_fingerprint": confirmation_fingerprint(pilot_session_id),
        "created_at": created_at,
        "expires_at": expires_at,
    }
    return _build_fingerprinted_model(
        PublicResearchPilotAuthorizationEnvelope,
        payload,
        "authorization_envelope_fingerprint",
    )  # type: ignore[return-value]


def build_public_research_source_candidate(
    *,
    source_candidate_id: str,
    query_ids: tuple[str, ...],
    original_url: str,
    source_class: Literal[
        "primary_authoritative",
        "official_standard",
        "official_government",
        "peer_reviewed",
        "vendor_primary",
        "institutional_primary",
        "reputable_secondary",
    ],
    source_control_group_id: str,
    robots_policy_expectation: str = "allowed_or_not_applicable",
    licence_policy_status: Literal["permitted", "not_applicable"] = "permitted",
    expected_content_types: tuple[str, ...] = ("text/html", "text/plain"),
    method: Literal["GET", "HEAD"] = "GET",
    domain_allowlisted: bool = True,
) -> PublicResearchPilotSourceCandidate:
    """Build a self-fingerprinted explicit HTTPS source candidate."""

    split = urlsplit(validate_public_research_url(original_url))
    domain = validate_domain_name(split.hostname or "", "source candidate hostname")
    payload = {
        "source_candidate_id": source_candidate_id,
        "query_ids": tuple(query_ids),
        "original_url": original_url,
        "canonical_url_fingerprint": public_research_fingerprint(
            {"canonical_url": original_url}
        ),
        "domain": domain,
        "source_class": source_class,
        "source_control_group_id": source_control_group_id,
        "robots_policy_expectation": robots_policy_expectation,
        "licence_policy_status": licence_policy_status,
        "expected_content_types": tuple(expected_content_types),
        "method": method,
        "domain_allowlisted": domain_allowlisted,
    }
    return _build_fingerprinted_model(
        PublicResearchPilotSourceCandidate,
        payload,
        "candidate_fingerprint",
    )  # type: ignore[return-value]


def build_public_research_claim_specification(
    *,
    claim_specification_id: str,
    claim_id: str,
    operator_supplied_claim_text: str,
    claim_kind: str,
    evidence_bindings: tuple[str, ...],
    evidence_direction_by_source: dict[str, Literal["supports", "opposes", "contextual"]],
    target_valid_time: datetime,
    jurisdiction: str,
    version_scope: str,
    domain_codes: tuple[str, ...],
    risk_class: Literal["low", "medium", "high"] = "low",
) -> PublicResearchClaimSpecification:
    """Build a self-fingerprinted explicit claim specification."""

    payload = {
        "claim_specification_id": claim_specification_id,
        "claim_id": claim_id,
        "operator_supplied_claim_text": operator_supplied_claim_text,
        "claim_text_fingerprint": public_research_fingerprint(
            {
                "claim_id": claim_id,
                "operator_supplied_claim_text": operator_supplied_claim_text,
            }
        ),
        "claim_kind": claim_kind,
        "evidence_bindings": tuple(evidence_bindings),
        "evidence_direction_by_source": dict(evidence_direction_by_source),
        "target_valid_time": target_valid_time,
        "jurisdiction": jurisdiction,
        "version_scope": version_scope,
        "domain_codes": tuple(domain_codes),
        "risk_class": risk_class,
    }
    return _build_fingerprinted_model(
        PublicResearchClaimSpecification,
        payload,
        "specification_fingerprint",
    )  # type: ignore[return-value]


def build_public_research_plan(
    *,
    pilot_plan_id: str,
    mode: PublicResearchPilotMode,
    research_plan: str,
    explicit_source_candidates: tuple[PublicResearchPilotSourceCandidate, ...],
    explicit_claim_specifications: tuple[PublicResearchClaimSpecification, ...],
    explicit_domain_allowlist: tuple[str, ...],
    allowed_methods: tuple[Literal["GET", "HEAD"], ...] = ("GET", "HEAD"),
    allowed_content_types: tuple[str, ...] = ("text/html", "text/plain"),
    created_at: datetime,
    expires_at: datetime,
    resource_budget: PublicResearchPilotResourceBudget | None = None,
) -> PublicResearchPilotPlan:
    """Build a self-fingerprinted public research pilot plan."""

    payload = {
        "pilot_plan_id": pilot_plan_id,
        "authorization_transaction_id": AUTHORIZATION_TRANSACTION_ID,
        "mode": mode,
        "research_plan": research_plan,
        "explicit_source_candidates": tuple(explicit_source_candidates),
        "explicit_claim_specifications": tuple(explicit_claim_specifications),
        "explicit_domain_allowlist": tuple(explicit_domain_allowlist),
        "allowed_methods": tuple(allowed_methods),
        "allowed_content_types": tuple(allowed_content_types),
        "resource_budget": resource_budget or PublicResearchPilotResourceBudget(),
        "created_at": created_at,
        "expires_at": expires_at,
    }
    return _build_fingerprinted_model(
        PublicResearchPilotPlan,
        payload,
        "plan_fingerprint",
    )  # type: ignore[return-value]


__all__ = [
    "APPROVAL_RECORD_ID",
    "APPROVED_CONTENT_TYPES",
    "APPROVED_ENCODINGS",
    "APPROVED_LICENCE_STATUSES",
    "APPROVED_METHODS",
    "APPROVED_SOURCE_CLASSES",
    "AUTHORIZATION_SCOPE",
    "AUTHORIZATION_TRANSACTION_ID",
    "FORMAL_CLOSEOUT_TASK",
    "IMPLEMENTATION_TASK",
    "LIVE_CONFIRMATION_TEXT",
    "PROGRAM_ID",
    "PUBLIC_RESEARCH_PILOT_AUTHORIZATION_SCHEMA_VERSION",
    "PUBLIC_RESEARCH_PILOT_BUDGET_SCHEMA_VERSION",
    "PUBLIC_RESEARCH_PILOT_CONTRACT_SCHEMA_VERSION",
    "PUBLIC_RESEARCH_PILOT_EVIDENCE_SCHEMA_VERSION",
    "PUBLIC_RESEARCH_PILOT_INTEGRITY_SCHEMA_VERSION",
    "PUBLIC_RESEARCH_PILOT_PLAN_SCHEMA_VERSION",
    "PUBLIC_RESEARCH_PILOT_REASON_CODE_REGISTRY_VERSION",
    "PUBLIC_RESEARCH_PILOT_RESOURCE_LIMITS",
    "PUBLIC_RESEARCH_PILOT_RESULT_SCHEMA_VERSION",
    "PUBLIC_RESEARCH_PILOT_SESSION_SCHEMA_VERSION",
    "PUBLIC_RESEARCH_PIPELINE_TRACE_SCHEMA_VERSION",
    "PUBLIC_RESEARCH_USER_AGENT",
    "PUBLIC_RESEARCH_CLAIM_SPECIFICATION_SCHEMA_VERSION",
    "PUBLIC_RESEARCH_DNS_RESOLUTION_SCHEMA_VERSION",
    "PUBLIC_RESEARCH_HTTP_EXCHANGE_SCHEMA_VERSION",
    "PUBLIC_RESEARCH_REDIRECT_HOP_SCHEMA_VERSION",
    "PUBLIC_RESEARCH_SOURCE_CANDIDATE_SCHEMA_VERSION",
    "PublicResearchCandidateOutcome",
    "PublicResearchClaimSpecification",
    "PublicResearchDnsEvidence",
    "PublicResearchDnsResolution",
    "PublicResearchDnsStatus",
    "PublicResearchHttpExchangeMetadata",
    "PublicResearchHttpOutcome",
    "PublicResearchKillSwitchState",
    "PublicResearchPilotAuthorizationEnvelope",
    "PublicResearchPilotBudgetDecision",
    "PublicResearchPilotDiagnostics",
    "PublicResearchPilotEvidenceBundle",
    "PublicResearchPilotIncident",
    "PublicResearchPilotIntegrityFinding",
    "PublicResearchPilotIntegrityReport",
    "PublicResearchPilotMode",
    "PublicResearchPilotOperatorReviewItem",
    "PublicResearchPilotPlan",
    "PublicResearchPilotResourceBudget",
    "PublicResearchPilotResourceUsage",
    "PublicResearchPilotResult",
    "PublicResearchPilotSession",
    "PublicResearchPilotSourceCandidate",
    "PublicResearchPilotStatus",
    "PublicResearchPinnedDestination",
    "PublicResearchPipelineTrace",
    "PublicResearchRedirectHop",
    "body_digest",
    "build_public_research_authorization_envelope",
    "build_public_research_claim_specification",
    "build_public_research_plan",
    "build_public_research_source_candidate",
    "budget_decision_for_usage",
    "confirmation_fingerprint",
    "deterministic_json_bytes",
    "public_research_fingerprint",
    "reject_prohibited_text",
    "utc_now",
    "validate_domain_name",
    "validate_public_research_url",
    "validate_safe_identifier",
]
