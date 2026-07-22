"""Active information-acquisition contracts owned by AION Brain."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal, Self, cast

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.cognitive_state import (
    FrozenDict,
    fingerprint_model,
    fingerprint_payload,
    freeze_payload,
)
from aion_brain.contracts.model_outputs import (
    reject_hidden_or_secret_text,
    reject_secret_like_payload,
)

SCHEMA_VERSION = "information-acquisition/v1"
CANONICALIZATION_VERSION = "information-acquisition-canonical-json/v1"
AUTHORIZATION_ID = "AION-193-CA-0006"
IMPLEMENTATION_TASK = "AION-194"

CandidateType = Literal["clarification", "retrieval", "observation", "experiment"]
CandidateStatus = Literal["proposed", "approved", "blocked"]
RiskSeverity = Literal["low", "medium", "high", "critical"]

SAFE_REFERENCE_PREFIXES = (
    "aion://",
    "memory://",
    "evidence://",
    "operator-approved://",
    "approved-local://",
    "synthetic://",
)
BLOCKED_REFERENCE_PREFIXES = (
    "http:",
    "https:",
    "ftp:",
    "file:",
    "s3:",
    "gs:",
)


def validate_acquisition_reference(value: str, field_name: str) -> str:
    """Validate an opaque, approved reference without allowing arbitrary locations."""

    reject_hidden_or_secret_text(value, field_name)
    stripped = value.strip()
    lowered = stripped.lower()
    if not stripped:
        raise ValueError(f"{field_name} must not be empty")
    if lowered.startswith(BLOCKED_REFERENCE_PREFIXES):
        raise ValueError(f"{field_name} must not be an arbitrary external location")
    if stripped.startswith(("/", "~")):
        raise ValueError(f"{field_name} must not be an implicit filesystem location")
    if "../" in stripped or "..\\" in stripped:
        raise ValueError(f"{field_name} must not contain traversal")
    if "://" in stripped and not lowered.startswith(SAFE_REFERENCE_PREFIXES):
        raise ValueError(f"{field_name} must use an approved opaque reference prefix")
    if lowered.startswith(".git") or "/.git" in lowered:
        raise ValueError(f"{field_name} must not target repository internals")
    return stripped


class InformationAcquisitionModel(BaseModel):
    """Base model for immutable active information-acquisition contracts."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = SCHEMA_VERSION

    @field_validator("schema_version")
    @classmethod
    def schema_version_must_match(cls, value: str) -> str:
        if value != SCHEMA_VERSION:
            raise ValueError(f"schema_version must be {SCHEMA_VERSION}")
        return value


class InformationAcquisitionFingerprintedModel(InformationAcquisitionModel):
    """Immutable model with a deterministic SHA-256 fingerprint."""

    fingerprint: str | None = None

    @model_validator(mode="after")
    def fingerprint_must_match_payload(self) -> Self:
        expected = fingerprint_model(self, exclude={"fingerprint"})
        if self.fingerprint is None:
            object.__setattr__(self, "fingerprint", expected)
        elif self.fingerprint != expected:
            raise ValueError("fingerprint must match canonical acquisition payload")
        return self


class InformationAcquisitionRuntimeBoundary(InformationAcquisitionFingerprintedModel):
    """Proof that acquisition planning remains offline and proposal-only."""

    boundary_id: str = Field(min_length=1)
    runtime_effect: bool = False
    arbitrary_location_access: bool = False
    network_calls: int = Field(default=0, ge=0)
    connector_calls: int = Field(default=0, ge=0)
    model_provider_calls: int = Field(default=0, ge=0)
    tool_execution: bool = False
    information_acquired: bool = False
    unauthorized_information_acquisition: int = Field(default=0, ge=0)
    background_loop: bool = False
    source_rewrite: bool = False
    git_mutation: bool = False
    production_exposure: bool = False
    model_weights_changed: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("boundary_id")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "acquisition boundary id")
        return value.strip()

    @model_validator(mode="after")
    def runtime_flags_must_remain_disabled(self) -> Self:
        for key in (
            "runtime_effect",
            "arbitrary_location_access",
            "tool_execution",
            "information_acquired",
            "background_loop",
            "source_rewrite",
            "git_mutation",
            "production_exposure",
            "model_weights_changed",
        ):
            if getattr(self, key):
                raise ValueError(f"{key} must be false")
        for key in (
            "network_calls",
            "connector_calls",
            "model_provider_calls",
            "unauthorized_information_acquisition",
        ):
            if getattr(self, key) != 0:
                raise ValueError(f"{key} must be zero")
        return self


