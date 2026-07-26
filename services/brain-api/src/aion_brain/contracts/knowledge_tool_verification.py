"""Deterministic simulation-only tool verification contracts."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.knowledge_research import (
    ensure_utc,
    fingerprint_payload,
    reject_protected_material,
    stable_json,
    validate_hex64,
    validate_safe_identifier,
)

TOOL_VERIFICATION_CONTRACT_SCHEMA_VERSION: Literal["aion-knowledge-tool-verification/v1"] = (
    "aion-knowledge-tool-verification/v1"
)
TOOL_MANIFEST_SCHEMA_VERSION: Literal["aion-knowledge-tool-manifest/v1"] = (
    "aion-knowledge-tool-manifest/v1"
)
TOOL_SCHEMA_DESCRIPTOR_VERSION: Literal["aion-knowledge-tool-schema-descriptor/v1"] = (
    "aion-knowledge-tool-schema-descriptor/v1"
)
TOOL_PERMISSION_SCHEMA_VERSION: Literal["aion-knowledge-tool-permission-envelope/v1"] = (
    "aion-knowledge-tool-permission-envelope/v1"
)
TOOL_EFFECT_SCHEMA_VERSION: Literal["aion-knowledge-tool-effect/v1"] = (
    "aion-knowledge-tool-effect/v1"
)
TOOL_REGISTRY_SCHEMA_VERSION: Literal["aion-knowledge-tool-registry/v1"] = (
    "aion-knowledge-tool-registry/v1"
)
TOOL_INTENT_SCHEMA_VERSION: Literal["aion-knowledge-tool-intent/v1"] = (
    "aion-knowledge-tool-intent/v1"
)
TOOL_CANDIDATE_SCHEMA_VERSION: Literal["aion-knowledge-tool-candidate/v1"] = (
    "aion-knowledge-tool-candidate/v1"
)
TOOL_PLAN_SCHEMA_VERSION: Literal["aion-knowledge-tool-plan/v1"] = "aion-knowledge-tool-plan/v1"
TOOL_PLAN_STEP_SCHEMA_VERSION: Literal["aion-knowledge-tool-plan-step/v1"] = (
    "aion-knowledge-tool-plan-step/v1"
)
TOOL_SIMULATION_SCHEMA_VERSION: Literal["aion-knowledge-tool-simulation/v1"] = (
    "aion-knowledge-tool-simulation/v1"
)
TOOL_SIMULATION_ARTIFACT_SCHEMA_VERSION: Literal["aion-knowledge-tool-simulation-artifact/v1"] = (
    "aion-knowledge-tool-simulation-artifact/v1"
)
TOOL_VERIFIER_PROFILE_SCHEMA_VERSION: Literal["aion-knowledge-tool-verifier-profile/v1"] = (
    "aion-knowledge-tool-verifier-profile/v1"
)
TOOL_VERIFICATION_RULE_SCHEMA_VERSION: Literal["aion-knowledge-tool-verification-rule/v1"] = (
    "aion-knowledge-tool-verification-rule/v1"
)
TOOL_FINDING_SCHEMA_VERSION: Literal["aion-knowledge-tool-verification-finding/v1"] = (
    "aion-knowledge-tool-verification-finding/v1"
)
TOOL_ATTESTATION_SCHEMA_VERSION: Literal["aion-knowledge-tool-attestation/v1"] = (
    "aion-knowledge-tool-attestation/v1"
)
TOOL_RESOURCE_SCHEMA_VERSION: Literal["aion-knowledge-tool-resource-budget/v1"] = (
    "aion-knowledge-tool-resource-budget/v1"
)
TOOL_FIXTURE_SCHEMA_VERSION: Literal["aion-knowledge-tool-verification-fixture/v1"] = (
    "aion-knowledge-tool-verification-fixture/v1"
)
TOOL_INTEGRITY_SCHEMA_VERSION: Literal["aion-knowledge-tool-verification-integrity/v1"] = (
    "aion-knowledge-tool-verification-integrity/v1"
)
TOOL_DIAGNOSTICS_SCHEMA_VERSION: Literal["aion-knowledge-tool-verification-diagnostics/v1"] = (
    "aion-knowledge-tool-verification-diagnostics/v1"
)
TOOL_INCIDENT_SCHEMA_VERSION: Literal["aion-knowledge-tool-verification-incident/v1"] = (
    "aion-knowledge-tool-verification-incident/v1"
)
TOOL_OPERATOR_REVIEW_SCHEMA_VERSION: Literal[
    "aion-knowledge-tool-verification-operator-review/v1"
] = "aion-knowledge-tool-verification-operator-review/v1"
TOOL_EVIDENCE_SCHEMA_VERSION: Literal["aion-knowledge-tool-verification-evidence/v1"] = (
    "aion-knowledge-tool-verification-evidence/v1"
)
TOOL_SESSION_SCHEMA_VERSION: Literal["aion-knowledge-tool-verification-session/v1"] = (
    "aion-knowledge-tool-verification-session/v1"
)
TOOL_QUERY_SCHEMA_VERSION: Literal["aion-knowledge-tool-verification-query/v1"] = (
    "aion-knowledge-tool-verification-query/v1"
)

PROGRAM_ID: Literal["AION-KNOWLEDGE-INTELLIGENCE-001"] = "AION-KNOWLEDGE-INTELLIGENCE-001"
PARENT_PROGRAM_ID: Literal["AION-COGNITIVE-ARCHITECTURE-001"] = "AION-COGNITIVE-ARCHITECTURE-001"
AUTHORIZATION_TRANSACTION_ID: Literal["AION-214-KI-0006"] = "AION-214-KI-0006"
APPROVAL_RECORD_ID: Literal["AION-214-KI-0006"] = "AION-214-KI-0006"
IMPLEMENTATION_TASK: Literal["AION-215"] = "AION-215"
FORMAL_CLOSEOUT_TASK: Literal["AION-216"] = "AION-216"
AUTHORIZATION_SCOPE: Literal[
    "deterministic-tool-manifest-intent-plan-simulation-verification-"
    "attestation-effect-evidence-rollback-abstention-core"
] = (
    "deterministic-tool-manifest-intent-plan-simulation-verification-"
    "attestation-effect-evidence-rollback-abstention-core"
)
TOOL_VERIFICATION_FABRIC_STATE: Literal[
    "implemented_deterministic_simulation_verification_attestation_persistent_write_disabled"
] = "implemented_deterministic_simulation_verification_attestation_persistent_write_disabled"

MAXIMUM_TOOL_MANIFESTS: Literal[500] = 500
MAXIMUM_TOOL_CANDIDATES_PER_PLAN: Literal[100] = 100
MAXIMUM_TOOL_STEPS_PER_PLAN: Literal[50] = 50
MAXIMUM_MANIFEST_BYTES: Literal[131072] = 131_072
MAXIMUM_INPUT_SCHEMA_BYTES: Literal[65536] = 65_536
MAXIMUM_OUTPUT_SCHEMA_BYTES: Literal[65536] = 65_536
MAXIMUM_PLAN_BYTES: Literal[1048576] = 1_048_576
MAXIMUM_PRECONDITIONS_PER_STEP: Literal[50] = 50
MAXIMUM_POSTCONDITIONS_PER_STEP: Literal[50] = 50
MAXIMUM_EXPECTED_EFFECTS_PER_STEP: Literal[50] = 50
MAXIMUM_FORBIDDEN_EFFECTS_PER_STEP: Literal[50] = 50
MAXIMUM_VERIFICATION_RULES_PER_STEP: Literal[100] = 100
MAXIMUM_VERIFIERS_PER_STEP: Literal[8] = 8
MAXIMUM_OUTPUT_ARTIFACTS_PER_STEP: Literal[100] = 100
MAXIMUM_EVIDENCE_REFERENCES_PER_STEP: Literal[100] = 100
MAXIMUM_ATTESTATIONS_PER_SESSION: Literal[500] = 500
MAXIMUM_ROLLBACK_STEPS_PER_PLAN: Literal[50] = 50
MAXIMUM_COMPENSATION_STEPS_PER_PLAN: Literal[50] = 50
MAXIMUM_SIMULATED_SESSIONS: Literal[100] = 100
MAXIMUM_QUERY_RESULTS: Literal[1000] = 1000
MAXIMUM_FIXTURE_RECORDS: Literal[5000] = 5000
MAXIMUM_FIXTURE_BYTES: Literal[4194304] = 4_194_304
MAXIMUM_CONCURRENT_PLANS: Literal[4] = 4
MAXIMUM_CONCURRENT_VERIFIERS: Literal[8] = 8
MAXIMUM_PERSISTENT_TOOL_STATE_WRITE_BATCH: Literal[0] = 0
MAXIMUM_ACTUAL_TOOL_EXECUTIONS: Literal[0] = 0
MAXIMUM_SHELL_COMMANDS: Literal[0] = 0
MAXIMUM_SUBPROCESS_EXECUTIONS: Literal[0] = 0
MAXIMUM_NETWORK_CALLS: Literal[0] = 0
MAXIMUM_DNS_RESOLUTIONS: Literal[0] = 0
MAXIMUM_BROWSER_ACTIONS: Literal[0] = 0
MAXIMUM_CONNECTOR_CALLS: Literal[0] = 0
MAXIMUM_SEARCH_PROVIDER_CALLS: Literal[0] = 0
MAXIMUM_MODEL_PROVIDER_CALLS: Literal[0] = 0
MAXIMUM_FILESYSTEM_MUTATIONS: Literal[0] = 0
MAXIMUM_SOURCE_MUTATIONS: Literal[0] = 0
MAXIMUM_GIT_OPERATIONS: Literal[0] = 0
MAXIMUM_RUNTIME_CREATED_PULL_REQUESTS: Literal[0] = 0
MAXIMUM_APPROVALS_CREATED: Literal[0] = 0
MAXIMUM_AUTONOMOUS_ACTIONS: Literal[0] = 0
MAXIMUM_HIGH_STAKES_ACTIONS: Literal[0] = 0
MAXIMUM_DEPLOYMENTS: Literal[0] = 0
MAXIMUM_KNOWLEDGE_PROMOTIONS: Literal[0] = 0
MAXIMUM_BELIEF_MUTATIONS: Literal[0] = 0
MAXIMUM_MODEL_WEIGHT_CHANGES: Literal[0] = 0

MODEL_CONFIG = ConfigDict(extra="forbid", hide_input_in_errors=True)
FROZEN_MODEL_CONFIG = ConfigDict(extra="forbid", hide_input_in_errors=True, frozen=True)


class ToolVerificationError(ValueError):
    """Raised when a deterministic tool verification contract is violated."""


class ToolOperationClass(StrEnum):
    PURE_COMPUTE = "pure_compute"
    DETERMINISTIC_PARSER = "deterministic_parser"
    DETERMINISTIC_VALIDATOR = "deterministic_validator"
    LOCAL_FIXTURE_READ = "local_fixture_read"
    FILESYSTEM_READ = "filesystem_read"
    EXTERNAL_READ = "external_read"
    EXTERNAL_WRITE = "external_write"
    SYSTEM_COMMAND = "system_command"
    BROWSER = "browser"
    CONNECTOR = "connector"
    MODEL_PROVIDER = "model_provider"
    SOURCE_WRITE = "source_write"
    GIT_WRITE = "git_write"
    DEPLOYMENT = "deployment"
    PRIVILEGED = "privileged"


class ToolRiskClass(StrEnum):
    MINIMAL = "minimal"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class ToolEffectType(StrEnum):
    READ = "read"
    COMPUTE = "compute"
    PARSE = "parse"
    VALIDATE = "validate"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    TRANSMIT = "transmit"
    EXECUTE = "execute"
    APPROVE = "approve"
    MERGE = "merge"
    DEPLOY = "deploy"
    TRAIN = "train"


class ToolVerificationStatus(StrEnum):
    PLANNED = "planned"
    SIMULATION_PASSED = "simulation_passed"
    SIMULATION_FAILED = "simulation_failed"
    VERIFICATION_PASSED = "verification_passed"
    VERIFICATION_FAILED = "verification_failed"
    INCONCLUSIVE = "inconclusive"
    BLOCKED = "blocked"
    ABSTAINED = "abstained"


class VerifierRole(StrEnum):
    SCHEMA = "schema_verifier"
    POLICY = "policy_verifier"
    EFFECT = "effect_verifier"
    PROVENANCE = "provenance_verifier"
    DETERMINISM = "determinism_verifier"
    SAFETY = "safety_verifier"
    ROLLBACK = "rollback_verifier"
    RESOURCE = "resource_verifier"


class ToolFindingSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ToolIntegrityStatus(StrEnum):
    PASS_ = "pass"
    FAIL = "fail"
    ABSTAIN = "abstain"


class ToolSessionOutcome(StrEnum):
    SIMULATION_PASSED = "simulation_passed"
    SIMULATION_FAILED = "simulation_failed"
    VERIFICATION_FAILED = "verification_failed"
    ABSTAINED = "abstained"
    PERSISTENT_WRITE_DISABLED = "persistent_write_disabled"


TOOL_REASON_CODES: tuple[str, ...] = (
    "tool_manifest_valid",
    "tool_manifest_invalid",
    "tool_registry_valid",
    "tool_registry_invalid",
    "tool_intent_valid",
    "tool_intent_invalid",
    "tool_candidate_eligible",
    "tool_candidate_rejected",
    "tool_candidate_selected",
    "tool_plan_valid",
    "tool_plan_invalid",
    "tool_schema_valid",
    "tool_schema_invalid",
    "tool_permission_valid",
    "tool_permission_invalid",
    "tool_precondition_valid",
    "tool_precondition_invalid",
    "tool_postcondition_valid",
    "tool_postcondition_invalid",
    "tool_effect_expected_matched",
    "tool_effect_forbidden_absent",
    "tool_effect_forbidden_detected",
    "tool_idempotency_valid",
    "tool_rollback_valid",
    "tool_rollback_invalid",
    "tool_compensation_valid",
    "tool_compensation_invalid",
    "tool_synthetic_simulation_passed",
    "tool_synthetic_simulation_failed",
    "tool_fixture_replayed",
    "tool_fixture_rejected",
    "tool_output_canonicalized",
    "tool_artifact_fingerprinted",
    "tool_verifier_independent",
    "tool_verifier_independence_missing",
    "tool_high_risk_safety_verified",
    "tool_high_risk_rollback_verified",
    "tool_high_risk_resource_verified",
    "tool_attestation_chained",
    "tool_attestation_invalid",
    "tool_provenance_preserved",
    "tool_abstention_explicit",
    "tool_runtime_disabled",
    "tool_actual_execution_blocked",
    "tool_persistent_state_write_blocked",
    "tool_operator_review_required",
    "tool_integrity_passed",
    "tool_integrity_failed",
)

_RISK_ORDER: dict[ToolRiskClass, int] = {
    ToolRiskClass.MINIMAL: 0,
    ToolRiskClass.LOW: 1,
    ToolRiskClass.MODERATE: 2,
    ToolRiskClass.HIGH: 3,
    ToolRiskClass.CRITICAL: 4,
}

_EXTERNAL_EFFECTS: frozenset[ToolEffectType] = frozenset(
    {
        ToolEffectType.CREATE,
        ToolEffectType.UPDATE,
        ToolEffectType.DELETE,
        ToolEffectType.TRANSMIT,
        ToolEffectType.EXECUTE,
        ToolEffectType.APPROVE,
        ToolEffectType.MERGE,
        ToolEffectType.DEPLOY,
        ToolEffectType.TRAIN,
    }
)

_RUNTIME_OPERATION_CLASSES: frozenset[ToolOperationClass] = frozenset(
    {
        ToolOperationClass.EXTERNAL_WRITE,
        ToolOperationClass.SYSTEM_COMMAND,
        ToolOperationClass.BROWSER,
        ToolOperationClass.CONNECTOR,
        ToolOperationClass.MODEL_PROVIDER,
        ToolOperationClass.SOURCE_WRITE,
        ToolOperationClass.GIT_WRITE,
        ToolOperationClass.DEPLOYMENT,
        ToolOperationClass.PRIVILEGED,
    }
)


def _jsonable(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, datetime):
        text = value.isoformat()
        return text[:-6] + "Z" if text.endswith("+00:00") else text
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_jsonable(item) for item in value]
    return value


def _without_fingerprint(value: BaseModel | dict[str, Any], field_name: str) -> dict[str, Any]:
    payload = _jsonable(value)
    if not isinstance(payload, dict):
        raise ToolVerificationError("fingerprint payload must be an object")
    payload.pop(field_name, None)
    return payload


def tool_verification_fingerprint(value: BaseModel | dict[str, Any], field_name: str) -> str:
    """Return a deterministic fingerprint excluding the requested fingerprint field."""

    payload = _without_fingerprint(value, field_name)
    return fingerprint_payload(
        {
            "kind": TOOL_VERIFICATION_CONTRACT_SCHEMA_VERSION,
            "payload": payload,
        }
    )


def validate_tool_reason_codes(values: tuple[str, ...]) -> tuple[str, ...]:
    """Validate ordered unique tool verification reason codes."""

    seen: set[str] = set()
    for code in values:
        if code not in TOOL_REASON_CODES:
            raise ValueError("unknown tool verification reason code")
        if code in seen:
            raise ValueError("duplicate tool verification reason code")
        validate_safe_identifier(code, "tool verification reason code")
        seen.add(code)
    return values


def validate_tool_identifier(value: str, field_name: str = "tool identifier") -> str:
    return validate_safe_identifier(value, field_name)


def risk_lte(left: ToolRiskClass, right: ToolRiskClass) -> bool:
    return _RISK_ORDER[left] <= _RISK_ORDER[right]


def risk_requires_extra_verification(risk_class: ToolRiskClass) -> bool:
    return risk_class in {ToolRiskClass.HIGH, ToolRiskClass.CRITICAL}


def forbidden_runtime_effects() -> frozenset[ToolEffectType]:
    return _EXTERNAL_EFFECTS


def runtime_operation_classes() -> frozenset[ToolOperationClass]:
    return _RUNTIME_OPERATION_CLASSES


class ToolSchemaDescriptor(BaseModel):
    """Strict descriptor for a synthetic tool input or output schema."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-tool-schema-descriptor/v1"] = (
        TOOL_SCHEMA_DESCRIPTOR_VERSION
    )
    schema_id: str = Field(min_length=1, max_length=128)
    required_fields: tuple[str, ...] = Field(default_factory=tuple, max_length=100)
    optional_fields: tuple[str, ...] = Field(default_factory=tuple, max_length=100)
    forbidden_fields: tuple[str, ...] = Field(default_factory=tuple, max_length=100)
    field_types: dict[str, str] = Field(default_factory=dict)
    strict: Literal[True] = True
    schema_fingerprint: str

    @field_validator("schema_id")
    @classmethod
    def schema_id_is_safe(cls, value: str) -> str:
        return validate_tool_identifier(value, "schema_id")

    @field_validator("required_fields", "optional_fields", "forbidden_fields")
    @classmethod
    def fields_are_safe(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        seen: set[str] = set()
        for value in values:
            validate_tool_identifier(value, "schema field")
            if value in seen:
                raise ValueError("duplicate schema field")
            seen.add(value)
        return values

    @field_validator("field_types")
    @classmethod
    def field_types_are_safe(cls, values: dict[str, str]) -> dict[str, str]:
        for key, value in values.items():
            validate_tool_identifier(key, "schema type field")
            validate_tool_identifier(value, "schema type")
        return values

    @field_validator("schema_fingerprint")
    @classmethod
    def schema_fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "tool schema fingerprint")

    @model_validator(mode="after")
    def schema_is_valid(self) -> Self:
        required = set(self.required_fields)
        optional = set(self.optional_fields)
        forbidden = set(self.forbidden_fields)
        if required & optional or required & forbidden or optional & forbidden:
            raise ValueError("schema field groups must be disjoint")
        if set(self.field_types) - (required | optional):
            raise ValueError("schema field type declared for unknown field")
        if len(stable_json(self.model_dump(mode="json"))) > MAXIMUM_INPUT_SCHEMA_BYTES:
            raise ValueError("tool schema descriptor byte limit exceeded")
        if self.schema_fingerprint != tool_verification_fingerprint(self, "schema_fingerprint"):
            raise ValueError("tool schema fingerprint mismatch")
        return self


