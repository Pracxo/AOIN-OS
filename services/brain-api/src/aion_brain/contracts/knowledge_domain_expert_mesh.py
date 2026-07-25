"""Deterministic in-memory domain expert mesh contracts."""

from __future__ import annotations

import math
import re
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.knowledge_epistemic_assessment import (
    ClaimEpistemicAssessment,
    EpistemicAssessmentStatus,
    quantize_score,
)
from aion_brain.contracts.knowledge_research import (
    ensure_utc,
    fingerprint_payload,
    reject_protected_material,
    stable_json,
    validate_hex64,
)

DOMAIN_EXPERT_MESH_CONTRACT_SCHEMA_VERSION: Literal["aion-knowledge-domain-expert-mesh/v1"] = (
    "aion-knowledge-domain-expert-mesh/v1"
)
DOMAIN_TAXONOMY_SCHEMA_VERSION: Literal["aion-knowledge-domain-taxonomy/v1"] = (
    "aion-knowledge-domain-taxonomy/v1"
)
DOMAIN_EXPERT_PROFILE_SCHEMA_VERSION: Literal["aion-knowledge-domain-expert-profile/v1"] = (
    "aion-knowledge-domain-expert-profile/v1"
)
DOMAIN_EXPERT_CASE_SCHEMA_VERSION: Literal["aion-knowledge-domain-expert-case/v1"] = (
    "aion-knowledge-domain-expert-case/v1"
)
EXPERT_PANEL_PLAN_SCHEMA_VERSION: Literal["aion-knowledge-expert-panel-plan/v1"] = (
    "aion-knowledge-expert-panel-plan/v1"
)
EXPERT_PERSPECTIVE_REPORT_SCHEMA_VERSION: Literal["aion-knowledge-expert-perspective-report/v1"] = (
    "aion-knowledge-expert-perspective-report/v1"
)
EXPERT_CRITIQUE_SCHEMA_VERSION: Literal["aion-knowledge-expert-critique/v1"] = (
    "aion-knowledge-expert-critique/v1"
)
EXPERT_CRITIQUE_RESPONSE_SCHEMA_VERSION: Literal["aion-knowledge-expert-critique-response/v1"] = (
    "aion-knowledge-expert-critique-response/v1"
)
EXPERT_DISAGREEMENT_MATRIX_SCHEMA_VERSION: Literal[
    "aion-knowledge-expert-disagreement-matrix/v1"
] = "aion-knowledge-expert-disagreement-matrix/v1"
EXPERT_MESH_SYNTHESIS_SCHEMA_VERSION: Literal["aion-knowledge-expert-mesh-synthesis/v1"] = (
    "aion-knowledge-expert-mesh-synthesis/v1"
)
EXPERT_MESH_SESSION_SCHEMA_VERSION: Literal["aion-knowledge-expert-mesh-session/v1"] = (
    "aion-knowledge-expert-mesh-session/v1"
)
EXPERT_MESH_INTEGRITY_SCHEMA_VERSION: Literal["aion-knowledge-expert-mesh-integrity/v1"] = (
    "aion-knowledge-expert-mesh-integrity/v1"
)
EXPERT_MESH_FIXTURE_SCHEMA_VERSION: Literal["aion-knowledge-expert-mesh-fixture/v1"] = (
    "aion-knowledge-expert-mesh-fixture/v1"
)
EXPERT_MESH_EVIDENCE_SCHEMA_VERSION: Literal["aion-knowledge-expert-mesh-evidence/v1"] = (
    "aion-knowledge-expert-mesh-evidence/v1"
)
EXPERT_MESH_REASON_CODE_REGISTRY_VERSION: Literal["aion-knowledge-expert-mesh-reasons/v1"] = (
    "aion-knowledge-expert-mesh-reasons/v1"
)

PROGRAM_ID: Literal["AION-KNOWLEDGE-INTELLIGENCE-001"] = "AION-KNOWLEDGE-INTELLIGENCE-001"
AUTHORIZATION_TRANSACTION_ID: Literal["AION-212-KI-0005"] = "AION-212-KI-0005"
APPROVAL_RECORD_ID: Literal["AION-212-KI-0005"] = "AION-212-KI-0005"
IMPLEMENTATION_TASK: Literal["AION-213"] = "AION-213"
FORMAL_CLOSEOUT_TASK: Literal["AION-214"] = "AION-214"
AUTHORIZATION_SCOPE: Literal[
    "deterministic-domain-taxonomy-expert-profile-routing-independent-analysis-"
    "deliberation-disagreement-synthesis-abstention-core"
] = (
    "deterministic-domain-taxonomy-expert-profile-routing-independent-analysis-"
    "deliberation-disagreement-synthesis-abstention-core"
)

MAXIMUM_DOMAINS_PER_CASE: Literal[20] = 20
MAXIMUM_SPECIALTIES_PER_CASE: Literal[50] = 50
MAXIMUM_CLAIMS_PER_CASE: Literal[100] = 100
MAXIMUM_EPISTEMIC_ASSESSMENTS_PER_CASE: Literal[100] = 100
MAXIMUM_SUBQUESTIONS_PER_CASE: Literal[50] = 50
MAXIMUM_EXPERT_PROFILES_CONSIDERED: Literal[100] = 100
MAXIMUM_PANEL_SIZE: Literal[12] = 12
MAXIMUM_REQUIRED_ROLES_PER_PANEL: Literal[8] = 8
MAXIMUM_EXPERT_REPORTS_PER_CASE: Literal[24] = 24
MAXIMUM_CRITIQUES_PER_CASE: Literal[100] = 100
MAXIMUM_DELIBERATION_ROUNDS: Literal[3] = 3
MAXIMUM_DISAGREEMENT_ITEMS_PER_CASE: Literal[100] = 100
MAXIMUM_EVIDENCE_REFERENCES_PER_REPORT: Literal[100] = 100
MAXIMUM_REASON_CODES_PER_REPORT: Literal[50] = 50
MAXIMUM_OPERATOR_REVIEW_ITEMS: Literal[100] = 100
MAXIMUM_MESH_SESSIONS: Literal[100] = 100
MAXIMUM_QUERY_RESULTS: Literal[1000] = 1000
MAXIMUM_FIXTURE_RECORDS: Literal[5000] = 5000
MAXIMUM_FIXTURE_BYTES: Literal[4194304] = 4_194_304
MAXIMUM_CONCURRENT_EXPERTS: Literal[8] = 8
MAXIMUM_PERSISTENT_MESH_WRITE_BATCH: Literal[0] = 0
MAXIMUM_MODEL_PROVIDER_CALLS: Literal[0] = 0
MAXIMUM_TOOL_EXECUTIONS: Literal[0] = 0
MAXIMUM_NETWORK_CALLS: Literal[0] = 0
MAXIMUM_SEARCH_PROVIDER_CALLS: Literal[0] = 0
MAXIMUM_CONNECTOR_CALLS: Literal[0] = 0
MAXIMUM_KNOWLEDGE_PROMOTIONS: Literal[0] = 0
MAXIMUM_BELIEF_MUTATIONS: Literal[0] = 0
MAXIMUM_SOURCE_MUTATIONS: Literal[0] = 0
MAXIMUM_GIT_OPERATIONS: Literal[0] = 0
MAXIMUM_RUNTIME_CREATED_PULL_REQUESTS: Literal[0] = 0
MAXIMUM_APPROVALS_CREATED: Literal[0] = 0
MAXIMUM_AUTONOMOUS_ACTIONS: Literal[0] = 0
MAXIMUM_HIGH_STAKES_ACTIONS: Literal[0] = 0
MAXIMUM_DEPLOYMENTS: Literal[0] = 0
MAXIMUM_MODEL_WEIGHT_CHANGES: Literal[0] = 0

MODEL_CONFIG = ConfigDict(extra="forbid", hide_input_in_errors=True)
FROZEN_MODEL_CONFIG = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)

_UNSAFE_REASON_RE = re.compile(r"[/:\\\\]")
_SAFE_MESH_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._:-]{0,127}$")
_SECRET_PREFIXES = ("sk-", "ghp_", "gho_", "xoxb-")
_TEXT_MARKERS = (
    "source body",
    "source preview",
    "raw prompt",
    "hidden reasoning",
    "raw user message",
    "chain of thought",
    "credential",
    "password",
    "bearer ",
    "authorization:",
    "cookie:",
    "private key",
    "unredacted personal data",
    "diff --git",
    "@@",
)


class CaseRiskClass(StrEnum):
    """Explicit case risk class."""

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class ExpertPerspectiveRole(StrEnum):
    """Computational perspective roles."""

    DOMAIN_ANALYST = "domain_analyst"
    EVIDENCE_AUDITOR = "evidence_auditor"
    METHODOLOGICAL_SKEPTIC = "methodological_skeptic"
    RISK_REVIEWER = "risk_reviewer"
    TEMPORAL_SCOPE_REVIEWER = "temporal_scope_reviewer"
    JURISDICTION_REVIEWER = "jurisdiction_reviewer"
    VERSION_REVIEWER = "version_reviewer"
    SYNTHESIS_COORDINATOR = "synthesis_coordinator"
    CROSS_DOMAIN_REVIEWER = "cross_domain_reviewer"


class ExpertReportPosition(StrEnum):
    """Advisory report posture, never a truth decision."""

    SUPPORTS = "supports"
    OPPOSES = "opposes"
    MIXED = "mixed"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    SCOPE_MISMATCH = "scope_mismatch"
    STALE = "stale"
    SUPERSEDED = "superseded"
    RETRACTED = "retracted"
    UNKNOWN = "unknown"
    ABSTAIN = "abstain"


class PanelAlignmentState(StrEnum):
    """Synthesis alignment state."""

    UNANIMOUS_ALIGNMENT = "unanimous_alignment"
    QUALIFIED_ALIGNMENT = "qualified_alignment"
    PLURAL_POSITIONS = "plural_positions"
    UNRESOLVED_DISAGREEMENT = "unresolved_disagreement"
    ABSTAIN = "abstain"


class DisagreementType(StrEnum):
    """Detected disagreement dimensions."""

    POSITION = "position"
    EVIDENCE = "evidence"
    SOURCE_INDEPENDENCE = "source_independence"
    METHODOLOGY = "methodology"
    ASSUMPTION = "assumption"
    LIMITATION = "limitation"
    TEMPORAL_SCOPE = "temporal_scope"
    JURISDICTION = "jurisdiction"
    VERSION = "version"
    RISK = "risk"
    CONFIDENCE_CAP = "confidence_cap"
    UNRESOLVED_REFERENCE = "unresolved_reference"


class MeshSessionOutcome(StrEnum):
    """Session outcome."""

    COMPLETED = "completed"
    COMPLETED_WITH_ABSTENTION = "completed_with_abstention"
    INTEGRITY_BLOCKED = "integrity_blocked"
    BUDGET_BLOCKED = "budget_blocked"
    FIXTURE_REJECTED = "fixture_rejected"
    PERSISTENT_WRITE_DISABLED = "persistent_write_disabled"


class MeshIntegrityStatus(StrEnum):
    """Integrity audit status."""

    PASSED = "passed"
    FAILED = "failed"


class DomainExpertMeshError(ValueError):
    """Raised when domain expert mesh input violates the authorization boundary."""


EXPERT_MESH_REASON_CODES: tuple[str, ...] = (
    "domain_mesh_case_valid",
    "domain_mesh_case_invalid",
    "domain_mesh_taxonomy_valid",
    "domain_mesh_taxonomy_cycle",
    "domain_mesh_profile_valid",
    "domain_mesh_profile_invalid",
    "domain_mesh_human_identity_blocked",
    "domain_mesh_professional_credential_blocked",
    "domain_mesh_domain_match",
    "domain_mesh_specialty_match",
    "domain_mesh_jurisdiction_match",
    "domain_mesh_version_match",
    "domain_mesh_temporal_scope_match",
    "domain_mesh_risk_match",
    "domain_mesh_profile_ineligible",
    "domain_mesh_required_role_assigned",
    "domain_mesh_required_role_missing",
    "domain_mesh_independence_group_duplicate",
    "domain_mesh_panel_selected",
    "domain_mesh_panel_incomplete",
    "domain_mesh_report_created",
    "domain_mesh_evidence_reference_resolved",
    "domain_mesh_evidence_reference_unresolved",
    "domain_mesh_assessment_reference_resolved",
    "domain_mesh_assessment_reference_unresolved",
    "domain_mesh_assumption_recorded",
    "domain_mesh_limitation_recorded",
    "domain_mesh_evidence_gap_recorded",
    "domain_mesh_self_review_rejected",
    "domain_mesh_circular_critique_rejected",
    "domain_mesh_critique_created",
    "domain_mesh_critique_response_created",
    "domain_mesh_disagreement_detected",
    "domain_mesh_dissent_preserved",
    "domain_mesh_alignment_unanimous",
    "domain_mesh_alignment_qualified",
    "domain_mesh_alignment_plural",
    "domain_mesh_alignment_unresolved",
    "domain_mesh_alignment_abstain",
    "domain_mesh_confidence_non_amplification_enforced",
    "domain_mesh_underlying_cap_propagated",
    "domain_mesh_high_stakes_abstention",
    "domain_mesh_operator_review_required",
    "domain_mesh_model_provider_blocked",
    "domain_mesh_tool_execution_blocked",
    "domain_mesh_network_blocked",
    "domain_mesh_absolute_truth_blocked",
    "domain_mesh_automatic_action_blocked",
    "domain_mesh_knowledge_promotion_blocked",
    "domain_mesh_belief_mutation_blocked",
    "domain_mesh_persistent_write_disabled",
    "domain_mesh_runtime_disabled",
    "domain_mesh_integrity_passed",
    "domain_mesh_integrity_failed",
)
EXPERT_MESH_REASON_CODE_REGISTRY = EXPERT_MESH_REASON_CODES