class InformationNeed(InformationAcquisitionFingerprintedModel):
    """Decision-relevant uncertainty that may justify bounded information asks."""

    need_id: str = Field(min_length=1)
    decision_id: str = Field(min_length=1)
    subject: str = Field(min_length=1)
    decision_context: str = Field(min_length=1)
    current_uncertainty: float = Field(ge=0.0, le=1.0)
    target_uncertainty: float = Field(ge=0.0, le=1.0)
    decision_relevance: float = Field(ge=0.0, le=1.0)
    urgency: float = Field(default=0.5, ge=0.0, le=1.0)
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("need_id", "decision_id", "subject", "decision_context")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "information need text")
        return value.strip()

    @field_validator("evidence_refs")
    @classmethod
    def refs_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(validate_acquisition_reference(item, "information need ref") for item in value)

    @model_validator(mode="after")
    def target_must_reduce_uncertainty(self) -> Self:
        if self.target_uncertainty > self.current_uncertainty:
            raise ValueError("target_uncertainty must not exceed current_uncertainty")
        return self


class KnowledgeGap(InformationAcquisitionFingerprintedModel):
    """Specific gap between current and required decision confidence."""

    gap_id: str = Field(min_length=1)
    need_id: str = Field(min_length=1)
    subject: str = Field(min_length=1)
    current_uncertainty: float = Field(ge=0.0, le=1.0)
    target_uncertainty: float = Field(ge=0.0, le=1.0)
    uncertainty_delta: float = Field(ge=0.0, le=1.0)
    decision_relevance: float = Field(ge=0.0, le=1.0)
    rationale: str = Field(min_length=1)
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("gap_id", "need_id", "subject", "rationale")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "knowledge gap text")
        return value.strip()

    @field_validator("evidence_refs")
    @classmethod
    def refs_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(validate_acquisition_reference(item, "knowledge gap ref") for item in value)

    @model_validator(mode="after")
    def uncertainty_delta_must_match_gap(self) -> Self:
        expected = self.current_uncertainty - self.target_uncertainty
        if expected <= 0:
            raise ValueError("knowledge gaps require reducible uncertainty")
        if abs(self.uncertainty_delta - expected) > 1e-9:
            raise ValueError("uncertainty_delta must equal current minus target uncertainty")
        return self


class _InformationCandidateBase(InformationAcquisitionFingerprintedModel):
    candidate_id: str = Field(min_length=1)
    need_id: str = Field(min_length=1)
    gap_id: str = Field(min_length=1)
    candidate_type: CandidateType
    request_summary: str = Field(min_length=1)
    permission_granted: bool = False
    status: CandidateStatus = "proposed"
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("candidate_id", "need_id", "gap_id", "request_summary")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "candidate text")
        return value.strip()

    @field_validator("evidence_refs")
    @classmethod
    def refs_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(validate_acquisition_reference(item, "candidate ref") for item in value)

    @model_validator(mode="after")
    def approved_status_requires_permission(self) -> Self:
        if self.status == "approved" and not self.permission_granted:
            raise ValueError("approved candidates require permission")
        return self