class ToolPermissionEnvelope(BaseModel):
    """Declared permissions for a manifest with prohibited runtime channels disabled."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-tool-permission-envelope/v1"] = (
        TOOL_PERMISSION_SCHEMA_VERSION
    )
    permission_ids: tuple[str, ...] = Field(default_factory=tuple, max_length=50)
    requires_local_fixture_read: bool = False
    requires_filesystem_read: bool = False
    requires_network: Literal[False] = False
    requires_dns: Literal[False] = False
    requires_shell: Literal[False] = False
    requires_subprocess: Literal[False] = False
    requires_browser: Literal[False] = False
    requires_connector: Literal[False] = False
    requires_model_provider: Literal[False] = False
    requires_filesystem_write: Literal[False] = False
    requires_source_write: Literal[False] = False
    requires_git_write: Literal[False] = False
    requires_deployment: Literal[False] = False
    requires_approval_creation: Literal[False] = False
    requires_persistence: Literal[False] = False
    permission_fingerprint: str

    @field_validator("permission_ids")
    @classmethod
    def permission_ids_are_safe(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        seen: set[str] = set()
        for value in values:
            validate_tool_identifier(value, "permission_id")
            if value in seen:
                raise ValueError("duplicate permission_id")
            seen.add(value)
        return values

    @field_validator("permission_fingerprint")
    @classmethod
    def permission_fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "tool permission fingerprint")

    @model_validator(mode="after")
    def envelope_is_valid(self) -> Self:
        if self.requires_filesystem_read and not self.requires_local_fixture_read:
            raise ValueError("only explicit local fixture read is allowed")
        if self.permission_fingerprint != tool_verification_fingerprint(
            self, "permission_fingerprint"
        ):
            raise ValueError("tool permission fingerprint mismatch")
        return self


class ToolExpectedEffect(BaseModel):
    """Expected synthetic effect from a tool plan step."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-tool-effect/v1"] = TOOL_EFFECT_SCHEMA_VERSION
    effect_id: str = Field(min_length=1, max_length=128)
    effect_type: ToolEffectType
    effect_scope: str = Field(min_length=1, max_length=128)
    artifact_id: str | None = None
    requires_actual_execution: Literal[False] = False
    requires_persistent_write: Literal[False] = False
    synthetic: Literal[True] = True
    runtime_effect: Literal[False] = False
    effect_fingerprint: str

    @field_validator("effect_id", "effect_scope", "artifact_id")
    @classmethod
    def effect_fields_are_safe(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return validate_tool_identifier(value, "tool effect field")

    @field_validator("effect_fingerprint")
    @classmethod
    def effect_fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "tool effect fingerprint")

    @model_validator(mode="after")
    def effect_is_valid(self) -> Self:
        if self.effect_type in _EXTERNAL_EFFECTS:
            raise ValueError("runtime effect cannot be expected in AION-215")
        if self.effect_fingerprint != tool_verification_fingerprint(self, "effect_fingerprint"):
            raise ValueError("tool effect fingerprint mismatch")
        return self