def validate_mesh_reason_codes(values: tuple[str, ...]) -> tuple[str, ...]:
    """Validate immutable ordered mesh reason codes."""

    seen: set[str] = set()
    for code in values:
        if code not in EXPERT_MESH_REASON_CODE_REGISTRY:
            raise ValueError("unknown domain expert mesh reason code")
        if code in seen:
            raise ValueError("duplicate domain expert mesh reason code")
        if _UNSAFE_REASON_RE.search(code):
            raise ValueError("domain expert mesh reason code must not embed path text")
        reject_protected_material(code, "domain expert mesh reason code")
        seen.add(code)
    return values


def validate_mesh_identifier(value: str, field_name: str = "identifier") -> str:
    """Validate a bounded safe ASCII identifier for explicit mesh records."""

    if not _SAFE_MESH_ID_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a safe lowercase identifier")
    if value.lower().startswith(_SECRET_PREFIXES):
        raise ValueError(f"{field_name} contains protected material")
    return value


def validate_mesh_text(value: str, field_name: str) -> str:
    """Validate bounded redacted text without echoing unsafe content."""

    if not value or len(value) > 240:
        raise ValueError(f"{field_name} must be bounded")
    if value.strip() != value:
        raise ValueError(f"{field_name} must not include surrounding whitespace")
    lowered = value.lower()
    if any(marker in lowered for marker in _TEXT_MARKERS):
        raise ValueError(f"{field_name} must remain redacted")
    reject_protected_material(value, field_name)
    return value


def reject_mesh_protected_material(value: Any, field_name: str = "payload") -> None:
    """Reject unsafe recursive payload shapes without leaking rejected content."""

    seen: set[int] = set()

    def visit(item: Any) -> None:
        if callable(item) or isinstance(item, BaseException):
            raise ValueError(f"{field_name} contains unsupported material")
        if isinstance(item, dict):
            marker = id(item)
            if marker in seen:
                raise ValueError(f"{field_name} contains recursive material")
            seen.add(marker)
            for key, child in item.items():
                validate_mesh_text(str(key), f"{field_name} key")
                visit(child)
            seen.remove(marker)
            return
        if isinstance(item, (list, tuple, set, frozenset)):
            marker = id(item)
            if marker in seen:
                raise ValueError(f"{field_name} contains recursive material")
            seen.add(marker)
            for child in item:
                visit(child)
            seen.remove(marker)
            return
        if isinstance(item, str):
            validate_mesh_text(item, field_name)
            return
        reject_protected_material(item, field_name)

    visit(value)


def _json_ready(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return _json_ready(value.model_dump(mode="json", exclude_defaults=True))
    if isinstance(value, Decimal):
        return format(quantize_score(value), "f")
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, datetime):
        text = ensure_utc(value, "fingerprint timestamp").isoformat()
        return f"{text[:-6]}Z" if text.endswith("+00:00") else text
    if isinstance(value, dict):
        prepared: dict[str, Any] = {}
        for key, item in sorted(value.items()):
            normalized = _json_ready(item)
            if normalized is None or normalized == [] or normalized == {}:
                continue
            prepared[str(key)] = normalized
        return prepared
    if isinstance(value, (tuple, list)):
        return [_json_ready(item) for item in value]
    if isinstance(value, set | frozenset):
        return sorted(_json_ready(item) for item in value)
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("non-finite value rejected")
        return value
    return value


def domain_mesh_fingerprint(model: BaseModel | dict[str, Any], field_name: str) -> str:
    """Fingerprint a model after excluding its fingerprint field."""

    payload = (
        model.model_dump(mode="json", exclude_defaults=True)
        if isinstance(model, BaseModel)
        else dict(model)
    )
    payload.pop(field_name, None)
    return fingerprint_payload(_json_ready(payload))


def json_size(payload: object) -> int:
    """Return deterministic JSON byte size."""

    return len(stable_json(_json_ready(payload)).encode("utf-8"))


def _safe_id_tuple(values: tuple[str, ...], field_name: str, *, max_length: int) -> tuple[str, ...]:
    if len(values) > max_length:
        raise ValueError(f"{field_name} exceeds maximum")
    validated = tuple(sorted(validate_mesh_identifier(item, field_name) for item in values))
    if len(set(validated)) != len(validated):
        raise ValueError(f"duplicate {field_name} rejected")
    return validated


def _role_tuple(values: tuple[ExpertPerspectiveRole, ...]) -> tuple[ExpertPerspectiveRole, ...]:
    if len(set(values)) != len(values):
        raise ValueError("duplicate perspective roles rejected")
    return tuple(values)


def _risk_tuple(values: tuple[CaseRiskClass, ...]) -> tuple[CaseRiskClass, ...]:
    if len(set(values)) != len(values):
        raise ValueError("duplicate risk classes rejected")
    return tuple(sorted(values, key=lambda item: item.value))


def _confidence(value: Decimal) -> Decimal:
    score = quantize_score(value)
    if score < Decimal("0.000000") or score > Decimal("1.000000"):
        raise ValueError("confidence must be between zero and one")
    return score


class DomainSpecialty(BaseModel):
    """Explicit specialty belonging to a taxonomy domain."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-domain-taxonomy/v1"] = DOMAIN_TAXONOMY_SCHEMA_VERSION
    specialty_id: str
    domain_id: str
    label: str = Field(max_length=80)
    specialty_fingerprint: str
    runtime_effect: Literal[False] = False

    @field_validator("specialty_id", "domain_id")
    @classmethod
    def ids_are_safe(cls, value: str) -> str:
        return validate_mesh_identifier(value, "domain specialty identifier")

    @field_validator("label")
    @classmethod
    def label_is_safe(cls, value: str) -> str:
        return validate_mesh_text(value, "domain specialty label")

    @field_validator("specialty_fingerprint")
    @classmethod
    def fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "domain specialty fingerprint")

    @model_validator(mode="after")
    def fingerprint_matches(self) -> Self:
        if self.specialty_fingerprint != domain_specialty_fingerprint(self):
            raise ValueError("domain specialty fingerprint mismatch")
        return self


def domain_specialty_fingerprint(specialty: DomainSpecialty | dict[str, Any]) -> str:
    return domain_mesh_fingerprint(specialty, "specialty_fingerprint")


class DomainTaxonomyNode(BaseModel):
    """Explicit taxonomy node without embedded domain knowledge."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-domain-taxonomy/v1"] = DOMAIN_TAXONOMY_SCHEMA_VERSION
    domain_id: str
    label: str = Field(max_length=80)
    parent_domain_id: str | None = None
    specialty_ids: tuple[str, ...] = Field(
        default_factory=tuple, max_length=MAXIMUM_SPECIALTIES_PER_CASE
    )
    node_fingerprint: str
    explicit_safe_ids: Literal[True] = True
    deterministic_hierarchy: Literal[True] = True
    network_ontology_lookup_enabled: Literal[False] = False
    model_generated_domain: Literal[False] = False
    universal_wildcard_domain: Literal[False] = False
    runtime_effect: Literal[False] = False

    @field_validator("domain_id", "parent_domain_id")
    @classmethod
    def ids_are_safe(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return validate_mesh_identifier(value, "domain taxonomy identifier")

    @field_validator("specialty_ids")
    @classmethod
    def specialty_ids_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return _safe_id_tuple(
            value, "domain taxonomy specialty", max_length=MAXIMUM_SPECIALTIES_PER_CASE
        )

    @field_validator("label")
    @classmethod
    def label_is_safe(cls, value: str) -> str:
        return validate_mesh_text(value, "domain taxonomy label")

    @field_validator("node_fingerprint")
    @classmethod
    def fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "domain taxonomy node fingerprint")

    @model_validator(mode="after")
    def node_is_valid(self) -> Self:
        if self.parent_domain_id == self.domain_id:
            raise ValueError("domain taxonomy self-parent rejected")
        if self.node_fingerprint != domain_taxonomy_node_fingerprint(self):
            raise ValueError("domain taxonomy node fingerprint mismatch")
        return self


def domain_taxonomy_node_fingerprint(node: DomainTaxonomyNode | dict[str, Any]) -> str:
    return domain_mesh_fingerprint(node, "node_fingerprint")