class ObservationCandidate(_InformationCandidateBase):
    """Approved local observation request; it does not perform observation."""

    candidate_type: Literal["observation"] = "observation"
    observation_scope: str = Field(min_length=1)
    approved_observation_ref: str | None = None

    @field_validator("observation_scope")
    @classmethod
    def scope_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "observation scope")
        return value.strip()

    @field_validator("approved_observation_ref")
    @classmethod
    def approved_ref_must_be_safe(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return validate_acquisition_reference(value, "approved observation ref")


class ClarificationCandidate(_InformationCandidateBase):
    """Clarification request for an operator or approved local reviewer."""

    candidate_type: Literal["clarification"] = "clarification"
    clarification_question: str = Field(min_length=1)
    recipient_role: str = Field(min_length=1)

    @field_validator("clarification_question", "recipient_role")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "clarification text")
        return value.strip()


class RetrievalCandidate(_InformationCandidateBase):
    """Approved retrieval request against opaque approved references only."""

    candidate_type: Literal["retrieval"] = "retrieval"
    retrieval_ref: str = Field(min_length=1)
    query_summary: str = Field(min_length=1)
    approved_source_refs: tuple[str, ...] = Field(default_factory=tuple)

    @field_validator("retrieval_ref")
    @classmethod
    def retrieval_ref_must_be_safe(cls, value: str) -> str:
        return validate_acquisition_reference(value, "retrieval ref")

    @field_validator("query_summary")
    @classmethod
    def query_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "retrieval query summary")
        return value.strip()

    @field_validator("approved_source_refs")
    @classmethod
    def approved_refs_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(validate_acquisition_reference(item, "approved source ref") for item in value)

    @model_validator(mode="after")
    def approved_retrieval_requires_sources(self) -> Self:
        if self.permission_granted and not self.approved_source_refs:
            raise ValueError("approved retrieval candidates require approved source refs")
        return self


class ExperimentCandidate(_InformationCandidateBase):
    """Synthetic experiment request; it does not execute an experiment."""

    candidate_type: Literal["experiment"] = "experiment"
    experiment_design: str = Field(min_length=1)
    synthetic_only: bool = True
    expected_observations: tuple[str, ...] = Field(default_factory=tuple)

    @field_validator("experiment_design")
    @classmethod
    def design_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "experiment design")
        return value.strip()

    @field_validator("expected_observations")
    @classmethod
    def observations_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            reject_hidden_or_secret_text(item, "expected observation")
        return value

    @model_validator(mode="after")
    def experiments_must_be_synthetic(self) -> Self:
        if not self.synthetic_only:
            raise ValueError("experiment candidates must be synthetic_only")
        return self


InformationCandidate = (
    ClarificationCandidate | RetrievalCandidate | ObservationCandidate | ExperimentCandidate
)


class ExpectedInformationGain(InformationAcquisitionFingerprintedModel):
    """Expected uncertainty reduction for one candidate."""

    estimate_id: str = Field(min_length=1)
    candidate_id: str = Field(min_length=1)
    gap_id: str = Field(min_length=1)
    prior_uncertainty: float = Field(ge=0.0, le=1.0)
    expected_posterior_uncertainty: float = Field(ge=0.0, le=1.0)
    decision_relevance: float = Field(ge=0.0, le=1.0)
    expected_information_gain: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("estimate_id", "candidate_id", "gap_id")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "information gain text")
        return value.strip()

    @field_validator("evidence_refs")
    @classmethod
    def refs_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(validate_acquisition_reference(item, "information gain ref") for item in value)

    @model_validator(mode="after")
    def expected_gain_must_match_uncertainty_reduction(self) -> Self:
        if self.expected_posterior_uncertainty > self.prior_uncertainty:
            raise ValueError("expected posterior uncertainty must not increase")
        expected = (self.prior_uncertainty - self.expected_posterior_uncertainty) * (
            self.decision_relevance
        )
        if abs(self.expected_information_gain - expected) > 1e-9:
            raise ValueError("expected_information_gain must match weighted uncertainty reduction")
        return self


