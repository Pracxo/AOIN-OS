"""AION-226 governed engagement-learning shadow-application contracts.

The records in this module model only deterministic, operator-approved,
non-factual engagement-learning shadow application. They do not persist
overlays, mutate production policy, write memory, create approvals, or affect
beliefs.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable, Mapping, Sequence
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from pathlib import Path
from types import MappingProxyType
from typing import Any, ClassVar, Final, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.governed_learning_memory_persistence import (
    LocalKnowledgeQueryResult,
    LocalProjectionQueryResult,
)
from aion_brain.contracts.knowledge_research import (
    ensure_utc,
    fingerprint_payload,
    reject_protected_material,
    validate_hex64,
)
from aion_brain.contracts.knowledge_verified_memory import (
    EngagementLearningCandidate,
    EngagementLearningCandidateKind,
    EngagementLearningLifecycleStatus,
    EngagementSignalBatch,
)

ENGAGEMENT_APPLICATION_CONTRACT_SCHEMA_VERSION: Final[
    Literal["aion-glm-engagement-application/v1"]
] = "aion-glm-engagement-application/v1"
ENGAGEMENT_APPLICATION_AUTHORIZATION_SCHEMA_VERSION: Final[
    Literal["aion-glm-engagement-application-authorization/v1"]
] = "aion-glm-engagement-application-authorization/v1"
ENGAGEMENT_CANDIDATE_BINDING_SCHEMA_VERSION: Final[
    Literal["aion-glm-engagement-candidate-binding/v1"]
] = "aion-glm-engagement-candidate-binding/v1"
ENGAGEMENT_CANDIDATE_LIFECYCLE_SCHEMA_VERSION: Final[
    Literal["aion-glm-engagement-candidate-lifecycle/v1"]
] = "aion-glm-engagement-candidate-lifecycle/v1"
ENGAGEMENT_APPLICATION_APPROVAL_EVIDENCE_SCHEMA_VERSION: Final[
    Literal["aion-glm-engagement-application-approval-evidence/v1"]
] = "aion-glm-engagement-application-approval-evidence/v1"
ENGAGEMENT_APPLICATION_APPROVAL_BUNDLE_SCHEMA_VERSION: Final[
    Literal["aion-glm-engagement-application-approval-bundle/v1"]
] = "aion-glm-engagement-application-approval-bundle/v1"
ENGAGEMENT_APPLICATION_RISK_SCHEMA_VERSION: Final[
    Literal["aion-glm-engagement-application-risk/v1"]
] = "aion-glm-engagement-application-risk/v1"
ENGAGEMENT_ADAPTATION_IDENTITY_SCHEMA_VERSION: Final[
    Literal["aion-glm-engagement-adaptation-identity/v1"]
] = "aion-glm-engagement-adaptation-identity/v1"
ENGAGEMENT_ADAPTATION_CONFLICT_SCHEMA_VERSION: Final[
    Literal["aion-glm-engagement-adaptation-conflict/v1"]
] = "aion-glm-engagement-adaptation-conflict/v1"
ENGAGEMENT_ADAPTATION_VERSION_SCHEMA_VERSION: Final[
    Literal["aion-glm-engagement-adaptation-version/v1"]
] = "aion-glm-engagement-adaptation-version/v1"
ENGAGEMENT_TARGET_POLICY_SCHEMA_VERSION: Final[
    Literal["aion-glm-engagement-target-policy/v1"]
] = "aion-glm-engagement-target-policy/v1"
ENGAGEMENT_OVERLAY_RECORD_SCHEMA_VERSION: Final[
    Literal["aion-glm-engagement-overlay-record/v1"]
] = "aion-glm-engagement-overlay-record/v1"
ENGAGEMENT_OVERLAY_SNAPSHOT_SCHEMA_VERSION: Final[
    Literal["aion-glm-engagement-overlay-snapshot/v1"]
] = "aion-glm-engagement-overlay-snapshot/v1"
ENGAGEMENT_BASELINE_SNAPSHOT_SCHEMA_VERSION: Final[
    Literal["aion-glm-engagement-baseline-snapshot/v1"]
] = "aion-glm-engagement-baseline-snapshot/v1"
ENGAGEMENT_COUNTERFACTUAL_CASE_SCHEMA_VERSION: Final[
    Literal["aion-glm-engagement-counterfactual-case/v1"]
] = "aion-glm-engagement-counterfactual-case/v1"
ENGAGEMENT_COUNTERFACTUAL_RESULT_SCHEMA_VERSION: Final[
    Literal["aion-glm-engagement-counterfactual-result/v1"]
] = "aion-glm-engagement-counterfactual-result/v1"
ENGAGEMENT_METRIC_DELTA_SCHEMA_VERSION: Final[
    Literal["aion-glm-engagement-metric-delta/v1"]
] = "aion-glm-engagement-metric-delta/v1"
ENGAGEMENT_ROLLBACK_PLAN_SCHEMA_VERSION: Final[
    Literal["aion-glm-engagement-rollback/v1"]
] = "aion-glm-engagement-rollback/v1"
ENGAGEMENT_APPLICATION_PLAN_SCHEMA_VERSION: Final[
    Literal["aion-glm-engagement-application-plan/v1"]
] = "aion-glm-engagement-application-plan/v1"
ENGAGEMENT_APPLICATION_RESULT_SCHEMA_VERSION: Final[
    Literal["aion-glm-engagement-application-result/v1"]
] = "aion-glm-engagement-application-result/v1"
ENGAGEMENT_APPLICATION_QUERY_SCHEMA_VERSION: Final[
    Literal["aion-glm-engagement-application-query/v1"]
] = "aion-glm-engagement-application-query/v1"
ENGAGEMENT_APPLICATION_QUERY_RESULT_SCHEMA_VERSION: Final[
    Literal["aion-glm-engagement-application-query-result/v1"]
] = "aion-glm-engagement-application-query-result/v1"
ENGAGEMENT_APPLICATION_FIXTURE_SCHEMA_VERSION: Final[
    Literal["aion-glm-engagement-application-fixture/v1"]
] = "aion-glm-engagement-application-fixture/v1"
ENGAGEMENT_APPLICATION_INTEGRITY_SCHEMA_VERSION: Final[
    Literal["aion-glm-engagement-application-integrity/v1"]
] = "aion-glm-engagement-application-integrity/v1"
ENGAGEMENT_APPLICATION_EVIDENCE_SCHEMA_VERSION: Final[
    Literal["aion-glm-engagement-application-evidence/v1"]
] = "aion-glm-engagement-application-evidence/v1"
ENGAGEMENT_APPLICATION_REASON_REGISTRY_VERSION: Final = (
    "aion-glm-engagement-application-reasons/v1"
)

PROGRAM_ID: Final = "AION-GOVERNED-LEARNING-MEMORY-001"
AUTHORIZATION_TRANSACTION_ID: Final = "AION-225-GLM-0003"
APPROVAL_RECORD_ID: Final = "AION-225-GLM-0003"
IMPLEMENTATION_TASK: Final = "AION-226"
FORMAL_CLOSEOUT_TASK: Final = "AION-227"
AUTHORIZATION_SCOPE: Final = (
    "engagement-learning-candidate-non-factual-validation-operator-approval-"
    "risk-routing-bounded-adaptation-versioning-isolated-in-memory-shadow-overlay-"
    "counterfactual-evaluation-rollback-expiry-audit-core"
)

MODEL_CONFIG: Final = ConfigDict(extra="forbid", hide_input_in_errors=True)
FROZEN_MODEL_CONFIG: Final = ConfigDict(
    extra="forbid", hide_input_in_errors=True, frozen=True
)
QUANT: Final = Decimal("0.000001")
ZERO: Final = Decimal("0.000000")

MAXIMUM_ENGAGEMENT_CANDIDATES_PER_BATCH = 500
MAXIMUM_SIGNAL_REFERENCES_PER_CANDIDATE = 1000
MAXIMUM_CANDIDATE_VERSIONS_PER_IDENTITY = 100
MAXIMUM_TARGET_COMPONENTS = 9
MAXIMUM_APPROVAL_EVIDENCE_RECORDS_PER_APPLICATION = 4
MAXIMUM_ADAPTATION_PLANS_PER_BATCH = 500
MAXIMUM_OVERLAY_RECORDS_PER_SESSION = 500
MAXIMUM_OVERLAY_VERSIONS_PER_IDENTITY = 100
MAXIMUM_OVERLAY_SNAPSHOTS_PER_SESSION = 100
MAXIMUM_COUNTERFACTUAL_CASES_PER_SESSION = 1000
MAXIMUM_METRICS_PER_CASE = 100
MAXIMUM_BASELINE_CANDIDATE_COMPARISONS = 1000
MAXIMUM_ROLLBACK_STEPS_PER_APPLICATION = 50
MAXIMUM_OPERATOR_REVIEW_ITEMS = 500
MAXIMUM_QUERY_RESULTS = 1000
MAXIMUM_FIXTURE_RECORDS = 5000
MAXIMUM_FIXTURE_BYTES = 4_194_304
MAXIMUM_CONCURRENCY = 4

ZERO_EFFECT_LIMITS: Final[Mapping[str, int]] = MappingProxyType(
    {
        "maximum_persistent_engagement_overlay_writes": 0,
        "maximum_aion_224_store_writes": 0,
        "maximum_production_policy_mutations": 0,
        "maximum_engagement_fact_promotions": 0,
        "maximum_engagement_confidence_effects": 0,
        "maximum_engagement_knowledge_effects": 0,
        "maximum_engagement_source_independence_effects": 0,
        "maximum_cognitive_memory_writes": 0,
        "maximum_actual_belief_creations": 0,
        "maximum_actual_belief_mutations": 0,
        "maximum_automatic_candidate_approvals": 0,
        "maximum_automatic_knowledge_promotions": 0,
        "maximum_network_calls": 0,
        "maximum_search_provider_calls": 0,
        "maximum_connector_calls": 0,
        "maximum_model_provider_calls": 0,
        "maximum_actual_tool_executions": 0,
        "maximum_shell_commands": 0,
        "maximum_subprocess_executions": 0,
        "maximum_browser_actions": 0,
        "maximum_source_mutations": 0,
        "maximum_git_operations": 0,
        "maximum_runtime_created_pull_requests": 0,
        "maximum_runtime_created_approvals": 0,
        "maximum_deployments": 0,
        "maximum_model_weight_changes": 0,
    }
)

RESOURCE_LIMITS: Final[Mapping[str, int]] = MappingProxyType(
    {
        "maximum_engagement_candidates_per_batch": MAXIMUM_ENGAGEMENT_CANDIDATES_PER_BATCH,
        "maximum_signal_references_per_candidate": MAXIMUM_SIGNAL_REFERENCES_PER_CANDIDATE,
        "maximum_candidate_versions_per_identity": MAXIMUM_CANDIDATE_VERSIONS_PER_IDENTITY,
        "maximum_target_components": MAXIMUM_TARGET_COMPONENTS,
        "maximum_approval_evidence_records_per_application": (
            MAXIMUM_APPROVAL_EVIDENCE_RECORDS_PER_APPLICATION
        ),
        "maximum_adaptation_plans_per_batch": MAXIMUM_ADAPTATION_PLANS_PER_BATCH,
        "maximum_overlay_records_per_session": MAXIMUM_OVERLAY_RECORDS_PER_SESSION,
        "maximum_overlay_versions_per_identity": MAXIMUM_OVERLAY_VERSIONS_PER_IDENTITY,
        "maximum_overlay_snapshots_per_session": MAXIMUM_OVERLAY_SNAPSHOTS_PER_SESSION,
        "maximum_counterfactual_cases_per_session": MAXIMUM_COUNTERFACTUAL_CASES_PER_SESSION,
        "maximum_metrics_per_case": MAXIMUM_METRICS_PER_CASE,
        "maximum_baseline_candidate_comparisons": MAXIMUM_BASELINE_CANDIDATE_COMPARISONS,
        "maximum_rollback_steps_per_application": MAXIMUM_ROLLBACK_STEPS_PER_APPLICATION,
        "maximum_operator_review_items": MAXIMUM_OPERATOR_REVIEW_ITEMS,
        "maximum_query_results": MAXIMUM_QUERY_RESULTS,
        "maximum_fixture_records": MAXIMUM_FIXTURE_RECORDS,
        "maximum_fixture_bytes": MAXIMUM_FIXTURE_BYTES,
        "maximum_concurrency": MAXIMUM_CONCURRENCY,
        **ZERO_EFFECT_LIMITS,
    }
)

_SAFE_ID_RE: Final = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_HEX_RE: Final = re.compile(r"^[0-9a-f]{64}$")
_URI_RE: Final = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
_PROTECTED_FIXTURE_MARKERS: Final = (
    "raw user message",
    "prompt transcript",
    "personal data",
    "credential",
    "token",
    "source body",
    "source preview",
    "click url",
    "ip address",
    "device fingerprint",
    "hidden reasoning",
    "source patch",
    "raw diff",
    "shell command",
    "executable code",
)


class EngagementApplicationMode(StrEnum):
    DETERMINISTIC_SIMULATION = "deterministic_simulation"
    OPERATOR_INVOKED_SHADOW = "operator_invoked_shadow"


class EngagementApplicationRiskClass(StrEnum):
    LOW = "low"
    ELEVATED = "elevated"


class EngagementCandidateDisposition(StrEnum):
    ELIGIBLE_FOR_SHADOW = "eligible_for_shadow"
    INELIGIBLE = "ineligible"
    EXPIRED = "expired"
    SUPERSEDED = "superseded"
    RETRACTED = "retracted"
    REJECTED = "rejected"
    EXACT_DUPLICATE_NO_OP = "exact_duplicate_no_op"
    CONFLICT_BLOCKED = "conflict_blocked"
    APPROVAL_BLOCKED = "approval_blocked"
    ABSTAINED = "abstained"


class EngagementAdaptationOperation(StrEnum):
    FLAG_RESEARCH_GAP = "flag_research_gap"
    REQUIRE_CLARIFICATION_REVIEW = "require_clarification_review"
    SELECT_RETRIEVAL_STRATEGY_CANDIDATE = "select_retrieval_strategy_candidate"
    SELECT_SOURCE_SELECTION_CANDIDATE = "select_source_selection_candidate"
    SELECT_DOMAIN_ROUTING_CANDIDATE = "select_domain_routing_candidate"
    SELECT_VERIFICATION_RULE_CANDIDATE = "select_verification_rule_candidate"
    RECORD_TOOL_MANIFEST_GAP_CANDIDATE = "record_tool_manifest_gap_candidate"
    SELECT_RESPONSE_QUALITY_CANDIDATE = "select_response_quality_candidate"
    SELECT_PREFERENCE_HINT_CANDIDATE = "select_preference_hint_candidate"


class EngagementAdaptationVersionDisposition(StrEnum):
    INITIAL_VERSION_PLANNED = "initial_version_planned"
    NEW_VERSION_PLANNED = "new_version_planned"
    SUPERSESSION_PLANNED = "supersession_planned"
    RETRACTION_PLANNED = "retraction_planned"
    EXPIRY_PLANNED = "expiry_planned"
    EXACT_DUPLICATE_NO_OP = "exact_duplicate_no_op"
    BLOCKED = "blocked"


class EngagementOverlayStatus(StrEnum):
    PLANNED = "planned"
    ACTIVE_SHADOW = "active_shadow"
    EXPIRED = "expired"
    ROLLED_BACK = "rolled_back"
    BLOCKED = "blocked"


class EngagementApplicationStatus(StrEnum):
    DRAFTED = "drafted"
    VALIDATED = "validated"
    SHADOW_APPLIED = "shadow_applied"
    BASELINE_RETAINED = "baseline_retained"
    CANDIDATE_REVISION_REQUIRED = "candidate_revision_required"
    CANDIDATE_REJECTED = "candidate_rejected"
    ABSTAINED = "abstained"
    BLOCKED = "blocked"
    DUPLICATE_NO_OP = "duplicate_no_op"
    EXPIRED = "expired"
    ROLLED_BACK = "rolled_back"
    INTEGRITY_FAILED = "integrity_failed"


class EngagementCounterfactualRecommendation(StrEnum):
    RETAIN_BASELINE = "retain_baseline"
    APPROVE_SHADOW_CANDIDATE = "approve_shadow_candidate"
    REVISE_CANDIDATE = "revise_candidate"
    REJECT_CANDIDATE = "reject_candidate"
    ABSTAIN = "abstain"


class EngagementMetricDirection(StrEnum):
    HIGHER_IS_BETTER = "higher_is_better"
    LOWER_IS_BETTER = "lower_is_better"
    ZERO_REQUIRED = "zero_required"


class EngagementIntegrityStatus(StrEnum):
    PASSED = "passed"
    FAILED = "failed"


class EngagementTargetSpec(BaseModel):
    model_config = FROZEN_MODEL_CONFIG

    candidate_kind: EngagementLearningCandidateKind
    target_component_code: str
    target_policy_code: str
    canonical_operation: EngagementAdaptationOperation
    risk_class: EngagementApplicationRiskClass


TARGET_REGISTRY: Final[Mapping[EngagementLearningCandidateKind, EngagementTargetSpec]] = (
    MappingProxyType(
        {
            EngagementLearningCandidateKind.RESEARCH_GAP: EngagementTargetSpec(
                candidate_kind=EngagementLearningCandidateKind.RESEARCH_GAP,
                target_component_code="research-acquisition",
                target_policy_code="research-gap-review",
                canonical_operation=EngagementAdaptationOperation.FLAG_RESEARCH_GAP,
                risk_class=EngagementApplicationRiskClass.LOW,
            ),
            EngagementLearningCandidateKind.CLARIFICATION_NEED: EngagementTargetSpec(
                candidate_kind=EngagementLearningCandidateKind.CLARIFICATION_NEED,
                target_component_code="operator-dialogue",
                target_policy_code="clarification-review",
                canonical_operation=(
                    EngagementAdaptationOperation.REQUIRE_CLARIFICATION_REVIEW
                ),
                risk_class=EngagementApplicationRiskClass.LOW,
            ),
            EngagementLearningCandidateKind.RETRIEVAL_STRATEGY: EngagementTargetSpec(
                candidate_kind=EngagementLearningCandidateKind.RETRIEVAL_STRATEGY,
                target_component_code="retrieval-planning",
                target_policy_code="retrieval-strategy-review",
                canonical_operation=(
                    EngagementAdaptationOperation.SELECT_RETRIEVAL_STRATEGY_CANDIDATE
                ),
                risk_class=EngagementApplicationRiskClass.ELEVATED,
            ),
            EngagementLearningCandidateKind.SOURCE_SELECTION: EngagementTargetSpec(
                candidate_kind=EngagementLearningCandidateKind.SOURCE_SELECTION,
                target_component_code="source-registry",
                target_policy_code="source-selection-review",
                canonical_operation=(
                    EngagementAdaptationOperation.SELECT_SOURCE_SELECTION_CANDIDATE
                ),
                risk_class=EngagementApplicationRiskClass.ELEVATED,
            ),
            EngagementLearningCandidateKind.DOMAIN_ROUTING: EngagementTargetSpec(
                candidate_kind=EngagementLearningCandidateKind.DOMAIN_ROUTING,
                target_component_code="domain-expert-mesh",
                target_policy_code="domain-routing-review",
                canonical_operation=(
                    EngagementAdaptationOperation.SELECT_DOMAIN_ROUTING_CANDIDATE
                ),
                risk_class=EngagementApplicationRiskClass.ELEVATED,
            ),
            EngagementLearningCandidateKind.VERIFICATION_RULE: EngagementTargetSpec(
                candidate_kind=EngagementLearningCandidateKind.VERIFICATION_RULE,
                target_component_code="tool-verification",
                target_policy_code="verification-rule-review",
                canonical_operation=(
                    EngagementAdaptationOperation.SELECT_VERIFICATION_RULE_CANDIDATE
                ),
                risk_class=EngagementApplicationRiskClass.ELEVATED,
            ),
            EngagementLearningCandidateKind.TOOL_MANIFEST_GAP: EngagementTargetSpec(
                candidate_kind=EngagementLearningCandidateKind.TOOL_MANIFEST_GAP,
                target_component_code="tool-manifest-registry",
                target_policy_code="tool-manifest-gap-review",
                canonical_operation=(
                    EngagementAdaptationOperation.RECORD_TOOL_MANIFEST_GAP_CANDIDATE
                ),
                risk_class=EngagementApplicationRiskClass.ELEVATED,
            ),
            EngagementLearningCandidateKind.RESPONSE_QUALITY: EngagementTargetSpec(
                candidate_kind=EngagementLearningCandidateKind.RESPONSE_QUALITY,
                target_component_code="operator-response",
                target_policy_code="response-quality-review",
                canonical_operation=(
                    EngagementAdaptationOperation.SELECT_RESPONSE_QUALITY_CANDIDATE
                ),
                risk_class=EngagementApplicationRiskClass.LOW,
            ),
            EngagementLearningCandidateKind.PREFERENCE_CANDIDATE: EngagementTargetSpec(
                candidate_kind=EngagementLearningCandidateKind.PREFERENCE_CANDIDATE,
                target_component_code="preference-review",
                target_policy_code="operator-preference-review",
                canonical_operation=(
                    EngagementAdaptationOperation.SELECT_PREFERENCE_HINT_CANDIDATE
                ),
                risk_class=EngagementApplicationRiskClass.LOW,
            ),
        }
    )
)

PARAMETER_CODE_REGISTRY: Final[tuple[str, ...]] = (
    "additional_validation_required",
    "baseline_fallback_required",
    "candidate_enabled_for_shadow",
    "candidate_preferred_for_shadow",
    "operator_confirmation_required",
    "review_required",
)

METRIC_DIRECTIONS: Final[Mapping[str, EngagementMetricDirection]] = MappingProxyType(
    {
        "task_completion": EngagementMetricDirection.HIGHER_IS_BETTER,
        "retrieval_success": EngagementMetricDirection.HIGHER_IS_BETTER,
        "source_diversity": EngagementMetricDirection.HIGHER_IS_BETTER,
        "citation_completeness": EngagementMetricDirection.HIGHER_IS_BETTER,
        "abstention_correctness": EngagementMetricDirection.HIGHER_IS_BETTER,
        "routing_consistency": EngagementMetricDirection.HIGHER_IS_BETTER,
        "verification_coverage": EngagementMetricDirection.HIGHER_IS_BETTER,
        "response_format_compliance": EngagementMetricDirection.HIGHER_IS_BETTER,
        "clarification_count": EngagementMetricDirection.LOWER_IS_BETTER,
        "latency": EngagementMetricDirection.LOWER_IS_BETTER,
        "bounded_resource_cost": EngagementMetricDirection.LOWER_IS_BETTER,
        "policy_violations": EngagementMetricDirection.ZERO_REQUIRED,
        "safety_violations": EngagementMetricDirection.ZERO_REQUIRED,
    }
)

REASON_CODE_REGISTRY: Final[tuple[str, ...]] = (
    "engagement_candidate_binding_valid",
    "engagement_candidate_binding_invalid",
    "engagement_signal_lineage_valid",
    "engagement_signal_lineage_invalid",
    "engagement_candidate_non_factual_passed",
    "engagement_candidate_non_factual_failed",
    "engagement_candidate_zero_confidence_effect_passed",
    "engagement_candidate_zero_confidence_effect_failed",
    "engagement_candidate_zero_knowledge_effect_passed",
    "engagement_candidate_zero_knowledge_effect_failed",
    "engagement_candidate_zero_source_independence_effect_passed",
    "engagement_candidate_zero_source_independence_effect_failed",
    "engagement_candidate_zero_belief_effect_passed",
    "engagement_candidate_zero_belief_effect_failed",
    "engagement_candidate_expired",
    "engagement_candidate_superseded",
    "engagement_candidate_retracted",
    "engagement_candidate_rejected",
    "engagement_candidate_version_valid",
    "engagement_candidate_version_invalid",
    "engagement_risk_low",
    "engagement_risk_elevated",
    "engagement_risk_downgrade_rejected",
    "engagement_approval_valid",
    "engagement_approval_expired",
    "engagement_approval_revoked",
    "engagement_approval_denied",
    "engagement_approval_cancelled",
    "engagement_approval_scope_mismatch",
    "engagement_approval_candidate_mismatch",
    "engagement_approval_overlay_mismatch",
    "engagement_approval_baseline_mismatch",
    "engagement_approval_fixture_mismatch",
    "engagement_approval_rollback_mismatch",
    "engagement_approval_insufficient_approvers",
    "engagement_separation_of_duties_passed",
    "engagement_separation_of_duties_failed",
    "engagement_runtime_approval_creation_blocked",
    "engagement_adaptation_identity_derived",
    "engagement_adaptation_identity_collision",
    "engagement_adaptation_duplicate",
    "engagement_adaptation_conflict",
    "engagement_target_conflict",
    "engagement_version_initial_planned",
    "engagement_version_new_planned",
    "engagement_version_supersession_planned",
    "engagement_version_retraction_planned",
    "engagement_version_expiry_planned",
    "engagement_version_collision",
    "engagement_overlay_planned",
    "engagement_overlay_active_shadow",
    "engagement_overlay_expired",
    "engagement_overlay_rolled_back",
    "engagement_overlay_persistence_blocked",
    "engagement_production_policy_mutation_blocked",
    "engagement_baseline_valid",
    "engagement_counterfactual_valid",
    "engagement_metric_delta_valid",
    "engagement_safety_gate_passed",
    "engagement_safety_gate_failed",
    "engagement_policy_gate_passed",
    "engagement_policy_gate_failed",
    "engagement_retain_baseline",
    "engagement_approve_shadow_candidate",
    "engagement_revise_candidate",
    "engagement_reject_candidate",
    "engagement_abstain",
    "engagement_rollback_valid",
    "engagement_rollback_invalid",
    "engagement_expiry_valid",
    "engagement_expiry_invalid",
    "engagement_integrity_passed",
    "engagement_integrity_failed",
    "engagement_fixture_replay_passed",
    "engagement_resource_budget_passed",
    "engagement_resource_budget_failed",
    "engagement_factual_effect_blocked",
    "engagement_confidence_effect_blocked",
    "engagement_knowledge_effect_blocked",
    "engagement_source_independence_effect_blocked",
    "engagement_memory_write_blocked",
    "engagement_belief_effect_blocked",
    "engagement_model_weight_effect_blocked",
    "engagement_network_effect_blocked",
    "engagement_runtime_disabled",
)
REASON_CODE_SET: Final = frozenset(REASON_CODE_REGISTRY)

def utc_now() -> datetime:
    return datetime.now(UTC)


def validate_safe_id(value: str, field_name: str = "identifier") -> str:
    if not _SAFE_ID_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a safe bounded ASCII identifier")
    reject_protected_material(value, field_name)
    return value


def validate_reason_codes(value: Sequence[str]) -> tuple[str, ...]:
    reason_codes = tuple(value)
    if len(reason_codes) != len(set(reason_codes)):
        raise ValueError("duplicate engagement reason code")
    unknown = [code for code in reason_codes if code not in REASON_CODE_SET]
    if unknown:
        raise ValueError("unknown engagement reason code")
    return reason_codes


def validate_parameter_codes(value: Sequence[str]) -> tuple[str, ...]:
    codes = tuple(value)
    if len(codes) != len(set(codes)):
        raise ValueError("duplicate engagement parameter code")
    unknown = [code for code in codes if code not in PARAMETER_CODE_REGISTRY]
    if unknown:
        raise ValueError("unknown engagement parameter code")
    return codes


def _q(value: Decimal | int | float | str) -> Decimal:
    try:
        decimal = Decimal(str(value)).quantize(QUANT)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("metric value must be finite decimal") from exc
    if not decimal.is_finite():
        raise ValueError("metric value must be finite")
    return decimal


def _jsonable(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return _jsonable(value.model_dump(mode="python"))
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


def engagement_fingerprint(value: Any) -> str:
    return fingerprint_payload(_jsonable(value))


def model_fingerprint(model: BaseModel, exclude: set[str]) -> str:
    return engagement_fingerprint(model.model_dump(mode="python", exclude=exclude))


def build_record[T: BaseModel](
    model: type[T], payload: Mapping[str, Any], fingerprint_field: str
) -> T:
    data = dict(payload)
    data[fingerprint_field] = "0" * 64
    draft = model.model_construct(**data)
    data[fingerprint_field] = model_fingerprint(draft, {fingerprint_field})
    return model.model_validate(data)


def target_spec_for_candidate_kind(
    candidate_kind: EngagementLearningCandidateKind,
) -> EngagementTargetSpec:
    try:
        return TARGET_REGISTRY[candidate_kind]
    except KeyError as exc:
        raise ValueError("unknown engagement candidate kind") from exc


class StrictFrozenModel(BaseModel):
    model_config = FROZEN_MODEL_CONFIG
    fingerprint_field: ClassVar[str | None] = None

    @field_validator("*")
    @classmethod
    def validate_common_values(cls, value: Any) -> Any:
        if isinstance(value, datetime):
            return ensure_utc(value)
        if isinstance(value, Decimal):
            return _q(value)
        if isinstance(value, str) and _HEX_RE.fullmatch(value):
            return validate_hex64(value)
        return value

    @model_validator(mode="after")
    def validate_record(self) -> Self:
        field = self.fingerprint_field
        if field is not None:
            expected = model_fingerprint(self, {field})
            if getattr(self, field) != expected:
                raise ValueError(f"{field} mismatch")
        return self


class EngagementCandidateLifecycleEvidence(StrictFrozenModel):
    fingerprint_field: ClassVar[str | None] = "lifecycle_fingerprint"

    schema_version: Literal["aion-glm-engagement-candidate-lifecycle/v1"] = (
        ENGAGEMENT_CANDIDATE_LIFECYCLE_SCHEMA_VERSION
    )
    lifecycle_evidence_id: str
    learning_candidate_id: str
    candidate_fingerprint: str
    candidate_version: int = Field(ge=1, le=MAXIMUM_CANDIDATE_VERSIONS_PER_IDENTITY)
    lifecycle_status: EngagementLearningLifecycleStatus
    supersedes_candidate_id: str | None = None
    retraction_record_fingerprint: str | None = None
    observed_at: datetime
    valid_until: datetime
    externally_supplied: Literal[True] = True
    read_only: Literal[True] = True
    redacted: Literal[True] = True
    lifecycle_fingerprint: str

    @model_validator(mode="after")
    def validate_lifecycle_evidence(self) -> Self:
        if self.valid_until <= self.observed_at:
            raise ValueError("lifecycle evidence must be unexpired when observed")
        if self.retraction_record_fingerprint is not None:
            validate_hex64(self.retraction_record_fingerprint, "retraction fingerprint")
        return self


class EngagementCandidateBinding(StrictFrozenModel):
    fingerprint_field: ClassVar[str | None] = "binding_fingerprint"

    schema_version: Literal["aion-glm-engagement-candidate-binding/v1"] = (
        ENGAGEMENT_CANDIDATE_BINDING_SCHEMA_VERSION
    )
    binding_id: str
    candidate: EngagementLearningCandidate
    signal_batch: EngagementSignalBatch
    learning_candidate_id: str
    candidate_fingerprint: str
    candidate_kind: EngagementLearningCandidateKind
    candidate_version: int = Field(ge=1, le=MAXIMUM_CANDIDATE_VERSIONS_PER_IDENTITY)
    lifecycle_status: EngagementLearningLifecycleStatus
    signal_ids: tuple[str, ...]
    signal_fingerprints: tuple[str, ...]
    subject_fingerprints: tuple[str, ...]
    target_component_code: str
    target_policy_code: str
    canonical_operation: EngagementAdaptationOperation
    lifecycle_evidence: EngagementCandidateLifecycleEvidence
    candidate_disposition: EngagementCandidateDisposition
    reason_codes: tuple[str, ...]
    non_factual_invariant_passed: bool
    zero_confidence_effect_passed: bool
    zero_knowledge_effect_passed: bool
    zero_source_independence_effect_passed: bool
    zero_belief_effect_passed: bool
    read_only: Literal[True] = True
    redacted: Literal[True] = True
    runtime_effect: Literal[False] = False
    binding_fingerprint: str

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_are_known(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_reason_codes(value)

    @model_validator(mode="after")
    def validate_binding(self) -> Self:
        if self.learning_candidate_id != self.candidate.learning_candidate_id:
            raise ValueError("candidate id mismatch")
        if self.candidate_fingerprint != self.candidate.candidate_fingerprint:
            raise ValueError("candidate fingerprint mismatch")
        if self.candidate_version != self.candidate.candidate_version:
            raise ValueError("candidate version mismatch")
        if self.candidate_kind != self.candidate.candidate_kind:
            raise ValueError("candidate kind mismatch")
        if self.signal_ids != self.candidate.signal_ids:
            raise ValueError("signal id lineage mismatch")
        if self.signal_fingerprints != self.candidate.signal_fingerprints:
            raise ValueError("signal fingerprint lineage mismatch")
        by_id = {signal.signal_id: signal for signal in self.signal_batch.signals}
        if not set(self.signal_ids).issubset(by_id):
            raise ValueError("signal batch id mismatch")
        if tuple(by_id[item].signal_fingerprint for item in self.signal_ids) != (
            self.signal_fingerprints
        ):
            raise ValueError("signal batch fingerprint mismatch")
        spec = target_spec_for_candidate_kind(self.candidate_kind)
        if (
            self.target_component_code != spec.target_component_code
            or self.target_policy_code != spec.target_policy_code
            or self.canonical_operation != spec.canonical_operation
        ):
            raise ValueError("engagement target mapping mismatch")
        if self.lifecycle_evidence.learning_candidate_id != self.learning_candidate_id:
            raise ValueError("lifecycle candidate mismatch")
        if self.lifecycle_evidence.candidate_fingerprint != self.candidate_fingerprint:
            raise ValueError("lifecycle fingerprint mismatch")
        return self


class EngagementApplicationRiskAssessment(StrictFrozenModel):
    fingerprint_field: ClassVar[str | None] = "assessment_fingerprint"

    schema_version: Literal["aion-glm-engagement-application-risk/v1"] = (
        ENGAGEMENT_APPLICATION_RISK_SCHEMA_VERSION
    )
    risk_assessment_id: str
    candidate_id: str
    candidate_fingerprint: str
    candidate_kind: EngagementLearningCandidateKind
    target_component_code: str
    target_policy_code: str
    risk_class: EngagementApplicationRiskClass
    required_independent_approvers: int = Field(ge=1, le=2)
    risk_reason_codes: tuple[str, ...]
    assessed_at: datetime
    assessment_fingerprint: str
    read_only: Literal[True] = True
    redacted: Literal[True] = True
    runtime_effect: Literal[False] = False

    @field_validator("risk_reason_codes")
    @classmethod
    def reasons_are_known(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_reason_codes(value)

    @model_validator(mode="after")
    def validate_risk(self) -> Self:
        spec = target_spec_for_candidate_kind(self.candidate_kind)
        if self.risk_class != spec.risk_class:
            raise ValueError("risk classification mismatch")
        expected = 1 if self.risk_class is EngagementApplicationRiskClass.LOW else 2
        if self.required_independent_approvers != expected:
            raise ValueError("required approver count mismatch")
        return self


class EngagementApplicationApprovalEvidence(StrictFrozenModel):
    fingerprint_field: ClassVar[str | None] = "evidence_fingerprint"

    schema_version: Literal[
        "aion-glm-engagement-application-approval-evidence/v1"
    ] = ENGAGEMENT_APPLICATION_APPROVAL_EVIDENCE_SCHEMA_VERSION
    approval_evidence_id: str
    approval_request_id: str
    approval_decision_id: str
    approval_request_fingerprint: str
    approval_decision_fingerprint: str
    requester_identity_fingerprint: str
    approver_identity_fingerprint: str
    action_type: str
    resource_type: str
    resource_id: str
    approval_scope: str
    decision: Literal["approve"]
    request_status: Literal["approved"]
    candidate_id: str
    candidate_fingerprint: str
    candidate_version: int = Field(ge=1)
    signal_fingerprints: tuple[str, ...]
    adaptation_identity_id: str
    adaptation_version: int = Field(ge=1)
    target_component_code: str
    target_policy_code: str
    overlay_fingerprint: str
    baseline_snapshot_fingerprint: str
    fixture_fingerprint: str
    rollback_plan_fingerprint: str
    overlay_expires_at: datetime
    requested_at: datetime
    decided_at: datetime
    approval_expires_at: datetime
    revoked_at: datetime | None = None
    evidence_origin: Literal["operator_supplied_existing_approval"] = (
        "operator_supplied_existing_approval"
    )
    approval_creation_performed_by_aion226: Literal[False] = False
    approval_decision_performed_by_aion226: Literal[False] = False
    read_only: Literal[True] = True
    redacted: Literal[True] = True
    runtime_effect: Literal[False] = False
    evidence_fingerprint: str

    @model_validator(mode="after")
    def validate_approval_evidence(self) -> Self:
        if self.requester_identity_fingerprint == self.approver_identity_fingerprint:
            raise ValueError("separation of duties failed")
        if self.approval_expires_at <= self.decided_at:
            raise ValueError("approval expired before decision")
        if self.revoked_at is not None:
            raise ValueError("revoked approval cannot authorize shadow application")
        return self


class EngagementApplicationApprovalBundle(StrictFrozenModel):
    fingerprint_field: ClassVar[str | None] = "bundle_fingerprint"

    schema_version: Literal[
        "aion-glm-engagement-application-approval-bundle/v1"
    ] = ENGAGEMENT_APPLICATION_APPROVAL_BUNDLE_SCHEMA_VERSION
    bundle_id: str
    risk_class: EngagementApplicationRiskClass
    evidence_records: tuple[EngagementApplicationApprovalEvidence, ...]
    independent_approver_fingerprints: tuple[str, ...]
    independent_approver_count: int = Field(ge=0, le=4)
    required_independent_approvers: int = Field(ge=1, le=2)
    separation_of_duties_passed: bool
    approval_status: Literal["approved", "blocked"]
    reason_codes: tuple[str, ...]
    bundle_fingerprint: str
    read_only: Literal[True] = True
    redacted: Literal[True] = True
    runtime_effect: Literal[False] = False

    @field_validator("reason_codes")
    @classmethod
    def reasons_are_known(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_reason_codes(value)

    @model_validator(mode="after")
    def validate_bundle(self) -> Self:
        if len(self.evidence_records) > MAXIMUM_APPROVAL_EVIDENCE_RECORDS_PER_APPLICATION:
            raise ValueError("too many approval evidence records")
        approvers = tuple(
            sorted({item.approver_identity_fingerprint for item in self.evidence_records})
        )
        if self.independent_approver_fingerprints != approvers:
            raise ValueError("independent approver fingerprint mismatch")
        if self.independent_approver_count != len(approvers):
            raise ValueError("independent approver count mismatch")
        passed = self.independent_approver_count >= self.required_independent_approvers
        if self.separation_of_duties_passed is not passed:
            raise ValueError("separation of duties status mismatch")
        if self.approval_status == "approved" and not passed:
            raise ValueError("approval bundle lacks independent approvers")
        return self


class EngagementAdaptationIdentity(StrictFrozenModel):
    fingerprint_field: ClassVar[str | None] = "identity_fingerprint"

    schema_version: Literal["aion-glm-engagement-adaptation-identity/v1"] = (
        ENGAGEMENT_ADAPTATION_IDENTITY_SCHEMA_VERSION
    )
    adaptation_identity_id: str
    candidate_kind: EngagementLearningCandidateKind
    target_component_code: str
    target_policy_code: str
    canonical_operation: EngagementAdaptationOperation
    subject_scope_fingerprint: str
    adaptation_scope_fingerprint: str
    candidate_id: str
    candidate_fingerprint: str
    identity_fingerprint: str
    runtime_effect: Literal[False] = False


class EngagementAdaptationConflictFinding(StrictFrozenModel):
    fingerprint_field: ClassVar[str | None] = "finding_fingerprint"

    finding_id: str
    candidate_ids: tuple[str, ...]
    adaptation_identity_id: str | None = None
    conflict_type: Literal["duplicate", "collision", "target_conflict", "material_conflict"]
    reason_codes: tuple[str, ...]
    finding_fingerprint: str
    redacted: Literal[True] = True
    runtime_effect: Literal[False] = False

    @field_validator("reason_codes")
    @classmethod
    def reasons_are_known(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_reason_codes(value)


class EngagementAdaptationConflictReport(StrictFrozenModel):
    fingerprint_field: ClassVar[str | None] = "report_fingerprint"

    schema_version: Literal["aion-glm-engagement-adaptation-conflict/v1"] = (
        ENGAGEMENT_ADAPTATION_CONFLICT_SCHEMA_VERSION
    )
    conflict_report_id: str
    findings: tuple[EngagementAdaptationConflictFinding, ...]
    exact_duplicate_count: int = Field(ge=0)
    material_conflict_count: int = Field(ge=0)
    unresolved_material_conflicts: bool
    reason_codes: tuple[str, ...]
    report_fingerprint: str
    read_only: Literal[True] = True
    redacted: Literal[True] = True
    runtime_effect: Literal[False] = False

    @field_validator("reason_codes")
    @classmethod
    def reasons_are_known(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_reason_codes(value)


class EngagementAdaptationVersionPlan(StrictFrozenModel):
    fingerprint_field: ClassVar[str | None] = "version_plan_fingerprint"

    schema_version: Literal["aion-glm-engagement-adaptation-version/v1"] = (
        ENGAGEMENT_ADAPTATION_VERSION_SCHEMA_VERSION
    )
    version_plan_id: str
    adaptation_identity_id: str
    disposition: EngagementAdaptationVersionDisposition
    planned_version_number: int = Field(ge=1, le=MAXIMUM_OVERLAY_VERSIONS_PER_IDENTITY)
    previous_version_id: str | None = None
    candidate_id: str
    candidate_fingerprint: str
    candidate_version: int = Field(ge=1)
    target_component_code: str
    target_policy_code: str
    canonical_operation: EngagementAdaptationOperation
    approval_bundle_fingerprint: str
    effective_from: datetime
    expires_at: datetime
    supersedes_version_id: str | None = None
    retracts_version_id: str | None = None
    append_only: Literal[True] = True
    historical_versions_preserved: Literal[True] = True
    persistent_version_created: Literal[False] = False
    reason_codes: tuple[str, ...]
    runtime_effect: Literal[False] = False
    version_plan_fingerprint: str

    @field_validator("reason_codes")
    @classmethod
    def reasons_are_known(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_reason_codes(value)

    @model_validator(mode="after")
    def validate_version(self) -> Self:
        if self.expires_at <= self.effective_from:
            raise ValueError("adaptation version expiry must be after effective time")
        if self.planned_version_number == 1 and self.previous_version_id is not None:
            raise ValueError("initial version cannot have previous version")
        if self.planned_version_number > 1 and self.previous_version_id is None:
            raise ValueError("later version requires previous version")
        return self


class EngagementTargetPolicy(StrictFrozenModel):
    fingerprint_field: ClassVar[str | None] = "policy_fingerprint"

    schema_version: Literal["aion-glm-engagement-target-policy/v1"] = (
        ENGAGEMENT_TARGET_POLICY_SCHEMA_VERSION
    )
    target_policy_id: str
    candidate_kind: EngagementLearningCandidateKind
    target_component_code: str
    target_policy_code: str
    canonical_operation: EngagementAdaptationOperation
    bounded_parameter_codes: tuple[str, ...]
    target_scope_fingerprint: str
    policy_fingerprint: str
    production_component_reference_present: Literal[False] = False
    production_policy_mutation_authorized: Literal[False] = False
    persistent_write_authorized: Literal[False] = False
    runtime_effect: Literal[False] = False

    @field_validator("bounded_parameter_codes")
    @classmethod
    def parameter_codes_are_known(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_parameter_codes(value)

    @model_validator(mode="after")
    def validate_target_policy(self) -> Self:
        spec = target_spec_for_candidate_kind(self.candidate_kind)
        if (
            self.target_component_code != spec.target_component_code
            or self.target_policy_code != spec.target_policy_code
            or self.canonical_operation != spec.canonical_operation
        ):
            raise ValueError("target policy registry mismatch")
        return self


class EngagementReadOnlyKnowledgeContext(StrictFrozenModel):
    fingerprint_field: ClassVar[str | None] = "context_fingerprint"

    context_id: str
    knowledge_query_fingerprints: tuple[str, ...] = ()
    projection_query_fingerprints: tuple[str, ...] = ()
    result_counts: tuple[int, ...] = ()
    record_fingerprints: tuple[str, ...] = ()
    knowledge_identity_ids: tuple[str, ...] = ()
    version_ids: tuple[str, ...] = ()
    projection_ids: tuple[str, ...] = ()
    content_fingerprints: tuple[str, ...] = ()
    confidence_caps: tuple[Decimal, ...] = ()
    local_knowledge_context_fingerprint: str
    context_fingerprint: str
    read_only: Literal[True] = True
    redacted: Literal[True] = True
    aion_224_store_write_applied: Literal[False] = False
    knowledge_confidence_effect: Literal[False] = False
    runtime_effect: Literal[False] = False


class EngagementBaselineSnapshot(StrictFrozenModel):
    fingerprint_field: ClassVar[str | None] = "snapshot_fingerprint"

    schema_version: Literal["aion-glm-engagement-baseline-snapshot/v1"] = (
        ENGAGEMENT_BASELINE_SNAPSHOT_SCHEMA_VERSION
    )
    baseline_snapshot_id: str
    target_component_fingerprints: tuple[str, ...]
    target_policy_fingerprints: tuple[str, ...]
    local_knowledge_context_fingerprint: str
    fixture_fingerprint: str
    baseline_configuration_codes: tuple[str, ...]
    captured_at: datetime
    snapshot_fingerprint: str
    production_reference_present: Literal[False] = False
    read_only: Literal[True] = True
    redacted: Literal[True] = True
    runtime_effect: Literal[False] = False


class EngagementRollbackStep(StrictFrozenModel):
    fingerprint_field: ClassVar[str | None] = "step_fingerprint"

    rollback_step_id: str
    operation: Literal[
        "remove_overlay_from_shadow_session",
        "restore_baseline_snapshot",
        "invalidate_overlay_snapshot",
        "expire_adaptation_version",
        "preserve_evaluation_evidence",
        "create_operator_review_item",
        "retain_baseline",
    ]
    target_reference_id: str
    order: int = Field(ge=1, le=MAXIMUM_ROLLBACK_STEPS_PER_APPLICATION)
    step_fingerprint: str
    persistent_write_applied: Literal[False] = False
    production_policy_effect: Literal[False] = False
    runtime_effect: Literal[False] = False


class EngagementRollbackPlan(StrictFrozenModel):
    fingerprint_field: ClassVar[str | None] = "rollback_plan_fingerprint"

    schema_version: Literal["aion-glm-engagement-rollback/v1"] = (
        ENGAGEMENT_ROLLBACK_PLAN_SCHEMA_VERSION
    )
    rollback_plan_id: str
    shadow_session_id: str
    overlay_snapshot_fingerprint: str
    baseline_snapshot_fingerprint: str
    steps: tuple[EngagementRollbackStep, ...]
    step_count: int = Field(ge=1, le=MAXIMUM_ROLLBACK_STEPS_PER_APPLICATION)
    reason_codes: tuple[str, ...]
    rollback_plan_fingerprint: str
    read_only: Literal[True] = True
    redacted: Literal[True] = True
    persistent_write_applied: Literal[False] = False
    production_policy_effect: Literal[False] = False
    runtime_effect: Literal[False] = False

    @field_validator("reason_codes")
    @classmethod
    def reasons_are_known(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_reason_codes(value)

    @model_validator(mode="after")
    def validate_plan(self) -> Self:
        if self.step_count != len(self.steps):
            raise ValueError("rollback step count mismatch")
        ids = tuple(step.rollback_step_id for step in self.steps)
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate rollback step id")
        if tuple(step.order for step in self.steps) != tuple(range(1, len(self.steps) + 1)):
            raise ValueError("rollback steps must be deterministic and contiguous")
        return self


class EngagementOverlayRecord(StrictFrozenModel):
    fingerprint_field: ClassVar[str | None] = "overlay_fingerprint"

    schema_version: Literal["aion-glm-engagement-overlay-record/v1"] = (
        ENGAGEMENT_OVERLAY_RECORD_SCHEMA_VERSION
    )
    overlay_record_id: str
    shadow_session_id: str
    adaptation_identity_id: str
    adaptation_version: int = Field(ge=1, le=MAXIMUM_OVERLAY_VERSIONS_PER_IDENTITY)
    candidate_id: str
    candidate_fingerprint: str
    candidate_kind: EngagementLearningCandidateKind
    signal_fingerprints: tuple[str, ...]
    target_policy: EngagementTargetPolicy
    risk_assessment_fingerprint: str
    approval_bundle_fingerprint: str
    baseline_snapshot_fingerprint: str
    fixture_fingerprint: str
    rollback_plan_fingerprint: str
    effective_from: datetime
    expires_at: datetime
    status: EngagementOverlayStatus
    reason_codes: tuple[str, ...]
    persistent_write_applied: Literal[False] = False
    aion_224_store_write_applied: Literal[False] = False
    production_policy_effect: Literal[False] = False
    factual_effect: Literal[False] = False
    confidence_effect: Literal[False] = False
    knowledge_effect: Literal[False] = False
    source_independence_effect: Literal[False] = False
    citation_coverage_effect: Literal[False] = False
    provenance_effect: Literal[False] = False
    contradiction_resolution_effect: Literal[False] = False
    freshness_effect: Literal[False] = False
    cognitive_memory_effect: Literal[False] = False
    belief_effect: Literal[False] = False
    model_weight_effect: Literal[False] = False
    runtime_effect: Literal[False] = False
    overlay_fingerprint: str

    @field_validator("reason_codes")
    @classmethod
    def reasons_are_known(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_reason_codes(value)

    @model_validator(mode="after")
    def validate_overlay(self) -> Self:
        if self.expires_at <= self.effective_from:
            raise ValueError("overlay expiry must be after effective time")
        if self.target_policy.candidate_kind != self.candidate_kind:
            raise ValueError("overlay target policy candidate mismatch")
        return self


class EngagementOverlaySnapshot(StrictFrozenModel):
    fingerprint_field: ClassVar[str | None] = "snapshot_fingerprint"

    schema_version: Literal["aion-glm-engagement-overlay-snapshot/v1"] = (
        ENGAGEMENT_OVERLAY_SNAPSHOT_SCHEMA_VERSION
    )
    overlay_snapshot_id: str
    shadow_session_id: str
    records: tuple[EngagementOverlayRecord, ...]
    record_count: int = Field(ge=0, le=MAXIMUM_OVERLAY_RECORDS_PER_SESSION)
    adaptation_identity_ids: tuple[str, ...]
    adaptation_version_vector: tuple[str, ...]
    created_at: datetime
    expires_at: datetime
    snapshot_fingerprint: str
    immutable: Literal[True] = True
    in_memory_only: Literal[True] = True
    persistent_write_applied: Literal[False] = False
    production_policy_effect: Literal[False] = False
    runtime_effect: Literal[False] = False

    @model_validator(mode="after")
    def validate_snapshot(self) -> Self:
        if self.record_count != len(self.records):
            raise ValueError("overlay record count mismatch")
        ids = tuple(record.overlay_record_id for record in self.records)
        if ids != tuple(sorted(ids)) or len(ids) != len(set(ids)):
            raise ValueError("overlay records must be sorted and unique")
        pairs = tuple(
            f"{record.adaptation_identity_id}:{record.adaptation_version}"
            for record in self.records
        )
        if len(pairs) != len(set(pairs)):
            raise ValueError("duplicate adaptation identity version")
        if self.expires_at <= self.created_at:
            raise ValueError("overlay snapshot expiry must be after creation")
        if any(record.expires_at > self.expires_at for record in self.records):
            raise ValueError("overlay record expires after snapshot")
        return self


class EngagementApplicationAuthorizationEnvelope(StrictFrozenModel):
    fingerprint_field: ClassVar[str | None] = "envelope_fingerprint"

    schema_version: Literal["aion-glm-engagement-application-authorization/v1"] = (
        ENGAGEMENT_APPLICATION_AUTHORIZATION_SCHEMA_VERSION
    )
    authorization_transaction_id: Literal["AION-225-GLM-0003"]
    approval_record_id: Literal["AION-225-GLM-0003"]
    shadow_session_id: str
    operator_identity_fingerprint: str
    candidate_ids: tuple[str, ...]
    candidate_fingerprints: tuple[str, ...]
    overlay_snapshot_fingerprint: str
    baseline_snapshot_fingerprint: str
    fixture_fingerprint: str
    allowed_target_components: tuple[str, ...]
    mode: EngagementApplicationMode
    created_at: datetime
    expires_at: datetime
    operator_invoked: Literal[True] = True
    background_execution: Literal[False] = False
    scheduled_execution: Literal[False] = False
    production_application: Literal[False] = False
    persistent_overlay: Literal[False] = False
    approval_created: Literal[False] = False
    runtime_effect: Literal[False] = False
    envelope_fingerprint: str

    @model_validator(mode="after")
    def validate_envelope(self) -> Self:
        if self.expires_at <= self.created_at:
            raise ValueError("authorization envelope expired")
        if self.expires_at - self.created_at > timedelta(hours=1):
            raise ValueError("authorization envelope exceeds one hour")
        if self.candidate_ids != tuple(sorted(self.candidate_ids)):
            raise ValueError("candidate ids must be sorted")
        if self.allowed_target_components != tuple(sorted(self.allowed_target_components)):
            raise ValueError("allowed targets must be sorted")
        return self


class EngagementCounterfactualCase(StrictFrozenModel):
    fingerprint_field: ClassVar[str | None] = "case_fingerprint"

    schema_version: Literal["aion-glm-engagement-counterfactual-case/v1"] = (
        ENGAGEMENT_COUNTERFACTUAL_CASE_SCHEMA_VERSION
    )
    case_id: str
    target_component_code: str
    target_policy_code: str
    input_codes: tuple[str, ...]
    baseline_expected_codes: tuple[str, ...]
    hard_gate_codes: tuple[str, ...]
    metric_registry: tuple[str, ...]
    case_fingerprint: str
    synthetic_or_redacted: Literal[True] = True
    raw_user_message_present: Literal[False] = False
    read_only: Literal[True] = True

    @field_validator("metric_registry")
    @classmethod
    def metrics_are_known(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        unknown = [metric for metric in value if metric not in METRIC_DIRECTIONS]
        if unknown:
            raise ValueError("unknown engagement metric")
        return value


class EngagementCounterfactualOutcome(StrictFrozenModel):
    fingerprint_field: ClassVar[str | None] = "outcome_fingerprint"

    outcome_id: str
    outcome_codes: tuple[str, ...]
    metrics: Mapping[str, Decimal]
    safety_violations: int = Field(ge=0)
    policy_violations: int = Field(ge=0)
    outcome_fingerprint: str
    runtime_effect: Literal[False] = False

    @field_validator("metrics")
    @classmethod
    def metric_values_are_finite(cls, value: Mapping[str, Decimal]) -> Mapping[str, Decimal]:
        unknown = [metric for metric in value if metric not in METRIC_DIRECTIONS]
        if unknown:
            raise ValueError("unknown engagement metric")
        return {key: _q(metric) for key, metric in sorted(value.items())}


class EngagementMetricDelta(StrictFrozenModel):
    fingerprint_field: ClassVar[str | None] = "metric_fingerprint"

    schema_version: Literal["aion-glm-engagement-metric-delta/v1"] = (
        ENGAGEMENT_METRIC_DELTA_SCHEMA_VERSION
    )
    metric_name: str
    direction: EngagementMetricDirection
    baseline_value: Decimal
    candidate_value: Decimal
    delta: Decimal
    improved: bool
    regressed: bool
    hard_gate: bool
    metric_fingerprint: str

    @model_validator(mode="after")
    def validate_metric(self) -> Self:
        if METRIC_DIRECTIONS.get(self.metric_name) != self.direction:
            raise ValueError("metric direction mismatch")
        expected_delta = _q(self.candidate_value - self.baseline_value)
        if self.delta != expected_delta:
            raise ValueError("metric delta mismatch")
        if self.direction is EngagementMetricDirection.HIGHER_IS_BETTER:
            improved = self.candidate_value > self.baseline_value
            regressed = self.candidate_value < self.baseline_value
        elif self.direction is EngagementMetricDirection.LOWER_IS_BETTER:
            improved = self.candidate_value < self.baseline_value
            regressed = self.candidate_value > self.baseline_value
        else:
            improved = self.candidate_value == ZERO
            regressed = self.candidate_value != ZERO
        if self.improved != improved or self.regressed != regressed:
            raise ValueError("metric improvement flags mismatch")
        return self


class EngagementCounterfactualResult(StrictFrozenModel):
    fingerprint_field: ClassVar[str | None] = "result_fingerprint"

    schema_version: Literal["aion-glm-engagement-counterfactual-result/v1"] = (
        ENGAGEMENT_COUNTERFACTUAL_RESULT_SCHEMA_VERSION
    )
    case_id: str
    baseline_outcome_fingerprint: str
    candidate_outcome_fingerprint: str
    metric_deltas: tuple[EngagementMetricDelta, ...]
    safety_gate_passed: bool
    policy_gate_passed: bool
    recommendation: EngagementCounterfactualRecommendation
    reason_codes: tuple[str, ...]
    result_fingerprint: str
    factual_effect: Literal[False] = False
    confidence_effect: Literal[False] = False
    knowledge_effect: Literal[False] = False
    production_policy_effect: Literal[False] = False
    runtime_effect: Literal[False] = False

    @field_validator("reason_codes")
    @classmethod
    def reasons_are_known(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_reason_codes(value)

    @model_validator(mode="after")
    def validate_result(self) -> Self:
        if not self.safety_gate_passed and self.recommendation not in {
            EngagementCounterfactualRecommendation.RETAIN_BASELINE,
            EngagementCounterfactualRecommendation.REJECT_CANDIDATE,
            EngagementCounterfactualRecommendation.ABSTAIN,
        }:
            raise ValueError("safety failure cannot approve candidate")
        if not self.policy_gate_passed and self.recommendation not in {
            EngagementCounterfactualRecommendation.RETAIN_BASELINE,
            EngagementCounterfactualRecommendation.REJECT_CANDIDATE,
            EngagementCounterfactualRecommendation.ABSTAIN,
        }:
            raise ValueError("policy failure cannot approve candidate")
        return self


class EngagementApplicationResourceBudget(StrictFrozenModel):
    fingerprint_field: ClassVar[str | None] = "budget_fingerprint"

    budget_id: str
    limits: Mapping[str, int]
    budget_fingerprint: str
    runtime_effect: Literal[False] = False

    @model_validator(mode="after")
    def validate_budget(self) -> Self:
        if dict(self.limits) != dict(RESOURCE_LIMITS):
            raise ValueError("resource budget must match AION-225-GLM-0003")
        return self


class EngagementApplicationResourceUsage(StrictFrozenModel):
    fingerprint_field: ClassVar[str | None] = "usage_fingerprint"

    usage_id: str
    engagement_candidates: int = Field(ge=0)
    signal_references_per_candidate: int = Field(ge=0)
    candidate_versions: int = Field(ge=0)
    target_components: int = Field(ge=0)
    approval_records: int = Field(ge=0)
    adaptation_plans: int = Field(ge=0)
    overlay_records: int = Field(ge=0)
    overlay_versions: int = Field(ge=0)
    overlay_snapshots: int = Field(ge=0)
    counterfactual_cases: int = Field(ge=0)
    metrics_per_case: int = Field(ge=0)
    comparisons: int = Field(ge=0)
    rollback_steps: int = Field(ge=0)
    operator_review_items: int = Field(ge=0)
    query_results: int = Field(ge=0)
    fixture_records: int = Field(ge=0)
    fixture_bytes: int = Field(ge=0)
    concurrency: int = Field(ge=0)
    persistent_engagement_overlay_writes: Literal[0] = 0
    aion_224_store_writes: Literal[0] = 0
    production_policy_mutations: Literal[0] = 0
    engagement_fact_promotions: Literal[0] = 0
    engagement_confidence_effects: Literal[0] = 0
    engagement_knowledge_effects: Literal[0] = 0
    engagement_source_independence_effects: Literal[0] = 0
    cognitive_memory_writes: Literal[0] = 0
    actual_belief_creations: Literal[0] = 0
    actual_belief_mutations: Literal[0] = 0
    automatic_candidate_approvals: Literal[0] = 0
    automatic_knowledge_promotions: Literal[0] = 0
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
    usage_fingerprint: str
    runtime_effect: Literal[False] = False


class EngagementApplicationBudgetDecision(StrictFrozenModel):
    fingerprint_field: ClassVar[str | None] = "decision_fingerprint"

    decision_id: str
    budget: EngagementApplicationResourceBudget
    usage: EngagementApplicationResourceUsage
    budget_passed: bool
    reason_codes: tuple[str, ...]
    decision_fingerprint: str
    runtime_effect: Literal[False] = False

    @field_validator("reason_codes")
    @classmethod
    def reasons_are_known(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_reason_codes(value)


class EngagementApplicationIntegrityFinding(StrictFrozenModel):
    fingerprint_field: ClassVar[str | None] = "finding_fingerprint"

    finding_id: str
    status: EngagementIntegrityStatus
    reason_codes: tuple[str, ...]
    safe_ids: tuple[str, ...] = ()
    fingerprints: tuple[str, ...] = ()
    bounded_count: int = Field(default=0, ge=0)
    redacted_summary: str
    finding_fingerprint: str
    runtime_effect: Literal[False] = False

    @field_validator("reason_codes")
    @classmethod
    def reasons_are_known(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_reason_codes(value)


class EngagementApplicationIntegrityReport(StrictFrozenModel):
    fingerprint_field: ClassVar[str | None] = "report_fingerprint"

    schema_version: Literal["aion-glm-engagement-application-integrity/v1"] = (
        ENGAGEMENT_APPLICATION_INTEGRITY_SCHEMA_VERSION
    )
    integrity_report_id: str
    status: EngagementIntegrityStatus
    findings: tuple[EngagementApplicationIntegrityFinding, ...]
    finding_count: int = Field(ge=0, le=MAXIMUM_OPERATOR_REVIEW_ITEMS)
    report_fingerprint: str
    read_only: Literal[True] = True
    redacted: Literal[True] = True
    runtime_effect: Literal[False] = False

    @model_validator(mode="after")
    def validate_integrity_report(self) -> Self:
        if self.finding_count != len(self.findings):
            raise ValueError("integrity finding count mismatch")
        if self.status is EngagementIntegrityStatus.PASSED and any(
            finding.status is EngagementIntegrityStatus.FAILED for finding in self.findings
        ):
            raise ValueError("passed integrity report cannot contain failures")
        return self


class EngagementApplicationDiagnostics(StrictFrozenModel):
    fingerprint_field: ClassVar[str | None] = "diagnostics_fingerprint"

    diagnostics_id: str
    reason_codes: tuple[str, ...]
    bounded_counts: Mapping[str, int]
    diagnostics_fingerprint: str
    redacted: Literal[True] = True
    runtime_effect: Literal[False] = False

    @field_validator("reason_codes")
    @classmethod
    def reasons_are_known(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_reason_codes(value)


class EngagementApplicationIncident(StrictFrozenModel):
    fingerprint_field: ClassVar[str | None] = "incident_fingerprint"

    incident_id: str
    status: EngagementIntegrityStatus
    reason_codes: tuple[str, ...]
    safe_ids: tuple[str, ...]
    incident_fingerprint: str
    redacted: Literal[True] = True
    runtime_effect: Literal[False] = False

    @field_validator("reason_codes")
    @classmethod
    def reasons_are_known(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_reason_codes(value)


class EngagementApplicationOperatorReviewItem(StrictFrozenModel):
    fingerprint_field: ClassVar[str | None] = "review_item_fingerprint"

    review_item_id: str
    candidate_id: str
    recommendation: EngagementCounterfactualRecommendation
    reason_codes: tuple[str, ...]
    operator_review_required: Literal[True] = True
    candidate_is_non_factual: Literal[True] = True
    operator_approval_is_not_factual_proof: Literal[True] = True
    shadow_application_is_not_production_application: Literal[True] = True
    metric_improvement_is_not_factual_validation: Literal[True] = True
    overlay_is_in_memory_only: Literal[True] = True
    persistent_overlay_authorized: Literal[False] = False
    production_policy_mutation_authorized: Literal[False] = False
    knowledge_confidence_change_authorized: Literal[False] = False
    source_independence_change_authorized: Literal[False] = False
    cognitive_memory_write_authorized: Literal[False] = False
    belief_mutation_authorized: Literal[False] = False
    automatic_application_authorized: Literal[False] = False
    model_training_authorized: Literal[False] = False
    approval_created: Literal[False] = False
    new_implementation_authorization_created: Literal[False] = False
    review_item_fingerprint: str
    redacted: Literal[True] = True
    runtime_effect: Literal[False] = False

    @field_validator("reason_codes")
    @classmethod
    def reasons_are_known(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_reason_codes(value)


class EngagementApplicationEvidenceBundle(StrictFrozenModel):
    fingerprint_field: ClassVar[str | None] = "evidence_bundle_fingerprint"

    schema_version: Literal["aion-glm-engagement-application-evidence/v1"] = (
        ENGAGEMENT_APPLICATION_EVIDENCE_SCHEMA_VERSION
    )
    evidence_bundle_id: str
    diagnostics: EngagementApplicationDiagnostics
    incidents: tuple[EngagementApplicationIncident, ...]
    operator_review_items: tuple[EngagementApplicationOperatorReviewItem, ...]
    evidence_bundle_fingerprint: str
    redacted: Literal[True] = True
    runtime_effect: Literal[False] = False


class EngagementApplicationQuery(StrictFrozenModel):
    fingerprint_field: ClassVar[str | None] = "query_fingerprint"

    schema_version: Literal["aion-glm-engagement-application-query/v1"] = (
        ENGAGEMENT_APPLICATION_QUERY_SCHEMA_VERSION
    )
    query_id: str
    shadow_session_id: str | None = None
    candidate_id: str | None = None
    candidate_fingerprint: str | None = None
    candidate_kind: EngagementLearningCandidateKind | None = None
    adaptation_identity_id: str | None = None
    adaptation_version: int | None = Field(default=None, ge=1)
    target_component_code: str | None = None
    target_policy_code: str | None = None
    risk_class: EngagementApplicationRiskClass | None = None
    approval_status: str | None = None
    application_status: EngagementApplicationStatus | None = None
    recommendation: EngagementCounterfactualRecommendation | None = None
    overlay_status: EngagementOverlayStatus | None = None
    expiry_state: Literal["active", "expired"] | None = None
    operator_review_required: bool | None = None
    limit: int = Field(default=100, ge=1, le=MAXIMUM_QUERY_RESULTS)
    query_fingerprint: str
    runtime_effect: Literal[False] = False


class EngagementApplicationQueryResult(StrictFrozenModel):
    fingerprint_field: ClassVar[str | None] = "result_fingerprint"

    schema_version: Literal["aion-glm-engagement-application-query-result/v1"] = (
        ENGAGEMENT_APPLICATION_QUERY_RESULT_SCHEMA_VERSION
    )
    query_fingerprint: str
    overlay_records: tuple[EngagementOverlayRecord, ...]
    result_count: int = Field(ge=0, le=MAXIMUM_QUERY_RESULTS)
    result_fingerprint: str
    read_only: Literal[True] = True
    redacted: Literal[True] = True
    runtime_effect: Literal[False] = False

    @model_validator(mode="after")
    def validate_query_result(self) -> Self:
        if self.result_count != len(self.overlay_records):
            raise ValueError("query result count mismatch")
        return self


class EngagementApplicationFixtureEnvelope(StrictFrozenModel):
    fingerprint_field: ClassVar[str | None] = "fixture_fingerprint"

    schema_version: Literal["aion-glm-engagement-application-fixture/v1"] = (
        ENGAGEMENT_APPLICATION_FIXTURE_SCHEMA_VERSION
    )
    fixture_id: str
    records: tuple[Mapping[str, object], ...]
    record_count: int = Field(ge=0, le=MAXIMUM_FIXTURE_RECORDS)
    fixture_bytes: int = Field(ge=0, le=MAXIMUM_FIXTURE_BYTES)
    synthetic_or_redacted: Literal[True] = True
    raw_user_message_present: Literal[False] = False
    fixture_fingerprint: str
    read_only: Literal[True] = True
    runtime_effect: Literal[False] = False

    @field_validator("records")
    @classmethod
    def records_are_safe(
        cls, value: tuple[Mapping[str, object], ...]
    ) -> tuple[Mapping[str, object], ...]:
        reject_protected_material(value, "engagement fixture")
        text = json.dumps(_jsonable(value), sort_keys=True, ensure_ascii=True).lower()
        if any(marker in text for marker in _PROTECTED_FIXTURE_MARKERS):
            raise ValueError("fixture contains protected material")
        return value

    @model_validator(mode="after")
    def validate_fixture(self) -> Self:
        if self.record_count != len(self.records):
            raise ValueError("fixture record count mismatch")
        return self


class EngagementApplicationPlan(StrictFrozenModel):
    fingerprint_field: ClassVar[str | None] = "plan_fingerprint"

    schema_version: Literal["aion-glm-engagement-application-plan/v1"] = (
        ENGAGEMENT_APPLICATION_PLAN_SCHEMA_VERSION
    )
    application_plan_id: str
    authorization_envelope: EngagementApplicationAuthorizationEnvelope
    candidate_bindings: tuple[EngagementCandidateBinding, ...]
    risk_assessments: tuple[EngagementApplicationRiskAssessment, ...]
    approval_bundles: tuple[EngagementApplicationApprovalBundle, ...]
    adaptation_identities: tuple[EngagementAdaptationIdentity, ...]
    conflict_report: EngagementAdaptationConflictReport
    version_plans: tuple[EngagementAdaptationVersionPlan, ...]
    target_policies: tuple[EngagementTargetPolicy, ...]
    baseline_snapshot: EngagementBaselineSnapshot
    overlay_snapshot: EngagementOverlaySnapshot
    rollback_plans: tuple[EngagementRollbackPlan, ...]
    counterfactual_cases: tuple[EngagementCounterfactualCase, ...]
    resource_budget_decision: EngagementApplicationBudgetDecision
    operator_review_required: Literal[True] = True
    production_application_authorized: Literal[False] = False
    persistent_overlay_authorized: Literal[False] = False
    automatic_application: Literal[False] = False
    runtime_effect: Literal[False] = False
    plan_fingerprint: str


class EngagementApplicationResult(StrictFrozenModel):
    fingerprint_field: ClassVar[str | None] = "result_fingerprint"

    schema_version: Literal["aion-glm-engagement-application-result/v1"] = (
        ENGAGEMENT_APPLICATION_RESULT_SCHEMA_VERSION
    )
    application_result_id: str
    shadow_session_id: str
    status: EngagementApplicationStatus
    candidate_dispositions: Mapping[str, EngagementCandidateDisposition]
    adaptation_dispositions: Mapping[str, EngagementAdaptationVersionDisposition]
    overlay_snapshot_fingerprint: str
    baseline_snapshot_fingerprint: str
    counterfactual_results: tuple[EngagementCounterfactualResult, ...]
    aggregate_metric_deltas: tuple[EngagementMetricDelta, ...]
    recommendation: EngagementCounterfactualRecommendation
    reason_codes: tuple[str, ...]
    integrity_report: EngagementApplicationIntegrityReport
    evidence_bundle: EngagementApplicationEvidenceBundle
    operator_review_items: tuple[EngagementApplicationOperatorReviewItem, ...]
    overlay_expired_or_rolled_back: bool
    active_overlay_records_after_close: Literal[0] = 0
    persistent_engagement_overlay_writes: Literal[0] = 0
    aion_224_store_writes: Literal[0] = 0
    production_policy_mutations: Literal[0] = 0
    engagement_fact_promotions: Literal[0] = 0
    engagement_confidence_effects: Literal[0] = 0
    engagement_knowledge_effects: Literal[0] = 0
    engagement_source_independence_effects: Literal[0] = 0
    cognitive_memory_writes: Literal[0] = 0
    actual_belief_creations: Literal[0] = 0
    actual_belief_mutations: Literal[0] = 0
    automatic_candidate_approvals: Literal[0] = 0
    automatic_knowledge_promotions: Literal[0] = 0
    model_weight_changes: Literal[0] = 0
    runtime_effect: Literal[False] = False
    result_fingerprint: str

    @field_validator("reason_codes")
    @classmethod
    def reasons_are_known(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_reason_codes(value)


def project_read_only_knowledge_context(
    *,
    context_id: str,
    knowledge_results: Iterable[LocalKnowledgeQueryResult] = (),
    projection_results: Iterable[LocalProjectionQueryResult] = (),
) -> EngagementReadOnlyKnowledgeContext:
    knowledge = tuple(knowledge_results)
    projections = tuple(projection_results)
    payload = {
        "context_id": context_id,
        "knowledge_query_fingerprints": tuple(
            sorted(result.query_fingerprint for result in knowledge)
        ),
        "projection_query_fingerprints": tuple(
            sorted(result.query_fingerprint for result in projections)
        ),
        "result_counts": tuple(result.result_count for result in knowledge)
        + tuple(result.result_count for result in projections),
        "record_fingerprints": tuple(
            sorted(
                tuple(item.result_fingerprint for item in knowledge)
                + tuple(item.result_fingerprint for item in projections)
            )
        ),
        "knowledge_identity_ids": (),
        "version_ids": (),
        "projection_ids": (),
        "content_fingerprints": (),
        "confidence_caps": (),
        "local_knowledge_context_fingerprint": engagement_fingerprint(
            {
                "knowledge": [item.result_fingerprint for item in knowledge],
                "projections": [item.result_fingerprint for item in projections],
            }
        ),
        "read_only": True,
        "redacted": True,
        "aion_224_store_write_applied": False,
        "knowledge_confidence_effect": False,
        "runtime_effect": False,
    }
    return build_record(
        EngagementReadOnlyKnowledgeContext,
        payload,
        "context_fingerprint",
    )


def load_fixture_envelope(path: Path) -> EngagementApplicationFixtureEnvelope:
    resolved = path
    if not resolved.is_absolute():
        raise ValueError("fixture path must be absolute")
    if _URI_RE.match(str(resolved)):
        raise ValueError("fixture path must not use URI syntax")
    if "~" in str(resolved) or "$" in str(resolved):
        raise ValueError("fixture path must not use expansion syntax")
    if resolved.is_symlink() or not resolved.exists() or not resolved.is_file():
        raise ValueError("fixture path must be an existing regular file")
    if any(part.startswith(".") for part in resolved.parts):
        raise ValueError("fixture path must not contain hidden path components")
    repo_root = Path(__file__).resolve().parents[5]
    try:
        resolved.relative_to(repo_root)
    except ValueError:
        pass
    else:
        raise ValueError("fixture path must be outside repository")
    raw = resolved.read_bytes()
    if len(raw) > MAXIMUM_FIXTURE_BYTES:
        raise ValueError("fixture exceeds maximum bytes")
    text = raw.decode("utf-8")
    data = json.loads(text)
    if not isinstance(data, dict) or set(data) != {"fixture_id", "records"}:
        raise ValueError("fixture schema mismatch")
    records = tuple(data["records"])
    payload = {
        "schema_version": ENGAGEMENT_APPLICATION_FIXTURE_SCHEMA_VERSION,
        "fixture_id": data["fixture_id"],
        "records": records,
        "record_count": len(records),
        "fixture_bytes": len(raw),
        "synthetic_or_redacted": True,
        "raw_user_message_present": False,
        "read_only": True,
        "runtime_effect": False,
    }
    return build_record(EngagementApplicationFixtureEnvelope, payload, "fixture_fingerprint")


__all__ = [
    "APPROVAL_RECORD_ID",
    "AUTHORIZATION_SCOPE",
    "AUTHORIZATION_TRANSACTION_ID",
    "ENGAGEMENT_APPLICATION_REASON_REGISTRY_VERSION",
    "FORMAL_CLOSEOUT_TASK",
    "IMPLEMENTATION_TASK",
    "MAXIMUM_CONCURRENCY",
    "METRIC_DIRECTIONS",
    "PARAMETER_CODE_REGISTRY",
    "PROGRAM_ID",
    "REASON_CODE_REGISTRY",
    "RESOURCE_LIMITS",
    "TARGET_REGISTRY",
    "ZERO_EFFECT_LIMITS",
    "EngagementAdaptationConflictFinding",
    "EngagementAdaptationConflictReport",
    "EngagementAdaptationIdentity",
    "EngagementAdaptationOperation",
    "EngagementAdaptationVersionDisposition",
    "EngagementAdaptationVersionPlan",
    "EngagementApplicationAuthorizationEnvelope",
    "EngagementApplicationBudgetDecision",
    "EngagementApplicationDiagnostics",
    "EngagementApplicationEvidenceBundle",
    "EngagementApplicationFixtureEnvelope",
    "EngagementApplicationIncident",
    "EngagementApplicationIntegrityFinding",
    "EngagementApplicationIntegrityReport",
    "EngagementApplicationMode",
    "EngagementApplicationOperatorReviewItem",
    "EngagementApplicationPlan",
    "EngagementApplicationQuery",
    "EngagementApplicationQueryResult",
    "EngagementApplicationResourceBudget",
    "EngagementApplicationResourceUsage",
    "EngagementApplicationResult",
    "EngagementApplicationRiskAssessment",
    "EngagementApplicationRiskClass",
    "EngagementApplicationStatus",
    "EngagementBaselineSnapshot",
    "EngagementCandidateBinding",
    "EngagementCandidateDisposition",
    "EngagementCandidateLifecycleEvidence",
    "EngagementCounterfactualCase",
    "EngagementCounterfactualOutcome",
    "EngagementCounterfactualRecommendation",
    "EngagementCounterfactualResult",
    "EngagementIntegrityStatus",
    "EngagementMetricDelta",
    "EngagementMetricDirection",
    "EngagementOverlayRecord",
    "EngagementOverlaySnapshot",
    "EngagementOverlayStatus",
    "EngagementReadOnlyKnowledgeContext",
    "EngagementRollbackPlan",
    "EngagementRollbackStep",
    "EngagementTargetPolicy",
    "EngagementTargetSpec",
    "build_record",
    "engagement_fingerprint",
    "load_fixture_envelope",
    "project_read_only_knowledge_context",
    "target_spec_for_candidate_kind",
    "utc_now",
    "validate_parameter_codes",
    "validate_reason_codes",
    "validate_safe_id",
]