class DomainTaxonomy(BaseModel):
    """Versioned deterministic taxonomy used only for explicit routing."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-domain-taxonomy/v1"] = DOMAIN_TAXONOMY_SCHEMA_VERSION
    taxonomy_version: Literal["domain-taxonomy-v1"] = "domain-taxonomy-v1"
    nodes: tuple[DomainTaxonomyNode, ...]
    specialties: tuple[DomainSpecialty, ...]
    top_level_domain_ids: tuple[str, ...] = Field(max_length=MAXIMUM_DOMAINS_PER_CASE)
    taxonomy_fingerprint: str
    dynamic_domain_creation_enabled: Literal[False] = False
    model_generated_domain_enabled: Literal[False] = False
    embedding_classification_enabled: Literal[False] = False
    universal_wildcard_domain_enabled: Literal[False] = False
    runtime_effect: Literal[False] = False

    @field_validator("top_level_domain_ids")
    @classmethod
    def top_level_ids_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return _safe_id_tuple(
            value, "taxonomy top-level domain", max_length=MAXIMUM_DOMAINS_PER_CASE
        )

    @field_validator("taxonomy_fingerprint")
    @classmethod
    def fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "domain taxonomy fingerprint")

    @model_validator(mode="after")
    def taxonomy_is_valid(self) -> Self:
        node_ids = tuple(node.domain_id for node in self.nodes)
        if node_ids != tuple(sorted(node_ids)):
            raise ValueError("domain taxonomy nodes must use deterministic order")
        if len(set(node_ids)) != len(node_ids):
            raise ValueError("duplicate taxonomy nodes rejected")
        if set(self.top_level_domain_ids) - set(node_ids):
            raise ValueError("top-level domain must resolve")
        specialty_ids = tuple(specialty.specialty_id for specialty in self.specialties)
        if len(set(specialty_ids)) != len(specialty_ids):
            raise ValueError("duplicate taxonomy specialties rejected")
        for specialty in self.specialties:
            if specialty.domain_id not in node_ids:
                raise ValueError("taxonomy specialty orphan rejected")
        for node in self.nodes:
            if node.parent_domain_id is not None and node.parent_domain_id not in node_ids:
                raise ValueError("taxonomy orphan parent rejected")
            if set(node.specialty_ids) - set(specialty_ids):
                raise ValueError("taxonomy node specialty reference rejected")
        if _has_taxonomy_cycle(self.nodes):
            raise ValueError("taxonomy cycle rejected")
        if self.taxonomy_fingerprint != domain_taxonomy_fingerprint(self):
            raise ValueError("domain taxonomy fingerprint mismatch")
        return self


def _has_taxonomy_cycle(nodes: tuple[DomainTaxonomyNode, ...]) -> bool:
    parents = {node.domain_id: node.parent_domain_id for node in nodes}
    for node_id in parents:
        seen: set[str] = set()
        current: str | None = node_id
        while current is not None:
            if current in seen:
                return True
            seen.add(current)
            current = parents.get(current)
    return False


def domain_taxonomy_fingerprint(taxonomy: DomainTaxonomy | dict[str, Any]) -> str:
    return domain_mesh_fingerprint(taxonomy, "taxonomy_fingerprint")


class ExpertCapabilityScope(BaseModel):
    """Explicit capability scope for one computational profile."""

    model_config = FROZEN_MODEL_CONFIG

    domain_ids: tuple[str, ...] = Field(max_length=MAXIMUM_DOMAINS_PER_CASE)
    specialty_ids: tuple[str, ...] = Field(
        default_factory=tuple, max_length=MAXIMUM_SPECIALTIES_PER_CASE
    )
    jurisdiction_ids: tuple[str, ...] = Field(
        default_factory=tuple, max_length=MAXIMUM_SPECIALTIES_PER_CASE
    )
    version_target_ids: tuple[str, ...] = Field(
        default_factory=tuple, max_length=MAXIMUM_SPECIALTIES_PER_CASE
    )
    supported_risk_classes: tuple[CaseRiskClass, ...]
    perspective_roles: tuple[ExpertPerspectiveRole, ...]
    temporal_scope_required: bool = False
    runtime_effect: Literal[False] = False

    @field_validator("domain_ids")
    @classmethod
    def domain_ids_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return _safe_id_tuple(value, "expert scope domain", max_length=MAXIMUM_DOMAINS_PER_CASE)

    @field_validator("specialty_ids", "jurisdiction_ids", "version_target_ids")
    @classmethod
    def scope_ids_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return _safe_id_tuple(
            value, "expert scope identifier", max_length=MAXIMUM_SPECIALTIES_PER_CASE
        )

    @field_validator("supported_risk_classes")
    @classmethod
    def risks_are_unique(cls, value: tuple[CaseRiskClass, ...]) -> tuple[CaseRiskClass, ...]:
        return _risk_tuple(value)

    @field_validator("perspective_roles")
    @classmethod
    def roles_are_unique(
        cls, value: tuple[ExpertPerspectiveRole, ...]
    ) -> tuple[ExpertPerspectiveRole, ...]:
        return _role_tuple(value)


class DomainExpertProfile(BaseModel):
    """Computational expert profile with no human identity or runtime effect."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-domain-expert-profile/v1"] = (
        DOMAIN_EXPERT_PROFILE_SCHEMA_VERSION
    )
    profile_id: str
    profile_version: Literal["profile-v1"] = "profile-v1"
    domain_ids: tuple[str, ...] = Field(max_length=MAXIMUM_DOMAINS_PER_CASE)
    specialty_ids: tuple[str, ...] = Field(
        default_factory=tuple, max_length=MAXIMUM_SPECIALTIES_PER_CASE
    )
    perspective_roles: tuple[ExpertPerspectiveRole, ...]
    jurisdiction_ids: tuple[str, ...] = Field(
        default_factory=tuple, max_length=MAXIMUM_SPECIALTIES_PER_CASE
    )
    version_target_ids: tuple[str, ...] = Field(
        default_factory=tuple, max_length=MAXIMUM_SPECIALTIES_PER_CASE
    )
    supported_risk_classes: tuple[CaseRiskClass, ...]
    independence_group_id: str
    required_input_kinds: tuple[str, ...]
    prohibited_input_kinds: tuple[str, ...]
    capability_scope: ExpertCapabilityScope
    profile_fingerprint: str
    computational_profile: Literal[True] = True
    human_identity_claimed: Literal[False] = False
    human_expert_impersonation: Literal[False] = False
    professional_credential_claimed: Literal[False] = False
    licensed_professional_claimed: Literal[False] = False
    model_provider_required: Literal[False] = False
    tool_execution_required: Literal[False] = False
    network_access_required: Literal[False] = False
    runtime_effect: Literal[False] = False

    @field_validator("profile_id", "independence_group_id")
    @classmethod
    def ids_are_safe(cls, value: str) -> str:
        return validate_mesh_identifier(value, "domain expert profile identifier")

    @field_validator("domain_ids")
    @classmethod
    def domain_ids_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return _safe_id_tuple(
            value, "domain expert profile domain", max_length=MAXIMUM_DOMAINS_PER_CASE
        )

    @field_validator("specialty_ids", "jurisdiction_ids", "version_target_ids")
    @classmethod
    def ids_tuple_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return _safe_id_tuple(
            value, "domain expert profile scope", max_length=MAXIMUM_SPECIALTIES_PER_CASE
        )

    @field_validator("required_input_kinds", "prohibited_input_kinds")
    @classmethod
    def input_kinds_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return _safe_id_tuple(
            value, "domain expert profile input kind", max_length=MAXIMUM_REASON_CODES_PER_REPORT
        )

    @field_validator("perspective_roles")
    @classmethod
    def roles_are_unique(
        cls, value: tuple[ExpertPerspectiveRole, ...]
    ) -> tuple[ExpertPerspectiveRole, ...]:
        return _role_tuple(value)

    @field_validator("supported_risk_classes")
    @classmethod
    def risks_are_unique(cls, value: tuple[CaseRiskClass, ...]) -> tuple[CaseRiskClass, ...]:
        return _risk_tuple(value)

    @field_validator("profile_fingerprint")
    @classmethod
    def fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "domain expert profile fingerprint")

    @model_validator(mode="after")
    def profile_is_safe(self) -> Self:
        if self.capability_scope.domain_ids != self.domain_ids:
            raise ValueError("profile capability domain scope mismatch")
        if self.capability_scope.specialty_ids != self.specialty_ids:
            raise ValueError("profile capability specialty scope mismatch")
        if self.capability_scope.jurisdiction_ids != self.jurisdiction_ids:
            raise ValueError("profile capability jurisdiction scope mismatch")
        if self.capability_scope.version_target_ids != self.version_target_ids:
            raise ValueError("profile capability version scope mismatch")
        if self.capability_scope.supported_risk_classes != self.supported_risk_classes:
            raise ValueError("profile capability risk scope mismatch")
        if self.capability_scope.perspective_roles != self.perspective_roles:
            raise ValueError("profile capability role scope mismatch")
        if self.profile_fingerprint != domain_expert_profile_fingerprint(self):
            raise ValueError("domain expert profile fingerprint mismatch")
        return self


def domain_expert_profile_fingerprint(profile: DomainExpertProfile | dict[str, Any]) -> str:
    return domain_mesh_fingerprint(profile, "profile_fingerprint")


class DomainExpertProfileRegistry(BaseModel):
    """Immutable ordered profile registry."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-domain-expert-profile/v1"] = (
        DOMAIN_EXPERT_PROFILE_SCHEMA_VERSION
    )
    registry_version: Literal["domain-expert-profile-registry-v1"] = (
        "domain-expert-profile-registry-v1"
    )
    profiles: tuple[DomainExpertProfile, ...] = Field(max_length=MAXIMUM_EXPERT_PROFILES_CONSIDERED)
    registry_fingerprint: str
    computational_profiles_only: Literal[True] = True
    runtime_effect: Literal[False] = False

    @field_validator("registry_fingerprint")
    @classmethod
    def fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "domain expert profile registry fingerprint")

    @model_validator(mode="after")
    def registry_is_valid(self) -> Self:
        profile_ids = tuple(profile.profile_id for profile in self.profiles)
        if profile_ids != tuple(sorted(profile_ids)):
            raise ValueError("domain expert profiles must use deterministic order")
        if len(set(profile_ids)) != len(profile_ids):
            raise ValueError("duplicate profile IDs rejected")
        if any(not profile.computational_profile for profile in self.profiles):
            raise ValueError("profile registry allows computational profiles only")
        if any(profile.human_identity_claimed for profile in self.profiles):
            raise ValueError("profile human identity claim rejected")
        if any(profile.professional_credential_claimed for profile in self.profiles):
            raise ValueError("profile professional credential claim rejected")
        if self.registry_fingerprint != domain_expert_profile_registry_fingerprint(self):
            raise ValueError("domain expert profile registry fingerprint mismatch")
        return self


def domain_expert_profile_registry_fingerprint(
    registry: DomainExpertProfileRegistry | dict[str, Any],
) -> str:
    return domain_mesh_fingerprint(registry, "registry_fingerprint")


class DomainExpertCase(BaseModel):
    """Explicitly tagged advisory case."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-domain-expert-case/v1"] = (
        DOMAIN_EXPERT_CASE_SCHEMA_VERSION
    )
    case_id: str
    question_summary: str = Field(max_length=240)
    claim_ids: tuple[str, ...] = Field(min_length=1, max_length=MAXIMUM_CLAIMS_PER_CASE)
    epistemic_assessment_ids: tuple[str, ...] = Field(
        min_length=1,
        max_length=MAXIMUM_EPISTEMIC_ASSESSMENTS_PER_CASE,
    )
    domain_ids: tuple[str, ...] = Field(min_length=1, max_length=MAXIMUM_DOMAINS_PER_CASE)
    specialty_ids: tuple[str, ...] = Field(
        default_factory=tuple, max_length=MAXIMUM_SPECIALTIES_PER_CASE
    )
    target_valid_time: datetime | None = None
    target_jurisdiction_ids: tuple[str, ...] = Field(
        default_factory=tuple, max_length=MAXIMUM_SPECIALTIES_PER_CASE
    )
    target_version_ids: tuple[str, ...] = Field(
        default_factory=tuple, max_length=MAXIMUM_SPECIALTIES_PER_CASE
    )
    risk_class: CaseRiskClass
    explicit_subquestions: tuple[str, ...] = Field(
        default_factory=tuple,
        max_length=MAXIMUM_SUBQUESTIONS_PER_CASE,
    )
    operator_supplied: Literal[True] = True
    synthetic: bool
    read_only: Literal[True] = True
    redacted: Literal[True] = True
    advisory_only: Literal[True] = True
    case_fingerprint: str
    runtime_effect: Literal[False] = False

    @field_validator("case_id")
    @classmethod
    def case_id_is_safe(cls, value: str) -> str:
        return validate_mesh_identifier(value, "domain expert case identifier")

    @field_validator("question_summary")
    @classmethod
    def summary_is_safe(cls, value: str) -> str:
        return validate_mesh_text(value, "domain expert case summary")

    @field_validator("claim_ids")
    @classmethod
    def claim_ids_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return _safe_id_tuple(value, "domain expert case claim", max_length=MAXIMUM_CLAIMS_PER_CASE)

    @field_validator("epistemic_assessment_ids")
    @classmethod
    def assessment_ids_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return _safe_id_tuple(
            value,
            "domain expert case assessment",
            max_length=MAXIMUM_EPISTEMIC_ASSESSMENTS_PER_CASE,
        )

    @field_validator("domain_ids")
    @classmethod
    def domain_ids_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return _safe_id_tuple(
            value, "domain expert case domain", max_length=MAXIMUM_DOMAINS_PER_CASE
        )

    @field_validator("specialty_ids", "target_jurisdiction_ids", "target_version_ids")
    @classmethod
    def scope_ids_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return _safe_id_tuple(
            value, "domain expert case scope", max_length=MAXIMUM_SPECIALTIES_PER_CASE
        )

    @field_validator("target_valid_time")
    @classmethod
    def target_valid_time_is_utc(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return value
        return ensure_utc(value, "domain expert case target_valid_time")

    @field_validator("explicit_subquestions")
    @classmethod
    def subquestions_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if len(set(value)) != len(value):
            raise ValueError("duplicate explicit subquestions rejected")
        return tuple(validate_mesh_text(item, "domain expert case subquestion") for item in value)

    @field_validator("case_fingerprint")
    @classmethod
    def fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "domain expert case fingerprint")

    @model_validator(mode="after")
    def case_is_valid(self) -> Self:
        if self.case_fingerprint != domain_expert_case_fingerprint(self):
            raise ValueError("domain expert case fingerprint mismatch")
        return self


def domain_expert_case_fingerprint(case: DomainExpertCase | dict[str, Any]) -> str:
    return domain_mesh_fingerprint(case, "case_fingerprint")