class AcquisitionCost(InformationAcquisitionFingerprintedModel):
    """Bounded local cost estimate for one candidate."""

    cost_id: str = Field(min_length=1)
    candidate_id: str = Field(min_length=1)
    time_cost: float = Field(ge=0.0, le=1.0)
    attention_cost: float = Field(ge=0.0, le=1.0)
    resource_cost: float = Field(ge=0.0, le=1.0)
    total_cost: float = Field(ge=0.0, le=1.0)
    network_calls: int = Field(default=0, ge=0)
    connector_calls: int = Field(default=0, ge=0)
    model_provider_calls: int = Field(default=0, ge=0)
    tool_calls: int = Field(default=0, ge=0)
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("cost_id", "candidate_id")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "acquisition cost text")
        return value.strip()

    @field_validator("evidence_refs")
    @classmethod
    def refs_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(validate_acquisition_reference(item, "acquisition cost ref") for item in value)

    @model_validator(mode="after")
    def cost_must_be_bounded_and_local(self) -> Self:
        expected = min(1.0, self.time_cost + self.attention_cost + self.resource_cost)
        if abs(self.total_cost - expected) > 1e-9:
            raise ValueError("total_cost must equal bounded component sum")
        for key in ("network_calls", "connector_calls", "model_provider_calls", "tool_calls"):
            if getattr(self, key) != 0:
                raise ValueError(f"{key} must be zero")
        return self


class AcquisitionRisk(InformationAcquisitionFingerprintedModel):
    """Fail-closed permission, safety, and policy risk for one candidate."""

    risk_id: str = Field(min_length=1)
    candidate_id: str = Field(min_length=1)
    severity: RiskSeverity
    safety_risk: float = Field(ge=0.0, le=1.0)
    privacy_risk: float = Field(ge=0.0, le=1.0)
    policy_risk: float = Field(ge=0.0, le=1.0)
    irreversible_risk: float = Field(default=0.0, ge=0.0, le=1.0)
    overall_risk: float = Field(ge=0.0, le=1.0)
    permission_required: bool = True
    permission_granted: bool = False
    blocked: bool = False
    rationale: str = Field(min_length=1)
    unauthorized_information_acquisition: int = Field(default=0, ge=0)
    external_call_risk: int = Field(default=0, ge=0)
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("risk_id", "candidate_id", "rationale")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "acquisition risk text")
        return value.strip()

    @field_validator("evidence_refs")
    @classmethod
    def refs_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(validate_acquisition_reference(item, "acquisition risk ref") for item in value)

    @model_validator(mode="after")
    def risk_must_fail_closed(self) -> Self:
        expected = max(
            self.safety_risk,
            self.privacy_risk,
            self.policy_risk,
            self.irreversible_risk,
        )
        if abs(self.overall_risk - expected) > 1e-9:
            raise ValueError("overall_risk must equal the highest risk component")
        if self.permission_required and not self.permission_granted and not self.blocked:
            raise ValueError("unapproved candidates must be blocked")
        if self.unauthorized_information_acquisition != 0:
            raise ValueError("unauthorized_information_acquisition must be zero")
        if self.external_call_risk != 0:
            raise ValueError("external_call_risk must be zero")
        return self