class ToolForbiddenEffect(BaseModel):
    """Forbidden effect that must remain absent during simulation."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-tool-effect/v1"] = TOOL_EFFECT_SCHEMA_VERSION
    effect_id: str = Field(min_length=1, max_length=128)
    effect_type: ToolEffectType
    effect_scope: str = Field(min_length=1, max_length=128)
    reason_code: str
    effect_fingerprint: str

    @field_validator("effect_id", "effect_scope")
    @classmethod
    def effect_fields_are_safe(cls, value: str) -> str:
        return validate_tool_identifier(value, "tool forbidden effect field")

    @field_validator("reason_code")
    @classmethod
    def reason_code_is_safe(cls, value: str) -> str:
        return validate_tool_reason_codes((value,))[0]

    @field_validator("effect_fingerprint")
    @classmethod
    def effect_fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "tool forbidden effect fingerprint")

    @model_validator(mode="after")
    def forbidden_effect_is_valid(self) -> Self:
        if self.effect_fingerprint != tool_verification_fingerprint(self, "effect_fingerprint"):
            raise ValueError("tool forbidden effect fingerprint mismatch")
        return self


class ToolCapabilityManifest(BaseModel):
    """Immutable capability declaration for a synthetic simulation-only tool."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-tool-manifest/v1"] = TOOL_MANIFEST_SCHEMA_VERSION
    program_id: Literal["AION-KNOWLEDGE-INTELLIGENCE-001"] = PROGRAM_ID
    authorization_transaction_id: Literal["AION-214-KI-0006"] = AUTHORIZATION_TRANSACTION_ID
    implementation_task: Literal["AION-215"] = IMPLEMENTATION_TASK
    formal_closeout_task: Literal["AION-216"] = FORMAL_CLOSEOUT_TASK
    authorization_scope: Literal[
        "deterministic-tool-manifest-intent-plan-simulation-verification-"
        "attestation-effect-evidence-rollback-abstention-core"
    ] = AUTHORIZATION_SCOPE
    manifest_id: str = Field(min_length=1, max_length=128)
    tool_id: str = Field(min_length=1, max_length=128)
    tool_version: str = Field(min_length=1, max_length=32)
    operation_class: ToolOperationClass
    risk_class: ToolRiskClass
    input_schema: ToolSchemaDescriptor
    output_schema: ToolSchemaDescriptor
    permission_envelope: ToolPermissionEnvelope
    declared_effects: tuple[ToolExpectedEffect, ...] = Field(
        default_factory=tuple,
        max_length=MAXIMUM_EXPECTED_EFFECTS_PER_STEP,
    )
    prohibited_effects: tuple[ToolForbiddenEffect, ...] = Field(
        default_factory=tuple,
        max_length=MAXIMUM_FORBIDDEN_EFFECTS_PER_STEP,
    )
    deterministic_simulation_supported: Literal[True] = True
    idempotency_supported: Literal[True] = True
    rollback_supported: Literal[True] = True
    compensation_supported: Literal[True] = True
    synthetic: Literal[True] = True
    read_only: Literal[True] = True
    redacted: Literal[True] = True
    actual_execution_enabled: Literal[False] = False
    actual_tool_executed: Literal[False] = False
    persistent_write_applied: Literal[False] = False
    runtime_effect: Literal[False] = False
    manifest_fingerprint: str

    @field_validator("manifest_id", "tool_id", "tool_version")
    @classmethod
    def manifest_fields_are_safe(cls, value: str) -> str:
        return validate_tool_identifier(value, "tool manifest field")

    @field_validator("manifest_fingerprint")
    @classmethod
    def manifest_fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "tool manifest fingerprint")

    @model_validator(mode="after")
    def manifest_is_valid(self) -> Self:
        declared = {item.effect_type for item in self.declared_effects}
        forbidden = {item.effect_type for item in self.prohibited_effects}
        if declared & forbidden:
            raise ValueError("declared and forbidden effects must not overlap")
        if self.operation_class in _RUNTIME_OPERATION_CLASSES:
            raise ValueError("runtime operation classes cannot be executable AION-215 manifests")
        if len(stable_json(self.model_dump(mode="json"))) > MAXIMUM_MANIFEST_BYTES:
            raise ValueError("tool manifest byte limit exceeded")
        if self.manifest_fingerprint != tool_verification_fingerprint(self, "manifest_fingerprint"):
            raise ValueError("tool manifest fingerprint mismatch")
        return self


