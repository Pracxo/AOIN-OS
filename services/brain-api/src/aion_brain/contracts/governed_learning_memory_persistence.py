"""Operator-approved local append-only GLM persistence contracts.

These contracts describe the AION-223-authorized AION-224 local store. They are
separate from AION production memory, approval creation, belief creation, API
routes, schedulers, model providers, connectors, and network access.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from datetime import datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from enum import StrEnum
from types import MappingProxyType
from typing import Any, Final, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from aion_brain.contracts.approvals import ApprovalDecision, ApprovalRequest
from aion_brain.contracts.governed_learning_memory import (
    MemoryProjectionTarget,
    PromotionTransactionPlan,
    PromotionTransactionResult,
    PromotionTransactionStatus,
    audit_promotion_transaction_plan,
    audit_promotion_transaction_result,
    governed_learning_memory_fingerprint,
)
from aion_brain.contracts.knowledge_research import (
    ensure_utc,
    reject_protected_material,
    validate_hex64,
)

LOCAL_PERSISTENCE_CONTRACT_SCHEMA_VERSION: Final[Literal["aion-glm-local-persistence/v1"]] = (
    "aion-glm-local-persistence/v1"
)
LOCAL_PERSISTENCE_AUTHORIZATION_SCHEMA_VERSION: Final[
    Literal["aion-glm-local-persistence-authorization/v1"]
] = "aion-glm-local-persistence-authorization/v1"
PERSISTENCE_APPROVAL_EVIDENCE_SCHEMA_VERSION: Final[
    Literal["aion-glm-persistence-approval-evidence/v1"]
] = "aion-glm-persistence-approval-evidence/v1"
PERSISTENCE_APPROVAL_BUNDLE_SCHEMA_VERSION: Final[
    Literal["aion-glm-persistence-approval-bundle/v1"]
] = "aion-glm-persistence-approval-bundle/v1"
APPROVED_KNOWLEDGE_CONTENT_SCHEMA_VERSION: Final[
    Literal["aion-glm-approved-knowledge-content/v1"]
] = "aion-glm-approved-knowledge-content/v1"
PERSISTENT_CANDIDATE_RECEIPT_SCHEMA_VERSION: Final[
    Literal["aion-glm-persistent-candidate-receipt/v1"]
] = "aion-glm-persistent-candidate-receipt/v1"
PERSISTENT_KNOWLEDGE_IDENTITY_SCHEMA_VERSION: Final[
    Literal["aion-glm-persistent-knowledge-identity/v1"]
] = "aion-glm-persistent-knowledge-identity/v1"
PERSISTENT_KNOWLEDGE_VERSION_SCHEMA_VERSION: Final[
    Literal["aion-glm-persistent-knowledge-version/v1"]
] = "aion-glm-persistent-knowledge-version/v1"
PERSISTENT_APPROVAL_BINDING_SCHEMA_VERSION: Final[
    Literal["aion-glm-persistent-approval-binding/v1"]
] = "aion-glm-persistent-approval-binding/v1"
PERSISTENT_MEMORY_PROJECTION_SCHEMA_VERSION: Final[
    Literal["aion-glm-persistent-memory-projection/v1"]
] = "aion-glm-persistent-memory-projection/v1"
PERSISTENT_BELIEF_CANDIDATE_SCHEMA_VERSION: Final[
    Literal["aion-glm-persistent-belief-candidate/v1"]
] = "aion-glm-persistent-belief-candidate/v1"
PERSISTENCE_LEDGER_EVENT_SCHEMA_VERSION: Final[Literal["aion-glm-persistence-ledger-event/v1"]] = (
    "aion-glm-persistence-ledger-event/v1"
)
PERSISTENCE_TRANSACTION_REQUEST_SCHEMA_VERSION: Final[
    Literal["aion-glm-persistence-transaction-request/v1"]
] = "aion-glm-persistence-transaction-request/v1"
PERSISTENCE_TRANSACTION_RECEIPT_SCHEMA_VERSION: Final[
    Literal["aion-glm-persistence-transaction-receipt/v1"]
] = "aion-glm-persistence-transaction-receipt/v1"
LOCAL_KNOWLEDGE_QUERY_SCHEMA_VERSION: Final[Literal["aion-glm-local-knowledge-query/v1"]] = (
    "aion-glm-local-knowledge-query/v1"
)
LOCAL_KNOWLEDGE_QUERY_RESULT_SCHEMA_VERSION: Final[
    Literal["aion-glm-local-knowledge-query-result/v1"]
] = "aion-glm-local-knowledge-query-result/v1"
LOCAL_PROJECTION_QUERY_SCHEMA_VERSION: Final[Literal["aion-glm-local-projection-query/v1"]] = (
    "aion-glm-local-projection-query/v1"
)
LOCAL_PROJECTION_QUERY_RESULT_SCHEMA_VERSION: Final[
    Literal["aion-glm-local-projection-query-result/v1"]
] = "aion-glm-local-projection-query-result/v1"
LOCAL_STORE_INTEGRITY_SCHEMA_VERSION: Final[Literal["aion-glm-local-store-integrity/v1"]] = (
    "aion-glm-local-store-integrity/v1"
)
LOCAL_STORE_CHECKPOINT_SCHEMA_VERSION: Final[Literal["aion-glm-local-store-checkpoint/v1"]] = (
    "aion-glm-local-store-checkpoint/v1"
)
LOCAL_STORE_BACKUP_MANIFEST_SCHEMA_VERSION: Final[
    Literal["aion-glm-local-store-backup-manifest/v1"]
] = "aion-glm-local-store-backup-manifest/v1"
LOCAL_STORE_RESTORE_PLAN_SCHEMA_VERSION: Final[Literal["aion-glm-local-store-restore-plan/v1"]] = (
    "aion-glm-local-store-restore-plan/v1"
)
LOCAL_STORE_RESTORE_RESULT_SCHEMA_VERSION: Final[
    Literal["aion-glm-local-store-restore-result/v1"]
] = "aion-glm-local-store-restore-result/v1"
LOCAL_PERSISTENCE_EVIDENCE_SCHEMA_VERSION: Final[
    Literal["aion-glm-local-persistence-evidence/v1"]
] = "aion-glm-local-persistence-evidence/v1"
LOCAL_PERSISTENCE_REASON_REGISTRY_VERSION: Final[
    Literal["aion-glm-local-persistence-reasons/v1"]
] = "aion-glm-local-persistence-reasons/v1"

PROGRAM_ID: Final = "AION-GOVERNED-LEARNING-MEMORY-001"
AUTHORIZATION_TRANSACTION_ID: Final = "AION-223-GLM-0002"
APPROVAL_RECORD_ID: Final = "AION-223-GLM-0002"
IMPLEMENTATION_TASK: Final = "AION-224"
FORMAL_CLOSEOUT_TASK: Final = "AION-225"
AUTHORIZATION_SCOPE: Final = (
    "operator-approved-local-append-only-knowledge-version-store-transactional-"
    "semantic-episodic-procedural-projection-belief-candidate-record-"
    "tamper-evidence-backup-restore-core"
)
SQLITE_APPLICATION_ID: Final = 223224
SQLITE_USER_VERSION: Final = 1
ZERO_HASH: Final = "0" * 64

MODEL_CONFIG = ConfigDict(extra="forbid", hide_input_in_errors=True)
FROZEN_MODEL_CONFIG = ConfigDict(
    extra="forbid",
    hide_input_in_errors=True,
    frozen=True,
)
SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
QUANT = Decimal("0.000001")
MAXIMUM_CONTENT_BYTES_PER_KNOWLEDGE_VERSION = 16_384
MAXIMUM_SUMMARY_BYTES_PER_PROJECTION = 4_096
MAXIMUM_METADATA_BYTES_PER_RECORD = 16_384
MAXIMUM_TOTAL_TRANSACTION_BYTES = 4_194_304
MAXIMUM_QUERY_RESULTS = 1_000
MAXIMUM_APPROVAL_EVIDENCE_RECORDS_PER_TRANSACTION = 4
MINIMUM_INDEPENDENT_APPROVERS_PER_TRANSACTION = 2

PROTECTED_KEY_MARKERS = (
    "source_body",
    "source-preview",
    "source_preview",
    "raw_approval_payload",
    "raw_prompt",
    "hidden_reasoning",
    "raw_user_message",
    "credential",
    "token",
    "cookie",
    "authorization_header",
    "private_key",
    "client_certificate",
    "personal_data",
    "source_patch",
    "raw_diff",
    "shell_command",
    "executable_code",
)
PROTECTED_VALUE_MARKERS = (
    "source body",
    "source preview",
    "raw approval payload",
    "raw prompt",
    "hidden reasoning",
    "raw user message",
    "credential",
    "token:",
    "cookie:",
    "authorization:",
    "private key",
    "client certificate",
    "personal data",
    "diff --git",
    "sk-",
    "ghp_",
    "gho_",
)


class LocalPersistenceError(ValueError):
    """Raised for local persistence contract, policy, or integrity rejection."""


class LocalPersistenceMode(StrEnum):
    SYNTHETIC_TEST = "synthetic_test"
    OPERATOR_LOCAL = "operator_local"


class LocalPersistenceOperation(StrEnum):
    INITIALIZE = "initialize"
    PERSIST = "persist"
    QUERY = "query"
    AUDIT = "audit"
    CHECKPOINT = "checkpoint"
    BACKUP = "backup"
    RESTORE = "restore"


class LocalStoreStatus(StrEnum):
    INITIALIZED = "initialized"
    READY = "ready"
    INTEGRITY_FAILED = "integrity_failed"
    READ_ONLY = "read_only"
    CLOSED = "closed"


class LocalPersistenceTransactionStatus(StrEnum):
    COMMITTED = "committed"
    IDEMPOTENT_REPLAY = "idempotent_replay"
    BLOCKED = "blocked"
    ROLLED_BACK = "rolled_back"
    INTEGRITY_FAILED = "integrity_failed"


class PersistentKnowledgeEventType(StrEnum):
    INITIAL_VERSION = "initial_version"
    NEW_VERSION = "new_version"
    SUPERSESSION_MARKER = "supersession_marker"
    RETRACTION_MARKER = "retraction_marker"
    EXPIRY_MARKER = "expiry_marker"
    ROLLBACK_MARKER = "rollback_marker"


class PersistentProjectionType(StrEnum):
    SEMANTIC = "semantic"
    EPISODIC = "episodic"
    PROCEDURAL = "procedural"
    BELIEF_CANDIDATE = "belief_candidate"


class LocalStoreIntegrityStatus(StrEnum):
    PASSED = "passed"
    FAILED = "failed"


class LocalBackupStatus(StrEnum):
    CREATED = "created"
    INTEGRITY_FAILED = "integrity_failed"
    BLOCKED = "blocked"


class LocalRestoreStatus(StrEnum):
    VALIDATED = "validated"
    RESTORED_TO_NEW_STORE = "restored_to_new_store"
    BLOCKED = "blocked"
    INTEGRITY_FAILED = "integrity_failed"


PERSISTENCE_REASON_CODES: tuple[str, ...] = (
    "authorization_valid",
    "authorization_rejected",
    "path_validation_passed",
    "path_validation_failed",
    "schema_bootstrap_passed",
    "schema_mismatch",
    "approval_binding_passed",
    "approval_binding_failed",
    "dual_approval_passed",
    "dual_approval_failed",
    "content_validation_passed",
    "content_validation_failed",
    "transaction_validation_passed",
    "transaction_validation_failed",
    "idempotent_replay_detected",
    "changed_replay_rejected",
    "identity_insertion_passed",
    "identity_collision_rejected",
    "version_insertion_passed",
    "version_collision_rejected",
    "projection_insertion_passed",
    "belief_candidate_insertion_passed",
    "append_only_enforced",
    "update_rejected",
    "delete_rejected",
    "global_hash_chain_passed",
    "global_hash_chain_failed",
    "transaction_hash_chain_passed",
    "transaction_hash_chain_failed",
    "read_after_write_passed",
    "database_size_passed",
    "database_size_exceeded",
    "transaction_size_passed",
    "transaction_size_exceeded",
    "checkpoint_passed",
    "backup_passed",
    "backup_failed",
    "restore_passed",
    "restore_failed",
    "source_body_rejected",
    "sensitive_content_rejected",
    "production_memory_rejected",
    "belief_write_rejected",
    "automatic_promotion_rejected",
    "network_rejected",
    "runtime_disabled",
    "integrity_passed",
    "integrity_failed",
)
PERSISTENCE_REASON_CODE_REGISTRY = MappingProxyType(
    {code: LOCAL_PERSISTENCE_REASON_REGISTRY_VERSION for code in PERSISTENCE_REASON_CODES}
)


def _q(value: Decimal) -> Decimal:
    return value.quantize(QUANT, rounding=ROUND_HALF_UP)


def _safe_id(value: str, field_name: str = "id") -> str:
    if not SAFE_ID_RE.fullmatch(value):
        raise ValueError(f"{field_name} is not a safe bounded ID")
    return value


def _ensure_hex64(value: str, field_name: str = "fingerprint") -> str:
    return validate_hex64(value, field_name)


def _ensure_utc(value: datetime, field_name: str = "timestamp") -> datetime:
    return ensure_utc(value, field_name)


def _jsonable(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, Decimal):
        return f"{_q(value):.6f}"
    if isinstance(value, datetime):
        return _ensure_utc(value).isoformat().replace("+00:00", "Z")
    if isinstance(value, Mapping):
        return {str(key): _jsonable(nested) for key, nested in value.items()}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    return value


def persistence_fingerprint(value: Any) -> str:
    return governed_learning_memory_fingerprint(_jsonable(value))


def model_fingerprint(model: BaseModel, exclude: set[str]) -> str:
    return persistence_fingerprint(model.model_dump(mode="python", exclude=exclude))


def build_model[T: BaseModel](model: type[T], payload: Mapping[str, Any], field: str) -> T:
    base = dict(payload)
    base[field] = ZERO_HASH
    draft = model.model_construct(**base)
    base[field] = model_fingerprint(draft, {field})
    return model.model_validate(base)


def validate_persistence_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if len(value) != len(set(value)):
        raise ValueError("duplicate local persistence reason code")
    unknown = [code for code in value if code not in PERSISTENCE_REASON_CODE_REGISTRY]
    if unknown:
        raise ValueError("unknown local persistence reason code")
    return value


def reject_persistence_protected_material(value: Any, field_name: str = "payload") -> None:
    seen: set[int] = set()

    def walk(item: Any, label: str) -> None:
        ident = id(item)
        if ident in seen:
            raise ValueError(f"{label} contains recursive protected material")
        if isinstance(item, Mapping):
            seen.add(ident)
            for key, nested in item.items():
                lowered = str(key).lower().replace("-", "_")
                if any(marker in lowered for marker in PROTECTED_KEY_MARKERS):
                    raise ValueError(f"{label} contains protected material")
                walk(nested, label)
            seen.discard(ident)
        elif isinstance(item, (tuple, list, set)):
            seen.add(ident)
            for nested in item:
                walk(nested, label)
            seen.discard(ident)
        elif isinstance(item, str):
            lowered = item.lower()
            if any(marker in lowered for marker in PROTECTED_VALUE_MARKERS):
                raise ValueError(f"{label} contains protected material")
            reject_protected_material(item, label)
        elif isinstance(item, (BaseException, type(lambda: None))):
            raise ValueError(f"{label} contains executable or exception material")

    walk(value, field_name)


class StrictFrozenModel(BaseModel):
    model_config = FROZEN_MODEL_CONFIG

    @field_validator("*", mode="after", check_fields=False)
    @classmethod
    def normalize_common_fields(cls, value: Any, info: Any) -> Any:
        field_name = info.field_name or ""
        if field_name.endswith("_id") and isinstance(value, str):
            return _safe_id(value, field_name)
        if "fingerprint" in field_name and isinstance(value, str):
            return _ensure_hex64(value, field_name)
        if "fingerprint" in field_name and isinstance(value, (tuple, list)):
            return tuple(_ensure_hex64(str(item), field_name) for item in value)
        if isinstance(value, Decimal):
            return _q(value)
        if isinstance(value, datetime):
            return _ensure_utc(value, field_name)
        return value

    @field_validator("reason_codes", check_fields=False)
    @classmethod
    def reason_codes_are_known(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        return validate_persistence_reason_codes(value)


class LocalPersistenceAuthorizationEnvelope(StrictFrozenModel):
    schema_version: Literal["aion-glm-local-persistence-authorization/v1"] = (
        LOCAL_PERSISTENCE_AUTHORIZATION_SCHEMA_VERSION
    )
    authorization_transaction_id: Literal["AION-223-GLM-0002"]
    approval_record_id: Literal["AION-223-GLM-0002"]
    persistence_session_id: str
    store_id: str
    store_identity_fingerprint: str
    database_path_fingerprint: str
    operator_identity_fingerprint: str
    mode: LocalPersistenceMode
    allowed_operations: tuple[LocalPersistenceOperation, ...]
    created_at: datetime
    expires_at: datetime
    operator_invoked: Literal[True] = True
    background_execution: Literal[False] = False
    scheduled_execution: Literal[False] = False
    production_store: Literal[False] = False
    existing_memory_repository: Literal[False] = False
    automatic_initialization: Literal[False] = False
    transaction_approval_required: Literal[True] = True
    individual_transaction_persistence_approved: Literal[False] = False
    runtime_effect: Literal[False] = False
    envelope_fingerprint: str

    @model_validator(mode="after")
    def validate_envelope(self) -> Self:
        if self.expires_at <= self.created_at:
            raise ValueError("authorization envelope expires before creation")
        if self.expires_at > self.created_at + timedelta(hours=1):
            raise ValueError("authorization envelope exceeds one-hour lifetime")
        if not self.allowed_operations:
            raise ValueError("authorization envelope requires operations")
        if len(set(self.allowed_operations)) != len(self.allowed_operations):
            raise ValueError("duplicate local persistence operation")
        expected = model_fingerprint(self, {"envelope_fingerprint"})
        if self.envelope_fingerprint != expected:
            raise ValueError("authorization envelope fingerprint mismatch")
        return self


class PersistenceApprovalEvidence(StrictFrozenModel):
    schema_version: Literal["aion-glm-persistence-approval-evidence/v1"] = (
        PERSISTENCE_APPROVAL_EVIDENCE_SCHEMA_VERSION
    )
    approval_evidence_id: str
    role: Literal["knowledge_steward", "memory_operator"]
    approval_request_id: str
    approval_decision_id: str
    action_type: Literal[
        "governed_learning_memory.persist_local_knowledge_version",
        "governed_learning_memory.persist_local_memory_projection",
    ]
    approval_scope_fingerprint: str
    request_fingerprint: str
    decision_fingerprint: str
    approver_identity_fingerprint: str
    requester_identity_fingerprint: str
    transaction_id: str
    store_identity_fingerprint: str
    database_path_fingerprint: str
    promotion_request_fingerprint: str
    promotion_plan_fingerprint: str
    promotion_result_fingerprint: str
    knowledge_identity_ids: tuple[str, ...]
    knowledge_version_plan_fingerprints: tuple[str, ...]
    memory_projection_fingerprints: tuple[str, ...]
    approved_content_fingerprints: tuple[str, ...]
    backup_policy_fingerprint: str
    transaction_binding_fingerprint: str
    decided_at: datetime
    expires_at: datetime
    revoked_at: datetime | None = None
    evidence_origin: Literal["operator_supplied_existing_approval"] = (
        "operator_supplied_existing_approval"
    )
    approval_creation_performed_by_aion224: Literal[False] = False
    approval_decision_performed_by_aion224: Literal[False] = False
    raw_payload_persisted: Literal[False] = False
    read_only: Literal[True] = True
    redacted: Literal[True] = True
    runtime_effect: Literal[False] = False
    evidence_fingerprint: str

    @model_validator(mode="after")
    def validate_evidence(self) -> Self:
        if self.revoked_at is not None:
            raise ValueError("revoked persistence approval evidence is rejected")
        if self.expires_at <= self.decided_at:
            raise ValueError("persistence approval is expired")
        if self.approver_identity_fingerprint == self.requester_identity_fingerprint:
            raise ValueError("requester and approver must differ")
        if not self.knowledge_identity_ids:
            raise ValueError("approval evidence requires knowledge identity binding")
        expected = model_fingerprint(self, {"evidence_fingerprint"})
        if self.evidence_fingerprint != expected:
            raise ValueError("persistence approval evidence fingerprint mismatch")
        return self


class PersistenceApprovalBundle(StrictFrozenModel):
    schema_version: Literal["aion-glm-persistence-approval-bundle/v1"] = (
        PERSISTENCE_APPROVAL_BUNDLE_SCHEMA_VERSION
    )
    approval_bundle_id: str
    evidence_records: tuple[PersistenceApprovalEvidence, ...]
    independent_approver_fingerprints: tuple[str, ...]
    independent_approver_count: int = Field(ge=0, le=4)
    required_approver_count: Literal[2] = 2
    required_roles: tuple[Literal["knowledge_steward", "memory_operator"], ...]
    roles_present: tuple[Literal["knowledge_steward", "memory_operator"], ...]
    separation_of_duties_passed: bool
    plan_approval_can_authorize_persistence: Literal[False] = False
    approval_status: Literal["valid", "invalid"]
    reason_codes: tuple[str, ...]
    bundle_fingerprint: str
    redacted: Literal[True] = True
    runtime_effect: Literal[False] = False

    @model_validator(mode="after")
    def validate_bundle(self) -> Self:
        if len(self.evidence_records) > MAXIMUM_APPROVAL_EVIDENCE_RECORDS_PER_TRANSACTION:
            raise ValueError("too many persistence approval evidence records")
        roles = tuple(sorted({record.role for record in self.evidence_records}))
        approvers = tuple(
            sorted({record.approver_identity_fingerprint for record in self.evidence_records})
        )
        if self.roles_present != roles:
            raise ValueError("approval role summary mismatch")
        if self.independent_approver_fingerprints != approvers:
            raise ValueError("approval approver summary mismatch")
        if self.independent_approver_count != len(approvers):
            raise ValueError("approval approver count mismatch")
        passed = (
            self.independent_approver_count >= MINIMUM_INDEPENDENT_APPROVERS_PER_TRANSACTION
            and set(roles) == {"knowledge_steward", "memory_operator"}
        )
        if self.separation_of_duties_passed is not passed:
            raise ValueError("approval separation-of-duties mismatch")
        expected = model_fingerprint(self, {"bundle_fingerprint"})
        if self.bundle_fingerprint != expected:
            raise ValueError("persistence approval bundle fingerprint mismatch")
        return self


def _approval_projection_fingerprint(payload: Mapping[str, Any]) -> str:
    return persistence_fingerprint(payload)


def project_existing_persistence_approval_evidence(
    approval_request: ApprovalRequest,
    approval_decision: ApprovalDecision,
    *,
    approval_evidence_id: str,
    role: Literal["knowledge_steward", "memory_operator"],
    transaction_id: str,
    store_identity_fingerprint: str,
    database_path_fingerprint: str,
    promotion_request_fingerprint: str,
    promotion_plan_fingerprint: str,
    promotion_result_fingerprint: str,
    knowledge_identity_ids: tuple[str, ...],
    knowledge_version_plan_fingerprints: tuple[str, ...],
    memory_projection_fingerprints: tuple[str, ...],
    approved_content_fingerprints: tuple[str, ...],
    backup_policy_fingerprint: str,
    observed_at: datetime,
    revoked_at: datetime | None = None,
) -> PersistenceApprovalEvidence:
    if approval_request.approval_request_id != approval_decision.approval_request_id:
        raise ValueError("approval request and decision ID mismatch")
    if approval_request.status != "approved" or approval_decision.decision != "approve":
        raise ValueError("persistence approval requires approved decision")
    required_action = {
        "knowledge_steward": "governed_learning_memory.persist_local_knowledge_version",
        "memory_operator": "governed_learning_memory.persist_local_memory_projection",
    }[role]
    required_scope = {
        "knowledge_steward": "governed-learning-memory:persist-local-knowledge",
        "memory_operator": "governed-learning-memory:persist-local-projection",
    }[role]
    if approval_request.action_type != required_action:
        raise ValueError("persistence approval action type mismatch")
    if required_scope not in approval_request.approval_scope:
        raise ValueError("persistence approval scope mismatch")
    if approval_request.resource_type != "promotion_transaction_result":
        raise ValueError("persistence approval resource type mismatch")
    if approval_request.resource_id not in {transaction_id, promotion_result_fingerprint}:
        raise ValueError("persistence approval resource binding mismatch")
    observed_at = _ensure_utc(observed_at)
    requested_at = _ensure_utc(approval_request.created_at or observed_at)
    decided_at = _ensure_utc(approval_decision.created_at or observed_at)
    expires_at = _ensure_utc(approval_request.expires_at or (requested_at + timedelta(hours=1)))
    if expires_at <= observed_at or revoked_at is not None:
        raise ValueError("persistence approval expired or revoked")
    payload = approval_request.payload
    reject_persistence_protected_material(payload, "approval_payload")
    expected_payload = {
        "persistence_role": role,
        "store_identity_fingerprint": store_identity_fingerprint,
        "database_path_fingerprint": database_path_fingerprint,
        "transaction_id": transaction_id,
        "promotion_request_fingerprint": promotion_request_fingerprint,
        "promotion_plan_fingerprint": promotion_plan_fingerprint,
        "promotion_result_fingerprint": promotion_result_fingerprint,
        "knowledge_identity_ids": list(knowledge_identity_ids),
        "knowledge_version_plan_fingerprints": list(knowledge_version_plan_fingerprints),
        "memory_projection_fingerprints": list(memory_projection_fingerprints),
        "approved_content_fingerprints": list(approved_content_fingerprints),
        "backup_policy_fingerprint": backup_policy_fingerprint,
    }
    for key, expected in expected_payload.items():
        if payload.get(key) != expected:
            raise ValueError("persistence approval payload binding mismatch")
    requester = approval_request.requested_by or approval_request.actor_id or "requester"
    approver = approval_decision.decided_by or approval_request.assigned_to or "approver"
    request_fp = _approval_projection_fingerprint(
        {
            "approval_request_id": approval_request.approval_request_id,
            "action_type": approval_request.action_type,
            "resource_type": approval_request.resource_type,
            "resource_id": approval_request.resource_id,
            "approval_scope": sorted(approval_request.approval_scope),
            "status": approval_request.status,
            "payload_fingerprint": persistence_fingerprint(expected_payload),
        }
    )
    decision_fp = _approval_projection_fingerprint(
        {
            "approval_decision_id": approval_decision.approval_decision_id,
            "approval_request_id": approval_decision.approval_request_id,
            "decision": approval_decision.decision,
            "decided_by": approver,
        }
    )
    binding_fp = persistence_fingerprint(expected_payload)
    return build_model(
        PersistenceApprovalEvidence,
        {
            "approval_evidence_id": approval_evidence_id,
            "role": role,
            "approval_request_id": approval_request.approval_request_id,
            "approval_decision_id": approval_decision.approval_decision_id,
            "action_type": required_action,
            "approval_scope_fingerprint": persistence_fingerprint((required_scope,)),
            "request_fingerprint": request_fp,
            "decision_fingerprint": decision_fp,
            "approver_identity_fingerprint": persistence_fingerprint(approver),
            "requester_identity_fingerprint": persistence_fingerprint(requester),
            "transaction_id": transaction_id,
            "store_identity_fingerprint": store_identity_fingerprint,
            "database_path_fingerprint": database_path_fingerprint,
            "promotion_request_fingerprint": promotion_request_fingerprint,
            "promotion_plan_fingerprint": promotion_plan_fingerprint,
            "promotion_result_fingerprint": promotion_result_fingerprint,
            "knowledge_identity_ids": tuple(sorted(knowledge_identity_ids)),
            "knowledge_version_plan_fingerprints": tuple(
                sorted(knowledge_version_plan_fingerprints)
            ),
            "memory_projection_fingerprints": tuple(sorted(memory_projection_fingerprints)),
            "approved_content_fingerprints": tuple(sorted(approved_content_fingerprints)),
            "backup_policy_fingerprint": backup_policy_fingerprint,
            "transaction_binding_fingerprint": binding_fp,
            "decided_at": decided_at,
            "expires_at": expires_at,
            "revoked_at": revoked_at,
        },
        "evidence_fingerprint",
    )


def build_persistence_approval_bundle(
    *,
    approval_bundle_id: str,
    evidence_records: tuple[PersistenceApprovalEvidence, ...],
) -> PersistenceApprovalBundle:
    roles = tuple(sorted({record.role for record in evidence_records}))
    approvers = tuple(sorted({record.approver_identity_fingerprint for record in evidence_records}))
    passed = len(approvers) >= 2 and set(roles) == {"knowledge_steward", "memory_operator"}
    return build_model(
        PersistenceApprovalBundle,
        {
            "approval_bundle_id": approval_bundle_id,
            "evidence_records": tuple(
                sorted(evidence_records, key=lambda item: item.approval_evidence_id)
            ),
            "independent_approver_fingerprints": approvers,
            "independent_approver_count": len(approvers),
            "required_roles": ("knowledge_steward", "memory_operator"),
            "roles_present": roles,
            "separation_of_duties_passed": passed,
            "approval_status": "valid" if passed else "invalid",
            "reason_codes": (
                "dual_approval_passed" if passed else "dual_approval_failed",
                "approval_binding_passed" if passed else "approval_binding_failed",
            ),
        },
        "bundle_fingerprint",
    )


class ApprovedKnowledgeContentEnvelope(StrictFrozenModel):
    schema_version: Literal["aion-glm-approved-knowledge-content/v1"] = (
        APPROVED_KNOWLEDGE_CONTENT_SCHEMA_VERSION
    )
    content_envelope_id: str
    knowledge_identity_id: str
    candidate_id: str
    candidate_fingerprint: str
    candidate_kind: str
    canonical_statement: str = Field(min_length=1)
    bounded_summary: str = Field(min_length=1)
    language_code: str = Field(pattern=r"^[a-z]{2,3}(-[A-Z]{2})?$")
    sensitivity: Literal["public", "internal"]
    content_fingerprint: str
    lineage_fingerprint: str
    transaction_plan_fingerprint: str
    transaction_result_fingerprint: str
    persistence_approval_bundle_fingerprint: str
    explicitly_operator_supplied: Literal[True] = True
    model_generated: Literal[False] = False
    source_body: Literal[False] = False
    source_preview: Literal[False] = False
    raw_prompt: Literal[False] = False
    hidden_reasoning: Literal[False] = False
    redacted: Literal[True] = True
    created_at: datetime
    expires_at: datetime
    envelope_fingerprint: str

    @field_validator("canonical_statement", "bounded_summary")
    @classmethod
    def content_is_bounded_and_safe(cls, value: str, info: Any) -> str:
        limit = 4_096 if info.field_name == "canonical_statement" else 2_048
        if len(value.encode("utf-8")) > limit:
            raise ValueError("approved content exceeds byte limit")
        reject_persistence_protected_material(value, info.field_name or "content")
        return value

    @model_validator(mode="after")
    def validate_content_envelope(self) -> Self:
        if self.expires_at <= self.created_at:
            raise ValueError("content envelope expires before creation")
        if (
            len(self.model_dump_json().encode("utf-8"))
            > MAXIMUM_CONTENT_BYTES_PER_KNOWLEDGE_VERSION
        ):
            raise ValueError("content envelope exceeds record byte limit")
        expected_content = persistence_fingerprint(
            {
                "knowledge_identity_id": self.knowledge_identity_id,
                "candidate_id": self.candidate_id,
                "candidate_fingerprint": self.candidate_fingerprint,
                "canonical_statement": self.canonical_statement,
                "bounded_summary": self.bounded_summary,
                "language_code": self.language_code,
                "sensitivity": self.sensitivity,
            }
        )
        if self.content_fingerprint != expected_content:
            raise ValueError("approved content fingerprint mismatch")
        expected = model_fingerprint(self, {"envelope_fingerprint"})
        if self.envelope_fingerprint != expected:
            raise ValueError("approved content envelope fingerprint mismatch")
        return self


class PersistentApprovalBinding(StrictFrozenModel):
    schema_version: Literal["aion-glm-persistent-approval-binding/v1"] = (
        PERSISTENT_APPROVAL_BINDING_SCHEMA_VERSION
    )
    binding_id: str
    transaction_id: str
    role: str
    action_type: str
    approval_scope_fingerprint: str
    request_fingerprint: str
    decision_fingerprint: str
    approver_identity_fingerprint: str
    transaction_binding_fingerprint: str
    persisted_raw_payload: Literal[False] = False
    binding_fingerprint: str
    redacted: Literal[True] = True
    runtime_effect: Literal[False] = False


class PersistentCandidateEvidenceReceipt(StrictFrozenModel):
    schema_version: Literal["aion-glm-persistent-candidate-receipt/v1"] = (
        PERSISTENT_CANDIDATE_RECEIPT_SCHEMA_VERSION
    )
    candidate_receipt_id: str
    transaction_id: str
    candidate_id: str
    candidate_fingerprint: str
    lineage_fingerprint: str
    eligibility_fingerprint: str
    candidate_integrity_fingerprint: str
    promotion_plan_fingerprint: str
    promotion_result_fingerprint: str
    candidate_body_persisted: Literal[False] = False
    receipt_fingerprint: str
    redacted: Literal[True] = True
    runtime_effect: Literal[False] = False


class PersistentKnowledgeIdentity(StrictFrozenModel):
    schema_version: Literal["aion-glm-persistent-knowledge-identity/v1"] = (
        PERSISTENT_KNOWLEDGE_IDENTITY_SCHEMA_VERSION
    )
    knowledge_identity_id: str
    claim_identity_fingerprint: str
    valid_time_fingerprint: str
    jurisdiction_fingerprint: str
    version_scope_fingerprint: str
    created_transaction_id: str
    identity_fingerprint: str
    redacted: Literal[True] = True
    runtime_effect: Literal[False] = False


class PersistentKnowledgeVersion(StrictFrozenModel):
    schema_version: Literal["aion-glm-persistent-knowledge-version/v1"] = (
        PERSISTENT_KNOWLEDGE_VERSION_SCHEMA_VERSION
    )
    knowledge_version_id: str
    knowledge_identity_id: str
    version_number: int = Field(ge=1, le=100)
    event_type: PersistentKnowledgeEventType
    candidate_posture: str
    candidate_id: str
    approved_bounded_statement: str
    bounded_summary: str
    language_code: str
    sensitivity: Literal["public", "internal"]
    content_fingerprint: str
    candidate_fingerprint: str
    lineage_fingerprint: str
    approval_bundle_fingerprint: str
    promotion_plan_fingerprint: str
    promotion_result_fingerprint: str
    confidence_cap: Decimal = Field(ge=Decimal("0.000000"), le=Decimal("1.000000"))
    valid_from: datetime
    valid_to: datetime | None = None
    supersedes_version_id: str | None = None
    retracts_version_id: str | None = None
    expires_version_id: str | None = None
    created_transaction_id: str
    version_fingerprint: str
    redacted: Literal[True] = True
    runtime_effect: Literal[False] = False

    @field_validator("approved_bounded_statement", "bounded_summary")
    @classmethod
    def persisted_text_is_safe(cls, value: str, info: Any) -> str:
        reject_persistence_protected_material(value, info.field_name or "persisted_content")
        return value


class PersistentMemoryProjectionRecord(StrictFrozenModel):
    schema_version: Literal["aion-glm-persistent-memory-projection/v1"] = (
        PERSISTENT_MEMORY_PROJECTION_SCHEMA_VERSION
    )
    projection_record_id: str
    projection_type: Literal["semantic", "episodic", "procedural"]
    transaction_id: str
    knowledge_identity_id: str
    knowledge_version_id: str
    content_reference_fingerprint: str
    summary: str
    confidence_cap: Decimal = Field(ge=Decimal("0.000000"), le=Decimal("1.000000"))
    sensitivity: Literal["public", "internal"]
    owner_scope_fingerprints: tuple[str, ...]
    provenance_fingerprints: tuple[str, ...]
    projection_fingerprint: str
    created_transaction_id: str
    production_memory_written: Literal[False] = False
    redacted: Literal[True] = True
    runtime_effect: Literal[False] = False

    @field_validator("summary")
    @classmethod
    def summary_is_bounded_and_safe(cls, value: str) -> str:
        if len(value.encode("utf-8")) > MAXIMUM_SUMMARY_BYTES_PER_PROJECTION:
            raise ValueError("projection summary exceeds byte limit")
        reject_persistence_protected_material(value, "projection_summary")
        return value


class PersistentBeliefProjectionCandidateRecord(StrictFrozenModel):
    schema_version: Literal["aion-glm-persistent-belief-candidate/v1"] = (
        PERSISTENT_BELIEF_CANDIDATE_SCHEMA_VERSION
    )
    belief_candidate_id: str
    transaction_id: str
    knowledge_identity_id: str
    knowledge_version_id: str
    proposed_posture: str
    confidence_cap: Decimal = Field(ge=Decimal("0.000000"), le=Decimal("1.000000"))
    uncertainty_fingerprint: str
    contradiction_fingerprint: str
    provenance_fingerprints: tuple[str, ...]
    candidate_fingerprint: str
    actual_belief_created: Literal[False] = False
    actual_belief_mutated: Literal[False] = False
    redacted: Literal[True] = True
    runtime_effect: Literal[False] = False


class PersistenceLedgerEvent(StrictFrozenModel):
    schema_version: Literal["aion-glm-persistence-ledger-event/v1"] = (
        PERSISTENCE_LEDGER_EVENT_SCHEMA_VERSION
    )
    global_sequence: int = Field(ge=1)
    transaction_id: str
    transaction_sequence: int = Field(ge=1)
    event_type: str
    record_type: str
    record_id: str
    record_fingerprint: str
    previous_global_hash: str
    global_event_hash: str
    previous_transaction_hash: str
    transaction_event_hash: str
    created_at: datetime


class PersistenceTransactionRequest(StrictFrozenModel):
    schema_version: Literal["aion-glm-persistence-transaction-request/v1"] = (
        PERSISTENCE_TRANSACTION_REQUEST_SCHEMA_VERSION
    )
    persistence_request_id: str
    persistence_session_id: str
    store_id: str
    store_identity_fingerprint: str
    database_path_fingerprint: str
    local_authorization_envelope: LocalPersistenceAuthorizationEnvelope
    promotion_transaction_plan: PromotionTransactionPlan
    promotion_transaction_result: PromotionTransactionResult
    persistence_approval_bundle: PersistenceApprovalBundle
    approved_content_envelopes: tuple[ApprovedKnowledgeContentEnvelope, ...]
    requested_at: datetime
    expires_at: datetime
    operator_invoked: Literal[True] = True
    background_execution: Literal[False] = False
    automatic_promotion: Literal[False] = False
    production_memory_write_requested: Literal[False] = False
    actual_belief_write_requested: Literal[False] = False
    request_fingerprint: str

    @model_validator(mode="after")
    def validate_request(self) -> Self:
        if self.expires_at <= self.requested_at:
            raise ValueError("persistence request expires before request time")
        envelope = self.local_authorization_envelope
        plan = self.promotion_transaction_plan
        result = self.promotion_transaction_result
        if self.store_id != envelope.store_id:
            raise ValueError("request store ID does not match authorization")
        if self.store_identity_fingerprint != envelope.store_identity_fingerprint:
            raise ValueError("request store fingerprint does not match authorization")
        if self.database_path_fingerprint != envelope.database_path_fingerprint:
            raise ValueError("request path fingerprint does not match authorization")
        if plan.transaction_id != result.transaction_id:
            raise ValueError("promotion plan/result transaction mismatch")
        if result.status is not PromotionTransactionStatus.DRY_RUN_PASSED:
            raise ValueError("only dry_run_passed results can be persisted")
        if result.ready_for_future_persistence_review is not True:
            raise ValueError("result is not ready for future persistence review")
        if result.future_persistence_authorized is not False:
            raise ValueError("AION-222 result cannot authorize persistence")
        if audit_promotion_transaction_plan(plan).status.value != "passed":
            raise ValueError("promotion plan audit failed")
        if audit_promotion_transaction_result(result).status.value != "passed":
            raise ValueError("promotion result audit failed")
        if not plan.rollback_plan.valid or not plan.compensation_plan.valid:
            raise ValueError("rollback and compensation lineage must be valid")
        bundle = self.persistence_approval_bundle
        if not bundle.separation_of_duties_passed:
            raise ValueError("persistence request requires dual approval")
        if any(
            record.transaction_id != plan.transaction_id
            or record.store_identity_fingerprint != self.store_identity_fingerprint
            or record.database_path_fingerprint != self.database_path_fingerprint
            or record.promotion_request_fingerprint != plan.promotion_request.request_fingerprint
            or record.promotion_plan_fingerprint != plan.transaction_plan_fingerprint
            or record.promotion_result_fingerprint != result.result_fingerprint
            for record in bundle.evidence_records
        ):
            raise ValueError("persistence approval binding mismatch")
        identity_ids = {plan.knowledge_identity_id for plan in plan.knowledge_identity_plans}
        content_by_identity = {
            envelope.knowledge_identity_id: envelope for envelope in self.approved_content_envelopes
        }
        if set(content_by_identity) != identity_ids:
            raise ValueError("approved content envelopes must match knowledge identities")
        content_fps = tuple(
            sorted(item.content_fingerprint for item in content_by_identity.values())
        )
        if any(
            tuple(sorted(record.approved_content_fingerprints)) != content_fps
            for record in bundle.evidence_records
        ):
            raise ValueError("approved content fingerprints do not match approvals")
        if len(self.model_dump_json().encode("utf-8")) > MAXIMUM_TOTAL_TRANSACTION_BYTES:
            raise ValueError("persistence transaction exceeds byte limit")
        expected = model_fingerprint(self, {"request_fingerprint"})
        if self.request_fingerprint != expected:
            raise ValueError("persistence request fingerprint mismatch")
        return self


class PersistenceTransactionReceipt(StrictFrozenModel):
    schema_version: Literal["aion-glm-persistence-transaction-receipt/v1"] = (
        PERSISTENCE_TRANSACTION_RECEIPT_SCHEMA_VERSION
    )
    receipt_id: str
    store_id: str
    store_identity_fingerprint: str
    database_path_fingerprint: str
    transaction_id: str
    promotion_request_fingerprint: str
    promotion_plan_fingerprint: str
    promotion_result_fingerprint: str
    persistence_approval_bundle_fingerprint: str
    knowledge_identity_ids: tuple[str, ...]
    knowledge_version_ids: tuple[str, ...]
    projection_record_ids: tuple[str, ...]
    belief_candidate_record_ids: tuple[str, ...]
    candidate_receipt_ids: tuple[str, ...]
    approval_binding_ids: tuple[str, ...]
    row_counts: Mapping[str, int]
    ledger_start_sequence: int = Field(ge=0)
    ledger_end_sequence: int = Field(ge=0)
    ledger_head_before: str
    ledger_head_after: str
    transaction_chain_head: str
    idempotent_replay: bool
    isolated_local_persistence_applied: bool
    production_memory_written: Literal[False] = False
    actual_belief_created: Literal[False] = False
    actual_belief_mutated: Literal[False] = False
    automatic_promotion_applied: Literal[False] = False
    read_after_write_verified: bool
    integrity_status: LocalStoreIntegrityStatus
    created_at: datetime
    receipt_fingerprint: str
    redacted: Literal[True] = True
    runtime_effect: Literal[False] = False

    @model_validator(mode="after")
    def validate_receipt(self) -> Self:
        expected = model_fingerprint(self, {"receipt_fingerprint"})
        if self.receipt_fingerprint != expected:
            raise ValueError("persistence receipt fingerprint mismatch")
        return self


class LocalKnowledgeQuery(StrictFrozenModel):
    schema_version: Literal["aion-glm-local-knowledge-query/v1"] = (
        LOCAL_KNOWLEDGE_QUERY_SCHEMA_VERSION
    )
    store_id: str | None = None
    transaction_id: str | None = None
    knowledge_identity_id: str | None = None
    knowledge_version_id: str | None = None
    version_number: int | None = Field(default=None, ge=1)
    candidate_id: str | None = None
    candidate_fingerprint: str | None = None
    candidate_posture: str | None = None
    content_fingerprint: str | None = None
    event_type: PersistentKnowledgeEventType | None = None
    created_from: datetime | None = None
    created_to: datetime | None = None
    limit: int = Field(default=100, ge=1, le=MAXIMUM_QUERY_RESULTS)
    query_fingerprint: str

    @model_validator(mode="after")
    def validate_query(self) -> Self:
        if self.created_from and self.created_to and self.created_to < self.created_from:
            raise ValueError("knowledge query time range invalid")
        expected = model_fingerprint(self, {"query_fingerprint"})
        if self.query_fingerprint != expected:
            raise ValueError("knowledge query fingerprint mismatch")
        return self


class LocalKnowledgeQueryResult(StrictFrozenModel):
    schema_version: Literal["aion-glm-local-knowledge-query-result/v1"] = (
        LOCAL_KNOWLEDGE_QUERY_RESULT_SCHEMA_VERSION
    )
    query_fingerprint: str
    records: tuple[PersistentKnowledgeVersion, ...]
    result_count: int = Field(ge=0, le=MAXIMUM_QUERY_RESULTS)
    evidence_bound: Literal[True] = True
    implies_absolute_truth: Literal[False] = False
    result_fingerprint: str
    redacted: Literal[True] = True
    runtime_effect: Literal[False] = False

    @model_validator(mode="after")
    def validate_result(self) -> Self:
        if self.result_count != len(self.records):
            raise ValueError("knowledge query result count mismatch")
        expected = model_fingerprint(self, {"result_fingerprint"})
        if self.result_fingerprint != expected:
            raise ValueError("knowledge query result fingerprint mismatch")
        return self


class LocalProjectionQuery(StrictFrozenModel):
    schema_version: Literal["aion-glm-local-projection-query/v1"] = (
        LOCAL_PROJECTION_QUERY_SCHEMA_VERSION
    )
    projection_record_id: str | None = None
    transaction_id: str | None = None
    knowledge_identity_id: str | None = None
    knowledge_version_id: str | None = None
    projection_type: PersistentProjectionType | None = None
    projection_fingerprint: str | None = None
    limit: int = Field(default=100, ge=1, le=MAXIMUM_QUERY_RESULTS)
    query_fingerprint: str

    @model_validator(mode="after")
    def validate_query(self) -> Self:
        expected = model_fingerprint(self, {"query_fingerprint"})
        if self.query_fingerprint != expected:
            raise ValueError("projection query fingerprint mismatch")
        return self


class LocalProjectionQueryResult(StrictFrozenModel):
    schema_version: Literal["aion-glm-local-projection-query-result/v1"] = (
        LOCAL_PROJECTION_QUERY_RESULT_SCHEMA_VERSION
    )
    query_fingerprint: str
    memory_projection_records: tuple[PersistentMemoryProjectionRecord, ...]
    belief_candidate_records: tuple[PersistentBeliefProjectionCandidateRecord, ...]
    result_count: int = Field(ge=0, le=MAXIMUM_QUERY_RESULTS)
    evidence_bound: Literal[True] = True
    implies_production_memory_write: Literal[False] = False
    implies_actual_belief: Literal[False] = False
    result_fingerprint: str
    redacted: Literal[True] = True
    runtime_effect: Literal[False] = False

    @model_validator(mode="after")
    def validate_result(self) -> Self:
        total = len(self.memory_projection_records) + len(self.belief_candidate_records)
        if self.result_count != total:
            raise ValueError("projection query result count mismatch")
        expected = model_fingerprint(self, {"result_fingerprint"})
        if self.result_fingerprint != expected:
            raise ValueError("projection query result fingerprint mismatch")
        return self


class LocalStoreIntegrityFinding(StrictFrozenModel):
    finding_id: str
    status: LocalStoreIntegrityStatus
    reason_codes: tuple[str, ...]
    safe_ids: tuple[str, ...] = ()
    fingerprints: tuple[str, ...] = ()
    bounded_count: int = Field(default=0, ge=0)
    redacted_summary: str = "redacted local persistence finding"
    finding_fingerprint: str
    redacted: Literal[True] = True
    runtime_effect: Literal[False] = False

    @model_validator(mode="after")
    def validate_finding(self) -> Self:
        expected = model_fingerprint(self, {"finding_fingerprint"})
        if self.finding_fingerprint != expected:
            raise ValueError("integrity finding fingerprint mismatch")
        return self


class LocalStoreIntegrityReport(StrictFrozenModel):
    schema_version: Literal["aion-glm-local-store-integrity/v1"] = (
        LOCAL_STORE_INTEGRITY_SCHEMA_VERSION
    )
    report_id: str
    store_id: str
    status: LocalStoreIntegrityStatus
    findings: tuple[LocalStoreIntegrityFinding, ...]
    finding_count: int = Field(ge=0, le=1_000)
    global_hash_chain_passed: bool
    transaction_hash_chain_passed: bool
    append_only_triggers_present: bool
    no_prohibited_content: bool
    no_production_memory_markers: bool
    no_actual_belief_markers: bool
    no_automatic_promotion_markers: bool
    report_fingerprint: str
    redacted: Literal[True] = True
    runtime_effect: Literal[False] = False

    @model_validator(mode="after")
    def validate_report(self) -> Self:
        if self.finding_count != len(self.findings):
            raise ValueError("integrity report finding count mismatch")
        expected_status = (
            LocalStoreIntegrityStatus.PASSED
            if all(finding.status is LocalStoreIntegrityStatus.PASSED for finding in self.findings)
            and self.global_hash_chain_passed
            and self.transaction_hash_chain_passed
            and self.append_only_triggers_present
            and self.no_prohibited_content
            and self.no_production_memory_markers
            and self.no_actual_belief_markers
            and self.no_automatic_promotion_markers
            else LocalStoreIntegrityStatus.FAILED
        )
        if self.status is not expected_status:
            raise ValueError("integrity report status mismatch")
        expected = model_fingerprint(self, {"report_fingerprint"})
        if self.report_fingerprint != expected:
            raise ValueError("integrity report fingerprint mismatch")
        return self


class LocalStoreCheckpoint(StrictFrozenModel):
    schema_version: Literal["aion-glm-local-store-checkpoint/v1"] = (
        LOCAL_STORE_CHECKPOINT_SCHEMA_VERSION
    )
    checkpoint_id: str
    store_id: str
    ledger_head: str
    last_ledger_sequence: int = Field(ge=0)
    checkpoint_mode: Literal["FULL"]
    sqlite_checkpoint_result: tuple[int, int, int]
    database_fingerprint: str
    created_at: datetime
    checkpoint_fingerprint: str
    operator_invoked: Literal[True] = True
    runtime_effect: Literal[False] = False

    @model_validator(mode="after")
    def validate_checkpoint(self) -> Self:
        expected = model_fingerprint(self, {"checkpoint_fingerprint"})
        if self.checkpoint_fingerprint != expected:
            raise ValueError("checkpoint fingerprint mismatch")
        return self


class LocalStoreBackupManifest(StrictFrozenModel):
    schema_version: Literal["aion-glm-local-store-backup-manifest/v1"] = (
        LOCAL_STORE_BACKUP_MANIFEST_SCHEMA_VERSION
    )
    backup_manifest_id: str
    store_id: str
    store_identity_fingerprint: str
    schema_version_value: str
    application_id: Literal[223224]
    last_ledger_sequence: int = Field(ge=0)
    ledger_head_hash: str
    source_database_fingerprint: str
    backup_database_fingerprint: str
    backup_path_fingerprint: str
    backup_size: int = Field(ge=0, le=1_073_741_824)
    created_at: datetime
    integrity_status: LocalBackupStatus
    manifest_fingerprint: str
    redacted: Literal[True] = True
    runtime_effect: Literal[False] = False

    @model_validator(mode="after")
    def validate_manifest(self) -> Self:
        expected = model_fingerprint(self, {"manifest_fingerprint"})
        if self.manifest_fingerprint != expected:
            raise ValueError("backup manifest fingerprint mismatch")
        return self


class LocalStoreRestorePlan(StrictFrozenModel):
    schema_version: Literal["aion-glm-local-store-restore-plan/v1"] = (
        LOCAL_STORE_RESTORE_PLAN_SCHEMA_VERSION
    )
    restore_plan_id: str
    backup_manifest_id: str
    backup_database_fingerprint: str
    backup_path_fingerprint: str
    destination_path_fingerprint: str
    target_new_absent_path: Literal[True] = True
    overwrite_existing_store: Literal[False] = False
    switch_active_store_automatically: Literal[False] = False
    created_at: datetime
    plan_fingerprint: str
    runtime_effect: Literal[False] = False

    @model_validator(mode="after")
    def validate_plan(self) -> Self:
        expected = model_fingerprint(self, {"plan_fingerprint"})
        if self.plan_fingerprint != expected:
            raise ValueError("restore plan fingerprint mismatch")
        return self


class LocalStoreRestoreResult(StrictFrozenModel):
    schema_version: Literal["aion-glm-local-store-restore-result/v1"] = (
        LOCAL_STORE_RESTORE_RESULT_SCHEMA_VERSION
    )
    restore_result_id: str
    restore_plan_id: str
    store_id: str
    status: LocalRestoreStatus
    source_manifest_fingerprint: str
    restored_database_fingerprint: str
    restored_path_fingerprint: str
    restored_ledger_head_hash: str
    restored_last_ledger_sequence: int = Field(ge=0)
    integrity_status: LocalStoreIntegrityStatus
    active_store_switched: Literal[False] = False
    created_at: datetime
    result_fingerprint: str
    redacted: Literal[True] = True
    runtime_effect: Literal[False] = False

    @model_validator(mode="after")
    def validate_result(self) -> Self:
        expected = model_fingerprint(self, {"result_fingerprint"})
        if self.result_fingerprint != expected:
            raise ValueError("restore result fingerprint mismatch")
        return self


class LocalPersistenceIncident(StrictFrozenModel):
    schema_version: Literal["aion-glm-local-persistence-evidence/v1"] = (
        LOCAL_PERSISTENCE_EVIDENCE_SCHEMA_VERSION
    )
    incident_id: str
    severity_code: str
    reason_codes: tuple[str, ...]
    safe_ids: tuple[str, ...]
    fingerprints: tuple[str, ...]
    created_at: datetime
    incident_fingerprint: str
    redacted: Literal[True] = True
    runtime_effect: Literal[False] = False

    @model_validator(mode="after")
    def validate_incident(self) -> Self:
        expected = model_fingerprint(self, {"incident_fingerprint"})
        if self.incident_fingerprint != expected:
            raise ValueError("incident fingerprint mismatch")
        return self


class LocalPersistenceOperatorReviewItem(StrictFrozenModel):
    review_item_id: str
    transaction_id: str
    reason_codes: tuple[str, ...]
    operator_review_required: Literal[True] = True
    persisted_record_is_not_absolute_truth: Literal[True] = True
    approval_is_not_factual_proof: Literal[True] = True
    isolated_store_is_not_production_memory: Literal[True] = True
    belief_candidate_is_not_belief_creation: Literal[True] = True
    automatic_promotion_authorized: Literal[False] = False
    production_memory_write_authorized: Literal[False] = False
    background_persistence_authorized: Literal[False] = False
    network_access_authorized: Literal[False] = False
    approval_created: Literal[False] = False
    new_implementation_authorization_created: Literal[False] = False
    review_fingerprint: str
    redacted: Literal[True] = True
    runtime_effect: Literal[False] = False

    @model_validator(mode="after")
    def validate_review_item(self) -> Self:
        expected = model_fingerprint(self, {"review_fingerprint"})
        if self.review_fingerprint != expected:
            raise ValueError("operator review fingerprint mismatch")
        return self


class LocalPersistenceEvidenceBundle(StrictFrozenModel):
    schema_version: Literal["aion-glm-local-persistence-evidence/v1"] = (
        LOCAL_PERSISTENCE_EVIDENCE_SCHEMA_VERSION
    )
    evidence_bundle_id: str
    receipt: PersistenceTransactionReceipt | None = None
    incidents: tuple[LocalPersistenceIncident, ...] = ()
    operator_review_items: tuple[LocalPersistenceOperatorReviewItem, ...] = ()
    evidence_fingerprint: str
    redacted: Literal[True] = True
    runtime_effect: Literal[False] = False

    @model_validator(mode="after")
    def validate_evidence_bundle(self) -> Self:
        expected = model_fingerprint(self, {"evidence_fingerprint"})
        if self.evidence_fingerprint != expected:
            raise ValueError("persistence evidence bundle fingerprint mismatch")
        return self


def build_authorization_envelope(
    *,
    persistence_session_id: str,
    store_id: str,
    store_identity_fingerprint: str,
    database_path_fingerprint: str,
    operator_identity_fingerprint: str,
    mode: LocalPersistenceMode,
    allowed_operations: tuple[LocalPersistenceOperation, ...],
    created_at: datetime,
) -> LocalPersistenceAuthorizationEnvelope:
    return build_model(
        LocalPersistenceAuthorizationEnvelope,
        {
            "authorization_transaction_id": AUTHORIZATION_TRANSACTION_ID,
            "approval_record_id": APPROVAL_RECORD_ID,
            "persistence_session_id": persistence_session_id,
            "store_id": store_id,
            "store_identity_fingerprint": store_identity_fingerprint,
            "database_path_fingerprint": database_path_fingerprint,
            "operator_identity_fingerprint": operator_identity_fingerprint,
            "mode": mode,
            "allowed_operations": tuple(sorted(allowed_operations)),
            "created_at": created_at,
            "expires_at": created_at + timedelta(hours=1),
        },
        "envelope_fingerprint",
    )


def build_content_envelope(
    *,
    content_envelope_id: str,
    knowledge_identity_id: str,
    candidate_id: str,
    candidate_fingerprint: str,
    candidate_kind: str,
    canonical_statement: str,
    bounded_summary: str,
    language_code: str,
    sensitivity: Literal["public", "internal"],
    lineage_fingerprint: str,
    transaction_plan_fingerprint: str,
    transaction_result_fingerprint: str,
    persistence_approval_bundle_fingerprint: str,
    created_at: datetime,
) -> ApprovedKnowledgeContentEnvelope:
    content_fingerprint = persistence_fingerprint(
        {
            "knowledge_identity_id": knowledge_identity_id,
            "candidate_id": candidate_id,
            "candidate_fingerprint": candidate_fingerprint,
            "canonical_statement": canonical_statement,
            "bounded_summary": bounded_summary,
            "language_code": language_code,
            "sensitivity": sensitivity,
        }
    )
    return build_model(
        ApprovedKnowledgeContentEnvelope,
        {
            "content_envelope_id": content_envelope_id,
            "knowledge_identity_id": knowledge_identity_id,
            "candidate_id": candidate_id,
            "candidate_fingerprint": candidate_fingerprint,
            "candidate_kind": candidate_kind,
            "canonical_statement": canonical_statement,
            "bounded_summary": bounded_summary,
            "language_code": language_code,
            "sensitivity": sensitivity,
            "content_fingerprint": content_fingerprint,
            "lineage_fingerprint": lineage_fingerprint,
            "transaction_plan_fingerprint": transaction_plan_fingerprint,
            "transaction_result_fingerprint": transaction_result_fingerprint,
            "persistence_approval_bundle_fingerprint": persistence_approval_bundle_fingerprint,
            "created_at": created_at,
            "expires_at": created_at + timedelta(hours=1),
        },
        "envelope_fingerprint",
    )


def target_to_projection_type(target: MemoryProjectionTarget) -> PersistentProjectionType:
    return {
        MemoryProjectionTarget.SEMANTIC_MEMORY: PersistentProjectionType.SEMANTIC,
        MemoryProjectionTarget.EPISODIC_MEMORY: PersistentProjectionType.EPISODIC,
        MemoryProjectionTarget.PROCEDURAL_MEMORY: PersistentProjectionType.PROCEDURAL,
        MemoryProjectionTarget.BELIEF_CANDIDATE: PersistentProjectionType.BELIEF_CANDIDATE,
    }[target]