class InformationStoppingDecision(InformationAcquisitionFingerprintedModel):
    """Decision to continue or stop based on expected value, cost, and risk."""

    decision_id: str = Field(min_length=1)
    plan_id: str = Field(min_length=1)
    continue_acquisition: bool
    reason: str = Field(min_length=1)
    selected_candidate_ids: tuple[str, ...] = Field(default_factory=tuple)
    expected_value: float = Field(ge=0.0, le=1.0)
    total_cost: float = Field(ge=0.0, le=1.0)
    total_risk: float = Field(ge=0.0, le=1.0)
    stopped_because_value_below_cost: bool = False
    unauthorized_information_acquisition_count: int = Field(default=0, ge=0)
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("decision_id", "plan_id", "reason")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "stopping decision text")
        return value.strip()

    @field_validator("selected_candidate_ids", "evidence_refs")
    @classmethod
    def refs_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            reject_hidden_or_secret_text(item, "stopping decision ref")
        return value

    @model_validator(mode="after")
    def stopping_rule_must_hold(self) -> Self:
        if self.unauthorized_information_acquisition_count != 0:
            raise ValueError("unauthorized information acquisition count must be zero")
        threshold = self.total_cost + self.total_risk
        if self.expected_value <= threshold:
            if self.continue_acquisition:
                raise ValueError("continue_acquisition requires value above cost and risk")
            if not self.stopped_because_value_below_cost:
                raise ValueError("low expected value must set stopped_because_value_below_cost")
        if self.continue_acquisition and not self.selected_candidate_ids:
            raise ValueError("continuing acquisition requires selected candidates")
        if not self.continue_acquisition and self.selected_candidate_ids:
            raise ValueError("stopped decisions must not select candidates")
        return self


class InformationAcquisitionEvidence(InformationAcquisitionFingerprintedModel):
    """Implementation evidence for AION-194 active information acquisition."""

    evidence_id: str = Field(min_length=1)
    plan_id: str = Field(min_length=1)
    authorization_id: str = AUTHORIZATION_ID
    implementation_task: str = IMPLEMENTATION_TASK
    uncertainty_detection_count: int = Field(ge=0)
    expected_information_gain_required: bool = True
    candidate_ranking_deterministic: bool = True
    permission_enforcement_passed: bool = True
    stopping_decision_required: bool = True
    unauthorized_information_acquisition_count: int = Field(default=0, ge=0)
    forbidden_side_effects: int = Field(default=0, ge=0)
    runtime_boundary: InformationAcquisitionRuntimeBoundary
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("evidence_id", "plan_id", "authorization_id", "implementation_task")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "acquisition evidence text")
        return value.strip()

    @field_validator("evidence_refs")
    @classmethod
    def refs_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(
            validate_acquisition_reference(item, "acquisition evidence ref") for item in value
        )

    @model_validator(mode="after")
    def hard_pass_invariants_must_hold(self) -> Self:
        if self.authorization_id != AUTHORIZATION_ID:
            raise ValueError(f"authorization_id must be {AUTHORIZATION_ID}")
        if self.implementation_task != IMPLEMENTATION_TASK:
            raise ValueError(f"implementation_task must be {IMPLEMENTATION_TASK}")
        for key in (
            "expected_information_gain_required",
            "candidate_ranking_deterministic",
            "permission_enforcement_passed",
            "stopping_decision_required",
        ):
            if not getattr(self, key):
                raise ValueError(f"{key} must be true")
        if self.uncertainty_detection_count < 1:
            raise ValueError("uncertainty detection must produce at least one gap")
        if self.unauthorized_information_acquisition_count != 0:
            raise ValueError("unauthorized information acquisition must be zero")
        if self.forbidden_side_effects != 0:
            raise ValueError("forbidden_side_effects must be zero")
        return self