class ToolManifestRegistrySnapshot(BaseModel):
    """Versioned immutable in-memory manifest and schema registry snapshot."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-tool-registry/v1"] = TOOL_REGISTRY_SCHEMA_VERSION
    registry_id: str = Field(min_length=1, max_length=128)
    registry_version: int = Field(ge=1)
    manifests: tuple[ToolCapabilityManifest, ...] = Field(max_length=MAXIMUM_TOOL_MANIFESTS)
    schemas: tuple[ToolSchemaDescriptor, ...] = Field(default_factory=tuple, max_length=1000)
    in_memory_only: Literal[True] = True
    persistent_write_applied: Literal[False] = False
    runtime_effect: Literal[False] = False
    registry_fingerprint: str

    @field_validator("registry_id")
    @classmethod
    def registry_id_is_safe(cls, value: str) -> str:
        return validate_tool_identifier(value, "registry_id")

    @field_validator("registry_fingerprint")
    @classmethod
    def registry_fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "tool registry fingerprint")

    @model_validator(mode="after")
    def registry_is_valid(self) -> Self:
        manifest_ids = [item.manifest_id for item in self.manifests]
        schema_ids = [item.schema_id for item in self.schemas]
        if len(manifest_ids) != len(set(manifest_ids)):
            raise ValueError("duplicate tool manifest id")
        if len(schema_ids) != len(set(schema_ids)):
            raise ValueError("duplicate tool schema id")
        if self.registry_fingerprint != tool_verification_fingerprint(self, "registry_fingerprint"):
            raise ValueError("tool registry fingerprint mismatch")
        return self


class ToolIntent(BaseModel):
    """Explicit tool intent bound to AION-213, AION-209, and AION-211 records."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-tool-intent/v1"] = TOOL_INTENT_SCHEMA_VERSION
    program_id: Literal["AION-KNOWLEDGE-INTELLIGENCE-001"] = PROGRAM_ID
    authorization_transaction_id: Literal["AION-214-KI-0006"] = AUTHORIZATION_TRANSACTION_ID
    implementation_task: Literal["AION-215"] = IMPLEMENTATION_TASK
    formal_closeout_task: Literal["AION-216"] = FORMAL_CLOSEOUT_TASK
    intent_id: str = Field(min_length=1, max_length=128)
    case_id: str = Field(min_length=1, max_length=128)
    claim_ids: tuple[str, ...] = Field(min_length=1, max_length=100)
    epistemic_assessment_ids: tuple[str, ...] = Field(min_length=1, max_length=100)
    mesh_synthesis_id: str = Field(min_length=1, max_length=128)
    requested_tool_ids: tuple[str, ...] = Field(default_factory=tuple, max_length=50)
    required_operation_classes: tuple[ToolOperationClass, ...] = Field(min_length=1, max_length=5)
    expected_effects: tuple[ToolExpectedEffect, ...] = Field(min_length=1, max_length=50)
    forbidden_effects: tuple[ToolForbiddenEffect, ...] = Field(min_length=1, max_length=50)
    max_risk_class: ToolRiskClass
    input_payload: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str = Field(min_length=1, max_length=128)
    operator_review_required: Literal[True] = True
    explicit_abstention_supported: Literal[True] = True
    synthetic: Literal[True] = True
    read_only: Literal[True] = True
    redacted: Literal[True] = True
    actual_tool_executed: Literal[False] = False
    persistent_write_applied: Literal[False] = False
    runtime_effect: Literal[False] = False
    intent_fingerprint: str

    @field_validator(
        "intent_id",
        "case_id",
        "mesh_synthesis_id",
        "idempotency_key",
    )
    @classmethod
    def intent_fields_are_safe(cls, value: str) -> str:
        return validate_tool_identifier(value, "tool intent field")

    @field_validator("claim_ids", "epistemic_assessment_ids", "requested_tool_ids")
    @classmethod
    def intent_refs_are_safe(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        seen: set[str] = set()
        for value in values:
            validate_tool_identifier(value, "tool intent reference")
            if value in seen:
                raise ValueError("duplicate tool intent reference")
            seen.add(value)
        return values

    @field_validator("input_payload")
    @classmethod
    def input_payload_is_redacted(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_protected_material(value, "tool intent input payload")
        return value

    @field_validator("intent_fingerprint")
    @classmethod
    def intent_fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "tool intent fingerprint")

    @model_validator(mode="after")
    def intent_is_valid(self) -> Self:
        if len(stable_json(self.input_payload)) > MAXIMUM_INPUT_SCHEMA_BYTES:
            raise ValueError("tool intent input payload byte limit exceeded")
        if self.intent_fingerprint != tool_verification_fingerprint(self, "intent_fingerprint"):
            raise ValueError("tool intent fingerprint mismatch")
        return self


class ToolCandidate(BaseModel):
    """Deterministically enumerated manifest candidate for an intent."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-tool-candidate/v1"] = TOOL_CANDIDATE_SCHEMA_VERSION
    candidate_id: str = Field(min_length=1, max_length=128)
    intent_id: str = Field(min_length=1, max_length=128)
    manifest_id: str = Field(min_length=1, max_length=128)
    tool_id: str = Field(min_length=1, max_length=128)
    risk_class: ToolRiskClass
    eligible: bool
    candidate_rank: int = Field(ge=1)
    matched_effect_types: tuple[ToolEffectType, ...] = Field(default_factory=tuple, max_length=50)
    reason_codes: tuple[str, ...] = Field(default_factory=tuple, max_length=20)
    candidate_fingerprint: str

    @field_validator("candidate_id", "intent_id", "manifest_id", "tool_id")
    @classmethod
    def candidate_fields_are_safe(cls, value: str) -> str:
        return validate_tool_identifier(value, "tool candidate field")

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_are_safe(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return validate_tool_reason_codes(values)

    @field_validator("candidate_fingerprint")
    @classmethod
    def candidate_fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "tool candidate fingerprint")

    @model_validator(mode="after")
    def candidate_is_valid(self) -> Self:
        if self.candidate_fingerprint != tool_verification_fingerprint(
            self, "candidate_fingerprint"
        ):
            raise ValueError("tool candidate fingerprint mismatch")
        return self


class ToolPrecondition(BaseModel):
    """Precondition checked before synthetic simulation."""

    model_config = FROZEN_MODEL_CONFIG

    condition_id: str = Field(min_length=1, max_length=128)
    check_name: str = Field(min_length=1, max_length=128)
    satisfied: bool
    reason_codes: tuple[str, ...] = Field(min_length=1, max_length=10)
    condition_fingerprint: str

    @field_validator("condition_id", "check_name")
    @classmethod
    def condition_fields_are_safe(cls, value: str) -> str:
        return validate_tool_identifier(value, "tool precondition field")

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_are_safe(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return validate_tool_reason_codes(values)

    @field_validator("condition_fingerprint")
    @classmethod
    def condition_fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "tool precondition fingerprint")

    @model_validator(mode="after")
    def condition_is_valid(self) -> Self:
        if self.condition_fingerprint != tool_verification_fingerprint(
            self, "condition_fingerprint"
        ):
            raise ValueError("tool precondition fingerprint mismatch")
        return self


class ToolPostcondition(BaseModel):
    """Postcondition checked after synthetic simulation."""

    model_config = FROZEN_MODEL_CONFIG

    condition_id: str = Field(min_length=1, max_length=128)
    check_name: str = Field(min_length=1, max_length=128)
    satisfied: bool
    reason_codes: tuple[str, ...] = Field(min_length=1, max_length=10)
    condition_fingerprint: str

    @field_validator("condition_id", "check_name")
    @classmethod
    def condition_fields_are_safe(cls, value: str) -> str:
        return validate_tool_identifier(value, "tool postcondition field")

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_are_safe(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return validate_tool_reason_codes(values)

    @field_validator("condition_fingerprint")
    @classmethod
    def condition_fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "tool postcondition fingerprint")

    @model_validator(mode="after")
    def condition_is_valid(self) -> Self:
        if self.condition_fingerprint != tool_verification_fingerprint(
            self, "condition_fingerprint"
        ):
            raise ValueError("tool postcondition fingerprint mismatch")
        return self


class ToolRollbackPlan(BaseModel):
    """Synthetic rollback plan; validation never grants execution approval."""

    model_config = FROZEN_MODEL_CONFIG

    rollback_id: str = Field(min_length=1, max_length=128)
    step_ids: tuple[str, ...] = Field(
        default_factory=tuple, max_length=MAXIMUM_ROLLBACK_STEPS_PER_PLAN
    )
    available: bool
    validated: bool
    requires_actual_execution: Literal[False] = False
    requires_persistent_write: Literal[False] = False
    reason_codes: tuple[str, ...] = Field(min_length=1, max_length=20)
    rollback_fingerprint: str

    @field_validator("rollback_id")
    @classmethod
    def rollback_id_is_safe(cls, value: str) -> str:
        return validate_tool_identifier(value, "rollback_id")

    @field_validator("step_ids")
    @classmethod
    def step_ids_are_safe(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(validate_tool_identifier(value, "rollback step id") for value in values)

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_are_safe(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return validate_tool_reason_codes(values)

    @field_validator("rollback_fingerprint")
    @classmethod
    def rollback_fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "tool rollback fingerprint")

    @model_validator(mode="after")
    def rollback_is_valid(self) -> Self:
        if self.available is not self.validated:
            raise ValueError("rollback availability must match validation state")
        if self.rollback_fingerprint != tool_verification_fingerprint(self, "rollback_fingerprint"):
            raise ValueError("tool rollback fingerprint mismatch")
        return self


class ToolCompensationPlan(BaseModel):
    """Synthetic compensation plan; validation never applies a real effect."""

    model_config = FROZEN_MODEL_CONFIG

    compensation_id: str = Field(min_length=1, max_length=128)
    step_ids: tuple[str, ...] = Field(
        default_factory=tuple,
        max_length=MAXIMUM_COMPENSATION_STEPS_PER_PLAN,
    )
    available: bool
    validated: bool
    requires_actual_execution: Literal[False] = False
    requires_persistent_write: Literal[False] = False
    reason_codes: tuple[str, ...] = Field(min_length=1, max_length=20)
    compensation_fingerprint: str

    @field_validator("compensation_id")
    @classmethod
    def compensation_id_is_safe(cls, value: str) -> str:
        return validate_tool_identifier(value, "compensation_id")

    @field_validator("step_ids")
    @classmethod
    def step_ids_are_safe(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(validate_tool_identifier(value, "compensation step id") for value in values)

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_are_safe(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return validate_tool_reason_codes(values)

    @field_validator("compensation_fingerprint")
    @classmethod
    def compensation_fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "tool compensation fingerprint")

    @model_validator(mode="after")
    def compensation_is_valid(self) -> Self:
        if self.available is not self.validated:
            raise ValueError("compensation availability must match validation state")
        if self.compensation_fingerprint != tool_verification_fingerprint(
            self, "compensation_fingerprint"
        ):
            raise ValueError("tool compensation fingerprint mismatch")
        return self


class ToolPlanStep(BaseModel):
    """Bounded ordered synthetic tool-plan step."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-tool-plan-step/v1"] = TOOL_PLAN_STEP_SCHEMA_VERSION
    step_id: str = Field(min_length=1, max_length=128)
    step_order: int = Field(ge=1, le=MAXIMUM_TOOL_STEPS_PER_PLAN)
    intent_id: str = Field(min_length=1, max_length=128)
    manifest_id: str = Field(min_length=1, max_length=128)
    tool_id: str = Field(min_length=1, max_length=128)
    operation_class: ToolOperationClass
    risk_class: ToolRiskClass
    input_payload: dict[str, Any] = Field(default_factory=dict)
    expected_effects: tuple[ToolExpectedEffect, ...] = Field(min_length=1, max_length=50)
    forbidden_effects: tuple[ToolForbiddenEffect, ...] = Field(min_length=1, max_length=50)
    preconditions: tuple[ToolPrecondition, ...] = Field(min_length=1, max_length=50)
    postconditions: tuple[ToolPostcondition, ...] = Field(min_length=1, max_length=50)
    idempotency_key: str = Field(min_length=1, max_length=128)
    rollback_plan: ToolRollbackPlan
    compensation_plan: ToolCompensationPlan
    required_verifier_roles: tuple[VerifierRole, ...] = Field(min_length=4, max_length=8)
    simulation_only: Literal[True] = True
    actual_execution_enabled: Literal[False] = False
    actual_tool_executed: Literal[False] = False
    persistent_write_applied: Literal[False] = False
    runtime_effect: Literal[False] = False
    step_fingerprint: str

    @field_validator("step_id", "intent_id", "manifest_id", "tool_id", "idempotency_key")
    @classmethod
    def step_fields_are_safe(cls, value: str) -> str:
        return validate_tool_identifier(value, "tool plan step field")

    @field_validator("input_payload")
    @classmethod
    def input_payload_is_redacted(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_protected_material(value, "tool plan input")
        return value

    @field_validator("step_fingerprint")
    @classmethod
    def step_fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "tool plan step fingerprint")

    @model_validator(mode="after")
    def step_is_valid(self) -> Self:
        if self.operation_class in _RUNTIME_OPERATION_CLASSES:
            raise ValueError("runtime operation class cannot be planned")
        roles = set(self.required_verifier_roles)
        required = {
            VerifierRole.SCHEMA,
            VerifierRole.POLICY,
            VerifierRole.EFFECT,
            VerifierRole.PROVENANCE,
        }
        if not required.issubset(roles):
            raise ValueError("mandatory verifier roles missing")
        if risk_requires_extra_verification(self.risk_class) and not {
            VerifierRole.SAFETY,
            VerifierRole.ROLLBACK,
            VerifierRole.RESOURCE,
        }.issubset(roles):
            raise ValueError("high risk tool plan requires safety, rollback, and resource roles")
        if self.step_fingerprint != tool_verification_fingerprint(self, "step_fingerprint"):
            raise ValueError("tool plan step fingerprint mismatch")
        return self