class ExpertSubquestion(BaseModel):
    """Deterministic subquestion over explicit case metadata."""

    model_config = FROZEN_MODEL_CONFIG

    subquestion_id: str
    case_id: str
    category: str
    perspective_role: ExpertPerspectiveRole
    domain_ids: tuple[str, ...] = Field(max_length=MAXIMUM_DOMAINS_PER_CASE)
    specialty_ids: tuple[str, ...] = Field(max_length=MAXIMUM_SPECIALTIES_PER_CASE)
    claim_ids: tuple[str, ...] = Field(max_length=MAXIMUM_CLAIMS_PER_CASE)
    assessment_ids: tuple[str, ...] = Field(max_length=MAXIMUM_EPISTEMIC_ASSESSMENTS_PER_CASE)
    subquestion_fingerprint: str
    runtime_effect: Literal[False] = False

    @field_validator("subquestion_id", "case_id", "category")
    @classmethod
    def ids_are_safe(cls, value: str) -> str:
        return validate_mesh_identifier(value, "expert subquestion identifier")

    @field_validator("domain_ids")
    @classmethod
    def domain_ids_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return _safe_id_tuple(
            value, "expert subquestion domain", max_length=MAXIMUM_DOMAINS_PER_CASE
        )

    @field_validator("specialty_ids")
    @classmethod
    def specialty_ids_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return _safe_id_tuple(
            value, "expert subquestion specialty", max_length=MAXIMUM_SPECIALTIES_PER_CASE
        )

    @field_validator("claim_ids")
    @classmethod
    def claim_ids_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return _safe_id_tuple(value, "expert subquestion claim", max_length=MAXIMUM_CLAIMS_PER_CASE)

    @field_validator("assessment_ids")
    @classmethod
    def assessment_ids_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return _safe_id_tuple(
            value,
            "expert subquestion assessment",
            max_length=MAXIMUM_EPISTEMIC_ASSESSMENTS_PER_CASE,
        )

    @field_validator("subquestion_fingerprint")
    @classmethod
    def fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "expert subquestion fingerprint")

    @model_validator(mode="after")
    def fingerprint_matches(self) -> Self:
        if self.subquestion_fingerprint != expert_subquestion_fingerprint(self):
            raise ValueError("expert subquestion fingerprint mismatch")
        return self


def expert_subquestion_fingerprint(subquestion: ExpertSubquestion | dict[str, Any]) -> str:
    return domain_mesh_fingerprint(subquestion, "subquestion_fingerprint")


class ExpertSubquestionPlan(BaseModel):
    """Bounded deterministic decomposition plan."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-expert-panel-plan/v1"] = (
        EXPERT_PANEL_PLAN_SCHEMA_VERSION
    )
    plan_id: str
    case_id: str
    subquestions: tuple[ExpertSubquestion, ...] = Field(max_length=MAXIMUM_SUBQUESTIONS_PER_CASE)
    subquestion_count: int = Field(ge=0, le=MAXIMUM_SUBQUESTIONS_PER_CASE)
    decomposition_policy_fingerprint: str
    plan_fingerprint: str
    model_inference_used: Literal[False] = False
    external_research_requested: Literal[False] = False
    runtime_effect: Literal[False] = False

    @field_validator("plan_id", "case_id")
    @classmethod
    def ids_are_safe(cls, value: str) -> str:
        return validate_mesh_identifier(value, "expert subquestion plan identifier")

    @field_validator("decomposition_policy_fingerprint", "plan_fingerprint")
    @classmethod
    def fingerprints_are_hex(cls, value: str) -> str:
        return validate_hex64(value, "expert subquestion plan fingerprint")

    @model_validator(mode="after")
    def plan_is_valid(self) -> Self:
        if self.subquestion_count != len(self.subquestions):
            raise ValueError("subquestion_count must match subquestions")
        if self.plan_fingerprint != expert_subquestion_plan_fingerprint(self):
            raise ValueError("expert subquestion plan fingerprint mismatch")
        return self


def expert_subquestion_plan_fingerprint(plan: ExpertSubquestionPlan | dict[str, Any]) -> str:
    return domain_mesh_fingerprint(plan, "plan_fingerprint")


class ExpertAssignment(BaseModel):
    """One profile assignment to one required or optional role."""

    model_config = FROZEN_MODEL_CONFIG

    assignment_id: str
    profile_id: str
    perspective_role: ExpertPerspectiveRole
    independence_group_id: str
    domain_match_ids: tuple[str, ...] = Field(
        default_factory=tuple, max_length=MAXIMUM_DOMAINS_PER_CASE
    )
    specialty_match_ids: tuple[str, ...] = Field(
        default_factory=tuple, max_length=MAXIMUM_SPECIALTIES_PER_CASE
    )
    jurisdiction_match_ids: tuple[str, ...] = Field(
        default_factory=tuple, max_length=MAXIMUM_SPECIALTIES_PER_CASE
    )
    version_match_ids: tuple[str, ...] = Field(
        default_factory=tuple, max_length=MAXIMUM_SPECIALTIES_PER_CASE
    )
    temporal_scope_match: bool
    risk_class_match: bool
    required_role: bool
    assignment_fingerprint: str
    runtime_effect: Literal[False] = False

    @field_validator("assignment_id", "profile_id", "independence_group_id")
    @classmethod
    def ids_are_safe(cls, value: str) -> str:
        return validate_mesh_identifier(value, "expert assignment identifier")

    @field_validator(
        "domain_match_ids",
        "specialty_match_ids",
        "jurisdiction_match_ids",
        "version_match_ids",
    )
    @classmethod
    def match_ids_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return _safe_id_tuple(
            value, "expert assignment match", max_length=MAXIMUM_SPECIALTIES_PER_CASE
        )

    @field_validator("assignment_fingerprint")
    @classmethod
    def fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "expert assignment fingerprint")

    @model_validator(mode="after")
    def assignment_is_valid(self) -> Self:
        if self.assignment_fingerprint != expert_assignment_fingerprint(self):
            raise ValueError("expert assignment fingerprint mismatch")
        return self


def expert_assignment_fingerprint(assignment: ExpertAssignment | dict[str, Any]) -> str:
    return domain_mesh_fingerprint(assignment, "assignment_fingerprint")


class ExpertPanelPlan(BaseModel):
    """Deterministic expert panel plan."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-expert-panel-plan/v1"] = (
        EXPERT_PANEL_PLAN_SCHEMA_VERSION
    )
    panel_id: str
    case_id: str
    assignments: tuple[ExpertAssignment, ...] = Field(max_length=MAXIMUM_PANEL_SIZE)
    required_roles: tuple[ExpertPerspectiveRole, ...] = Field(
        max_length=MAXIMUM_REQUIRED_ROLES_PER_PANEL
    )
    optional_roles: tuple[ExpertPerspectiveRole, ...] = Field(default_factory=tuple)
    missing_required_roles: tuple[ExpertPerspectiveRole, ...] = Field(default_factory=tuple)
    panel_size: int = Field(ge=0, le=MAXIMUM_PANEL_SIZE)
    independence_group_count: int = Field(ge=0, le=MAXIMUM_PANEL_SIZE)
    routing_reason_codes: tuple[str, ...]
    routing_policy_fingerprint: str
    panel_fingerprint: str
    operator_review_required: bool
    explicit_abstention_required: bool
    maximum_panel_size: Literal[12] = MAXIMUM_PANEL_SIZE
    panel_size_confidence_amplification_enabled: Literal[False] = False
    majority_alignment_establishes_truth: Literal[False] = False
    dissent_preservation_required: Literal[True] = True
    self_review_rejected: Literal[True] = True
    circular_critique_rejected: Literal[True] = True
    runtime_effect: Literal[False] = False

    @field_validator("panel_id", "case_id")
    @classmethod
    def ids_are_safe(cls, value: str) -> str:
        return validate_mesh_identifier(value, "expert panel identifier")

    @field_validator("required_roles", "optional_roles", "missing_required_roles")
    @classmethod
    def roles_are_unique(
        cls, value: tuple[ExpertPerspectiveRole, ...]
    ) -> tuple[ExpertPerspectiveRole, ...]:
        return _role_tuple(value)

    @field_validator("routing_reason_codes")
    @classmethod
    def reason_codes_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_mesh_reason_codes(value)

    @field_validator("routing_policy_fingerprint", "panel_fingerprint")
    @classmethod
    def fingerprints_are_hex(cls, value: str) -> str:
        return validate_hex64(value, "expert panel fingerprint")

    @model_validator(mode="after")
    def panel_is_valid(self) -> Self:
        if self.panel_size != len(self.assignments):
            raise ValueError("panel_size must match assignments")
        if self.independence_group_count != len(
            {item.independence_group_id for item in self.assignments}
        ):
            raise ValueError("independence_group_count mismatch")
        if len({item.profile_id for item in self.assignments}) != len(self.assignments):
            raise ValueError("duplicate panel profile IDs rejected")
        if set(self.missing_required_roles) - set(self.required_roles):
            raise ValueError("missing role must be required")
        assigned_required = {
            item.perspective_role for item in self.assignments if item.required_role
        }
        if set(self.required_roles) - assigned_required != set(self.missing_required_roles):
            raise ValueError("missing required roles mismatch")
        if self.panel_fingerprint != expert_panel_plan_fingerprint(self):
            raise ValueError("expert panel fingerprint mismatch")
        return self


def expert_panel_plan_fingerprint(plan: ExpertPanelPlan | dict[str, Any]) -> str:
    return domain_mesh_fingerprint(plan, "panel_fingerprint")


class ExpertPerspectiveReport(BaseModel):
    """Immutable evidence-bound computational report."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-expert-perspective-report/v1"] = (
        EXPERT_PERSPECTIVE_REPORT_SCHEMA_VERSION
    )
    report_id: str
    case_id: str
    panel_id: str
    profile_id: str
    assignment_id: str
    perspective_role: ExpertPerspectiveRole
    claim_ids: tuple[str, ...] = Field(max_length=MAXIMUM_CLAIMS_PER_CASE)
    assessment_ids: tuple[str, ...] = Field(max_length=MAXIMUM_EPISTEMIC_ASSESSMENTS_PER_CASE)
    evidence_reference_ids: tuple[str, ...] = Field(
        max_length=MAXIMUM_EVIDENCE_REFERENCES_PER_REPORT
    )
    finding_codes: tuple[str, ...] = Field(max_length=MAXIMUM_REASON_CODES_PER_REPORT)
    assumption_codes: tuple[str, ...] = Field(
        default_factory=tuple, max_length=MAXIMUM_REASON_CODES_PER_REPORT
    )
    limitation_codes: tuple[str, ...] = Field(
        default_factory=tuple, max_length=MAXIMUM_REASON_CODES_PER_REPORT
    )
    evidence_gap_codes: tuple[str, ...] = Field(
        default_factory=tuple, max_length=MAXIMUM_REASON_CODES_PER_REPORT
    )
    position: ExpertReportPosition
    underlying_assessment_confidence_cap: Decimal
    report_confidence_cap: Decimal
    explicit_abstention: bool
    report_fingerprint: str
    computational_profile: Literal[True] = True
    human_authored: Literal[False] = False
    human_identity_claimed: Literal[False] = False
    professional_credential_claimed: Literal[False] = False
    truth_decision: Literal[False] = False
    claim_accepted: Literal[False] = False
    claim_rejected: Literal[False] = False
    knowledge_promoted: Literal[False] = False
    belief_mutated: Literal[False] = False
    automatic_action: Literal[False] = False
    runtime_effect: Literal[False] = False

    @field_validator("report_id", "case_id", "panel_id", "profile_id", "assignment_id")
    @classmethod
    def ids_are_safe(cls, value: str) -> str:
        return validate_mesh_identifier(value, "expert report identifier")

    @field_validator("claim_ids")
    @classmethod
    def claim_ids_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return _safe_id_tuple(value, "expert report claim", max_length=MAXIMUM_CLAIMS_PER_CASE)

    @field_validator("assessment_ids", "evidence_reference_ids")
    @classmethod
    def reference_ids_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return _safe_id_tuple(
            value,
            "expert report reference",
            max_length=MAXIMUM_EPISTEMIC_ASSESSMENTS_PER_CASE,
        )

    @field_validator("finding_codes", "assumption_codes", "limitation_codes", "evidence_gap_codes")
    @classmethod
    def reason_codes_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_mesh_reason_codes(value)

    @field_validator("underlying_assessment_confidence_cap", "report_confidence_cap")
    @classmethod
    def confidence_is_quantized(cls, value: Decimal) -> Decimal:
        return _confidence(value)

    @field_validator("report_fingerprint")
    @classmethod
    def fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "expert report fingerprint")

    @model_validator(mode="after")
    def report_is_valid(self) -> Self:
        if self.report_confidence_cap > self.underlying_assessment_confidence_cap:
            raise ValueError("expert report confidence must not exceed underlying cap")
        if self.report_fingerprint != expert_perspective_report_fingerprint(self):
            raise ValueError("expert report fingerprint mismatch")
        return self


def expert_perspective_report_fingerprint(report: ExpertPerspectiveReport | dict[str, Any]) -> str:
    return domain_mesh_fingerprint(report, "report_fingerprint")


class ExpertCritique(BaseModel):
    """Cross-examination critique that preserves the target report."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-expert-critique/v1"] = EXPERT_CRITIQUE_SCHEMA_VERSION
    critique_id: str
    case_id: str
    panel_id: str
    critic_profile_id: str
    target_profile_id: str
    target_report_id: str
    deliberation_round: int = Field(ge=1, le=MAXIMUM_DELIBERATION_ROUNDS)
    issue_codes: tuple[str, ...] = Field(max_length=MAXIMUM_REASON_CODES_PER_REPORT)
    unsupported_reference_ids: tuple[str, ...] = Field(default_factory=tuple)
    methodology_issue_codes: tuple[str, ...] = Field(default_factory=tuple)
    scope_issue_codes: tuple[str, ...] = Field(default_factory=tuple)
    critique_fingerprint: str
    target_report_preserved: Literal[True] = True
    confidence_increased: Literal[False] = False
    runtime_effect: Literal[False] = False

    @field_validator(
        "critique_id",
        "case_id",
        "panel_id",
        "critic_profile_id",
        "target_profile_id",
        "target_report_id",
    )
    @classmethod
    def ids_are_safe(cls, value: str) -> str:
        return validate_mesh_identifier(value, "expert critique identifier")

    @field_validator("issue_codes", "methodology_issue_codes", "scope_issue_codes")
    @classmethod
    def reason_codes_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_mesh_reason_codes(value)

    @field_validator("unsupported_reference_ids")
    @classmethod
    def references_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return _safe_id_tuple(
            value, "expert critique reference", max_length=MAXIMUM_EVIDENCE_REFERENCES_PER_REPORT
        )

    @field_validator("critique_fingerprint")
    @classmethod
    def fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "expert critique fingerprint")

    @model_validator(mode="after")
    def critique_is_valid(self) -> Self:
        if self.critic_profile_id == self.target_profile_id:
            raise ValueError("self-review rejected")
        if self.critique_fingerprint != expert_critique_fingerprint(self):
            raise ValueError("expert critique fingerprint mismatch")
        return self