class InformationAcquisitionPlan(InformationAcquisitionFingerprintedModel):
    """Ranked, permission-bound information request plan."""

    plan_id: str = Field(min_length=1)
    need: InformationNeed
    gaps: tuple[KnowledgeGap, ...]
    candidates: tuple[InformationCandidate, ...]
    gain_estimates: tuple[ExpectedInformationGain, ...]
    costs: tuple[AcquisitionCost, ...]
    risks: tuple[AcquisitionRisk, ...]
    selected_candidate_ids: tuple[str, ...]
    stopping_decision: InformationStoppingDecision
    evidence: InformationAcquisitionEvidence
    acquisition_performed: bool = False
    external_call_performed: bool = False
    tool_execution_performed: bool = False
    hidden_mutation_performed: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("plan_id")
    @classmethod
    def text_must_be_safe(cls, value: str) -> str:
        reject_hidden_or_secret_text(value, "information acquisition plan id")
        return value.strip()

    @field_validator("selected_candidate_ids")
    @classmethod
    def selected_ids_must_be_safe(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for item in value:
            reject_hidden_or_secret_text(item, "selected candidate id")
        return value

    @model_validator(mode="after")
    def plan_consistency_must_hold(self) -> Self:
        if not self.gaps:
            raise ValueError("information acquisition plans require knowledge gaps")
        if not self.candidates:
            raise ValueError("information acquisition plans require candidates")
        candidate_ids = {candidate.candidate_id for candidate in self.candidates}
        selected_ids = set(self.selected_candidate_ids)
        if not selected_ids.issubset(candidate_ids):
            raise ValueError("selected candidates must exist in plan candidates")
        for collection_name, collection in (
            ("gain estimates", self.gain_estimates),
            ("costs", self.costs),
            ("risks", self.risks),
        ):
            missing = candidate_ids.difference(item.candidate_id for item in collection)
            if missing:
                raise ValueError(f"missing {collection_name} for candidates: {sorted(missing)}")
        risks_by_candidate = {risk.candidate_id: risk for risk in self.risks}
        candidates_by_id = {candidate.candidate_id: candidate for candidate in self.candidates}
        for candidate_id in selected_ids:
            candidate = candidates_by_id[candidate_id]
            risk = risks_by_candidate[candidate_id]
            if not candidate.permission_granted:
                raise ValueError("selected candidates require permission")
            if risk.blocked:
                raise ValueError("blocked candidates cannot be selected")
            if risk.unauthorized_information_acquisition != 0:
                raise ValueError("selected candidates must not acquire information")
        if tuple(self.selected_candidate_ids) != tuple(
            self.stopping_decision.selected_candidate_ids
        ):
            raise ValueError("stopping decision must match selected candidates")
        if self.stopping_decision.plan_id != self.plan_id:
            raise ValueError("stopping decision must refer to this plan")
        if self.evidence.plan_id != self.plan_id:
            raise ValueError("evidence must refer to this plan")
        for key in (
            "acquisition_performed",
            "external_call_performed",
            "tool_execution_performed",
            "hidden_mutation_performed",
        ):
            if getattr(self, key):
                raise ValueError(f"{key} must be false")
        return self


def acquisition_replay_hash(payload: object) -> str:
    """Return a deterministic information-acquisition hash."""

    return fingerprint_payload(payload)


def freeze_acquisition_metadata(value: dict[str, object]) -> FrozenDict:
    """Validate and freeze metadata used by information-acquisition fixtures."""

    reject_secret_like_payload(value)
    return cast(FrozenDict, freeze_payload(value))


__all__ = [
    "AUTHORIZATION_ID",
    "CANONICALIZATION_VERSION",
    "IMPLEMENTATION_TASK",
    "SCHEMA_VERSION",
    "AcquisitionCost",
    "AcquisitionRisk",
    "CandidateStatus",
    "CandidateType",
    "ClarificationCandidate",
    "ExpectedInformationGain",
    "ExperimentCandidate",
    "InformationAcquisitionEvidence",
    "InformationAcquisitionFingerprintedModel",
    "InformationAcquisitionModel",
    "InformationAcquisitionPlan",
    "InformationAcquisitionRuntimeBoundary",
    "InformationCandidate",
    "InformationNeed",
    "InformationStoppingDecision",
    "KnowledgeGap",
    "ObservationCandidate",
    "RetrievalCandidate",
    "RiskSeverity",
    "acquisition_replay_hash",
    "freeze_acquisition_metadata",
    "validate_acquisition_reference",
]