class ToolInvocationPlan(BaseModel):
    """Deterministic bounded plan for synthetic verification only."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-tool-plan/v1"] = TOOL_PLAN_SCHEMA_VERSION
    plan_id: str = Field(min_length=1, max_length=128)
    intent: ToolIntent
    candidates: tuple[ToolCandidate, ...] = Field(max_length=MAXIMUM_TOOL_CANDIDATES_PER_PLAN)
    selected_candidate_id: str
    steps: tuple[ToolPlanStep, ...] = Field(min_length=1, max_length=MAXIMUM_TOOL_STEPS_PER_PLAN)
    required_verifier_roles: tuple[VerifierRole, ...] = Field(min_length=4, max_length=8)
    reason_codes: tuple[str, ...] = Field(min_length=1, max_length=20)
    explicit_abstention_required: Literal[True] = True
    operator_review_required: Literal[True] = True
    simulation_only: Literal[True] = True
    actual_tool_executed: Literal[False] = False
    persistent_write_applied: Literal[False] = False
    runtime_effect: Literal[False] = False
    plan_fingerprint: str

    @field_validator("plan_id", "selected_candidate_id")
    @classmethod
    def plan_fields_are_safe(cls, value: str) -> str:
        return validate_tool_identifier(value, "tool plan field")

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_are_safe(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return validate_tool_reason_codes(values)

    @field_validator("plan_fingerprint")
    @classmethod
    def plan_fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "tool invocation plan fingerprint")

    @model_validator(mode="after")
    def plan_is_valid(self) -> Self:
        if tuple(step.step_order for step in self.steps) != tuple(range(1, len(self.steps) + 1)):
            raise ValueError("tool plan steps must be contiguous and ordered")
        if self.selected_candidate_id not in {item.candidate_id for item in self.candidates}:
            raise ValueError("selected candidate missing from plan candidates")
        if not set(self.required_verifier_roles).issubset(
            set(self.steps[0].required_verifier_roles)
        ):
            raise ValueError("plan verifier roles must be covered by step verifier roles")
        if len(stable_json(self.model_dump(mode="json"))) > MAXIMUM_PLAN_BYTES:
            raise ValueError("tool plan byte limit exceeded")
        if self.plan_fingerprint != tool_verification_fingerprint(self, "plan_fingerprint"):
            raise ValueError("tool invocation plan fingerprint mismatch")
        return self


class ToolSimulationArtifact(BaseModel):
    """Canonical synthetic artifact produced by dry-run simulation."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-tool-simulation-artifact/v1"] = (
        TOOL_SIMULATION_ARTIFACT_SCHEMA_VERSION
    )
    artifact_id: str = Field(min_length=1, max_length=128)
    step_id: str = Field(min_length=1, max_length=128)
    output_schema_id: str = Field(min_length=1, max_length=128)
    canonical_output: dict[str, Any] = Field(default_factory=dict)
    output_fingerprint: str
    synthetic: Literal[True] = True
    redacted: Literal[True] = True
    runtime_effect: Literal[False] = False
    artifact_fingerprint: str

    @field_validator("artifact_id", "step_id", "output_schema_id")
    @classmethod
    def artifact_fields_are_safe(cls, value: str) -> str:
        return validate_tool_identifier(value, "tool artifact field")

    @field_validator("canonical_output")
    @classmethod
    def output_is_redacted(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_protected_material(value, "tool simulation output")
        return value

    @field_validator("output_fingerprint", "artifact_fingerprint")
    @classmethod
    def fingerprints_are_hex(cls, value: str) -> str:
        return validate_hex64(value, "tool simulation artifact fingerprint")

    @model_validator(mode="after")
    def artifact_is_valid(self) -> Self:
        if self.output_fingerprint != fingerprint_payload(_jsonable(self.canonical_output)):
            raise ValueError("tool simulation output fingerprint mismatch")
        if self.artifact_fingerprint != tool_verification_fingerprint(self, "artifact_fingerprint"):
            raise ValueError("tool simulation artifact fingerprint mismatch")
        return self


class ToolSimulationResult(BaseModel):
    """Deterministic dry-run result without real tool execution."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-tool-simulation/v1"] = TOOL_SIMULATION_SCHEMA_VERSION
    simulation_id: str = Field(min_length=1, max_length=128)
    plan_id: str = Field(min_length=1, max_length=128)
    status: ToolVerificationStatus
    artifacts: tuple[ToolSimulationArtifact, ...] = Field(
        default_factory=tuple,
        max_length=MAXIMUM_OUTPUT_ARTIFACTS_PER_STEP,
    )
    observed_effects: tuple[ToolExpectedEffect, ...] = Field(default_factory=tuple, max_length=50)
    expected_effects_satisfied: bool
    forbidden_effects_absent: bool
    reason_codes: tuple[str, ...] = Field(min_length=1, max_length=20)
    canonical_output: dict[str, Any] = Field(default_factory=dict)
    output_fingerprint: str
    actual_tool_executed: Literal[False] = False
    persistent_write_applied: Literal[False] = False
    runtime_effect: Literal[False] = False
    simulation_fingerprint: str

    @field_validator("simulation_id", "plan_id")
    @classmethod
    def simulation_fields_are_safe(cls, value: str) -> str:
        return validate_tool_identifier(value, "tool simulation field")

    @field_validator("canonical_output")
    @classmethod
    def output_is_redacted(cls, value: dict[str, Any]) -> dict[str, Any]:
        reject_protected_material(value, "tool simulation canonical output")
        return value

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_are_safe(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return validate_tool_reason_codes(values)

    @field_validator("output_fingerprint", "simulation_fingerprint")
    @classmethod
    def fingerprints_are_hex(cls, value: str) -> str:
        return validate_hex64(value, "tool simulation fingerprint")

    @model_validator(mode="after")
    def simulation_is_valid(self) -> Self:
        if self.output_fingerprint != fingerprint_payload(_jsonable(self.canonical_output)):
            raise ValueError("tool simulation output fingerprint mismatch")
        if self.status is ToolVerificationStatus.SIMULATION_PASSED and (
            not self.expected_effects_satisfied or not self.forbidden_effects_absent
        ):
            raise ValueError("simulation pass requires expected and forbidden effect checks")
        if self.simulation_fingerprint != tool_verification_fingerprint(
            self, "simulation_fingerprint"
        ):
            raise ValueError("tool simulation fingerprint mismatch")
        return self


class ToolVerifierProfile(BaseModel):
    """Independent deterministic verifier profile."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-tool-verifier-profile/v1"] = (
        TOOL_VERIFIER_PROFILE_SCHEMA_VERSION
    )
    profile_id: str = Field(min_length=1, max_length=128)
    verifier_role: VerifierRole
    independence_group: str = Field(min_length=1, max_length=128)
    profile_version: str = Field(min_length=1, max_length=32)
    can_execute_tools: Literal[False] = False
    can_mutate_state: Literal[False] = False
    synthetic: Literal[True] = True
    read_only: Literal[True] = True
    redacted: Literal[True] = True
    profile_fingerprint: str

    @field_validator("profile_id", "independence_group", "profile_version")
    @classmethod
    def profile_fields_are_safe(cls, value: str) -> str:
        return validate_tool_identifier(value, "tool verifier profile field")

    @field_validator("profile_fingerprint")
    @classmethod
    def profile_fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "tool verifier profile fingerprint")

    @model_validator(mode="after")
    def profile_is_valid(self) -> Self:
        if self.profile_fingerprint != tool_verification_fingerprint(self, "profile_fingerprint"):
            raise ValueError("tool verifier profile fingerprint mismatch")
        return self