def expert_critique_fingerprint(critique: ExpertCritique | dict[str, Any]) -> str:
    return domain_mesh_fingerprint(critique, "critique_fingerprint")


class ExpertCritiqueResponse(BaseModel):
    """Response that preserves the critique and cannot rewrite reports."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-expert-critique-response/v1"] = (
        EXPERT_CRITIQUE_RESPONSE_SCHEMA_VERSION
    )
    response_id: str
    critique_id: str
    respondent_profile_id: str
    response_code: Literal["acknowledge", "qualify", "retain_disagreement"]
    retained_disagreement: bool
    response_fingerprint: str
    critique_preserved: Literal[True] = True
    report_rewritten: Literal[False] = False
    confidence_increased: Literal[False] = False
    runtime_effect: Literal[False] = False

    @field_validator("response_id", "critique_id", "respondent_profile_id")
    @classmethod
    def ids_are_safe(cls, value: str) -> str:
        return validate_mesh_identifier(value, "expert critique response identifier")

    @field_validator("response_fingerprint")
    @classmethod
    def fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "expert critique response fingerprint")

    @model_validator(mode="after")
    def response_is_valid(self) -> Self:
        if self.response_fingerprint != expert_critique_response_fingerprint(self):
            raise ValueError("expert critique response fingerprint mismatch")
        return self


def expert_critique_response_fingerprint(
    response: ExpertCritiqueResponse | dict[str, Any],
) -> str:
    return domain_mesh_fingerprint(response, "response_fingerprint")


class ExpertDisagreementItem(BaseModel):
    """One preserved disagreement dimension."""

    model_config = FROZEN_MODEL_CONFIG

    disagreement_id: str
    disagreement_type: DisagreementType
    report_ids: tuple[str, ...] = Field(min_length=1, max_length=MAXIMUM_EXPERT_REPORTS_PER_CASE)
    critique_ids: tuple[str, ...] = Field(
        default_factory=tuple, max_length=MAXIMUM_CRITIQUES_PER_CASE
    )
    position_values: tuple[ExpertReportPosition, ...] = Field(default_factory=tuple)
    reason_codes: tuple[str, ...]
    material: bool
    disagreement_fingerprint: str
    truth_value_assigned: Literal[False] = False
    winner_declared: Literal[False] = False
    runtime_effect: Literal[False] = False

    @field_validator("disagreement_id")
    @classmethod
    def disagreement_id_is_safe(cls, value: str) -> str:
        return validate_mesh_identifier(value, "expert disagreement identifier")

    @field_validator("report_ids", "critique_ids")
    @classmethod
    def reference_ids_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return _safe_id_tuple(
            value, "expert disagreement reference", max_length=MAXIMUM_CRITIQUES_PER_CASE
        )

    @field_validator("position_values")
    @classmethod
    def positions_are_unique(
        cls, value: tuple[ExpertReportPosition, ...]
    ) -> tuple[ExpertReportPosition, ...]:
        if len(set(value)) != len(value):
            raise ValueError("duplicate disagreement positions rejected")
        return tuple(sorted(value, key=lambda item: item.value))

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_mesh_reason_codes(value)

    @field_validator("disagreement_fingerprint")
    @classmethod
    def fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "expert disagreement fingerprint")

    @model_validator(mode="after")
    def disagreement_is_valid(self) -> Self:
        if self.disagreement_fingerprint != expert_disagreement_item_fingerprint(self):
            raise ValueError("expert disagreement fingerprint mismatch")
        return self


def expert_disagreement_item_fingerprint(item: ExpertDisagreementItem | dict[str, Any]) -> str:
    return domain_mesh_fingerprint(item, "disagreement_fingerprint")


class ExpertDisagreementMatrix(BaseModel):
    """Deterministic bounded disagreement matrix."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-expert-disagreement-matrix/v1"] = (
        EXPERT_DISAGREEMENT_MATRIX_SCHEMA_VERSION
    )
    matrix_id: str
    case_id: str
    panel_id: str
    disagreements: tuple[ExpertDisagreementItem, ...] = Field(
        max_length=MAXIMUM_DISAGREEMENT_ITEMS_PER_CASE
    )
    disagreement_count: int = Field(ge=0, le=MAXIMUM_DISAGREEMENT_ITEMS_PER_CASE)
    preserved_report_ids: tuple[str, ...] = Field(max_length=MAXIMUM_EXPERT_REPORTS_PER_CASE)
    preserved_critique_ids: tuple[str, ...] = Field(max_length=MAXIMUM_CRITIQUES_PER_CASE)
    dissent_preserved: Literal[True] = True
    matrix_fingerprint: str
    runtime_effect: Literal[False] = False

    @field_validator("matrix_id", "case_id", "panel_id")
    @classmethod
    def ids_are_safe(cls, value: str) -> str:
        return validate_mesh_identifier(value, "expert disagreement matrix identifier")

    @field_validator("preserved_report_ids", "preserved_critique_ids")
    @classmethod
    def reference_ids_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return _safe_id_tuple(
            value, "expert disagreement matrix reference", max_length=MAXIMUM_CRITIQUES_PER_CASE
        )

    @field_validator("matrix_fingerprint")
    @classmethod
    def fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "expert disagreement matrix fingerprint")

    @model_validator(mode="after")
    def matrix_is_valid(self) -> Self:
        if self.disagreement_count != len(self.disagreements):
            raise ValueError("disagreement_count must match disagreements")
        if self.matrix_fingerprint != expert_disagreement_matrix_fingerprint(self):
            raise ValueError("expert disagreement matrix fingerprint mismatch")
        return self


def expert_disagreement_matrix_fingerprint(
    matrix: ExpertDisagreementMatrix | dict[str, Any],
) -> str:
    return domain_mesh_fingerprint(matrix, "matrix_fingerprint")


class ExpertMeshSynthesis(BaseModel):
    """Bounded advisory synthesis that cannot amplify confidence."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-expert-mesh-synthesis/v1"] = (
        EXPERT_MESH_SYNTHESIS_SCHEMA_VERSION
    )
    synthesis_id: str
    case_id: str
    panel_id: str
    report_ids: tuple[str, ...] = Field(max_length=MAXIMUM_EXPERT_REPORTS_PER_CASE)
    critique_ids: tuple[str, ...] = Field(max_length=MAXIMUM_CRITIQUES_PER_CASE)
    disagreement_ids: tuple[str, ...] = Field(max_length=MAXIMUM_DISAGREEMENT_ITEMS_PER_CASE)
    alignment_state: PanelAlignmentState
    synthesis_codes: tuple[str, ...]
    evidence_gap_codes: tuple[str, ...] = Field(default_factory=tuple)
    unresolved_dissent_ids: tuple[str, ...] = Field(default_factory=tuple)
    underlying_assessment_confidence_cap: Decimal
    report_confidence_cap: Decimal
    synthesis_confidence_cap: Decimal
    explicit_abstention: bool
    operator_review_required: bool
    operator_escalation_recommended: bool
    synthesis_fingerprint: str
    confidence_amplified: Literal[False] = False
    truth_decision: Literal[False] = False
    claim_accepted: Literal[False] = False
    claim_rejected: Literal[False] = False
    automatic_action: Literal[False] = False
    knowledge_promoted: Literal[False] = False
    belief_mutated: Literal[False] = False
    runtime_effect: Literal[False] = False

    @field_validator("synthesis_id", "case_id", "panel_id")
    @classmethod
    def ids_are_safe(cls, value: str) -> str:
        return validate_mesh_identifier(value, "expert mesh synthesis identifier")

    @field_validator("report_ids", "critique_ids", "disagreement_ids", "unresolved_dissent_ids")
    @classmethod
    def reference_ids_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return _safe_id_tuple(
            value, "expert mesh synthesis reference", max_length=MAXIMUM_QUERY_RESULTS
        )

    @field_validator("synthesis_codes", "evidence_gap_codes")
    @classmethod
    def reason_codes_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_mesh_reason_codes(value)

    @field_validator(
        "underlying_assessment_confidence_cap",
        "report_confidence_cap",
        "synthesis_confidence_cap",
    )
    @classmethod
    def confidence_is_quantized(cls, value: Decimal) -> Decimal:
        return _confidence(value)

    @field_validator("synthesis_fingerprint")
    @classmethod
    def fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "expert mesh synthesis fingerprint")

    @model_validator(mode="after")
    def synthesis_is_valid(self) -> Self:
        if self.synthesis_confidence_cap > self.underlying_assessment_confidence_cap:
            raise ValueError("synthesis confidence must not exceed underlying cap")
        if self.synthesis_confidence_cap > self.report_confidence_cap:
            raise ValueError("synthesis confidence must not exceed report cap")
        if self.disagreement_ids and self.synthesis_confidence_cap > Decimal("0.650000"):
            raise ValueError("unresolved disagreement confidence cap exceeded")
        if self.synthesis_fingerprint != expert_mesh_synthesis_fingerprint(self):
            raise ValueError("expert mesh synthesis fingerprint mismatch")
        return self


def expert_mesh_synthesis_fingerprint(synthesis: ExpertMeshSynthesis | dict[str, Any]) -> str:
    return domain_mesh_fingerprint(synthesis, "synthesis_fingerprint")


class DomainExpertMeshIntegrityFinding(BaseModel):
    """Redacted integrity finding."""

    model_config = FROZEN_MODEL_CONFIG

    finding_id: str
    severity: Literal["low", "medium", "high", "critical"]
    reason_codes: tuple[str, ...]
    safe_ids: tuple[str, ...] = Field(default_factory=tuple)
    bounded_count: int | None = Field(default=None, ge=0)
    redacted_summary: str = Field(max_length=240)
    runtime_effect: Literal[False] = False

    @field_validator("finding_id")
    @classmethod
    def finding_id_is_safe(cls, value: str) -> str:
        return validate_mesh_identifier(value, "domain expert mesh finding")

    @field_validator("safe_ids")
    @classmethod
    def safe_ids_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return _safe_id_tuple(
            value, "domain expert mesh finding reference", max_length=MAXIMUM_QUERY_RESULTS
        )

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_mesh_reason_codes(value)

    @field_validator("redacted_summary")
    @classmethod
    def summary_is_safe(cls, value: str) -> str:
        return validate_mesh_text(value, "domain expert mesh finding summary")


class DomainExpertMeshIntegrityReport(BaseModel):
    """Integrity audit report for one mesh artifact."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-expert-mesh-integrity/v1"] = (
        EXPERT_MESH_INTEGRITY_SCHEMA_VERSION
    )
    report_id: str
    status: MeshIntegrityStatus
    finding_count: int = Field(ge=0)
    findings: tuple[DomainExpertMeshIntegrityFinding, ...] = Field(
        max_length=MAXIMUM_OPERATOR_REVIEW_ITEMS
    )
    reason_codes: tuple[str, ...]
    audit_timestamp: datetime
    report_fingerprint: str
    runtime_effect: Literal[False] = False

    @field_validator("report_id")
    @classmethod
    def report_id_is_safe(cls, value: str) -> str:
        return validate_mesh_identifier(value, "domain expert mesh integrity report")

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_mesh_reason_codes(value)

    @field_validator("audit_timestamp")
    @classmethod
    def audit_timestamp_is_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value, "domain expert mesh integrity audit timestamp")

    @field_validator("report_fingerprint")
    @classmethod
    def fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "domain expert mesh integrity report fingerprint")

    @model_validator(mode="after")
    def report_is_valid(self) -> Self:
        if self.finding_count != len(self.findings):
            raise ValueError("finding_count must match findings")
        if self.status == MeshIntegrityStatus.PASSED and self.findings:
            raise ValueError("passed integrity report must not contain findings")
        if self.report_fingerprint != domain_expert_mesh_integrity_report_fingerprint(self):
            raise ValueError("domain expert mesh integrity report fingerprint mismatch")
        return self


