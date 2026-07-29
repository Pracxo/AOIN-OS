"""AION-228 governed continual-learning pilot contracts."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from enum import StrEnum
from pathlib import Path
from typing import Any, ClassVar, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

CONTINUAL_LEARNING_CONTRACT_SCHEMA_VERSION: Literal["aion-glm-continual-learning/v1"] = (
    "aion-glm-continual-learning/v1"
)
CONTINUAL_LEARNING_AUTHORIZATION_SCHEMA_VERSION: Literal[
    "aion-glm-continual-learning-authorization/v1"
] = "aion-glm-continual-learning-authorization/v1"
CONTINUAL_LEARNING_SESSION_PLAN_SCHEMA_VERSION: Literal[
    "aion-glm-continual-learning-session-plan/v1"
] = "aion-glm-continual-learning-session-plan/v1"
CONTINUAL_LEARNING_CYCLE_PLAN_SCHEMA_VERSION: Literal[
    "aion-glm-continual-learning-cycle-plan/v1"
] = "aion-glm-continual-learning-cycle-plan/v1"
CONTINUAL_LEARNING_STAGE_COMMAND_SCHEMA_VERSION: Literal[
    "aion-glm-continual-learning-stage-command/v1"
] = "aion-glm-continual-learning-stage-command/v1"
CONTINUAL_LEARNING_STAGE_RECEIPT_SCHEMA_VERSION: Literal[
    "aion-glm-continual-learning-stage-receipt/v1"
] = "aion-glm-continual-learning-stage-receipt/v1"
CONTINUAL_LEARNING_ENGAGEMENT_INTAKE_SCHEMA_VERSION: Literal[
    "aion-glm-continual-learning-engagement-intake/v1"
] = "aion-glm-continual-learning-engagement-intake/v1"
CONTINUAL_LEARNING_RESEARCH_BINDING_SCHEMA_VERSION: Literal[
    "aion-glm-continual-learning-research-binding/v1"
] = "aion-glm-continual-learning-research-binding/v1"
CONTINUAL_LEARNING_KNOWLEDGE_BINDING_SCHEMA_VERSION: Literal[
    "aion-glm-continual-learning-knowledge-binding/v1"
] = "aion-glm-continual-learning-knowledge-binding/v1"
CONTINUAL_LEARNING_PROMOTION_BINDING_SCHEMA_VERSION: Literal[
    "aion-glm-continual-learning-promotion-binding/v1"
] = "aion-glm-continual-learning-promotion-binding/v1"
CONTINUAL_LEARNING_PERSISTENCE_BINDING_SCHEMA_VERSION: Literal[
    "aion-glm-continual-learning-persistence-binding/v1"
] = "aion-glm-continual-learning-persistence-binding/v1"
CONTINUAL_LEARNING_SHADOW_BINDING_SCHEMA_VERSION: Literal[
    "aion-glm-continual-learning-shadow-binding/v1"
] = "aion-glm-continual-learning-shadow-binding/v1"
CONTINUAL_LEARNING_CROSS_CYCLE_CONTEXT_SCHEMA_VERSION: Literal[
    "aion-glm-continual-learning-cross-cycle-context/v1"
] = "aion-glm-continual-learning-cross-cycle-context/v1"
CONTINUAL_LEARNING_CHECKPOINT_SCHEMA_VERSION: Literal[
    "aion-glm-continual-learning-checkpoint/v1"
] = "aion-glm-continual-learning-checkpoint/v1"
CONTINUAL_LEARNING_ROLLBACK_SCHEMA_VERSION: Literal["aion-glm-continual-learning-rollback/v1"] = (
    "aion-glm-continual-learning-rollback/v1"
)
CONTINUAL_LEARNING_CYCLE_OUTCOME_SCHEMA_VERSION: Literal[
    "aion-glm-continual-learning-cycle-outcome/v1"
] = "aion-glm-continual-learning-cycle-outcome/v1"
CONTINUAL_LEARNING_SESSION_RESULT_SCHEMA_VERSION: Literal[
    "aion-glm-continual-learning-session-result/v1"
] = "aion-glm-continual-learning-session-result/v1"
CONTINUAL_LEARNING_QUERY_SCHEMA_VERSION: Literal["aion-glm-continual-learning-query/v1"] = (
    "aion-glm-continual-learning-query/v1"
)
CONTINUAL_LEARNING_QUERY_RESULT_SCHEMA_VERSION: Literal[
    "aion-glm-continual-learning-query-result/v1"
] = "aion-glm-continual-learning-query-result/v1"
CONTINUAL_LEARNING_INTEGRITY_SCHEMA_VERSION: Literal["aion-glm-continual-learning-integrity/v1"] = (
    "aion-glm-continual-learning-integrity/v1"
)
CONTINUAL_LEARNING_EVIDENCE_SCHEMA_VERSION: Literal["aion-glm-continual-learning-evidence/v1"] = (
    "aion-glm-continual-learning-evidence/v1"
)
CONTINUAL_LEARNING_REASON_REGISTRY_VERSION: Literal["aion-glm-continual-learning-reasons/v1"] = (
    "aion-glm-continual-learning-reasons/v1"
)

PROGRAM_ID: Literal["AION-GOVERNED-LEARNING-MEMORY-001"] = "AION-GOVERNED-LEARNING-MEMORY-001"
AUTHORIZATION_TRANSACTION_ID: Literal["AION-227-GLM-0004"] = "AION-227-GLM-0004"
APPROVAL_RECORD_ID: Literal["AION-227-GLM-0004"] = "AION-227-GLM-0004"
IMPLEMENTATION_TASK: Literal["AION-228"] = "AION-228"
FORMAL_CLOSEOUT_TASK: Literal["AION-229"] = "AION-229"
AUTHORIZATION_SCOPE: Literal[
    "operator-invoked-bounded-engagement-intake-explicit-public-https-research-verified-knowledge-promotion-temporary-local-persistence-shadow-adaptation-cross-cycle-outcome-evaluation-rollback-cleanup-audit-pilot-core"
] = (
    "operator-invoked-bounded-engagement-intake-explicit-public-https-research-"
    "verified-knowledge-promotion-temporary-local-persistence-shadow-adaptation-"
    "cross-cycle-outcome-evaluation-rollback-cleanup-audit-pilot-core"
)
LIVE_CONFIRMATION_TEXT: Literal["RUN_CONTROLLED_LOCAL_CONTINUAL_LEARNING_PILOT"] = (
    "RUN_CONTROLLED_LOCAL_CONTINUAL_LEARNING_PILOT"
)
ZERO_HASH = "0" * 64

RESOURCE_LIMITS: dict[str, int] = {
    "maximum_live_pilot_sessions": 1,
    "maximum_cycles_per_live_pilot": 3,
    "maximum_synthetic_test_sessions": 20,
    "maximum_engagement_signals_per_cycle": 100,
    "maximum_engagement_candidates_per_cycle": 25,
    "maximum_research_gap_candidates_per_cycle": 10,
    "maximum_research_plans_per_cycle": 3,
    "maximum_queries_per_research_plan": 10,
    "maximum_explicit_source_urls_per_cycle": 20,
    "maximum_domains_per_cycle": 10,
    "maximum_source_candidates_per_cycle": 25,
    "maximum_dns_resolutions_per_cycle": 100,
    "maximum_public_https_requests_per_cycle": 50,
    "maximum_source_fetches_per_cycle": 25,
    "maximum_redirects_per_fetch": 3,
    "maximum_concurrency": 4,
    "maximum_timeout_seconds_per_request": 20,
    "maximum_wall_clock_seconds_per_cycle": 1800,
    "maximum_total_live_pilot_seconds": 7200,
    "maximum_response_bytes_per_source": 5_242_880,
    "maximum_transfer_bytes_per_cycle": 52_428_800,
    "maximum_source_snapshots_per_cycle": 50,
    "maximum_claim_specs_per_cycle": 50,
    "maximum_verified_candidates_per_cycle": 25,
    "maximum_promotion_plans_per_cycle": 25,
    "maximum_promotion_approval_records_per_transaction": 4,
    "maximum_temporary_local_persistence_transactions_per_cycle": 5,
    "maximum_knowledge_versions_written_per_cycle": 25,
    "maximum_projection_records_written_per_cycle": 100,
    "maximum_engagement_shadow_applications_per_cycle": 25,
    "maximum_counterfactual_cases_per_cycle": 250,
    "maximum_operator_review_items_per_cycle": 100,
    "maximum_cycle_checkpoints": 10,
    "maximum_cycle_evidence_bytes": 10_485_760,
    "maximum_retained_database_files": 0,
    "maximum_retained_wal_files": 0,
    "maximum_retained_shm_files": 0,
    "maximum_retained_backup_files": 0,
    "maximum_retained_manifest_files": 0,
    "maximum_operator_local_store_transactions": 0,
    "maximum_background_cycles": 0,
    "maximum_scheduled_cycles": 0,
    "maximum_automatic_cycle_continuations": 0,
    "maximum_automatic_source_discoveries": 0,
    "maximum_crawler_requests": 0,
    "maximum_search_provider_calls": 0,
    "maximum_connector_calls": 0,
    "maximum_model_provider_calls": 0,
    "maximum_automatic_candidate_approvals": 0,
    "maximum_automatic_knowledge_promotions": 0,
    "maximum_automatic_persistence_transactions": 0,
    "maximum_production_memory_writes": 0,
    "maximum_production_policy_mutations": 0,
    "maximum_cognitive_memory_writes": 0,
    "maximum_actual_belief_creations": 0,
    "maximum_actual_belief_mutations": 0,
    "maximum_persistent_engagement_overlay_writes": 0,
    "maximum_source_mutations": 0,
    "maximum_git_operations": 0,
    "maximum_runtime_created_pull_requests": 0,
    "maximum_runtime_created_approvals": 0,
    "maximum_deployments": 0,
    "maximum_model_weight_changes": 0,
}

MODEL_CONFIG = ConfigDict(extra="forbid", hide_input_in_errors=True)
FROZEN_MODEL_CONFIG = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
SAFE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._:-]{0,127}$")
DOMAIN_RE = re.compile(
    r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?"
    r"(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+$"
)
PROTECTED_TEXT_MARKERS = (
    "authorization:",
    "cookie:",
    "proxy-authorization:",
    "bearer ",
    "sk-",
    "ghp_",
    "gho_",
    "-----begin private key-----",
    "raw source body",
    "raw approval payload",
    "hidden reasoning",
)


class ContinualLearningError(ValueError):
    """Raised when the governed continual-learning pilot fails closed."""


class ContinualLearningPilotMode(StrEnum):
    """Allowed pilot execution modes."""

    DETERMINISTIC_SIMULATION = "deterministic_simulation"
    OPERATOR_INVOKED_LIVE = "operator_invoked_live"


class ContinualLearningSessionStatus(StrEnum):
    """Session lifecycle status."""

    DRAFTED = "drafted"
    AUTHORIZED = "authorized"
    RUNNING = "running"
    COMPLETED = "completed"
    COMPLETED_WITH_ABSTENTION = "completed_with_abstention"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"
    CLEANED = "cleaned"


class ContinualLearningCycleKind(StrEnum):
    """The three authorized live-pilot cycle kinds."""

    EVIDENCE_ACQUISITION_AND_TEMPORARY_CONTINUITY = "evidence_acquisition_and_temporary_continuity"
    READ_CONTEXT_AND_SHADOW_ADAPTATION = "read_context_and_shadow_adaptation"
    CONTRADICTION_ABSTENTION_AND_ROLLBACK = "contradiction_abstention_and_rollback"


class ContinualLearningCycleState(StrEnum):
    """Closed per-cycle state machine."""

    DRAFTED = "drafted"
    AUTHORIZED = "authorized"
    ENGAGEMENT_INTAKE_VALIDATED = "engagement_intake_validated"
    RESEARCH_GAP_SELECTED = "research_gap_selected"
    RESEARCH_PLANNED = "research_planned"
    RESEARCH_ACQUIRED = "research_acquired"
    EVIDENCE_ASSESSED = "evidence_assessed"
    VERIFIED_CANDIDATE_REVIEWED = "verified_candidate_reviewed"
    PROMOTION_PLANNED = "promotion_planned"
    PERSISTENCE_APPROVAL_VALIDATED = "persistence_approval_validated"
    TEMPORARILY_PERSISTED = "temporarily_persisted"
    SHADOW_APPLICATION_PLANNED = "shadow_application_planned"
    SHADOW_APPLICATION_EVALUATED = "shadow_application_evaluated"
    CYCLE_COMPLETED = "cycle_completed"
    ABSTAINED = "abstained"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"


class ContinualLearningStageDisposition(StrEnum):
    """Per-stage disposition."""

    EXECUTED = "executed"
    EXPLICIT_NO_OP_BY_CYCLE_POLICY = "explicit_no_op_by_cycle_policy"
    ABSTAINED = "abstained"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"


class ContinualLearningCycleOutcomeStatus(StrEnum):
    """Terminal cycle outcome."""

    COMPLETED = "completed"
    ABSTAINED = "abstained"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"


class ContinualLearningResearchStatus(StrEnum):
    """Research composition status."""

    PLANNED = "planned"
    ACQUIRED = "acquired"
    COMPLETED_WITH_REJECTIONS = "completed_with_rejections"
    ABSTAINED = "abstained"
    BLOCKED = "blocked"
    FAILED = "failed"


class ContinualLearningKnowledgeStatus(StrEnum):
    """Verified-knowledge composition status."""

    ELIGIBLE_FOR_REVIEW = "eligible_for_review"
    INELIGIBLE = "ineligible"
    REVALIDATION_REQUIRED = "revalidation_required"
    ABSTAINED = "abstained"


class ContinualLearningPromotionStatus(StrEnum):
    """Promotion composition status."""

    DRY_RUN_PASSED = "dry_run_passed"
    DUPLICATE_NO_OP = "duplicate_no_op"
    BLOCKED = "blocked"
    ABSTAINED = "abstained"


class ContinualLearningPersistenceStatus(StrEnum):
    """Temporary persistence composition status."""

    TEMPORARILY_PERSISTED = "temporarily_persisted"
    IDEMPOTENT_REPLAY = "idempotent_replay"
    BLOCKED = "blocked"
    NOT_APPLICABLE = "not_applicable"
    ROLLED_BACK = "rolled_back"


class ContinualLearningShadowStatus(StrEnum):
    """Shadow adaptation composition status."""

    SHADOW_APPLIED = "shadow_applied"
    BASELINE_RETAINED = "baseline_retained"
    CANDIDATE_REJECTED = "candidate_rejected"
    ABSTAINED = "abstained"
    NOT_APPLICABLE = "not_applicable"
    EXPIRED = "expired"
    ROLLED_BACK = "rolled_back"


ORDINARY_TRANSITIONS: dict[ContinualLearningCycleState, ContinualLearningCycleState] = {
    ContinualLearningCycleState.DRAFTED: ContinualLearningCycleState.AUTHORIZED,
    ContinualLearningCycleState.AUTHORIZED: (
        ContinualLearningCycleState.ENGAGEMENT_INTAKE_VALIDATED
    ),
    ContinualLearningCycleState.ENGAGEMENT_INTAKE_VALIDATED: (
        ContinualLearningCycleState.RESEARCH_GAP_SELECTED
    ),
    ContinualLearningCycleState.RESEARCH_GAP_SELECTED: (
        ContinualLearningCycleState.RESEARCH_PLANNED
    ),
    ContinualLearningCycleState.RESEARCH_PLANNED: (ContinualLearningCycleState.RESEARCH_ACQUIRED),
    ContinualLearningCycleState.RESEARCH_ACQUIRED: (ContinualLearningCycleState.EVIDENCE_ASSESSED),
    ContinualLearningCycleState.EVIDENCE_ASSESSED: (
        ContinualLearningCycleState.VERIFIED_CANDIDATE_REVIEWED
    ),
    ContinualLearningCycleState.VERIFIED_CANDIDATE_REVIEWED: (
        ContinualLearningCycleState.PROMOTION_PLANNED
    ),
    ContinualLearningCycleState.PROMOTION_PLANNED: (
        ContinualLearningCycleState.PERSISTENCE_APPROVAL_VALIDATED
    ),
    ContinualLearningCycleState.PERSISTENCE_APPROVAL_VALIDATED: (
        ContinualLearningCycleState.TEMPORARILY_PERSISTED
    ),
    ContinualLearningCycleState.TEMPORARILY_PERSISTED: (
        ContinualLearningCycleState.SHADOW_APPLICATION_PLANNED
    ),
    ContinualLearningCycleState.SHADOW_APPLICATION_PLANNED: (
        ContinualLearningCycleState.SHADOW_APPLICATION_EVALUATED
    ),
    ContinualLearningCycleState.SHADOW_APPLICATION_EVALUATED: (
        ContinualLearningCycleState.CYCLE_COMPLETED
    ),
}
TERMINAL_STATES = {
    ContinualLearningCycleState.CYCLE_COMPLETED,
    ContinualLearningCycleState.ABSTAINED,
    ContinualLearningCycleState.ROLLED_BACK,
    ContinualLearningCycleState.FAILED,
}
ABSTAINABLE_STATES = set(ORDINARY_TRANSITIONS) | {
    ContinualLearningCycleState.SHADOW_APPLICATION_EVALUATED
}


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""

    return datetime.now(UTC)


def ensure_utc(value: datetime) -> datetime:
    """Require timezone-aware UTC datetimes."""

    if value.tzinfo is None or value.utcoffset() is None:
        raise ContinualLearningError("timestamp must be timezone-aware")
    return value.astimezone(UTC)


def stable_json(payload: Any) -> str:
    """Serialize a value deterministically for fingerprinting."""

    return json.dumps(_normalize(payload), sort_keys=True, separators=(",", ":"))


def continual_fingerprint(payload: Any) -> str:
    """Return a deterministic SHA-256 fingerprint."""

    return hashlib.sha256(stable_json(payload).encode("utf-8")).hexdigest()


def sha256_bytes(data: bytes) -> str:
    """Return a SHA-256 digest for bytes."""

    return hashlib.sha256(data).hexdigest()


def validate_hex64(value: str) -> str:
    """Validate a lowercase SHA-256 fingerprint."""

    if not HEX64_RE.fullmatch(value):
        raise ValueError("expected lowercase 64-character SHA-256 fingerprint")
    return value


def safe_identifier(value: str) -> str:
    """Validate a bounded lower-case identifier."""

    if not SAFE_ID_RE.fullmatch(value):
        raise ValueError("unsafe identifier")
    return value


def quantize_decimal(value: Decimal | int | str | float) -> Decimal:
    """Quantize finite decimal values to six places."""

    decimal = Decimal(str(value))
    if not decimal.is_finite():
        raise ValueError("decimal value must be finite")
    return decimal.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)


def domain_allowlist_fingerprint(domains: tuple[str, ...]) -> str:
    """Return the redacted fingerprint for a domain allowlist."""

    normalized = tuple(sorted(validate_domain(value) for value in domains))
    return continual_fingerprint({"domains": normalized})


def validate_domain(value: str) -> str:
    """Validate an exact domain name."""

    normalized = value.strip().lower()
    if "*" in normalized or not DOMAIN_RE.fullmatch(normalized):
        raise ValueError("domain must be exact and non-wildcard")
    return normalized


def fingerprint_file_path(path: str | Path) -> str:
    """Fingerprint a path without exposing it in committed evidence."""

    return continual_fingerprint({"path": str(Path(path).resolve())})


def build_record[T: BaseModel](
    model: type[T],
    payload: Mapping[str, Any],
    fingerprint_field: str,
) -> T:
    """Build a frozen model with its deterministic fingerprint populated."""

    material = dict(payload)
    material.pop(fingerprint_field, None)
    fingerprint_material: dict[str, Any] = {}
    for field_name, field_info in model.model_fields.items():
        if field_name == fingerprint_field:
            continue
        if field_name in material:
            fingerprint_material[field_name] = material[field_name]
        elif not field_info.is_required():
            fingerprint_material[field_name] = field_info.get_default(call_default_factory=True)
    material[fingerprint_field] = continual_fingerprint(fingerprint_material)
    return model.model_validate(material)


def expected_model_fingerprint(model: BaseModel, fingerprint_field: str) -> str:
    """Recompute a model fingerprint."""

    payload = model.model_dump(mode="json")
    payload.pop(fingerprint_field, None)
    return continual_fingerprint(payload)


def assert_allowed_transition(
    state_before: ContinualLearningCycleState,
    state_after: ContinualLearningCycleState,
) -> None:
    """Validate one explicit state-machine transition."""

    if state_before in TERMINAL_STATES:
        raise ContinualLearningError("terminal cycle state cannot advance")
    ordinary = ORDINARY_TRANSITIONS.get(state_before)
    if state_after == ordinary:
        return
    if (
        state_after
        in {
            ContinualLearningCycleState.ABSTAINED,
            ContinualLearningCycleState.ROLLED_BACK,
            ContinualLearningCycleState.FAILED,
        }
        and state_before in ABSTAINABLE_STATES
    ):
        return
    raise ContinualLearningError("stage transition is not authorized")


def _normalize(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return _normalize(value.model_dump(mode="json"))
    if isinstance(value, datetime):
        return ensure_utc(value).isoformat().replace("+00:00", "Z")
    if isinstance(value, Decimal):
        return format(quantize_decimal(value), "f")
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, dict):
        return {str(key): _normalize(item) for key, item in sorted(value.items())}
    if isinstance(value, (list, tuple)):
        return [_normalize(item) for item in value]
    return value


def _reject_protected_material(value: Any) -> None:
    if isinstance(value, str):
        lowered = value.lower()
        if any(marker in lowered for marker in PROTECTED_TEXT_MARKERS):
            raise ValueError("protected material is not allowed")
        return
    if isinstance(value, dict):
        for item in value.values():
            _reject_protected_material(item)
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            _reject_protected_material(item)


class StrictModel(BaseModel):
    """Strict model base with protected material screening."""

    model_config = FROZEN_MODEL_CONFIG

    @model_validator(mode="after")
    def _validate_protected_values(self) -> Self:
        _reject_protected_material(self.model_dump(mode="python"))
        return self


class FingerprintedModel(StrictModel):
    """Strict model whose fingerprint is self-validating."""

    fingerprint_field: ClassVar[str]

    @model_validator(mode="after")
    def _validate_fingerprint(self) -> Self:
        field = self.fingerprint_field
        actual = getattr(self, field)
        validate_hex64(actual)
        expected = expected_model_fingerprint(self, field)
        if actual != expected:
            raise ValueError(f"{field} mismatch")
        return self


class ContinualLearningResourceBudget(StrictModel):
    """Exact AION-227-GLM-0004 resource budget."""

    schema_version: Literal["aion-glm-continual-learning/v1"] = (
        CONTINUAL_LEARNING_CONTRACT_SCHEMA_VERSION
    )
    limits: dict[str, int] = Field(default_factory=lambda: dict(RESOURCE_LIMITS))

    @model_validator(mode="after")
    def _validate_exact_limits(self) -> Self:
        if self.limits != RESOURCE_LIMITS:
            raise ValueError("continual-learning resource limits must match authorization")
        return self


class ContinualLearningResourceUsage(StrictModel):
    """Per-stage, per-cycle, or per-session usage counters."""

    live_pilot_sessions: int = 0
    cycles: int = 0
    synthetic_test_sessions: int = 0
    engagement_signals: int = 0
    engagement_candidates: int = 0
    research_gap_candidates: int = 0
    research_plans: int = 0
    queries_per_research_plan: int = 0
    explicit_source_urls: int = 0
    domains: int = 0
    source_candidates: int = 0
    dns_resolutions: int = 0
    public_https_requests: int = 0
    source_fetches: int = 0
    redirects_per_fetch: int = 0
    concurrency: int = 0
    timeout_seconds_per_request: int = 0
    wall_clock_seconds_per_cycle: int = 0
    total_live_pilot_seconds: int = 0
    response_bytes_per_source: int = 0
    transfer_bytes_per_cycle: int = 0
    source_snapshots: int = 0
    claim_specs: int = 0
    verified_candidates: int = 0
    promotion_plans: int = 0
    promotion_approval_records: int = 0
    temporary_local_persistence_transactions: int = 0
    knowledge_versions_written: int = 0
    projection_records_written: int = 0
    engagement_shadow_applications: int = 0
    counterfactual_cases: int = 0
    operator_review_items: int = 0
    cycle_checkpoints: int = 0
    cycle_evidence_bytes: int = 0
    retained_database_files: int = 0
    retained_wal_files: int = 0
    retained_shm_files: int = 0
    retained_backup_files: int = 0
    retained_manifest_files: int = 0
    operator_local_store_transactions: int = 0
    background_cycles: int = 0
    scheduled_cycles: int = 0
    automatic_cycle_continuations: int = 0
    automatic_source_discoveries: int = 0
    crawler_requests: int = 0
    search_provider_calls: int = 0
    connector_calls: int = 0
    model_provider_calls: int = 0
    automatic_candidate_approvals: int = 0
    automatic_knowledge_promotions: int = 0
    automatic_persistence_transactions: int = 0
    production_memory_writes: int = 0
    production_policy_mutations: int = 0
    cognitive_memory_writes: int = 0
    actual_belief_creations: int = 0
    actual_belief_mutations: int = 0
    persistent_engagement_overlay_writes: int = 0
    source_mutations: int = 0
    git_operations: int = 0
    runtime_created_pull_requests: int = 0
    runtime_created_approvals: int = 0
    deployments: int = 0
    model_weight_changes: int = 0

    @field_validator("*")
    @classmethod
    def _non_negative(cls, value: int) -> int:
        if value < 0:
            raise ValueError("usage counters must be non-negative")
        return value


class ContinualLearningBudgetDecision(FingerprintedModel):
    """Budget decision for one usage snapshot."""

    fingerprint_field: ClassVar[str] = "decision_fingerprint"

    budget_decision_id: str
    usage: ContinualLearningResourceUsage
    budget: ContinualLearningResourceBudget
    passed: bool
    violations: tuple[str, ...] = ()
    decision_fingerprint: str


def evaluate_resource_budget(
    usage: ContinualLearningResourceUsage,
    *,
    budget: ContinualLearningResourceBudget | None = None,
    budget_decision_id: str = "continual-learning-budget-decision",
) -> ContinualLearningBudgetDecision:
    """Fail closed on any one-over-limit value."""

    resolved = budget or ContinualLearningResourceBudget()
    usage_payload = usage.model_dump()
    usage_key_overrides = {
        "maximum_cycles_per_live_pilot": "cycles",
        "maximum_synthetic_test_sessions": "synthetic_test_sessions",
        "maximum_source_fetches_per_cycle": "source_fetches",
    }
    violations: list[str] = []
    for key, limit in resolved.limits.items():
        usage_key = usage_key_overrides.get(key, key.removeprefix("maximum_"))
        value = usage_payload.get(usage_key, 0)
        if value > limit:
            violations.append(key)
    return build_record(
        ContinualLearningBudgetDecision,
        {
            "budget_decision_id": budget_decision_id,
            "usage": usage,
            "budget": resolved,
            "passed": not violations,
            "violations": tuple(sorted(violations)),
        },
        "decision_fingerprint",
    )


class ContinualLearningPilotAuthorizationEnvelope(FingerprintedModel):
    """Current AION-227-GLM-0004 pilot authorization envelope."""

    fingerprint_field: ClassVar[str] = "authorization_envelope_fingerprint"

    schema_version: Literal["aion-glm-continual-learning-authorization/v1"]
    authorization_transaction_id: Literal["AION-227-GLM-0004"]
    approval_record_id: Literal["AION-227-GLM-0004"]
    session_id: str
    operator_identity_fingerprint: str
    mode: ContinualLearningPilotMode
    cycle_ids: tuple[str, ...]
    cycle_plan_fingerprints: tuple[str, ...]
    exact_domain_allowlist: tuple[str, ...]
    domain_allowlist_fingerprint: str
    explicit_source_url_fingerprints: tuple[str, ...]
    research_claim_fingerprints: tuple[str, ...]
    temporary_root_fingerprint: str
    temporary_store_path_fingerprint: str
    maximum_cycles: int
    maximum_session_seconds: int
    created_at: datetime
    expires_at: datetime
    confirmation_fingerprint: str
    operator_invoked: bool = True
    background_execution: bool = False
    scheduled_execution: bool = False
    automatic_cycle_continuation: bool = False
    automatic_source_discovery: bool = False
    crawler_enabled: bool = False
    search_provider_enabled: bool = False
    connector_enabled: bool = False
    model_provider_enabled: bool = False
    production_runtime: bool = False
    production_exposure: bool = False
    authorization_envelope_fingerprint: str

    @field_validator("session_id", *("cycle_ids",))
    @classmethod
    def _safe_ids(cls, value: Any) -> Any:
        if isinstance(value, tuple):
            return tuple(safe_identifier(item) for item in value)
        return safe_identifier(value)

    @field_validator(
        "operator_identity_fingerprint",
        "domain_allowlist_fingerprint",
        "temporary_root_fingerprint",
        "temporary_store_path_fingerprint",
        "confirmation_fingerprint",
    )
    @classmethod
    def _hex(cls, value: str) -> str:
        return validate_hex64(value)

    @field_validator(
        "cycle_plan_fingerprints",
        "explicit_source_url_fingerprints",
        "research_claim_fingerprints",
    )
    @classmethod
    def _hex_tuple(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(validate_hex64(item) for item in value)

    @field_validator("exact_domain_allowlist")
    @classmethod
    def _domains(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(sorted(validate_domain(item) for item in value))

    @model_validator(mode="after")
    def _validate_envelope(self) -> Self:
        created = ensure_utc(self.created_at)
        expires = ensure_utc(self.expires_at)
        if expires <= created or expires > created + timedelta(hours=2):
            raise ValueError("authorization envelope expires outside the authorized window")
        if self.maximum_cycles != RESOURCE_LIMITS["maximum_cycles_per_live_pilot"]:
            raise ValueError("maximum cycle count must be exactly three")
        if self.maximum_session_seconds > RESOURCE_LIMITS["maximum_total_live_pilot_seconds"]:
            raise ValueError("session duration exceeds authorization")
        if self.mode is ContinualLearningPilotMode.OPERATOR_INVOKED_LIVE:
            if len(self.cycle_ids) != 3 or len(self.cycle_plan_fingerprints) != 3:
                raise ValueError("live mode requires exactly three cycles")
            expected = continual_fingerprint({"confirmation": LIVE_CONFIRMATION_TEXT})
            if self.confirmation_fingerprint != expected:
                raise ValueError("live confirmation fingerprint mismatch")
        prohibited = (
            self.background_execution,
            self.scheduled_execution,
            self.automatic_cycle_continuation,
            self.automatic_source_discovery,
            self.crawler_enabled,
            self.search_provider_enabled,
            self.connector_enabled,
            self.model_provider_enabled,
            self.production_runtime,
            self.production_exposure,
        )
        if not self.operator_invoked or any(prohibited):
            raise ValueError("continual-learning pilot must be explicit and non-production")
        if self.domain_allowlist_fingerprint != domain_allowlist_fingerprint(
            self.exact_domain_allowlist
        ):
            raise ValueError("domain allowlist fingerprint mismatch")
        return self


class ContinualLearningCyclePlan(FingerprintedModel):
    """Immutable plan for one explicit cycle."""

    fingerprint_field: ClassVar[str] = "cycle_plan_fingerprint"

    schema_version: Literal["aion-glm-continual-learning-cycle-plan/v1"]
    cycle_id: str
    session_id: str
    cycle_kind: ContinualLearningCycleKind
    cycle_sequence: int
    required_stages: tuple[ContinualLearningCycleState, ...]
    explicit_no_op_stages: tuple[ContinualLearningCycleState, ...] = ()
    input_fingerprints: tuple[str, ...]
    approval_requirement_fingerprints: tuple[str, ...]
    expected_terminal_outcome: ContinualLearningCycleOutcomeStatus
    maximum_cycle_seconds: int
    rollback_plan_fingerprint: str
    cleanup_requirement_fingerprints: tuple[str, ...]
    created_at: datetime
    cycle_plan_fingerprint: str
    operator_invoked: bool = True
    automatic_transition: bool = False
    background_execution: bool = False
    scheduled_execution: bool = False
    production_effect: bool = False
    runtime_effect: bool = False

    @field_validator("cycle_id", "session_id")
    @classmethod
    def _safe_id(cls, value: str) -> str:
        return safe_identifier(value)

    @field_validator(
        "input_fingerprints",
        "approval_requirement_fingerprints",
        "cleanup_requirement_fingerprints",
    )
    @classmethod
    def _fingerprints(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(validate_hex64(item) for item in value)

    @field_validator("rollback_plan_fingerprint")
    @classmethod
    def _fingerprint(cls, value: str) -> str:
        return validate_hex64(value)

    @model_validator(mode="after")
    def _validate_plan(self) -> Self:
        ensure_utc(self.created_at)
        if self.maximum_cycle_seconds > RESOURCE_LIMITS["maximum_wall_clock_seconds_per_cycle"]:
            raise ValueError("cycle exceeds maximum wall clock duration")
        if not self.operator_invoked or any(
            (
                self.automatic_transition,
                self.background_execution,
                self.scheduled_execution,
                self.production_effect,
                self.runtime_effect,
            )
        ):
            raise ValueError("cycle plan violates explicit non-production execution")
        if self.required_stages[0] is not ContinualLearningCycleState.DRAFTED:
            raise ValueError("cycle plan must start at drafted")
        if self.required_stages[-1] not in TERMINAL_STATES:
            raise ValueError("cycle plan must terminate explicitly")
        return self


class ContinualLearningSessionPlan(FingerprintedModel):
    """Immutable three-cycle session plan."""

    fingerprint_field: ClassVar[str] = "session_plan_fingerprint"

    schema_version: Literal["aion-glm-continual-learning-session-plan/v1"]
    session_id: str
    authorization_transaction_id: Literal["AION-227-GLM-0004"]
    mode: ContinualLearningPilotMode
    cycle_plans: tuple[ContinualLearningCyclePlan, ...]
    exact_domain_allowlist: tuple[str, ...]
    explicit_source_url_fingerprints: tuple[str, ...]
    operator_identity_fingerprint: str
    maximum_session_seconds: int
    created_at: datetime
    expires_at: datetime
    final_cleanup_plan_fingerprint: str
    session_plan_fingerprint: str
    operator_invoked: bool = True
    automatic_cycle_continuation: bool = False
    background_execution: bool = False
    scheduled_execution: bool = False
    production_runtime: bool = False
    runtime_effect: bool = False

    @field_validator("session_id")
    @classmethod
    def _safe_id(cls, value: str) -> str:
        return safe_identifier(value)

    @field_validator(
        "operator_identity_fingerprint",
        "final_cleanup_plan_fingerprint",
    )
    @classmethod
    def _fingerprint(cls, value: str) -> str:
        return validate_hex64(value)

    @field_validator("explicit_source_url_fingerprints")
    @classmethod
    def _fingerprint_tuple(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(validate_hex64(item) for item in value)

    @field_validator("exact_domain_allowlist")
    @classmethod
    def _domains(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(sorted(validate_domain(item) for item in value))

    @model_validator(mode="after")
    def _validate_session(self) -> Self:
        created = ensure_utc(self.created_at)
        expires = ensure_utc(self.expires_at)
        if expires <= created or expires > created + timedelta(hours=2):
            raise ValueError("session plan expires outside authorized live-pilot window")
        if self.maximum_session_seconds > RESOURCE_LIMITS["maximum_total_live_pilot_seconds"]:
            raise ValueError("session exceeds maximum duration")
        if self.mode is ContinualLearningPilotMode.OPERATOR_INVOKED_LIVE:
            expected = (
                ContinualLearningCycleKind.EVIDENCE_ACQUISITION_AND_TEMPORARY_CONTINUITY,
                ContinualLearningCycleKind.READ_CONTEXT_AND_SHADOW_ADAPTATION,
                ContinualLearningCycleKind.CONTRADICTION_ABSTENTION_AND_ROLLBACK,
            )
            if len(self.cycle_plans) != 3:
                raise ValueError("live pilot requires exactly three cycle plans")
            if tuple(plan.cycle_kind for plan in self.cycle_plans) != expected:
                raise ValueError("live pilot cycle order mismatch")
        if not self.operator_invoked or any(
            (
                self.automatic_cycle_continuation,
                self.background_execution,
                self.scheduled_execution,
                self.production_runtime,
                self.runtime_effect,
            )
        ):
            raise ValueError("session plan must be explicit and non-production")
        return self


class ContinualLearningStageCommand(FingerprintedModel):
    """One explicit operator command that may advance one state."""

    fingerprint_field: ClassVar[str] = "command_fingerprint"

    schema_version: Literal["aion-glm-continual-learning-stage-command/v1"]
    stage_command_id: str
    session_id: str
    cycle_id: str
    authorization_transaction_id: Literal["AION-227-GLM-0004"]
    expected_current_state: ContinualLearningCycleState
    requested_next_state: ContinualLearningCycleState
    cycle_plan_fingerprint: str
    input_fingerprints: tuple[str, ...]
    approval_bundle_fingerprints: tuple[str, ...] = ()
    operator_identity_fingerprint: str
    operator_invoked: bool = True
    created_at: datetime
    expires_at: datetime
    command_fingerprint: str

    @field_validator("stage_command_id", "session_id", "cycle_id")
    @classmethod
    def _safe_id(cls, value: str) -> str:
        return safe_identifier(value)

    @field_validator(
        "cycle_plan_fingerprint",
        "operator_identity_fingerprint",
    )
    @classmethod
    def _fingerprint(cls, value: str) -> str:
        return validate_hex64(value)

    @field_validator("input_fingerprints", "approval_bundle_fingerprints")
    @classmethod
    def _fingerprint_tuple(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(validate_hex64(item) for item in value)

    @model_validator(mode="after")
    def _validate_command(self) -> Self:
        created = ensure_utc(self.created_at)
        expires = ensure_utc(self.expires_at)
        if expires <= created or expires > created + timedelta(minutes=30):
            raise ValueError("stage command expires outside 30-minute window")
        if not self.operator_invoked:
            raise ValueError("stage command must be operator invoked")
        assert_allowed_transition(self.expected_current_state, self.requested_next_state)
        return self


class ContinualLearningStageReceipt(FingerprintedModel):
    """Immutable receipt for one explicit state transition."""

    fingerprint_field: ClassVar[str] = "receipt_fingerprint"

    schema_version: Literal["aion-glm-continual-learning-stage-receipt/v1"]
    stage_receipt_id: str
    session_id: str
    cycle_id: str
    sequence_number: int
    prior_receipt_fingerprint: str
    state_before: ContinualLearningCycleState
    state_after: ContinualLearningCycleState
    disposition: ContinualLearningStageDisposition
    command_fingerprint: str
    input_fingerprints: tuple[str, ...]
    output_fingerprints: tuple[str, ...]
    approval_bundle_fingerprints: tuple[str, ...]
    bounded_counts: dict[str, int] = Field(default_factory=dict)
    reason_codes: tuple[str, ...]
    created_at: datetime
    receipt_fingerprint: str
    operator_invoked: bool = True
    background_execution: bool = False
    scheduled_execution: bool = False
    production_effect: bool = False
    runtime_effect: bool = False

    @field_validator("stage_receipt_id", "session_id", "cycle_id")
    @classmethod
    def _safe_id(cls, value: str) -> str:
        return safe_identifier(value)

    @field_validator(
        "prior_receipt_fingerprint",
        "command_fingerprint",
    )
    @classmethod
    def _fingerprint(cls, value: str) -> str:
        return validate_hex64(value)

    @field_validator(
        "input_fingerprints",
        "output_fingerprints",
        "approval_bundle_fingerprints",
    )
    @classmethod
    def _fingerprint_tuple(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(validate_hex64(item) for item in value)

    @field_validator("bounded_counts")
    @classmethod
    def _counts(cls, value: dict[str, int]) -> dict[str, int]:
        if any(count < 0 for count in value.values()):
            raise ValueError("bounded counts must be non-negative")
        return dict(sorted(value.items()))

    @model_validator(mode="after")
    def _validate_receipt(self) -> Self:
        ensure_utc(self.created_at)
        if self.sequence_number < 1:
            raise ValueError("receipt sequence must start at one")
        if not self.operator_invoked or any(
            (
                self.background_execution,
                self.scheduled_execution,
                self.production_effect,
                self.runtime_effect,
            )
        ):
            raise ValueError("stage receipt violates runtime boundary")
        if self.disposition is ContinualLearningStageDisposition.EXECUTED:
            assert_allowed_transition(self.state_before, self.state_after)
        return self


class ContinualLearningComponentInvocationBinding(FingerprintedModel):
    """Parent-authorized invocation of a historical component plane."""

    fingerprint_field: ClassVar[str] = "binding_fingerprint"

    binding_id: str
    current_authorization_transaction_id: Literal["AION-227-GLM-0004"]
    component_name: str
    component_implementation_task: str
    component_contract_authorization_id: str
    component_contract_authorization_closed: bool = True
    component_contract_authorization_reactivated: bool = False
    component_invocation_authorized_by_parent: bool = True
    cycle_id: str
    operation_fingerprint: str
    input_fingerprints: tuple[str, ...]
    output_fingerprints: tuple[str, ...]
    approval_bundle_fingerprints: tuple[str, ...]
    invoked_at: datetime
    binding_fingerprint: str
    read_only: bool = True
    redacted: bool = True
    runtime_effect: bool = False

    @field_validator("binding_id", "cycle_id")
    @classmethod
    def _safe_id(cls, value: str) -> str:
        return safe_identifier(value)

    @field_validator("operation_fingerprint")
    @classmethod
    def _fingerprint(cls, value: str) -> str:
        return validate_hex64(value)

    @field_validator(
        "input_fingerprints",
        "output_fingerprints",
        "approval_bundle_fingerprints",
    )
    @classmethod
    def _fingerprint_tuple(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(validate_hex64(item) for item in value)

    @model_validator(mode="after")
    def _validate_component_binding(self) -> Self:
        ensure_utc(self.invoked_at)
        if not self.component_contract_authorization_closed:
            raise ValueError("historical component authorization must remain closed")
        if self.component_contract_authorization_reactivated:
            raise ValueError("component authorization reactivation is prohibited")
        if not self.component_invocation_authorized_by_parent:
            raise ValueError("component invocation must be parent-authorized")
        if not self.read_only or not self.redacted or self.runtime_effect:
            raise ValueError("component binding must remain redacted and effect-free")
        return self


class ContinualLearningEngagementIntake(FingerprintedModel):
    """Non-factual engagement intake for a cycle."""

    fingerprint_field: ClassVar[str] = "intake_fingerprint"

    schema_version: Literal["aion-glm-continual-learning-engagement-intake/v1"]
    intake_id: str
    session_id: str
    cycle_id: str
    selected_candidate_id: str
    selected_candidate_kind: str
    signal_fingerprints: tuple[str, ...]
    candidate_fingerprints: tuple[str, ...]
    intake_role: str
    created_at: datetime
    intake_fingerprint: str
    engagement_is_non_factual: bool = True
    confidence_effect: bool = False
    knowledge_effect: bool = False
    source_independence_effect: bool = False
    citation_coverage_effect: bool = False
    provenance_effect: bool = False
    contradiction_resolution_effect: bool = False
    freshness_effect: bool = False
    cognitive_memory_effect: bool = False
    belief_effect: bool = False
    model_weight_effect: bool = False
    runtime_effect: bool = False

    @field_validator("intake_id", "session_id", "cycle_id", "selected_candidate_id")
    @classmethod
    def _safe_id(cls, value: str) -> str:
        return safe_identifier(value)

    @field_validator("signal_fingerprints", "candidate_fingerprints")
    @classmethod
    def _fingerprints(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(validate_hex64(item) for item in value)

    @model_validator(mode="after")
    def _validate_zero_effects(self) -> Self:
        ensure_utc(self.created_at)
        prohibited = (
            self.confidence_effect,
            self.knowledge_effect,
            self.source_independence_effect,
            self.citation_coverage_effect,
            self.provenance_effect,
            self.contradiction_resolution_effect,
            self.freshness_effect,
            self.cognitive_memory_effect,
            self.belief_effect,
            self.model_weight_effect,
            self.runtime_effect,
        )
        if not self.engagement_is_non_factual or any(prohibited):
            raise ValueError("engagement intake must remain non-factual and zero-effect")
        return self


class ContinualLearningResearchPlan(FingerprintedModel):
    """Explicit public research plan for one cycle."""

    fingerprint_field: ClassVar[str] = "research_plan_fingerprint"

    plan_id: str
    session_id: str
    cycle_id: str
    claim_fingerprint: str
    explicit_source_url_fingerprints: tuple[str, ...]
    exact_domains: tuple[str, ...]
    source_control_groups: tuple[str, ...]
    created_at: datetime
    research_plan_fingerprint: str
    explicit_urls_only: bool = True
    exact_domains_only: bool = True
    automatic_source_discovery: bool = False
    crawler_enabled: bool = False
    search_provider_enabled: bool = False
    runtime_effect: bool = False

    @field_validator("plan_id", "session_id", "cycle_id")
    @classmethod
    def _safe_id(cls, value: str) -> str:
        return safe_identifier(value)

    @field_validator("claim_fingerprint")
    @classmethod
    def _fingerprint(cls, value: str) -> str:
        return validate_hex64(value)

    @field_validator("explicit_source_url_fingerprints")
    @classmethod
    def _fingerprints(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(validate_hex64(item) for item in value)

    @field_validator("exact_domains")
    @classmethod
    def _domains(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(sorted(validate_domain(item) for item in value))

    @model_validator(mode="after")
    def _validate_research_plan(self) -> Self:
        ensure_utc(self.created_at)
        if len(self.explicit_source_url_fingerprints) < 3:
            raise ValueError("at least three explicit source URL fingerprints are required")
        if len(set(self.source_control_groups)) < 3:
            raise ValueError("at least three independent source-control groups are required")
        if any(
            (
                not self.explicit_urls_only,
                not self.exact_domains_only,
                self.automatic_source_discovery,
                self.crawler_enabled,
                self.search_provider_enabled,
                self.runtime_effect,
            )
        ):
            raise ValueError("research plan violates explicit allowlist boundary")
        return self


class ContinualLearningResearchSourceBinding(FingerprintedModel):
    """Redacted binding for one fetched explicit source."""

    fingerprint_field: ClassVar[str] = "source_binding_fingerprint"

    source_binding_id: str
    cycle_id: str
    url_fingerprint: str
    domain_fingerprint: str
    source_control_group: str
    dns_resolution_fingerprint: str
    http_exchange_fingerprint: str
    robots_policy_fingerprint: str
    provenance_fingerprint: str
    citation_fingerprint: str
    source_body_purged: bool = True
    source_body_retained: bool = False
    created_at: datetime
    source_binding_fingerprint: str
    runtime_effect: bool = False

    @field_validator("source_binding_id", "cycle_id")
    @classmethod
    def _safe_id(cls, value: str) -> str:
        return safe_identifier(value)

    @field_validator(
        "url_fingerprint",
        "domain_fingerprint",
        "dns_resolution_fingerprint",
        "http_exchange_fingerprint",
        "robots_policy_fingerprint",
        "provenance_fingerprint",
        "citation_fingerprint",
    )
    @classmethod
    def _fingerprint(cls, value: str) -> str:
        return validate_hex64(value)

    @model_validator(mode="after")
    def _validate_purge(self) -> Self:
        ensure_utc(self.created_at)
        if not self.source_body_purged or self.source_body_retained or self.runtime_effect:
            raise ValueError("source body must be purged and effect-free")
        return self


class ContinualLearningResearchBinding(FingerprintedModel):
    """Research acquisition binding for one cycle."""

    fingerprint_field: ClassVar[str] = "research_binding_fingerprint"

    schema_version: Literal["aion-glm-continual-learning-research-binding/v1"]
    binding_id: str
    session_id: str
    cycle_id: str
    status: ContinualLearningResearchStatus
    source_bindings: tuple[ContinualLearningResearchSourceBinding, ...]
    claim_fingerprint: str
    source_fetch_count: int
    dns_resolution_count: int
    public_https_request_count: int
    source_body_purge_count: int
    created_at: datetime
    research_binding_fingerprint: str
    source_bodies_retained: int = 0
    automatic_source_discoveries: int = 0
    crawler_requests: int = 0
    search_provider_calls: int = 0
    runtime_effect: bool = False

    @field_validator("binding_id", "session_id", "cycle_id")
    @classmethod
    def _safe_id(cls, value: str) -> str:
        return safe_identifier(value)

    @field_validator("claim_fingerprint")
    @classmethod
    def _fingerprint(cls, value: str) -> str:
        return validate_hex64(value)

    @model_validator(mode="after")
    def _validate_research(self) -> Self:
        ensure_utc(self.created_at)
        if self.status is ContinualLearningResearchStatus.ACQUIRED:
            if self.source_fetch_count < 3 or len(self.source_bindings) < 3:
                raise ValueError("acquired research requires three source fetches")
            if self.source_body_purge_count != self.source_fetch_count:
                raise ValueError("every fetched source body must be purged")
        if any(
            (
                self.source_bodies_retained,
                self.automatic_source_discoveries,
                self.crawler_requests,
                self.search_provider_calls,
                self.runtime_effect,
            )
        ):
            raise ValueError("research binding violates zero-effect boundary")
        return self


class ContinualLearningKnowledgeCandidateBinding(FingerprintedModel):
    """Verified-candidate composition result."""

    fingerprint_field: ClassVar[str] = "candidate_binding_fingerprint"

    schema_version: Literal["aion-glm-continual-learning-knowledge-binding/v1"]
    binding_id: str
    session_id: str
    cycle_id: str
    candidate_id: str
    candidate_status: ContinualLearningKnowledgeStatus
    candidate_fingerprint: str
    lineage_fingerprint: str
    provenance_complete: Decimal
    citation_coverage: Decimal
    evidence_coverage: Decimal
    candidate_confidence_cap: Decimal
    created_at: datetime
    candidate_binding_fingerprint: str
    automatic_promotion: bool = False
    persistent_write: bool = False
    cognitive_memory_write: bool = False
    belief_mutation: bool = False
    runtime_effect: bool = False

    @field_validator("binding_id", "session_id", "cycle_id", "candidate_id")
    @classmethod
    def _safe_id(cls, value: str) -> str:
        return safe_identifier(value)

    @field_validator("candidate_fingerprint", "lineage_fingerprint")
    @classmethod
    def _fingerprint(cls, value: str) -> str:
        return validate_hex64(value)

    @field_validator(
        "provenance_complete",
        "citation_coverage",
        "evidence_coverage",
        "candidate_confidence_cap",
    )
    @classmethod
    def _decimal(cls, value: Decimal) -> Decimal:
        return quantize_decimal(value)

    @model_validator(mode="after")
    def _validate_candidate(self) -> Self:
        ensure_utc(self.created_at)
        if self.candidate_status is ContinualLearningKnowledgeStatus.ELIGIBLE_FOR_REVIEW:
            required = Decimal("1.000000")
            if (
                self.provenance_complete != required
                or self.citation_coverage != required
                or self.evidence_coverage != required
                or self.candidate_confidence_cap < Decimal("0.850000")
            ):
                raise ValueError("eligible candidate lacks complete evidence")
        if any(
            (
                self.automatic_promotion,
                self.persistent_write,
                self.cognitive_memory_write,
                self.belief_mutation,
                self.runtime_effect,
            )
        ):
            raise ValueError("candidate binding violates zero-effect boundary")
        return self


class ContinualLearningPromotionBinding(FingerprintedModel):
    """Dry-run promotion composition result."""

    fingerprint_field: ClassVar[str] = "promotion_binding_fingerprint"

    schema_version: Literal["aion-glm-continual-learning-promotion-binding/v1"]
    binding_id: str
    session_id: str
    cycle_id: str
    transaction_id: str
    status: ContinualLearningPromotionStatus
    candidate_fingerprint: str
    promotion_plan_fingerprint: str
    promotion_result_fingerprint: str
    approval_bundle_fingerprint: str
    approval_count: int
    created_at: datetime
    promotion_binding_fingerprint: str
    future_persistence_review_required: bool = True
    future_persistence_authorized_by_promotion: bool = False
    actual_knowledge_promotion: bool = False
    persistent_writes: int = 0
    memory_writes: int = 0
    belief_mutations: int = 0
    runtime_effect: bool = False

    @field_validator("binding_id", "session_id", "cycle_id", "transaction_id")
    @classmethod
    def _safe_id(cls, value: str) -> str:
        return safe_identifier(value)

    @field_validator(
        "candidate_fingerprint",
        "promotion_plan_fingerprint",
        "promotion_result_fingerprint",
        "approval_bundle_fingerprint",
    )
    @classmethod
    def _fingerprint(cls, value: str) -> str:
        return validate_hex64(value)

    @model_validator(mode="after")
    def _validate_promotion(self) -> Self:
        ensure_utc(self.created_at)
        if self.status is ContinualLearningPromotionStatus.DRY_RUN_PASSED:
            if self.approval_count < 1:
                raise ValueError("dry-run promotion requires existing approval evidence")
        if any(
            (
                not self.future_persistence_review_required,
                self.future_persistence_authorized_by_promotion,
                self.actual_knowledge_promotion,
                self.persistent_writes,
                self.memory_writes,
                self.belief_mutations,
                self.runtime_effect,
            )
        ):
            raise ValueError("promotion binding violates dry-run boundary")
        return self


class ContinualLearningPersistenceBinding(FingerprintedModel):
    """Temporary local persistence composition result."""

    fingerprint_field: ClassVar[str] = "persistence_binding_fingerprint"

    schema_version: Literal["aion-glm-continual-learning-persistence-binding/v1"]
    binding_id: str
    session_id: str
    cycle_id: str
    transaction_id: str
    status: ContinualLearningPersistenceStatus
    temporary_store_fingerprint: str
    persistence_receipt_fingerprint: str
    knowledge_identity_ids: tuple[str, ...]
    knowledge_version_ids: tuple[str, ...]
    projection_record_fingerprints: tuple[str, ...]
    approval_bundle_fingerprint: str
    approval_count: int
    created_at: datetime
    persistence_binding_fingerprint: str
    temporary_store: bool = True
    production_memory_write: bool = False
    actual_belief_creation: bool = False
    actual_belief_mutation: bool = False
    retained_store: bool = False
    runtime_effect: bool = False

    @field_validator("binding_id", "session_id", "cycle_id", "transaction_id")
    @classmethod
    def _safe_id(cls, value: str) -> str:
        return safe_identifier(value)

    @field_validator(
        "temporary_store_fingerprint",
        "persistence_receipt_fingerprint",
        "approval_bundle_fingerprint",
    )
    @classmethod
    def _fingerprint(cls, value: str) -> str:
        return validate_hex64(value)

    @field_validator("projection_record_fingerprints")
    @classmethod
    def _fingerprint_tuple(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(validate_hex64(item) for item in value)

    @field_validator("knowledge_identity_ids", "knowledge_version_ids")
    @classmethod
    def _safe_tuple(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(safe_identifier(item) for item in value)

    @model_validator(mode="after")
    def _validate_persistence(self) -> Self:
        ensure_utc(self.created_at)
        if self.status is ContinualLearningPersistenceStatus.TEMPORARILY_PERSISTED:
            if self.approval_count < 2:
                raise ValueError("temporary persistence requires dual approvals")
            if not self.knowledge_version_ids:
                raise ValueError("temporary persistence must write at least one version")
        if any(
            (
                not self.temporary_store,
                self.production_memory_write,
                self.actual_belief_creation,
                self.actual_belief_mutation,
                self.retained_store,
                self.runtime_effect,
            )
        ):
            raise ValueError("persistence binding violates temporary-store boundary")
        return self


class ContinualLearningCrossCycleContext(FingerprintedModel):
    """Read-only session-scoped cross-cycle context."""

    fingerprint_field: ClassVar[str] = "context_fingerprint"

    schema_version: Literal["aion-glm-continual-learning-cross-cycle-context/v1"]
    context_id: str
    session_id: str
    completed_cycle_ids: tuple[str, ...]
    cycle_receipt_chain_heads: tuple[str, ...]
    research_result_fingerprints: tuple[str, ...]
    candidate_fingerprints: tuple[str, ...]
    promotion_result_fingerprints: tuple[str, ...]
    persistence_receipt_fingerprints: tuple[str, ...]
    exact_knowledge_query_fingerprints: tuple[str, ...]
    knowledge_identity_ids: tuple[str, ...]
    knowledge_version_ids: tuple[str, ...]
    shadow_result_fingerprints: tuple[str, ...]
    unresolved_gap_fingerprints: tuple[str, ...]
    contradiction_fingerprints: tuple[str, ...]
    created_at: datetime
    context_fingerprint: str
    read_only: bool = True
    temporary: bool = True
    production_memory: bool = False
    runtime_effect: bool = False

    @field_validator("context_id", "session_id")
    @classmethod
    def _safe_id(cls, value: str) -> str:
        return safe_identifier(value)

    @field_validator("completed_cycle_ids", "knowledge_identity_ids", "knowledge_version_ids")
    @classmethod
    def _safe_tuple(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(safe_identifier(item) for item in value)

    @field_validator(
        "cycle_receipt_chain_heads",
        "research_result_fingerprints",
        "candidate_fingerprints",
        "promotion_result_fingerprints",
        "persistence_receipt_fingerprints",
        "exact_knowledge_query_fingerprints",
        "shadow_result_fingerprints",
        "unresolved_gap_fingerprints",
        "contradiction_fingerprints",
    )
    @classmethod
    def _fingerprints(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(validate_hex64(item) for item in value)

    @model_validator(mode="after")
    def _validate_context(self) -> Self:
        ensure_utc(self.created_at)
        if (
            not self.read_only
            or not self.temporary
            or self.production_memory
            or self.runtime_effect
        ):
            raise ValueError("cross-cycle context must be read-only temporary evidence")
        return self


class ContinualLearningShadowBinding(FingerprintedModel):
    """Operator-approved in-memory shadow adaptation binding."""

    fingerprint_field: ClassVar[str] = "shadow_binding_fingerprint"

    schema_version: Literal["aion-glm-continual-learning-shadow-binding/v1"]
    binding_id: str
    session_id: str
    cycle_id: str
    status: ContinualLearningShadowStatus
    adaptation_identity_id: str
    candidate_fingerprint: str
    approval_bundle_fingerprint: str
    overlay_fingerprint: str
    baseline_fingerprint: str
    counterfactual_result_fingerprints: tuple[str, ...]
    recommendation_fingerprint: str
    approval_count: int
    active_overlay_records_after_cycle: int
    created_at: datetime
    shadow_binding_fingerprint: str
    persistent_overlay_write: bool = False
    aion_224_store_write: bool = False
    production_policy_mutation: bool = False
    factual_effect: bool = False
    confidence_effect: bool = False
    knowledge_effect: bool = False
    source_independence_effect: bool = False
    runtime_effect: bool = False

    @field_validator("binding_id", "session_id", "cycle_id", "adaptation_identity_id")
    @classmethod
    def _safe_id(cls, value: str) -> str:
        return safe_identifier(value)

    @field_validator(
        "candidate_fingerprint",
        "approval_bundle_fingerprint",
        "overlay_fingerprint",
        "baseline_fingerprint",
        "recommendation_fingerprint",
    )
    @classmethod
    def _fingerprint(cls, value: str) -> str:
        return validate_hex64(value)

    @field_validator("counterfactual_result_fingerprints")
    @classmethod
    def _fingerprint_tuple(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(validate_hex64(item) for item in value)

    @model_validator(mode="after")
    def _validate_shadow(self) -> Self:
        ensure_utc(self.created_at)
        if self.status is ContinualLearningShadowStatus.SHADOW_APPLIED:
            if self.approval_count < 1:
                raise ValueError("shadow application requires existing approval")
        prohibited = (
            self.active_overlay_records_after_cycle,
            self.persistent_overlay_write,
            self.aion_224_store_write,
            self.production_policy_mutation,
            self.factual_effect,
            self.confidence_effect,
            self.knowledge_effect,
            self.source_independence_effect,
            self.runtime_effect,
        )
        if any(prohibited):
            raise ValueError("shadow binding violates in-memory zero-effect boundary")
        return self


class ContinualLearningCheckpoint(FingerprintedModel):
    """Temporary redacted checkpoint for explicit resume."""

    fingerprint_field: ClassVar[str] = "checkpoint_fingerprint"

    schema_version: Literal["aion-glm-continual-learning-checkpoint/v1"]
    checkpoint_id: str
    session_id: str
    cycle_id: str
    current_state: ContinualLearningCycleState
    latest_stage_receipt_fingerprint: str
    receipt_chain_head: str
    cycle_plan_fingerprint: str
    authorization_envelope_fingerprint: str
    research_binding_fingerprint: str
    candidate_binding_fingerprint: str
    promotion_binding_fingerprint: str
    persistence_binding_fingerprint: str
    shadow_binding_fingerprint: str
    cross_cycle_context_fingerprint: str
    created_at: datetime
    expires_at: datetime
    temporary_file_fingerprint: str
    checkpoint_fingerprint: str
    operator_resume_required: bool = True
    automatic_resume: bool = False
    background_resume: bool = False
    redacted: bool = True
    runtime_effect: bool = False

    @field_validator("checkpoint_id", "session_id", "cycle_id")
    @classmethod
    def _safe_id(cls, value: str) -> str:
        return safe_identifier(value)

    @field_validator(
        "latest_stage_receipt_fingerprint",
        "receipt_chain_head",
        "cycle_plan_fingerprint",
        "authorization_envelope_fingerprint",
        "research_binding_fingerprint",
        "candidate_binding_fingerprint",
        "promotion_binding_fingerprint",
        "persistence_binding_fingerprint",
        "shadow_binding_fingerprint",
        "cross_cycle_context_fingerprint",
        "temporary_file_fingerprint",
    )
    @classmethod
    def _fingerprint(cls, value: str) -> str:
        return validate_hex64(value)

    @model_validator(mode="after")
    def _validate_checkpoint(self) -> Self:
        created = ensure_utc(self.created_at)
        expires = ensure_utc(self.expires_at)
        if expires <= created:
            raise ValueError("checkpoint must expire after creation")
        if any(
            (
                not self.operator_resume_required,
                self.automatic_resume,
                self.background_resume,
                not self.redacted,
                self.runtime_effect,
            )
        ):
            raise ValueError("checkpoint violates explicit resume boundary")
        return self


class ContinualLearningRollbackPlan(FingerprintedModel):
    """Closed rollback and cleanup plan."""

    fingerprint_field: ClassVar[str] = "rollback_plan_fingerprint"

    schema_version: Literal["aion-glm-continual-learning-rollback/v1"]
    rollback_plan_id: str
    session_id: str
    cycle_id: str
    rollback_operations: tuple[str, ...]
    referenced_fingerprints: tuple[str, ...]
    created_at: datetime
    rollback_plan_fingerprint: str
    production_mutation: bool = False
    arbitrary_command: bool = False
    runtime_effect: bool = False

    @field_validator("rollback_plan_id", "session_id", "cycle_id")
    @classmethod
    def _safe_id(cls, value: str) -> str:
        return safe_identifier(value)

    @field_validator("referenced_fingerprints")
    @classmethod
    def _fingerprints(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(validate_hex64(item) for item in value)

    @model_validator(mode="after")
    def _validate_rollback(self) -> Self:
        ensure_utc(self.created_at)
        if len(self.rollback_operations) > 50:
            raise ValueError("rollback plan exceeds maximum step count")
        if len(set(self.rollback_operations)) != len(self.rollback_operations):
            raise ValueError("rollback operations must be unique")
        if any((self.production_mutation, self.arbitrary_command, self.runtime_effect)):
            raise ValueError("rollback plan violates cleanup boundary")
        return self


class ContinualLearningCycleOutcome(FingerprintedModel):
    """Per-cycle outcome summary."""

    fingerprint_field: ClassVar[str] = "outcome_fingerprint"

    schema_version: Literal["aion-glm-continual-learning-cycle-outcome/v1"]
    cycle_id: str
    cycle_kind: ContinualLearningCycleKind
    terminal_status: ContinualLearningCycleOutcomeStatus
    final_state: ContinualLearningCycleState
    stage_receipt_count: int
    receipt_chain_head: str
    research_status: ContinualLearningResearchStatus
    candidate_status: ContinualLearningKnowledgeStatus
    promotion_status: ContinualLearningPromotionStatus
    persistence_status: ContinualLearningPersistenceStatus
    shadow_status: ContinualLearningShadowStatus
    evidence_gain_count: int
    duplicate_count: int
    contradiction_count: int
    abstention_reason_codes: tuple[str, ...]
    rollback_applied: bool
    cleanup_verified: bool
    outcome_fingerprint: str
    production_effect: bool = False
    runtime_effect: bool = False

    @field_validator("cycle_id")
    @classmethod
    def _safe_id(cls, value: str) -> str:
        return safe_identifier(value)

    @field_validator("receipt_chain_head")
    @classmethod
    def _fingerprint(cls, value: str) -> str:
        return validate_hex64(value)

    @model_validator(mode="after")
    def _validate_outcome(self) -> Self:
        if self.stage_receipt_count < 1:
            raise ValueError("cycle outcome requires at least one receipt")
        if not self.cleanup_verified or self.production_effect or self.runtime_effect:
            raise ValueError("cycle outcome cleanup or zero-effect boundary failed")
        return self


class ContinualLearningSessionResult(FingerprintedModel):
    """Complete three-cycle live or deterministic session result."""

    fingerprint_field: ClassVar[str] = "result_fingerprint"

    schema_version: Literal["aion-glm-continual-learning-session-result/v1"]
    session_id: str
    authorization_transaction_id: Literal["AION-227-GLM-0004"]
    mode: ContinualLearningPilotMode
    cycle_outcomes: tuple[ContinualLearningCycleOutcome, ...]
    cycle_count: int
    completed_cycle_count: int
    abstained_cycle_count: int
    rolled_back_cycle_count: int
    failed_cycle_count: int
    external_read_performed: bool
    dns_resolution_count: int
    public_https_request_count: int
    source_fetch_count: int
    source_body_purge_count: int
    verified_candidate_count: int
    promotion_plan_count: int
    temporary_persistence_transaction_count: int
    knowledge_version_write_count: int
    shadow_application_count: int
    cross_cycle_context_count: int
    stage_receipt_count: int
    checkpoint_count: int
    all_cleanup_verified: bool
    result_fingerprint: str
    active_overlay_records_after_close: int = 0
    retained_temporary_files: int = 0
    background_cycles: int = 0
    scheduled_cycles: int = 0
    automatic_approvals: int = 0
    automatic_promotions: int = 0
    automatic_persistence_transactions: int = 0
    production_memory_writes: int = 0
    production_policy_mutations: int = 0
    cognitive_memory_writes: int = 0
    actual_belief_creations: int = 0
    actual_belief_mutations: int = 0
    persistent_overlay_writes: int = 0
    source_mutations: int = 0
    git_operations: int = 0
    model_weight_changes: int = 0
    production_exposure: bool = False
    runtime_effect: bool = False

    @field_validator("session_id")
    @classmethod
    def _safe_id(cls, value: str) -> str:
        return safe_identifier(value)

    @model_validator(mode="after")
    def _validate_result(self) -> Self:
        if self.cycle_count != len(self.cycle_outcomes):
            raise ValueError("cycle count mismatch")
        if self.mode is ContinualLearningPilotMode.OPERATOR_INVOKED_LIVE and self.cycle_count != 3:
            raise ValueError("live pilot must have exactly three cycles")
        if self.source_body_purge_count != self.source_fetch_count:
            raise ValueError("every source body must be purged")
        prohibited_counts = (
            self.active_overlay_records_after_close,
            self.retained_temporary_files,
            self.background_cycles,
            self.scheduled_cycles,
            self.automatic_approvals,
            self.automatic_promotions,
            self.automatic_persistence_transactions,
            self.production_memory_writes,
            self.production_policy_mutations,
            self.cognitive_memory_writes,
            self.actual_belief_creations,
            self.actual_belief_mutations,
            self.persistent_overlay_writes,
            self.source_mutations,
            self.git_operations,
            self.model_weight_changes,
        )
        if any(prohibited_counts) or self.production_exposure or self.runtime_effect:
            raise ValueError("session result violates zero-effect boundary")
        if not self.all_cleanup_verified:
            raise ValueError("session cleanup is not verified")
        return self


class ContinualLearningQuery(FingerprintedModel):
    """Exact read-only query over pilot evidence."""

    fingerprint_field: ClassVar[str] = "query_fingerprint"

    schema_version: Literal["aion-glm-continual-learning-query/v1"]
    query_id: str
    filters: dict[str, str]
    limit: int = 1000
    query_fingerprint: str
    exact_match_only: bool = True
    semantic_search: bool = False
    fuzzy_search: bool = False
    popularity_ranking: bool = False
    runtime_effect: bool = False

    @field_validator("query_id")
    @classmethod
    def _safe_id(cls, value: str) -> str:
        return safe_identifier(value)

    @model_validator(mode="after")
    def _validate_query(self) -> Self:
        if self.limit > 1000:
            raise ValueError("query limit exceeds 1000")
        if any(
            (
                not self.exact_match_only,
                self.semantic_search,
                self.fuzzy_search,
                self.popularity_ranking,
                self.runtime_effect,
            )
        ):
            raise ValueError("only exact read-only queries are allowed")
        return self


class ContinualLearningQueryResult(FingerprintedModel):
    """Exact query result."""

    fingerprint_field: ClassVar[str] = "result_fingerprint"

    schema_version: Literal["aion-glm-continual-learning-query-result/v1"]
    query_id: str
    result_ids: tuple[str, ...]
    result_fingerprints: tuple[str, ...]
    result_count: int
    result_fingerprint: str
    deterministic_order: bool = True
    runtime_effect: bool = False

    @field_validator("query_id")
    @classmethod
    def _safe_id(cls, value: str) -> str:
        return safe_identifier(value)

    @field_validator("result_ids")
    @classmethod
    def _safe_tuple(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(safe_identifier(item) for item in value)

    @field_validator("result_fingerprints")
    @classmethod
    def _fingerprints(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(validate_hex64(item) for item in value)

    @model_validator(mode="after")
    def _validate_result(self) -> Self:
        if self.result_count != len(self.result_ids):
            raise ValueError("query result count mismatch")
        if not self.deterministic_order or self.runtime_effect:
            raise ValueError("query result must be deterministic and read-only")
        return self


class ContinualLearningIntegrityFinding(StrictModel):
    """Integrity finding."""

    finding_id: str
    severity: Literal["info", "warning", "error"]
    reason_code: str
    passed: bool
    related_fingerprints: tuple[str, ...] = ()


class ContinualLearningIntegrityReport(FingerprintedModel):
    """Integrity audit report."""

    fingerprint_field: ClassVar[str] = "integrity_report_fingerprint"

    schema_version: Literal["aion-glm-continual-learning-integrity/v1"]
    report_id: str
    session_id: str
    findings: tuple[ContinualLearningIntegrityFinding, ...]
    receipt_chain_valid: bool
    cleanup_valid: bool
    authorization_valid: bool
    component_authority_valid: bool
    zero_effect_boundary_valid: bool
    created_at: datetime
    integrity_report_fingerprint: str
    runtime_effect: bool = False

    @model_validator(mode="after")
    def _validate_integrity(self) -> Self:
        ensure_utc(self.created_at)
        if any(
            (
                not self.receipt_chain_valid,
                not self.cleanup_valid,
                not self.authorization_valid,
                not self.component_authority_valid,
                not self.zero_effect_boundary_valid,
                self.runtime_effect,
            )
        ):
            raise ValueError("continual-learning integrity report failed")
        if any(not finding.passed for finding in self.findings):
            raise ValueError("integrity report contains failed findings")
        return self


class ContinualLearningDiagnostics(StrictModel):
    """Redacted diagnostics for operator review."""

    diagnostics_id: str
    reason_codes: tuple[str, ...]
    redacted_summary: str
    created_at: datetime
    redacted: bool = True
    runtime_effect: bool = False


class ContinualLearningIncident(StrictModel):
    """Redacted incident record."""

    incident_id: str
    reason_code: str
    redacted_summary: str
    created_at: datetime
    redacted: bool = True
    runtime_effect: bool = False


class ContinualLearningOperatorReviewItem(FingerprintedModel):
    """Operator review item for the pilot result."""

    fingerprint_field: ClassVar[str] = "review_item_fingerprint"

    review_item_id: str
    session_id: str
    cycle_id: str | None = None
    reason_codes: tuple[str, ...]
    redacted_summary: str
    created_at: datetime
    review_item_fingerprint: str
    operator_review_required: bool = True
    pilot_is_not_production_learning: bool = True
    engagement_is_non_factual: bool = True
    approval_is_not_factual_proof: bool = True
    public_research_result_is_not_automatic_truth: bool = True
    verified_candidate_is_not_durable_production_knowledge: bool = True
    temporary_persistence_is_not_production_memory: bool = True
    shadow_application_is_not_production_policy: bool = True
    cross_cycle_context_is_temporary: bool = True
    automatic_cycle_continuation_authorized: bool = False
    automatic_approval_authorized: bool = False
    automatic_promotion_authorized: bool = False
    production_memory_write_authorized: bool = False
    production_policy_mutation_authorized: bool = False
    cognitive_memory_write_authorized: bool = False
    belief_mutation_authorized: bool = False
    model_training_authorized: bool = False
    source_rewrite_authorized: bool = False
    runtime_effect: bool = False

    @model_validator(mode="after")
    def _validate_review_item(self) -> Self:
        ensure_utc(self.created_at)
        required_true = (
            self.operator_review_required,
            self.pilot_is_not_production_learning,
            self.engagement_is_non_factual,
            self.approval_is_not_factual_proof,
            self.public_research_result_is_not_automatic_truth,
            self.verified_candidate_is_not_durable_production_knowledge,
            self.temporary_persistence_is_not_production_memory,
            self.shadow_application_is_not_production_policy,
            self.cross_cycle_context_is_temporary,
        )
        required_false = (
            self.automatic_cycle_continuation_authorized,
            self.automatic_approval_authorized,
            self.automatic_promotion_authorized,
            self.production_memory_write_authorized,
            self.production_policy_mutation_authorized,
            self.cognitive_memory_write_authorized,
            self.belief_mutation_authorized,
            self.model_training_authorized,
            self.source_rewrite_authorized,
            self.runtime_effect,
        )
        if not all(required_true) or any(required_false):
            raise ValueError("operator review item violates pilot boundary")
        return self


class ContinualLearningEvidenceBundle(FingerprintedModel):
    """Redacted committed evidence bundle."""

    fingerprint_field: ClassVar[str] = "evidence_bundle_fingerprint"

    schema_version: Literal["aion-glm-continual-learning-evidence/v1"]
    evidence_bundle_id: str
    session_id: str
    authorization_transaction_id: Literal["AION-227-GLM-0004"]
    session_result_fingerprint: str
    integrity_report_fingerprint: str
    operator_review_item_fingerprints: tuple[str, ...]
    diagnostics: tuple[ContinualLearningDiagnostics, ...] = ()
    incidents: tuple[ContinualLearningIncident, ...] = ()
    created_at: datetime
    evidence_bundle_fingerprint: str
    redacted: bool = True
    source_bodies_retained: int = 0
    approval_payloads_retained: int = 0
    temporary_paths_retained: int = 0
    runtime_effect: bool = False

    @field_validator("session_result_fingerprint", "integrity_report_fingerprint")
    @classmethod
    def _fingerprint(cls, value: str) -> str:
        return validate_hex64(value)

    @field_validator("operator_review_item_fingerprints")
    @classmethod
    def _fingerprint_tuple(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(validate_hex64(item) for item in value)

    @model_validator(mode="after")
    def _validate_evidence(self) -> Self:
        ensure_utc(self.created_at)
        if any(
            (
                not self.redacted,
                self.source_bodies_retained,
                self.approval_payloads_retained,
                self.temporary_paths_retained,
                self.runtime_effect,
            )
        ):
            raise ValueError("evidence bundle must be redacted and effect-free")
        return self


__all__ = [
    "APPROVAL_RECORD_ID",
    "AUTHORIZATION_SCOPE",
    "AUTHORIZATION_TRANSACTION_ID",
    "CONTINUAL_LEARNING_AUTHORIZATION_SCHEMA_VERSION",
    "CONTINUAL_LEARNING_CHECKPOINT_SCHEMA_VERSION",
    "CONTINUAL_LEARNING_CONTRACT_SCHEMA_VERSION",
    "CONTINUAL_LEARNING_CROSS_CYCLE_CONTEXT_SCHEMA_VERSION",
    "CONTINUAL_LEARNING_CYCLE_OUTCOME_SCHEMA_VERSION",
    "CONTINUAL_LEARNING_CYCLE_PLAN_SCHEMA_VERSION",
    "CONTINUAL_LEARNING_ENGAGEMENT_INTAKE_SCHEMA_VERSION",
    "CONTINUAL_LEARNING_EVIDENCE_SCHEMA_VERSION",
    "CONTINUAL_LEARNING_INTEGRITY_SCHEMA_VERSION",
    "CONTINUAL_LEARNING_KNOWLEDGE_BINDING_SCHEMA_VERSION",
    "CONTINUAL_LEARNING_PERSISTENCE_BINDING_SCHEMA_VERSION",
    "CONTINUAL_LEARNING_PROMOTION_BINDING_SCHEMA_VERSION",
    "CONTINUAL_LEARNING_QUERY_RESULT_SCHEMA_VERSION",
    "CONTINUAL_LEARNING_QUERY_SCHEMA_VERSION",
    "CONTINUAL_LEARNING_REASON_REGISTRY_VERSION",
    "CONTINUAL_LEARNING_RESEARCH_BINDING_SCHEMA_VERSION",
    "CONTINUAL_LEARNING_ROLLBACK_SCHEMA_VERSION",
    "CONTINUAL_LEARNING_SESSION_PLAN_SCHEMA_VERSION",
    "CONTINUAL_LEARNING_SESSION_RESULT_SCHEMA_VERSION",
    "CONTINUAL_LEARNING_SHADOW_BINDING_SCHEMA_VERSION",
    "CONTINUAL_LEARNING_STAGE_COMMAND_SCHEMA_VERSION",
    "CONTINUAL_LEARNING_STAGE_RECEIPT_SCHEMA_VERSION",
    "FORMAL_CLOSEOUT_TASK",
    "IMPLEMENTATION_TASK",
    "LIVE_CONFIRMATION_TEXT",
    "ORDINARY_TRANSITIONS",
    "PROGRAM_ID",
    "RESOURCE_LIMITS",
    "TERMINAL_STATES",
    "ZERO_HASH",
    "ContinualLearningBudgetDecision",
    "ContinualLearningCheckpoint",
    "ContinualLearningComponentInvocationBinding",
    "ContinualLearningCrossCycleContext",
    "ContinualLearningCycleKind",
    "ContinualLearningCycleOutcome",
    "ContinualLearningCycleOutcomeStatus",
    "ContinualLearningCyclePlan",
    "ContinualLearningCycleState",
    "ContinualLearningDiagnostics",
    "ContinualLearningEngagementIntake",
    "ContinualLearningError",
    "ContinualLearningEvidenceBundle",
    "ContinualLearningIncident",
    "ContinualLearningIntegrityFinding",
    "ContinualLearningIntegrityReport",
    "ContinualLearningKnowledgeCandidateBinding",
    "ContinualLearningKnowledgeStatus",
    "ContinualLearningOperatorReviewItem",
    "ContinualLearningPersistenceBinding",
    "ContinualLearningPersistenceStatus",
    "ContinualLearningPilotAuthorizationEnvelope",
    "ContinualLearningPilotMode",
    "ContinualLearningPromotionBinding",
    "ContinualLearningPromotionStatus",
    "ContinualLearningQuery",
    "ContinualLearningQueryResult",
    "ContinualLearningResearchBinding",
    "ContinualLearningResearchPlan",
    "ContinualLearningResearchSourceBinding",
    "ContinualLearningResearchStatus",
    "ContinualLearningResourceBudget",
    "ContinualLearningResourceUsage",
    "ContinualLearningRollbackPlan",
    "ContinualLearningSessionPlan",
    "ContinualLearningSessionResult",
    "ContinualLearningSessionStatus",
    "ContinualLearningShadowBinding",
    "ContinualLearningShadowStatus",
    "ContinualLearningStageCommand",
    "ContinualLearningStageDisposition",
    "ContinualLearningStageReceipt",
    "assert_allowed_transition",
    "build_record",
    "continual_fingerprint",
    "domain_allowlist_fingerprint",
    "ensure_utc",
    "evaluate_resource_budget",
    "fingerprint_file_path",
    "quantize_decimal",
    "safe_identifier",
    "sha256_bytes",
    "stable_json",
    "utc_now",
    "validate_domain",
    "validate_hex64",
]