class ToolVerificationRule(BaseModel):
    """Independent deterministic verification rule."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-tool-verification-rule/v1"] = (
        TOOL_VERIFICATION_RULE_SCHEMA_VERSION
    )
    rule_id: str = Field(min_length=1, max_length=128)
    verifier_role: VerifierRole
    rule_name: str = Field(min_length=1, max_length=128)
    required_for_risk_classes: tuple[ToolRiskClass, ...] = Field(min_length=1, max_length=5)
    reason_codes: tuple[str, ...] = Field(min_length=1, max_length=20)
    rule_fingerprint: str

    @field_validator("rule_id", "rule_name")
    @classmethod
    def rule_fields_are_safe(cls, value: str) -> str:
        return validate_tool_identifier(value, "tool verification rule field")

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_are_safe(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return validate_tool_reason_codes(values)

    @field_validator("rule_fingerprint")
    @classmethod
    def rule_fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "tool verification rule fingerprint")

    @model_validator(mode="after")
    def rule_is_valid(self) -> Self:
        if self.rule_fingerprint != tool_verification_fingerprint(self, "rule_fingerprint"):
            raise ValueError("tool verification rule fingerprint mismatch")
        return self


class ToolVerificationFinding(BaseModel):
    """Immutable verification finding."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-tool-verification-finding/v1"] = (
        TOOL_FINDING_SCHEMA_VERSION
    )
    finding_id: str = Field(min_length=1, max_length=128)
    plan_id: str = Field(min_length=1, max_length=128)
    simulation_id: str = Field(min_length=1, max_length=128)
    verifier_profile_id: str = Field(min_length=1, max_length=128)
    verifier_role: VerifierRole
    rule_id: str = Field(min_length=1, max_length=128)
    status: ToolVerificationStatus
    severity: ToolFindingSeverity
    passed: bool
    abstained: bool
    reason_codes: tuple[str, ...] = Field(min_length=1, max_length=20)
    evidence_fingerprint: str
    actual_execution_verified: Literal[False] = False
    approval_created: Literal[False] = False
    knowledge_promoted: Literal[False] = False
    belief_mutated: Literal[False] = False
    runtime_effect: Literal[False] = False
    finding_fingerprint: str

    @field_validator("finding_id", "plan_id", "simulation_id", "verifier_profile_id", "rule_id")
    @classmethod
    def finding_fields_are_safe(cls, value: str) -> str:
        return validate_tool_identifier(value, "tool finding field")

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_are_safe(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return validate_tool_reason_codes(values)

    @field_validator("evidence_fingerprint", "finding_fingerprint")
    @classmethod
    def fingerprints_are_hex(cls, value: str) -> str:
        return validate_hex64(value, "tool verification finding fingerprint")

    @model_validator(mode="after")
    def finding_is_valid(self) -> Self:
        if self.status is ToolVerificationStatus.VERIFICATION_PASSED and not self.passed:
            raise ValueError("passed finding must have passed true")
        if self.status is ToolVerificationStatus.ABSTAINED and not self.abstained:
            raise ValueError("abstained finding must have abstained true")
        if self.finding_fingerprint != tool_verification_fingerprint(self, "finding_fingerprint"):
            raise ValueError("tool verification finding fingerprint mismatch")
        return self


class ToolAttestation(BaseModel):
    """Hash-chained attestation for an immutable verification finding."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-tool-attestation/v1"] = TOOL_ATTESTATION_SCHEMA_VERSION
    attestation_id: str = Field(min_length=1, max_length=128)
    sequence_number: int = Field(ge=1, le=MAXIMUM_ATTESTATIONS_PER_SESSION)
    previous_attestation_fingerprint: str | None = None
    finding_id: str = Field(min_length=1, max_length=128)
    finding_fingerprint: str
    attested_at: datetime
    synthetic: Literal[True] = True
    read_only: Literal[True] = True
    redacted: Literal[True] = True
    runtime_effect: Literal[False] = False
    attestation_fingerprint: str

    @field_validator("attestation_id", "finding_id")
    @classmethod
    def attestation_fields_are_safe(cls, value: str) -> str:
        return validate_tool_identifier(value, "tool attestation field")

    @field_validator(
        "previous_attestation_fingerprint", "finding_fingerprint", "attestation_fingerprint"
    )
    @classmethod
    def fingerprints_are_hex(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return validate_hex64(value, "tool attestation fingerprint")

    @field_validator("attested_at")
    @classmethod
    def attested_at_is_utc(cls, value: datetime) -> datetime:
        return ensure_utc(value, "tool attestation time")

    @model_validator(mode="after")
    def attestation_is_valid(self) -> Self:
        if self.sequence_number == 1 and self.previous_attestation_fingerprint is not None:
            raise ValueError("first attestation must not have previous fingerprint")
        if self.sequence_number > 1 and self.previous_attestation_fingerprint is None:
            raise ValueError("chained attestation missing previous fingerprint")
        if self.attestation_fingerprint != tool_verification_fingerprint(
            self, "attestation_fingerprint"
        ):
            raise ValueError("tool attestation fingerprint mismatch")
        return self


class ToolVerificationResourceBudget(BaseModel):
    """AION-214-KI-0006 resource budget with every execution channel at zero."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-tool-resource-budget/v1"] = TOOL_RESOURCE_SCHEMA_VERSION
    maximum_tool_manifests: Literal[500] = MAXIMUM_TOOL_MANIFESTS
    maximum_tool_candidates_per_plan: Literal[100] = MAXIMUM_TOOL_CANDIDATES_PER_PLAN
    maximum_tool_steps_per_plan: Literal[50] = MAXIMUM_TOOL_STEPS_PER_PLAN
    maximum_manifest_bytes: Literal[131072] = MAXIMUM_MANIFEST_BYTES
    maximum_input_schema_bytes: Literal[65536] = MAXIMUM_INPUT_SCHEMA_BYTES
    maximum_output_schema_bytes: Literal[65536] = MAXIMUM_OUTPUT_SCHEMA_BYTES
    maximum_plan_bytes: Literal[1048576] = MAXIMUM_PLAN_BYTES
    maximum_preconditions_per_step: Literal[50] = MAXIMUM_PRECONDITIONS_PER_STEP
    maximum_postconditions_per_step: Literal[50] = MAXIMUM_POSTCONDITIONS_PER_STEP
    maximum_expected_effects_per_step: Literal[50] = MAXIMUM_EXPECTED_EFFECTS_PER_STEP
    maximum_forbidden_effects_per_step: Literal[50] = MAXIMUM_FORBIDDEN_EFFECTS_PER_STEP
    maximum_verification_rules_per_step: Literal[100] = MAXIMUM_VERIFICATION_RULES_PER_STEP
    maximum_verifiers_per_step: Literal[8] = MAXIMUM_VERIFIERS_PER_STEP
    maximum_output_artifacts_per_step: Literal[100] = MAXIMUM_OUTPUT_ARTIFACTS_PER_STEP
    maximum_evidence_references_per_step: Literal[100] = MAXIMUM_EVIDENCE_REFERENCES_PER_STEP
    maximum_attestations_per_session: Literal[500] = MAXIMUM_ATTESTATIONS_PER_SESSION
    maximum_rollback_steps_per_plan: Literal[50] = MAXIMUM_ROLLBACK_STEPS_PER_PLAN
    maximum_compensation_steps_per_plan: Literal[50] = MAXIMUM_COMPENSATION_STEPS_PER_PLAN
    maximum_simulated_sessions: Literal[100] = MAXIMUM_SIMULATED_SESSIONS
    maximum_query_results: Literal[1000] = MAXIMUM_QUERY_RESULTS
    maximum_fixture_records: Literal[5000] = MAXIMUM_FIXTURE_RECORDS
    maximum_fixture_bytes: Literal[4194304] = MAXIMUM_FIXTURE_BYTES
    maximum_concurrent_plans: Literal[4] = MAXIMUM_CONCURRENT_PLANS
    maximum_concurrent_verifiers: Literal[8] = MAXIMUM_CONCURRENT_VERIFIERS
    maximum_persistent_tool_state_write_batch: Literal[0] = (
        MAXIMUM_PERSISTENT_TOOL_STATE_WRITE_BATCH
    )
    maximum_actual_tool_executions: Literal[0] = MAXIMUM_ACTUAL_TOOL_EXECUTIONS
    maximum_shell_commands: Literal[0] = MAXIMUM_SHELL_COMMANDS
    maximum_subprocess_executions: Literal[0] = MAXIMUM_SUBPROCESS_EXECUTIONS
    maximum_network_calls: Literal[0] = MAXIMUM_NETWORK_CALLS
    maximum_dns_resolutions: Literal[0] = MAXIMUM_DNS_RESOLUTIONS
    maximum_browser_actions: Literal[0] = MAXIMUM_BROWSER_ACTIONS
    maximum_connector_calls: Literal[0] = MAXIMUM_CONNECTOR_CALLS
    maximum_search_provider_calls: Literal[0] = MAXIMUM_SEARCH_PROVIDER_CALLS
    maximum_model_provider_calls: Literal[0] = MAXIMUM_MODEL_PROVIDER_CALLS
    maximum_filesystem_mutations: Literal[0] = MAXIMUM_FILESYSTEM_MUTATIONS
    maximum_source_mutations: Literal[0] = MAXIMUM_SOURCE_MUTATIONS
    maximum_git_operations: Literal[0] = MAXIMUM_GIT_OPERATIONS
    maximum_runtime_created_pull_requests: Literal[0] = MAXIMUM_RUNTIME_CREATED_PULL_REQUESTS
    maximum_approvals_created: Literal[0] = MAXIMUM_APPROVALS_CREATED
    maximum_autonomous_actions: Literal[0] = MAXIMUM_AUTONOMOUS_ACTIONS
    maximum_high_stakes_actions: Literal[0] = MAXIMUM_HIGH_STAKES_ACTIONS
    maximum_deployments: Literal[0] = MAXIMUM_DEPLOYMENTS
    maximum_knowledge_promotions: Literal[0] = MAXIMUM_KNOWLEDGE_PROMOTIONS
    maximum_belief_mutations: Literal[0] = MAXIMUM_BELIEF_MUTATIONS
    maximum_model_weight_changes: Literal[0] = MAXIMUM_MODEL_WEIGHT_CHANGES


class ToolVerificationResourceUsage(BaseModel):
    """Measured counters for one in-memory simulation-only session."""

    model_config = FROZEN_MODEL_CONFIG

    tool_manifests: int = Field(default=0, ge=0)
    tool_candidates: int = Field(default=0, ge=0)
    tool_steps: int = Field(default=0, ge=0)
    output_artifacts: int = Field(default=0, ge=0)
    attestations: int = Field(default=0, ge=0)
    simulated_sessions: int = Field(default=0, ge=0)
    fixture_records: int = Field(default=0, ge=0)
    fixture_bytes: int = Field(default=0, ge=0)
    persistent_tool_state_write_batch: int = Field(default=0, ge=0)
    actual_tool_executions: int = Field(default=0, ge=0)
    shell_commands: int = Field(default=0, ge=0)
    subprocess_executions: int = Field(default=0, ge=0)
    network_calls: int = Field(default=0, ge=0)
    dns_resolutions: int = Field(default=0, ge=0)
    browser_actions: int = Field(default=0, ge=0)
    connector_calls: int = Field(default=0, ge=0)
    model_provider_calls: int = Field(default=0, ge=0)
    filesystem_mutations: int = Field(default=0, ge=0)
    source_mutations: int = Field(default=0, ge=0)
    git_operations: int = Field(default=0, ge=0)
    runtime_created_pull_requests: int = Field(default=0, ge=0)
    approvals_created: int = Field(default=0, ge=0)
    autonomous_actions: int = Field(default=0, ge=0)
    high_stakes_actions: int = Field(default=0, ge=0)
    deployments: int = Field(default=0, ge=0)
    knowledge_promotions: int = Field(default=0, ge=0)
    belief_mutations: int = Field(default=0, ge=0)
    model_weight_changes: int = Field(default=0, ge=0)


class ToolVerificationDiagnostics(BaseModel):
    """Redacted diagnostics for a simulation-only session."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-tool-verification-diagnostics/v1"] = (
        TOOL_DIAGNOSTICS_SCHEMA_VERSION
    )
    diagnostic_id: str = Field(min_length=1, max_length=128)
    reason_codes: tuple[str, ...] = Field(min_length=1, max_length=20)
    summary: str = Field(min_length=1, max_length=300)
    redacted: Literal[True] = True
    diagnostic_fingerprint: str

    @field_validator("diagnostic_id")
    @classmethod
    def diagnostic_id_is_safe(cls, value: str) -> str:
        return validate_tool_identifier(value, "diagnostic_id")

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_are_safe(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return validate_tool_reason_codes(values)

    @field_validator("summary")
    @classmethod
    def summary_is_redacted(cls, value: str) -> str:
        reject_protected_material(value, "tool diagnostics summary")
        return value

    @field_validator("diagnostic_fingerprint")
    @classmethod
    def diagnostic_fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "tool diagnostics fingerprint")

    @model_validator(mode="after")
    def diagnostics_are_valid(self) -> Self:
        if self.diagnostic_fingerprint != tool_verification_fingerprint(
            self, "diagnostic_fingerprint"
        ):
            raise ValueError("tool diagnostics fingerprint mismatch")
        return self


class ToolVerificationIncident(BaseModel):
    """Redacted incident record for blocked or abstained verification paths."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-tool-verification-incident/v1"] = (
        TOOL_INCIDENT_SCHEMA_VERSION
    )
    incident_id: str = Field(min_length=1, max_length=128)
    severity: ToolFindingSeverity
    reason_codes: tuple[str, ...] = Field(min_length=1, max_length=20)
    redacted_detail: str = Field(min_length=1, max_length=300)
    actual_tool_executed: Literal[False] = False
    runtime_effect: Literal[False] = False
    incident_fingerprint: str

    @field_validator("incident_id")
    @classmethod
    def incident_id_is_safe(cls, value: str) -> str:
        return validate_tool_identifier(value, "incident_id")

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_are_safe(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return validate_tool_reason_codes(values)

    @field_validator("redacted_detail")
    @classmethod
    def detail_is_redacted(cls, value: str) -> str:
        reject_protected_material(value, "tool incident detail")
        return value

    @field_validator("incident_fingerprint")
    @classmethod
    def incident_fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "tool incident fingerprint")

    @model_validator(mode="after")
    def incident_is_valid(self) -> Self:
        if self.incident_fingerprint != tool_verification_fingerprint(self, "incident_fingerprint"):
            raise ValueError("tool incident fingerprint mismatch")
        return self