def domain_expert_mesh_integrity_report_fingerprint(
    report: DomainExpertMeshIntegrityReport | dict[str, Any],
) -> str:
    return domain_mesh_fingerprint(report, "report_fingerprint")


class DomainExpertMeshIncidentRecord(BaseModel):
    """Safe redacted incident evidence."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-expert-mesh-evidence/v1"] = (
        EXPERT_MESH_EVIDENCE_SCHEMA_VERSION
    )
    incident_id: str
    reason_codes: tuple[str, ...]
    severity: Literal["low", "medium", "high", "critical"]
    redacted_summary: str = Field(max_length=240)
    created_at: datetime
    incident_fingerprint: str
    runtime_effect: Literal[False] = False

    @field_validator("incident_id")
    @classmethod
    def incident_id_is_safe(cls, value: str) -> str:
        return validate_mesh_identifier(value, "domain expert mesh incident")

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_mesh_reason_codes(value)

    @field_validator("redacted_summary")
    @classmethod
    def summary_is_safe(cls, value: str) -> str:
        return validate_mesh_text(value, "domain expert mesh incident summary")

    @field_validator("created_at")
    @classmethod
    def created_at_is_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value, "domain expert mesh incident timestamp")

    @field_validator("incident_fingerprint")
    @classmethod
    def fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "domain expert mesh incident fingerprint")

    @model_validator(mode="after")
    def incident_is_valid(self) -> Self:
        if self.incident_fingerprint != domain_expert_mesh_incident_fingerprint(self):
            raise ValueError("domain expert mesh incident fingerprint mismatch")
        return self


def domain_expert_mesh_incident_fingerprint(
    incident: DomainExpertMeshIncidentRecord | dict[str, Any],
) -> str:
    return domain_mesh_fingerprint(incident, "incident_fingerprint")


class DomainExpertMeshDiagnostics(BaseModel):
    """Redacted diagnostic counts for operator review."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-expert-mesh-evidence/v1"] = (
        EXPERT_MESH_EVIDENCE_SCHEMA_VERSION
    )
    session_id: str
    role_counts: dict[str, int]
    domain_counts: dict[str, int]
    risk_class: CaseRiskClass
    position_counts: dict[str, int]
    alignment_state: PanelAlignmentState
    disagreement_counts: dict[str, int]
    confidence_caps: tuple[Decimal, ...] = Field(max_length=MAXIMUM_EXPERT_REPORTS_PER_CASE)
    explicit_abstention: bool
    integrity_status: MeshIntegrityStatus
    reason_codes: tuple[str, ...]
    diagnostics_fingerprint: str
    read_only: Literal[True] = True
    redacted: Literal[True] = True
    runtime_effect: Literal[False] = False

    @field_validator("session_id")
    @classmethod
    def session_id_is_safe(cls, value: str) -> str:
        return validate_mesh_identifier(value, "domain expert mesh diagnostics session")

    @field_validator("confidence_caps")
    @classmethod
    def confidence_caps_are_quantized(cls, value: tuple[Decimal, ...]) -> tuple[Decimal, ...]:
        return tuple(_confidence(item) for item in value)

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_mesh_reason_codes(value)

    @field_validator("diagnostics_fingerprint")
    @classmethod
    def fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "domain expert mesh diagnostics fingerprint")

    @model_validator(mode="after")
    def diagnostics_is_valid(self) -> Self:
        reject_mesh_protected_material(self.role_counts, "domain expert mesh diagnostics")
        reject_mesh_protected_material(self.domain_counts, "domain expert mesh diagnostics")
        if self.diagnostics_fingerprint != domain_expert_mesh_diagnostics_fingerprint(self):
            raise ValueError("domain expert mesh diagnostics fingerprint mismatch")
        return self


def domain_expert_mesh_diagnostics_fingerprint(
    diagnostics: DomainExpertMeshDiagnostics | dict[str, Any],
) -> str:
    return domain_mesh_fingerprint(diagnostics, "diagnostics_fingerprint")


class DomainExpertMeshOperatorReviewItem(BaseModel):
    """Operator-review requirement; not an approval."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-expert-mesh-evidence/v1"] = (
        EXPERT_MESH_EVIDENCE_SCHEMA_VERSION
    )
    review_item_id: str
    session_id: str
    case_id: str
    reason_codes: tuple[str, ...]
    created_at: datetime
    expires_at: datetime
    review_fingerprint: str
    operator_review_required: Literal[True] = True
    human_domain_review_recommended: Literal[True] = True
    professional_advice_claimed: Literal[False] = False
    automatic_action_authorized: Literal[False] = False
    knowledge_promotion_authorized: Literal[False] = False
    belief_mutation_authorized: Literal[False] = False
    persistent_mesh_write_authorized: Literal[False] = False
    approval_created: Literal[False] = False
    implementation_authorization_created: Literal[False] = False
    runtime_effect: Literal[False] = False

    @field_validator("review_item_id", "session_id", "case_id")
    @classmethod
    def ids_are_safe(cls, value: str) -> str:
        return validate_mesh_identifier(value, "domain expert mesh review item")

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_mesh_reason_codes(value)

    @field_validator("created_at", "expires_at")
    @classmethod
    def timestamps_are_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value, "domain expert mesh review timestamp")

    @field_validator("review_fingerprint")
    @classmethod
    def fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "domain expert mesh review fingerprint")

    @model_validator(mode="after")
    def review_is_valid(self) -> Self:
        if self.expires_at <= self.created_at:
            raise ValueError("review expiry must be after creation")
        if (self.expires_at - self.created_at).total_seconds() > 7 * 24 * 60 * 60:
            raise ValueError("review expiry must be within seven days")
        if self.review_fingerprint != domain_expert_mesh_operator_review_fingerprint(self):
            raise ValueError("domain expert mesh operator review fingerprint mismatch")
        return self


def domain_expert_mesh_operator_review_fingerprint(
    item: DomainExpertMeshOperatorReviewItem | dict[str, Any],
) -> str:
    return domain_mesh_fingerprint(item, "review_fingerprint")


class DomainExpertMeshEvidenceBundle(BaseModel):
    """Safe evidence bundle for operator review."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-expert-mesh-evidence/v1"] = (
        EXPERT_MESH_EVIDENCE_SCHEMA_VERSION
    )
    session_id: str
    case_id: str
    fingerprints: tuple[str, ...]
    counts: dict[str, int]
    role_ids: tuple[ExpertPerspectiveRole, ...]
    domain_ids: tuple[str, ...]
    specialty_ids: tuple[str, ...]
    risk_class: CaseRiskClass
    positions: tuple[ExpertReportPosition, ...]
    alignment_state: PanelAlignmentState
    disagreement_types: tuple[DisagreementType, ...]
    confidence_caps: tuple[Decimal, ...]
    explicit_abstention: bool
    integrity_status: MeshIntegrityStatus
    authorization_transaction_id: Literal["AION-212-KI-0005"] = AUTHORIZATION_TRANSACTION_ID
    implementation_task: Literal["AION-213"] = IMPLEMENTATION_TASK
    formal_closeout_task: Literal["AION-214"] = FORMAL_CLOSEOUT_TASK
    domain_expert_mesh_runtime_enabled: Literal[False] = False
    persistent_expert_mesh_write_enabled: Literal[False] = False
    evidence_fingerprint: str
    runtime_effect: Literal[False] = False

    @field_validator("session_id", "case_id")
    @classmethod
    def ids_are_safe(cls, value: str) -> str:
        return validate_mesh_identifier(value, "domain expert mesh evidence identifier")

    @field_validator("fingerprints")
    @classmethod
    def fingerprints_are_hex(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if len(set(value)) != len(value):
            raise ValueError("duplicate evidence fingerprints rejected")
        return tuple(
            validate_hex64(item, "domain expert mesh evidence fingerprint") for item in value
        )

    @field_validator("domain_ids")
    @classmethod
    def domain_ids_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return _safe_id_tuple(
            value, "domain expert mesh evidence domain", max_length=MAXIMUM_DOMAINS_PER_CASE
        )

    @field_validator("specialty_ids")
    @classmethod
    def specialty_ids_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return _safe_id_tuple(
            value, "domain expert mesh evidence specialty", max_length=MAXIMUM_SPECIALTIES_PER_CASE
        )

    @field_validator("confidence_caps")
    @classmethod
    def confidence_caps_are_quantized(cls, value: tuple[Decimal, ...]) -> tuple[Decimal, ...]:
        return tuple(_confidence(item) for item in value)

    @field_validator("evidence_fingerprint")
    @classmethod
    def evidence_fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "domain expert mesh evidence bundle fingerprint")

    @model_validator(mode="after")
    def bundle_is_valid(self) -> Self:
        reject_mesh_protected_material(self.counts, "domain expert mesh evidence counts")
        if self.evidence_fingerprint != domain_expert_mesh_evidence_bundle_fingerprint(self):
            raise ValueError("domain expert mesh evidence bundle fingerprint mismatch")
        return self


def domain_expert_mesh_evidence_bundle_fingerprint(
    bundle: DomainExpertMeshEvidenceBundle | dict[str, Any],
) -> str:
    return domain_mesh_fingerprint(bundle, "evidence_fingerprint")


class DomainExpertMeshResourceBudget(BaseModel):
    """AION-212-KI-0005 resource budget with persistent mesh writes at zero."""

    model_config = FROZEN_MODEL_CONFIG

    maximum_domains_per_case: Literal[20] = MAXIMUM_DOMAINS_PER_CASE
    maximum_specialties_per_case: Literal[50] = MAXIMUM_SPECIALTIES_PER_CASE
    maximum_claims_per_case: Literal[100] = MAXIMUM_CLAIMS_PER_CASE
    maximum_epistemic_assessments_per_case: Literal[100] = MAXIMUM_EPISTEMIC_ASSESSMENTS_PER_CASE
    maximum_subquestions_per_case: Literal[50] = MAXIMUM_SUBQUESTIONS_PER_CASE
    maximum_expert_profiles_considered: Literal[100] = MAXIMUM_EXPERT_PROFILES_CONSIDERED
    maximum_panel_size: Literal[12] = MAXIMUM_PANEL_SIZE
    maximum_required_roles_per_panel: Literal[8] = MAXIMUM_REQUIRED_ROLES_PER_PANEL
    maximum_expert_reports_per_case: Literal[24] = MAXIMUM_EXPERT_REPORTS_PER_CASE
    maximum_critiques_per_case: Literal[100] = MAXIMUM_CRITIQUES_PER_CASE
    maximum_deliberation_rounds: Literal[3] = MAXIMUM_DELIBERATION_ROUNDS
    maximum_disagreement_items_per_case: Literal[100] = MAXIMUM_DISAGREEMENT_ITEMS_PER_CASE
    maximum_evidence_references_per_report: Literal[100] = MAXIMUM_EVIDENCE_REFERENCES_PER_REPORT
    maximum_reason_codes_per_report: Literal[50] = MAXIMUM_REASON_CODES_PER_REPORT
    maximum_operator_review_items: Literal[100] = MAXIMUM_OPERATOR_REVIEW_ITEMS
    maximum_mesh_sessions: Literal[100] = MAXIMUM_MESH_SESSIONS
    maximum_query_results: Literal[1000] = MAXIMUM_QUERY_RESULTS
    maximum_fixture_records: Literal[5000] = MAXIMUM_FIXTURE_RECORDS
    maximum_fixture_bytes: Literal[4194304] = MAXIMUM_FIXTURE_BYTES
    maximum_concurrent_experts: Literal[8] = MAXIMUM_CONCURRENT_EXPERTS
    maximum_persistent_mesh_write_batch: Literal[0] = MAXIMUM_PERSISTENT_MESH_WRITE_BATCH
    maximum_model_provider_calls: Literal[0] = MAXIMUM_MODEL_PROVIDER_CALLS
    maximum_tool_executions: Literal[0] = MAXIMUM_TOOL_EXECUTIONS
    maximum_network_calls: Literal[0] = MAXIMUM_NETWORK_CALLS
    maximum_search_provider_calls: Literal[0] = MAXIMUM_SEARCH_PROVIDER_CALLS
    maximum_connector_calls: Literal[0] = MAXIMUM_CONNECTOR_CALLS
    maximum_knowledge_promotions: Literal[0] = MAXIMUM_KNOWLEDGE_PROMOTIONS
    maximum_belief_mutations: Literal[0] = MAXIMUM_BELIEF_MUTATIONS
    maximum_source_mutations: Literal[0] = MAXIMUM_SOURCE_MUTATIONS
    maximum_git_operations: Literal[0] = MAXIMUM_GIT_OPERATIONS
    maximum_runtime_created_pull_requests: Literal[0] = MAXIMUM_RUNTIME_CREATED_PULL_REQUESTS
    maximum_approvals_created: Literal[0] = MAXIMUM_APPROVALS_CREATED
    maximum_autonomous_actions: Literal[0] = MAXIMUM_AUTONOMOUS_ACTIONS
    maximum_high_stakes_actions: Literal[0] = MAXIMUM_HIGH_STAKES_ACTIONS
    maximum_deployments: Literal[0] = MAXIMUM_DEPLOYMENTS
    maximum_model_weight_changes: Literal[0] = MAXIMUM_MODEL_WEIGHT_CHANGES


class DomainExpertMeshResourceUsage(BaseModel):
    """Measured resource usage for one in-memory session."""

    model_config = FROZEN_MODEL_CONFIG

    domains_per_case: int = Field(default=0, ge=0)
    specialties_per_case: int = Field(default=0, ge=0)
    claims_per_case: int = Field(default=0, ge=0)
    epistemic_assessments_per_case: int = Field(default=0, ge=0)
    subquestions_per_case: int = Field(default=0, ge=0)
    expert_profiles_considered: int = Field(default=0, ge=0)
    panel_size: int = Field(default=0, ge=0)
    required_roles_per_panel: int = Field(default=0, ge=0)
    expert_reports_per_case: int = Field(default=0, ge=0)
    critiques_per_case: int = Field(default=0, ge=0)
    deliberation_rounds: int = Field(default=0, ge=0)
    disagreement_items_per_case: int = Field(default=0, ge=0)
    evidence_references_per_report: int = Field(default=0, ge=0)
    reason_codes_per_report: int = Field(default=0, ge=0)
    operator_review_items: int = Field(default=0, ge=0)
    mesh_sessions: int = Field(default=0, ge=0)
    query_results: int = Field(default=0, ge=0)
    fixture_records: int = Field(default=0, ge=0)
    fixture_bytes: int = Field(default=0, ge=0)
    concurrent_experts: int = Field(default=0, ge=0)
    persistent_mesh_write_batch: int = Field(default=0, ge=0)
    model_provider_calls: int = Field(default=0, ge=0)
    tool_executions: int = Field(default=0, ge=0)
    network_calls: int = Field(default=0, ge=0)
    search_provider_calls: int = Field(default=0, ge=0)
    connector_calls: int = Field(default=0, ge=0)
    knowledge_promotions: int = Field(default=0, ge=0)
    belief_mutations: int = Field(default=0, ge=0)
    source_mutations: int = Field(default=0, ge=0)
    git_operations: int = Field(default=0, ge=0)
    runtime_created_pull_requests: int = Field(default=0, ge=0)
    approvals_created: int = Field(default=0, ge=0)
    autonomous_actions: int = Field(default=0, ge=0)
    high_stakes_actions: int = Field(default=0, ge=0)
    deployments: int = Field(default=0, ge=0)
    model_weight_changes: int = Field(default=0, ge=0)


class DomainExpertMeshBudgetDecision(BaseModel):
    """Budget decision for mesh work."""

    model_config = FROZEN_MODEL_CONFIG

    within_budget: bool
    usage: DomainExpertMeshResourceUsage
    budget: DomainExpertMeshResourceBudget
    reason_codes: tuple[str, ...]
    persistent_write_allowed: Literal[False] = False
    decision_fingerprint: str
    runtime_effect: Literal[False] = False

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_mesh_reason_codes(value)

    @field_validator("decision_fingerprint")
    @classmethod
    def fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "domain expert mesh budget fingerprint")

    @model_validator(mode="after")
    def decision_is_valid(self) -> Self:
        if self.decision_fingerprint != domain_expert_mesh_budget_decision_fingerprint(self):
            raise ValueError("domain expert mesh budget decision fingerprint mismatch")
        return self


def domain_expert_mesh_budget_decision_fingerprint(
    decision: DomainExpertMeshBudgetDecision | dict[str, Any],
) -> str:
    return domain_mesh_fingerprint(decision, "decision_fingerprint")


def evaluate_domain_expert_mesh_budget(
    usage: DomainExpertMeshResourceUsage,
    budget: DomainExpertMeshResourceBudget | None = None,
) -> DomainExpertMeshBudgetDecision:
    """Evaluate usage against AION-212-KI-0005 limits."""

    current = budget or DomainExpertMeshResourceBudget()
    checks = (
        (usage.domains_per_case, current.maximum_domains_per_case),
        (usage.specialties_per_case, current.maximum_specialties_per_case),
        (usage.claims_per_case, current.maximum_claims_per_case),
        (usage.epistemic_assessments_per_case, current.maximum_epistemic_assessments_per_case),
        (usage.subquestions_per_case, current.maximum_subquestions_per_case),
        (usage.expert_profiles_considered, current.maximum_expert_profiles_considered),
        (usage.panel_size, current.maximum_panel_size),
        (usage.required_roles_per_panel, current.maximum_required_roles_per_panel),
        (usage.expert_reports_per_case, current.maximum_expert_reports_per_case),
        (usage.critiques_per_case, current.maximum_critiques_per_case),
        (usage.deliberation_rounds, current.maximum_deliberation_rounds),
        (usage.disagreement_items_per_case, current.maximum_disagreement_items_per_case),
        (usage.evidence_references_per_report, current.maximum_evidence_references_per_report),
        (usage.reason_codes_per_report, current.maximum_reason_codes_per_report),
        (usage.operator_review_items, current.maximum_operator_review_items),
        (usage.mesh_sessions, current.maximum_mesh_sessions),
        (usage.query_results, current.maximum_query_results),
        (usage.fixture_records, current.maximum_fixture_records),
        (usage.fixture_bytes, current.maximum_fixture_bytes),
        (usage.concurrent_experts, current.maximum_concurrent_experts),
        (usage.persistent_mesh_write_batch, current.maximum_persistent_mesh_write_batch),
        (usage.model_provider_calls, current.maximum_model_provider_calls),
        (usage.tool_executions, current.maximum_tool_executions),
        (usage.network_calls, current.maximum_network_calls),
        (usage.search_provider_calls, current.maximum_search_provider_calls),
        (usage.connector_calls, current.maximum_connector_calls),
        (usage.knowledge_promotions, current.maximum_knowledge_promotions),
        (usage.belief_mutations, current.maximum_belief_mutations),
        (usage.source_mutations, current.maximum_source_mutations),
        (usage.git_operations, current.maximum_git_operations),
        (usage.runtime_created_pull_requests, current.maximum_runtime_created_pull_requests),
        (usage.approvals_created, current.maximum_approvals_created),
        (usage.autonomous_actions, current.maximum_autonomous_actions),
        (usage.high_stakes_actions, current.maximum_high_stakes_actions),
        (usage.deployments, current.maximum_deployments),
        (usage.model_weight_changes, current.maximum_model_weight_changes),
    )
    within = all(observed <= allowed for observed, allowed in checks)
    codes = ("domain_mesh_case_valid",) if within else ("domain_mesh_case_invalid",)
    payload = {
        "within_budget": within,
        "usage": usage,
        "budget": current,
        "reason_codes": codes,
    }
    return DomainExpertMeshBudgetDecision.model_validate(
        {
            **payload,
            "decision_fingerprint": domain_mesh_fingerprint(payload, "decision_fingerprint"),
        }
    )


class DomainExpertMeshFixtureEnvelope(BaseModel):
    """Explicit local synthetic fixture for deterministic replay."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-expert-mesh-fixture/v1"] = (
        EXPERT_MESH_FIXTURE_SCHEMA_VERSION
    )
    program_id: Literal["AION-KNOWLEDGE-INTELLIGENCE-001"] = PROGRAM_ID
    authorization_transaction_id: Literal["AION-212-KI-0005"] = AUTHORIZATION_TRANSACTION_ID
    implementation_task: Literal["AION-213"] = IMPLEMENTATION_TASK
    formal_closeout_task: Literal["AION-214"] = FORMAL_CLOSEOUT_TASK
    authorization_scope: Literal[
        "deterministic-domain-taxonomy-expert-profile-routing-independent-analysis-"
        "deliberation-disagreement-synthesis-abstention-core"
    ] = AUTHORIZATION_SCOPE
    case: DomainExpertCase
    assessments: tuple[ClaimEpistemicAssessment, ...] = Field(
        max_length=MAXIMUM_EPISTEMIC_ASSESSMENTS_PER_CASE
    )
    synthetic: Literal[True] = True
    read_only: Literal[True] = True
    redacted: Literal[True] = True
    persistent_write_applied: Literal[False] = False
    runtime_effect: Literal[False] = False
    fixture_fingerprint: str

    @field_validator("fixture_fingerprint")
    @classmethod
    def fixture_fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "domain expert mesh fixture fingerprint")

    @model_validator(mode="after")
    def fixture_is_valid(self) -> Self:
        if len(self.assessments) > MAXIMUM_FIXTURE_RECORDS:
            raise ValueError("fixture record limit exceeded")
        assessment_ids = {item.assessment_id for item in self.assessments}
        if set(self.case.epistemic_assessment_ids) - assessment_ids:
            raise ValueError("fixture assessment reference unresolved")
        if self.fixture_fingerprint != domain_expert_mesh_fixture_fingerprint(self):
            raise ValueError("domain expert mesh fixture fingerprint mismatch")
        return self


def domain_expert_mesh_fixture_fingerprint(
    fixture: DomainExpertMeshFixtureEnvelope | dict[str, Any],
) -> str:
    return domain_mesh_fingerprint(fixture, "fixture_fingerprint")


class DomainExpertMeshQuery(BaseModel):
    """Bounded exact query over in-memory sessions."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-expert-mesh-evidence/v1"] = (
        EXPERT_MESH_EVIDENCE_SCHEMA_VERSION
    )
    session_id: str | None = None
    case_id: str | None = None
    panel_id: str | None = None
    profile_id: str | None = None
    perspective_role: ExpertPerspectiveRole | None = None
    domain_id: str | None = None
    specialty_id: str | None = None
    risk_class: CaseRiskClass | None = None
    report_position: ExpertReportPosition | None = None
    disagreement_type: DisagreementType | None = None
    alignment_state: PanelAlignmentState | None = None
    explicit_abstention: bool | None = None
    operator_review_required: bool | None = None
    limit: int = Field(default=MAXIMUM_QUERY_RESULTS, ge=1, le=MAXIMUM_QUERY_RESULTS)
    fuzzy_search_enabled: Literal[False] = False
    semantic_search_enabled: Literal[False] = False
    consensus_ranking_enabled: Literal[False] = False

    @field_validator("session_id", "case_id", "panel_id", "profile_id", "domain_id", "specialty_id")
    @classmethod
    def ids_are_safe(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return validate_mesh_identifier(value, "domain expert mesh query identifier")


class DomainExpertMeshQueryResult(BaseModel):
    """Exact bounded query result."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-expert-mesh-evidence/v1"] = (
        EXPERT_MESH_EVIDENCE_SCHEMA_VERSION
    )
    query: DomainExpertMeshQuery
    session_ids: tuple[str, ...] = Field(max_length=MAXIMUM_QUERY_RESULTS)
    result_count: int = Field(ge=0, le=MAXIMUM_QUERY_RESULTS)
    truncated: bool
    query_fingerprint: str
    runtime_effect: Literal[False] = False

    @field_validator("session_ids")
    @classmethod
    def session_ids_are_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return _safe_id_tuple(
            value, "domain expert mesh query session", max_length=MAXIMUM_QUERY_RESULTS
        )

    @field_validator("query_fingerprint")
    @classmethod
    def query_fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "domain expert mesh query result fingerprint")

    @model_validator(mode="after")
    def query_result_is_valid(self) -> Self:
        if self.result_count != len(self.session_ids):
            raise ValueError("result_count must match query results")
        if self.query_fingerprint != domain_expert_mesh_query_result_fingerprint(self):
            raise ValueError("domain expert mesh query result fingerprint mismatch")
        return self


def domain_expert_mesh_query_result_fingerprint(
    result: DomainExpertMeshQueryResult | dict[str, Any],
) -> str:
    return domain_mesh_fingerprint(result, "query_fingerprint")


class DomainExpertMeshSession(BaseModel):
    """Immutable in-memory mesh session."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-expert-mesh-session/v1"] = (
        EXPERT_MESH_SESSION_SCHEMA_VERSION
    )
    session_id: str
    case: DomainExpertCase
    subquestion_plan: ExpertSubquestionPlan
    panel_plan: ExpertPanelPlan
    reports: tuple[ExpertPerspectiveReport, ...] = Field(max_length=MAXIMUM_EXPERT_REPORTS_PER_CASE)
    critiques: tuple[ExpertCritique, ...] = Field(max_length=MAXIMUM_CRITIQUES_PER_CASE)
    critique_responses: tuple[ExpertCritiqueResponse, ...] = Field(
        max_length=MAXIMUM_CRITIQUES_PER_CASE
    )
    disagreement_matrix: ExpertDisagreementMatrix
    synthesis: ExpertMeshSynthesis
    integrity_report: DomainExpertMeshIntegrityReport
    diagnostics: DomainExpertMeshDiagnostics
    operator_review_items: tuple[DomainExpertMeshOperatorReviewItem, ...] = Field(
        max_length=MAXIMUM_OPERATOR_REVIEW_ITEMS
    )
    evidence_bundle: DomainExpertMeshEvidenceBundle
    outcome: MeshSessionOutcome
    created_at: datetime
    session_fingerprint: str
    synthetic: Literal[True] = True
    read_only: Literal[True] = True
    redacted: Literal[True] = True
    persistent_write_applied: Literal[False] = False
    model_provider_called: Literal[False] = False
    tool_executed: Literal[False] = False
    network_accessed: Literal[False] = False
    automatic_action: Literal[False] = False
    knowledge_promoted: Literal[False] = False
    belief_mutated: Literal[False] = False
    runtime_effect: Literal[False] = False

    @field_validator("session_id")
    @classmethod
    def session_id_is_safe(cls, value: str) -> str:
        return validate_mesh_identifier(value, "domain expert mesh session")

    @field_validator("created_at")
    @classmethod
    def created_at_is_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value, "domain expert mesh session timestamp")

    @field_validator("session_fingerprint")
    @classmethod
    def session_fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "domain expert mesh session fingerprint")

    @model_validator(mode="after")
    def session_is_valid(self) -> Self:
        if self.case.case_id != self.panel_plan.case_id:
            raise ValueError("session panel case mismatch")
        if self.case.case_id != self.synthesis.case_id:
            raise ValueError("session synthesis case mismatch")
        if tuple(report.report_id for report in self.reports) != self.synthesis.report_ids:
            raise ValueError("session synthesis must preserve all reports")
        if (
            tuple(critique.critique_id for critique in self.critiques)
            != self.synthesis.critique_ids
        ):
            raise ValueError("session synthesis must preserve all critiques")
        if self.session_fingerprint != domain_expert_mesh_session_fingerprint(self):
            raise ValueError("domain expert mesh session fingerprint mismatch")
        return self