class ToolVerificationOperatorReviewItem(BaseModel):
    """Operator evidence that simulation is not execution or approval."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-tool-verification-operator-review/v1"] = (
        TOOL_OPERATOR_REVIEW_SCHEMA_VERSION
    )
    review_item_id: str = Field(min_length=1, max_length=128)
    session_id: str = Field(min_length=1, max_length=128)
    required: Literal[True] = True
    summary: str = Field(min_length=1, max_length=300)
    simulation_pass_not_execution: Literal[True] = True
    verification_pass_not_approval: Literal[True] = True
    tool_output_not_knowledge: Literal[True] = True
    actual_tool_executed: Literal[False] = False
    runtime_effect: Literal[False] = False
    review_fingerprint: str

    @field_validator("review_item_id", "session_id")
    @classmethod
    def review_fields_are_safe(cls, value: str) -> str:
        return validate_tool_identifier(value, "tool review field")

    @field_validator("summary")
    @classmethod
    def summary_is_redacted(cls, value: str) -> str:
        reject_protected_material(value, "tool review summary")
        return value

    @field_validator("review_fingerprint")
    @classmethod
    def review_fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "tool review fingerprint")

    @model_validator(mode="after")
    def review_is_valid(self) -> Self:
        if self.review_fingerprint != tool_verification_fingerprint(self, "review_fingerprint"):
            raise ValueError("tool operator review fingerprint mismatch")
        return self


class ToolVerificationEvidenceBundle(BaseModel):
    """Redacted evidence bundle for operator review and integrity checks."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-tool-verification-evidence/v1"] = (
        TOOL_EVIDENCE_SCHEMA_VERSION
    )
    evidence_id: str = Field(min_length=1, max_length=128)
    session_id: str = Field(min_length=1, max_length=128)
    artifact_fingerprints: tuple[str, ...] = Field(default_factory=tuple, max_length=100)
    finding_fingerprints: tuple[str, ...] = Field(default_factory=tuple, max_length=100)
    attestation_fingerprints: tuple[str, ...] = Field(default_factory=tuple, max_length=500)
    provenance_fingerprints: tuple[str, ...] = Field(default_factory=tuple, max_length=100)
    redacted: Literal[True] = True
    persistent_write_applied: Literal[False] = False
    runtime_effect: Literal[False] = False
    evidence_fingerprint: str

    @field_validator("evidence_id", "session_id")
    @classmethod
    def evidence_fields_are_safe(cls, value: str) -> str:
        return validate_tool_identifier(value, "tool evidence field")

    @field_validator(
        "artifact_fingerprints",
        "finding_fingerprints",
        "attestation_fingerprints",
        "provenance_fingerprints",
    )
    @classmethod
    def fingerprint_tuples_are_hex(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(validate_hex64(value, "tool evidence fingerprint") for value in values)

    @field_validator("evidence_fingerprint")
    @classmethod
    def evidence_fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "tool evidence fingerprint")

    @model_validator(mode="after")
    def evidence_is_valid(self) -> Self:
        if self.evidence_fingerprint != tool_verification_fingerprint(self, "evidence_fingerprint"):
            raise ValueError("tool evidence fingerprint mismatch")
        return self


class ToolVerificationSession(BaseModel):
    """Immutable in-memory session containing plan, simulation, verification, and evidence."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-tool-verification-session/v1"] = (
        TOOL_SESSION_SCHEMA_VERSION
    )
    program_id: Literal["AION-KNOWLEDGE-INTELLIGENCE-001"] = PROGRAM_ID
    authorization_transaction_id: Literal["AION-214-KI-0006"] = AUTHORIZATION_TRANSACTION_ID
    implementation_task: Literal["AION-215"] = IMPLEMENTATION_TASK
    formal_closeout_task: Literal["AION-216"] = FORMAL_CLOSEOUT_TASK
    session_id: str = Field(min_length=1, max_length=128)
    registry_snapshot: ToolManifestRegistrySnapshot
    intent: ToolIntent
    plan: ToolInvocationPlan
    simulation: ToolSimulationResult
    findings: tuple[ToolVerificationFinding, ...] = Field(default_factory=tuple, max_length=100)
    attestations: tuple[ToolAttestation, ...] = Field(default_factory=tuple, max_length=500)
    diagnostics: ToolVerificationDiagnostics
    incidents: tuple[ToolVerificationIncident, ...] = Field(default_factory=tuple, max_length=20)
    operator_review_items: tuple[ToolVerificationOperatorReviewItem, ...] = Field(
        default_factory=tuple,
        max_length=100,
    )
    evidence_bundle: ToolVerificationEvidenceBundle
    resource_usage: ToolVerificationResourceUsage
    overall_status: ToolSessionOutcome
    explicit_abstention: Literal[True] = True
    operator_review_required: Literal[True] = True
    tool_verification_fabric_authorized: Literal[True] = True
    tool_verification_fabric_implemented: Literal[True] = True
    tool_verification_fabric_state: Literal[
        "implemented_deterministic_simulation_verification_attestation_persistent_write_disabled"
    ] = TOOL_VERIFICATION_FABRIC_STATE
    tool_verification_fabric_runtime_enabled: Literal[False] = False
    actual_tool_execution_enabled: Literal[False] = False
    actual_tool_executed: Literal[False] = False
    persistent_tool_state_write_enabled: Literal[False] = False
    persistent_write_applied: Literal[False] = False
    knowledge_promoted: Literal[False] = False
    belief_mutated: Literal[False] = False
    synthetic: Literal[True] = True
    read_only: Literal[True] = True
    redacted: Literal[True] = True
    runtime_effect: Literal[False] = False
    session_fingerprint: str

    @field_validator("session_id")
    @classmethod
    def session_id_is_safe(cls, value: str) -> str:
        return validate_tool_identifier(value, "session_id")

    @field_validator("session_fingerprint")
    @classmethod
    def session_fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "tool verification session fingerprint")

    @model_validator(mode="after")
    def session_is_valid(self) -> Self:
        if self.intent.intent_id != self.plan.intent.intent_id:
            raise ValueError("session plan intent mismatch")
        if self.plan.plan_id != self.simulation.plan_id:
            raise ValueError("session simulation plan mismatch")
        if self.overall_status is ToolSessionOutcome.SIMULATION_PASSED and any(
            item.passed is not True for item in self.findings
        ):
            raise ValueError("simulation_passed session cannot contain failed findings")
        if self.session_fingerprint != tool_verification_fingerprint(self, "session_fingerprint"):
            raise ValueError("tool verification session fingerprint mismatch")
        return self


class ToolVerificationIntegrityFinding(BaseModel):
    """Integrity finding for a completed in-memory session."""

    model_config = FROZEN_MODEL_CONFIG

    finding_id: str = Field(min_length=1, max_length=128)
    status: ToolIntegrityStatus
    reason_codes: tuple[str, ...] = Field(min_length=1, max_length=20)
    finding_fingerprint: str

    @field_validator("finding_id")
    @classmethod
    def finding_id_is_safe(cls, value: str) -> str:
        return validate_tool_identifier(value, "integrity finding id")

    @field_validator("reason_codes")
    @classmethod
    def reason_codes_are_safe(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return validate_tool_reason_codes(values)

    @field_validator("finding_fingerprint")
    @classmethod
    def finding_fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "tool integrity finding fingerprint")

    @model_validator(mode="after")
    def finding_is_valid(self) -> Self:
        if self.finding_fingerprint != tool_verification_fingerprint(self, "finding_fingerprint"):
            raise ValueError("tool integrity finding fingerprint mismatch")
        return self


class ToolVerificationIntegrityReport(BaseModel):
    """Integrity report that verifies fingerprints, chain order, and zero runtime counters."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-tool-verification-integrity/v1"] = (
        TOOL_INTEGRITY_SCHEMA_VERSION
    )
    report_id: str = Field(min_length=1, max_length=128)
    session_id: str = Field(min_length=1, max_length=128)
    status: ToolIntegrityStatus
    findings: tuple[ToolVerificationIntegrityFinding, ...] = Field(min_length=1, max_length=100)
    resource_usage: ToolVerificationResourceUsage
    attestation_chain_valid: bool
    runtime_counters_zero: bool
    persistent_write_applied: Literal[False] = False
    runtime_effect: Literal[False] = False
    report_fingerprint: str

    @field_validator("report_id", "session_id")
    @classmethod
    def report_fields_are_safe(cls, value: str) -> str:
        return validate_tool_identifier(value, "tool integrity report field")

    @field_validator("report_fingerprint")
    @classmethod
    def report_fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "tool integrity report fingerprint")

    @model_validator(mode="after")
    def report_is_valid(self) -> Self:
        if self.status is ToolIntegrityStatus.PASS_ and (
            not self.attestation_chain_valid or not self.runtime_counters_zero
        ):
            raise ValueError("passing integrity report requires chain and zero runtime counters")
        if self.report_fingerprint != tool_verification_fingerprint(self, "report_fingerprint"):
            raise ValueError("tool integrity report fingerprint mismatch")
        return self


class ToolVerificationFixtureEnvelope(BaseModel):
    """Explicit local synthetic fixture for deterministic simulation replay."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-tool-verification-fixture/v1"] = (
        TOOL_FIXTURE_SCHEMA_VERSION
    )
    program_id: Literal["AION-KNOWLEDGE-INTELLIGENCE-001"] = PROGRAM_ID
    authorization_transaction_id: Literal["AION-214-KI-0006"] = AUTHORIZATION_TRANSACTION_ID
    implementation_task: Literal["AION-215"] = IMPLEMENTATION_TASK
    formal_closeout_task: Literal["AION-216"] = FORMAL_CLOSEOUT_TASK
    registry_snapshot: ToolManifestRegistrySnapshot
    intent: ToolIntent
    fixture_records: tuple[dict[str, Any], ...] = Field(
        default_factory=tuple,
        max_length=MAXIMUM_FIXTURE_RECORDS,
    )
    synthetic: Literal[True] = True
    read_only: Literal[True] = True
    redacted: Literal[True] = True
    persistent_write_applied: Literal[False] = False
    runtime_effect: Literal[False] = False
    fixture_fingerprint: str

    @field_validator("fixture_records")
    @classmethod
    def fixture_records_are_redacted(
        cls, values: tuple[dict[str, Any], ...]
    ) -> tuple[dict[str, Any], ...]:
        reject_protected_material(values, "tool fixture records")
        return values

    @field_validator("fixture_fingerprint")
    @classmethod
    def fixture_fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "tool fixture fingerprint")

    @model_validator(mode="after")
    def fixture_is_valid(self) -> Self:
        if self.fixture_fingerprint != tool_verification_fingerprint(self, "fixture_fingerprint"):
            raise ValueError("tool fixture fingerprint mismatch")
        return self


class ToolVerificationQuery(BaseModel):
    """Bounded exact query over the in-memory session repository."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-tool-verification-query/v1"] = TOOL_QUERY_SCHEMA_VERSION
    session_id: str | None = None
    intent_id: str | None = None
    plan_id: str | None = None
    overall_status: ToolSessionOutcome | None = None
    limit: int = Field(default=100, ge=1, le=MAXIMUM_QUERY_RESULTS)
    query_fingerprint: str

    @field_validator("session_id", "intent_id", "plan_id")
    @classmethod
    def query_fields_are_safe(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return validate_tool_identifier(value, "tool query field")

    @field_validator("query_fingerprint")
    @classmethod
    def query_fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "tool query fingerprint")

    @model_validator(mode="after")
    def query_is_valid(self) -> Self:
        if not any(
            value is not None
            for value in (self.session_id, self.intent_id, self.plan_id, self.overall_status)
        ):
            raise ValueError("tool verification query must include an exact filter")
        if self.query_fingerprint != tool_verification_fingerprint(self, "query_fingerprint"):
            raise ValueError("tool query fingerprint mismatch")
        return self