def domain_expert_mesh_session_fingerprint(
    session: DomainExpertMeshSession | dict[str, Any],
) -> str:
    return domain_mesh_fingerprint(session, "session_fingerprint")


def assert_fixture_path_allowed(path: Path, *, repository_root: Path) -> Path:
    """Validate explicit local fixture path constraints and return the path."""

    text = str(path)
    if "://" in text or text.startswith("~") or "$" in text:
        raise DomainExpertMeshError("fixture path syntax rejected")
    if not path.is_absolute():
        raise DomainExpertMeshError("fixture path must be absolute")
    if any(part.startswith(".") for part in path.parts[1:]):
        raise DomainExpertMeshError("hidden fixture path rejected")
    if path.is_symlink():
        raise DomainExpertMeshError("fixture symlink rejected")
    if not path.is_file():
        raise DomainExpertMeshError("fixture must be a regular file")
    resolved = path.resolve()
    root = repository_root.resolve()
    if resolved == root or root in resolved.parents:
        raise DomainExpertMeshError("fixture path inside repository rejected")
    if resolved.stat().st_size > MAXIMUM_FIXTURE_BYTES:
        raise DomainExpertMeshError("fixture byte limit exceeded")
    return resolved


def assessment_position(status: EpistemicAssessmentStatus) -> ExpertReportPosition:
    """Map AION-211 posture to an expert report posture without truth promotion."""

    mapping = {
        EpistemicAssessmentStatus.SUPPORTED: ExpertReportPosition.SUPPORTS,
        EpistemicAssessmentStatus.CONTRADICTED: ExpertReportPosition.OPPOSES,
        EpistemicAssessmentStatus.MIXED: ExpertReportPosition.MIXED,
        EpistemicAssessmentStatus.INSUFFICIENT_EVIDENCE: (
            ExpertReportPosition.INSUFFICIENT_EVIDENCE
        ),
        EpistemicAssessmentStatus.STALE: ExpertReportPosition.STALE,
        EpistemicAssessmentStatus.SUPERSEDED: ExpertReportPosition.SUPERSEDED,
        EpistemicAssessmentStatus.RETRACTED: ExpertReportPosition.RETRACTED,
        EpistemicAssessmentStatus.SCOPE_MISMATCH: ExpertReportPosition.SCOPE_MISMATCH,
        EpistemicAssessmentStatus.UNKNOWN: ExpertReportPosition.UNKNOWN,
    }
    return mapping[status]


__all__ = [
    "APPROVAL_RECORD_ID",
    "AUTHORIZATION_SCOPE",
    "AUTHORIZATION_TRANSACTION_ID",
    "CaseRiskClass",
    "DisagreementType",
    "DOMAIN_EXPERT_CASE_SCHEMA_VERSION",
    "DOMAIN_EXPERT_MESH_CONTRACT_SCHEMA_VERSION",
    "DOMAIN_EXPERT_PROFILE_SCHEMA_VERSION",
    "DOMAIN_TAXONOMY_SCHEMA_VERSION",
    "DomainExpertCase",
    "DomainExpertMeshBudgetDecision",
    "DomainExpertMeshDiagnostics",
    "DomainExpertMeshError",
    "DomainExpertMeshEvidenceBundle",
    "DomainExpertMeshFixtureEnvelope",
    "DomainExpertMeshIncidentRecord",
    "DomainExpertMeshIntegrityFinding",
    "DomainExpertMeshIntegrityReport",
    "DomainExpertMeshOperatorReviewItem",
    "DomainExpertMeshQuery",
    "DomainExpertMeshQueryResult",
    "DomainExpertMeshResourceBudget",
    "DomainExpertMeshResourceUsage",
    "DomainExpertMeshSession",
    "DomainExpertProfile",
    "DomainExpertProfileRegistry",
    "DomainSpecialty",
    "DomainTaxonomy",
    "DomainTaxonomyNode",
    "EXPERT_CRITIQUE_RESPONSE_SCHEMA_VERSION",
    "EXPERT_CRITIQUE_SCHEMA_VERSION",
    "EXPERT_DISAGREEMENT_MATRIX_SCHEMA_VERSION",
    "EXPERT_MESH_EVIDENCE_SCHEMA_VERSION",
    "EXPERT_MESH_FIXTURE_SCHEMA_VERSION",
    "EXPERT_MESH_INTEGRITY_SCHEMA_VERSION",
    "EXPERT_MESH_REASON_CODE_REGISTRY",
    "EXPERT_MESH_REASON_CODE_REGISTRY_VERSION",
    "EXPERT_MESH_SESSION_SCHEMA_VERSION",
    "EXPERT_MESH_SYNTHESIS_SCHEMA_VERSION",
    "EXPERT_PANEL_PLAN_SCHEMA_VERSION",
    "EXPERT_PERSPECTIVE_REPORT_SCHEMA_VERSION",
    "EXPERT_MESH_REASON_CODES",
    "ExpertAssignment",
    "ExpertCapabilityScope",
    "ExpertCritique",
    "ExpertCritiqueResponse",
    "ExpertDisagreementItem",
    "ExpertDisagreementMatrix",
    "ExpertMeshSynthesis",
    "ExpertPanelPlan",
    "ExpertPerspectiveReport",
    "ExpertPerspectiveRole",
    "ExpertReportPosition",
    "ExpertSubquestion",
    "ExpertSubquestionPlan",
    "FORMAL_CLOSEOUT_TASK",
    "IMPLEMENTATION_TASK",
    "MAXIMUM_AUTONOMOUS_ACTIONS",
    "MAXIMUM_BELIEF_MUTATIONS",
    "MAXIMUM_CLAIMS_PER_CASE",
    "MAXIMUM_CONCURRENT_EXPERTS",
    "MAXIMUM_CONNECTOR_CALLS",
    "MAXIMUM_CRITIQUES_PER_CASE",
    "MAXIMUM_DELIBERATION_ROUNDS",
    "MAXIMUM_DEPLOYMENTS",
    "MAXIMUM_DISAGREEMENT_ITEMS_PER_CASE",
    "MAXIMUM_DOMAINS_PER_CASE",
    "MAXIMUM_EPISTEMIC_ASSESSMENTS_PER_CASE",
    "MAXIMUM_EVIDENCE_REFERENCES_PER_REPORT",
    "MAXIMUM_EXPERT_PROFILES_CONSIDERED",
    "MAXIMUM_EXPERT_REPORTS_PER_CASE",
    "MAXIMUM_FIXTURE_BYTES",
    "MAXIMUM_FIXTURE_RECORDS",
    "MAXIMUM_GIT_OPERATIONS",
    "MAXIMUM_HIGH_STAKES_ACTIONS",
    "MAXIMUM_KNOWLEDGE_PROMOTIONS",
    "MAXIMUM_MESH_SESSIONS",
    "MAXIMUM_MODEL_PROVIDER_CALLS",
    "MAXIMUM_MODEL_WEIGHT_CHANGES",
    "MAXIMUM_NETWORK_CALLS",
    "MAXIMUM_OPERATOR_REVIEW_ITEMS",
    "MAXIMUM_PANEL_SIZE",
    "MAXIMUM_PERSISTENT_MESH_WRITE_BATCH",
    "MAXIMUM_QUERY_RESULTS",
    "MAXIMUM_REASON_CODES_PER_REPORT",
    "MAXIMUM_REQUIRED_ROLES_PER_PANEL",
    "MAXIMUM_SEARCH_PROVIDER_CALLS",
    "MAXIMUM_SOURCE_MUTATIONS",
    "MAXIMUM_SPECIALTIES_PER_CASE",
    "MAXIMUM_SUBQUESTIONS_PER_CASE",
    "MAXIMUM_TOOL_EXECUTIONS",
    "MeshIntegrityStatus",
    "MeshSessionOutcome",
    "PanelAlignmentState",
    "PROGRAM_ID",
    "assert_fixture_path_allowed",
    "assessment_position",
    "domain_expert_case_fingerprint",
    "domain_expert_mesh_budget_decision_fingerprint",
    "domain_expert_mesh_diagnostics_fingerprint",
    "domain_expert_mesh_evidence_bundle_fingerprint",
    "domain_expert_mesh_fixture_fingerprint",
    "domain_expert_mesh_incident_fingerprint",
    "domain_expert_mesh_integrity_report_fingerprint",
    "domain_expert_mesh_operator_review_fingerprint",
    "domain_expert_mesh_query_result_fingerprint",
    "domain_expert_mesh_session_fingerprint",
    "domain_expert_profile_fingerprint",
    "domain_expert_profile_registry_fingerprint",
    "domain_mesh_fingerprint",
    "domain_specialty_fingerprint",
    "domain_taxonomy_fingerprint",
    "domain_taxonomy_node_fingerprint",
    "evaluate_domain_expert_mesh_budget",
    "expert_assignment_fingerprint",
    "expert_critique_fingerprint",
    "expert_critique_response_fingerprint",
    "expert_disagreement_item_fingerprint",
    "expert_disagreement_matrix_fingerprint",
    "expert_mesh_synthesis_fingerprint",
    "expert_panel_plan_fingerprint",
    "expert_perspective_report_fingerprint",
    "expert_subquestion_fingerprint",
    "expert_subquestion_plan_fingerprint",
    "json_size",
    "reject_mesh_protected_material",
    "validate_mesh_reason_codes",
    "validate_mesh_text",
]