class ToolVerificationQueryResult(BaseModel):
    """Deterministic query result over immutable in-memory sessions."""

    model_config = FROZEN_MODEL_CONFIG

    schema_version: Literal["aion-knowledge-tool-verification-query/v1"] = TOOL_QUERY_SCHEMA_VERSION
    query: ToolVerificationQuery
    sessions: tuple[ToolVerificationSession, ...] = Field(max_length=MAXIMUM_QUERY_RESULTS)
    result_count: int = Field(ge=0, le=MAXIMUM_QUERY_RESULTS)
    query_result_fingerprint: str

    @field_validator("query_result_fingerprint")
    @classmethod
    def query_result_fingerprint_is_hex(cls, value: str) -> str:
        return validate_hex64(value, "tool query result fingerprint")

    @model_validator(mode="after")
    def result_is_valid(self) -> Self:
        if self.result_count != len(self.sessions):
            raise ValueError("tool query result count mismatch")
        if self.query_result_fingerprint != tool_verification_fingerprint(
            self, "query_result_fingerprint"
        ):
            raise ValueError("tool query result fingerprint mismatch")
        return self


def schema_descriptor_fingerprint(payload: ToolSchemaDescriptor | dict[str, Any]) -> str:
    return tool_verification_fingerprint(payload, "schema_fingerprint")


def permission_envelope_fingerprint(payload: ToolPermissionEnvelope | dict[str, Any]) -> str:
    return tool_verification_fingerprint(payload, "permission_fingerprint")


def tool_effect_fingerprint(
    payload: ToolExpectedEffect | ToolForbiddenEffect | dict[str, Any],
) -> str:
    return tool_verification_fingerprint(payload, "effect_fingerprint")


def tool_manifest_fingerprint(payload: ToolCapabilityManifest | dict[str, Any]) -> str:
    return tool_verification_fingerprint(payload, "manifest_fingerprint")


def tool_registry_fingerprint(payload: ToolManifestRegistrySnapshot | dict[str, Any]) -> str:
    return tool_verification_fingerprint(payload, "registry_fingerprint")


def tool_intent_fingerprint(payload: ToolIntent | dict[str, Any]) -> str:
    return tool_verification_fingerprint(payload, "intent_fingerprint")


def tool_candidate_fingerprint(payload: ToolCandidate | dict[str, Any]) -> str:
    return tool_verification_fingerprint(payload, "candidate_fingerprint")


def tool_condition_fingerprint(
    payload: ToolPrecondition | ToolPostcondition | dict[str, Any],
) -> str:
    return tool_verification_fingerprint(payload, "condition_fingerprint")


def tool_rollback_fingerprint(payload: ToolRollbackPlan | dict[str, Any]) -> str:
    return tool_verification_fingerprint(payload, "rollback_fingerprint")


def tool_compensation_fingerprint(payload: ToolCompensationPlan | dict[str, Any]) -> str:
    return tool_verification_fingerprint(payload, "compensation_fingerprint")


def tool_plan_step_fingerprint(payload: ToolPlanStep | dict[str, Any]) -> str:
    return tool_verification_fingerprint(payload, "step_fingerprint")


def tool_plan_fingerprint(payload: ToolInvocationPlan | dict[str, Any]) -> str:
    return tool_verification_fingerprint(payload, "plan_fingerprint")


def tool_artifact_fingerprint(payload: ToolSimulationArtifact | dict[str, Any]) -> str:
    return tool_verification_fingerprint(payload, "artifact_fingerprint")


def tool_simulation_fingerprint(payload: ToolSimulationResult | dict[str, Any]) -> str:
    return tool_verification_fingerprint(payload, "simulation_fingerprint")


def tool_verifier_profile_fingerprint(payload: ToolVerifierProfile | dict[str, Any]) -> str:
    return tool_verification_fingerprint(payload, "profile_fingerprint")


def tool_verification_rule_fingerprint(payload: ToolVerificationRule | dict[str, Any]) -> str:
    return tool_verification_fingerprint(payload, "rule_fingerprint")


def tool_finding_fingerprint(payload: ToolVerificationFinding | dict[str, Any]) -> str:
    return tool_verification_fingerprint(payload, "finding_fingerprint")


def tool_attestation_fingerprint(payload: ToolAttestation | dict[str, Any]) -> str:
    return tool_verification_fingerprint(payload, "attestation_fingerprint")


def tool_diagnostics_fingerprint(payload: ToolVerificationDiagnostics | dict[str, Any]) -> str:
    return tool_verification_fingerprint(payload, "diagnostic_fingerprint")


def tool_incident_fingerprint(payload: ToolVerificationIncident | dict[str, Any]) -> str:
    return tool_verification_fingerprint(payload, "incident_fingerprint")


def tool_operator_review_fingerprint(
    payload: ToolVerificationOperatorReviewItem | dict[str, Any],
) -> str:
    return tool_verification_fingerprint(payload, "review_fingerprint")


def tool_evidence_bundle_fingerprint(
    payload: ToolVerificationEvidenceBundle | dict[str, Any],
) -> str:
    return tool_verification_fingerprint(payload, "evidence_fingerprint")


def tool_session_fingerprint(payload: ToolVerificationSession | dict[str, Any]) -> str:
    return tool_verification_fingerprint(payload, "session_fingerprint")


def tool_integrity_finding_fingerprint(
    payload: ToolVerificationIntegrityFinding | dict[str, Any],
) -> str:
    return tool_verification_fingerprint(payload, "finding_fingerprint")


def tool_integrity_report_fingerprint(
    payload: ToolVerificationIntegrityReport | dict[str, Any],
) -> str:
    return tool_verification_fingerprint(payload, "report_fingerprint")


def tool_fixture_fingerprint(payload: ToolVerificationFixtureEnvelope | dict[str, Any]) -> str:
    return tool_verification_fingerprint(payload, "fixture_fingerprint")


def tool_query_fingerprint(payload: ToolVerificationQuery | dict[str, Any]) -> str:
    return tool_verification_fingerprint(payload, "query_fingerprint")


def tool_query_result_fingerprint(payload: ToolVerificationQueryResult | dict[str, Any]) -> str:
    return tool_verification_fingerprint(payload, "query_result_fingerprint")


__all__ = [
    "APPROVAL_RECORD_ID",
    "AUTHORIZATION_SCOPE",
    "AUTHORIZATION_TRANSACTION_ID",
    "FORMAL_CLOSEOUT_TASK",
    "FROZEN_MODEL_CONFIG",
    "IMPLEMENTATION_TASK",
    "MAXIMUM_ACTUAL_TOOL_EXECUTIONS",
    "MAXIMUM_PERSISTENT_TOOL_STATE_WRITE_BATCH",
    "MODEL_CONFIG",
    "PROGRAM_ID",
    "TOOL_REASON_CODES",
    "TOOL_VERIFICATION_CONTRACT_SCHEMA_VERSION",
    "TOOL_VERIFICATION_FABRIC_STATE",
    "ToolAttestation",
    "ToolCandidate",
    "ToolCapabilityManifest",
    "ToolCompensationPlan",
    "ToolEffectType",
    "ToolExpectedEffect",
    "ToolFindingSeverity",
    "ToolForbiddenEffect",
    "ToolIntegrityStatus",
    "ToolIntent",
    "ToolInvocationPlan",
    "ToolManifestRegistrySnapshot",
    "ToolOperationClass",
    "ToolPermissionEnvelope",
    "ToolPlanStep",
    "ToolPostcondition",
    "ToolPrecondition",
    "ToolRiskClass",
    "ToolRollbackPlan",
    "ToolSchemaDescriptor",
    "ToolSessionOutcome",
    "ToolSimulationArtifact",
    "ToolSimulationResult",
    "ToolVerificationDiagnostics",
    "ToolVerificationError",
    "ToolVerificationEvidenceBundle",
    "ToolVerificationFinding",
    "ToolVerificationFixtureEnvelope",
    "ToolVerificationIncident",
    "ToolVerificationIntegrityFinding",
    "ToolVerificationIntegrityReport",
    "ToolVerificationOperatorReviewItem",
    "ToolVerificationQuery",
    "ToolVerificationQueryResult",
    "ToolVerificationResourceBudget",
    "ToolVerificationResourceUsage",
    "ToolVerificationRule",
    "ToolVerificationSession",
    "ToolVerificationStatus",
    "ToolVerifierProfile",
    "VerifierRole",
    "forbidden_runtime_effects",
    "permission_envelope_fingerprint",
    "risk_lte",
    "risk_requires_extra_verification",
    "runtime_operation_classes",
    "schema_descriptor_fingerprint",
    "tool_artifact_fingerprint",
    "tool_attestation_fingerprint",
    "tool_candidate_fingerprint",
    "tool_compensation_fingerprint",
    "tool_condition_fingerprint",
    "tool_diagnostics_fingerprint",
    "tool_effect_fingerprint",
    "tool_evidence_bundle_fingerprint",
    "tool_finding_fingerprint",
    "tool_fixture_fingerprint",
    "tool_integrity_finding_fingerprint",
    "tool_integrity_report_fingerprint",
    "tool_intent_fingerprint",
    "tool_manifest_fingerprint",
    "tool_operator_review_fingerprint",
    "tool_plan_fingerprint",
    "tool_plan_step_fingerprint",
    "tool_query_fingerprint",
    "tool_query_result_fingerprint",
    "tool_registry_fingerprint",
    "tool_rollback_fingerprint",
    "tool_session_fingerprint",
    "tool_simulation_fingerprint",
    "tool_verification_fingerprint",
    "tool_verification_rule_fingerprint",
    "tool_verifier_profile_fingerprint",
    "validate_tool_identifier",
    "validate_tool_reason_codes",
]
