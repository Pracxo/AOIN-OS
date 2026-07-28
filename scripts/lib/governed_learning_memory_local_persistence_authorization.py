"""AION-223 local persistence authorization validators."""

from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Mapping
from scripts.lib import (
    governed_learning_memory_promotion_operator_evaluation as evaluation,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PROGRAM_ID = "AION-GOVERNED-LEARNING-MEMORY-001"
AION221_AUTHORIZATION_ID = "AION-221-GLM-0001"
AION223_AUTHORIZATION_ID = "AION-223-GLM-0002"
AION224_TASK = "AION-224"
AION225_TASK = "AION-225"
PASS_DECISION = "PROMOTION_TRANSACTION_OPERATOR_EVALUATION_PASS_RECOMMEND_LOCAL_APPEND_ONLY_KNOWLEDGE_PERSISTENCE_AUTHORIZATION"
AION222_FEATURE_COMMIT = "e415cc397b9aec70f8b3d19285f5fdd315048731"
AION222_MERGE_COMMIT = "b89c896b8e75955d28fd06d52b5fb66fb8ed5ac0"
AION222_MERGED_AT = "2026-07-28T09:00:39Z"
AION224_AUTHORIZATION_SCOPE = "operator-approved-local-append-only-knowledge-version-store-transactional-semantic-episodic-procedural-projection-belief-candidate-record-tamper-evidence-backup-restore-core"
AION222_SOURCE_SCOPE = [
    "services/brain-api/src/aion_brain/contracts/governed_learning_memory.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/__init__.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/promotion_requests.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/approval_evidence.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/eligibility_revalidation.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/knowledge_identity.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/version_planning.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/memory_projection.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/promotion_transactions.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/rollback.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/integrity.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/evidence.py",
]
AION224_SOURCE_SCOPE = [
    "services/brain-api/src/aion_brain/contracts/governed_learning_memory_persistence.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/local_persistence_policy.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/local_sqlite_schema.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/local_sqlite_store.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/persistence_approval.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/knowledge_content.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/knowledge_persistence.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/memory_projection_persistence.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/persistence_transactions.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/persistence_integrity.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/backup_restore.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/persistence_evidence.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/__init__.py",
]
AION224_APPROVED_CAPABILITIES = [
    "local_append_only_knowledge_store_approved",
    "operator_invoked_local_persistence_approved",
    "explicit_store_authorization_envelope_approved",
    "explicit_transaction_persistence_approval_approved",
    "separate_plan_and_persistence_approval_approved",
    "dual_approval_for_persistent_write_approved",
    "knowledge_steward_approval_role_approved",
    "memory_operator_approval_role_approved",
    "local_sqlite_store_approved",
    "sqlite_schema_v1_bootstrap_approved",
    "sqlite_foreign_keys_approved",
    "sqlite_wal_mode_approved",
    "sqlite_full_synchronous_approved",
    "sqlite_busy_timeout_approved",
    "sqlite_trusted_schema_off_approved",
    "sqlite_extension_loading_disabled_approved",
    "explicit_absolute_database_path_approved",
    "repository_database_path_rejection_approved",
    "symlink_path_rejection_approved",
    "operator_owned_directory_policy_approved",
    "database_file_mode_0600_approved",
    "append_only_table_design_approved",
    "update_rejection_triggers_approved",
    "delete_rejection_triggers_approved",
    "atomic_begin_immediate_transaction_approved",
    "transaction_idempotency_approved",
    "transaction_fingerprint_collision_rejection_approved",
    "global_ledger_hash_chain_approved",
    "per_transaction_hash_chain_approved",
    "knowledge_identity_persistence_approved",
    "knowledge_version_persistence_approved",
    "approval_binding_fingerprint_persistence_approved",
    "candidate_evidence_receipt_persistence_approved",
    "semantic_projection_record_persistence_approved",
    "episodic_projection_record_persistence_approved",
    "procedural_projection_record_persistence_approved",
    "belief_candidate_projection_record_persistence_approved",
    "approved_knowledge_content_envelope_approved",
    "bounded_redacted_knowledge_statement_approved",
    "content_fingerprint_binding_approved",
    "lineage_fingerprint_binding_approved",
    "promotion_plan_fingerprint_binding_approved",
    "promotion_result_fingerprint_binding_approved",
    "persistence_approval_fingerprint_binding_approved",
    "append_only_supersession_marker_approved",
    "append_only_retraction_marker_approved",
    "append_only_expiry_marker_approved",
    "append_only_rollback_marker_approved",
    "no_hard_delete_enforcement_approved",
    "read_after_write_verification_approved",
    "sqlite_integrity_check_approved",
    "ledger_chain_integrity_audit_approved",
    "deterministic_exact_queries_approved",
    "operator_invoked_checkpoint_approved",
    "operator_invoked_backup_approved",
    "operator_invoked_restore_to_new_store_approved",
    "backup_manifest_approved",
    "restore_integrity_validation_approved",
    "crash_atomicity_validation_approved",
    "concurrent_reader_policy_approved",
    "single_writer_policy_approved",
    "redacted_persistence_receipt_approved",
    "redacted_persistence_incident_approved",
    "operator_review_item_approved",
    "synthetic_local_persistence_fixture_approved",
    "documentation_and_static_evidence_approved",
]
AION224_PROHIBITED_CAPABILITIES = [
    "automatic_store_initialization_enabled",
    "automatic_schema_migration_enabled",
    "arbitrary_sql_execution_enabled",
    "sqlite_extension_loading_enabled",
    "database_path_inside_repository_enabled",
    "database_symlink_enabled",
    "shared_world_writable_store_enabled",
    "general_persistent_knowledge_write_enabled",
    "background_persistent_knowledge_write_enabled",
    "scheduled_persistent_knowledge_write_enabled",
    "production_persistent_knowledge_write_enabled",
    "automatic_candidate_approval_enabled",
    "automatic_knowledge_promotion_enabled",
    "automatic_memory_ingestion_enabled",
    "automatic_engagement_learning_application_enabled",
    "existing_memory_repository_write_enabled",
    "production_memory_repository_write_enabled",
    "actual_belief_creation_enabled",
    "actual_belief_mutation_enabled",
    "belief_repository_write_enabled",
    "hard_delete_enabled",
    "in_place_knowledge_version_update_enabled",
    "in_place_projection_update_enabled",
    "approval_creation_by_runtime_enabled",
    "approval_decision_by_runtime_enabled",
    "approval_reuse_for_changed_transaction_enabled",
    "single_actor_persistent_write_enabled",
    "confidential_content_persistence_enabled",
    "restricted_content_persistence_enabled",
    "raw_source_body_persistence_enabled",
    "raw_source_preview_persistence_enabled",
    "raw_approval_payload_persistence_enabled",
    "raw_user_message_persistence_enabled",
    "raw_prompt_persistence_enabled",
    "hidden_reasoning_persistence_enabled",
    "credential_persistence_enabled",
    "private_key_persistence_enabled",
    "network_access_enabled",
    "search_provider_integration_enabled",
    "connector_integration_enabled",
    "model_provider_integration_enabled",
    "actual_tool_execution_enabled",
    "shell_command_execution_enabled",
    "subprocess_execution_enabled",
    "browser_automation_enabled",
    "source_mutation_enabled",
    "git_mutation_enabled",
    "real_pull_request_creation_enabled",
    "runtime_approval_creation_enabled",
    "automatic_merge_enabled",
    "production_deployment_enabled",
    "model_weight_training_enabled",
    "api_route_enabled",
    "installed_cli_command_enabled",
    "kernel_registration_enabled",
    "application_startup_registration_enabled",
    "scheduler_enabled",
    "background_worker_enabled",
    "production_exposure",
    "v02_release_ready",
    "v02_tag_created",
    "v02_release_created",
]
AION224_RESOURCE_LIMITS = {
    "maximum_persistence_sessions": 10,
    "maximum_transactions_per_session": 100,
    "maximum_knowledge_identities_per_transaction": 100,
    "maximum_knowledge_versions_per_transaction": 100,
    "maximum_candidate_evidence_receipts_per_transaction": 100,
    "maximum_projection_records_per_transaction": 100,
    "maximum_semantic_projection_records_per_transaction": 100,
    "maximum_episodic_projection_records_per_transaction": 100,
    "maximum_procedural_projection_records_per_transaction": 100,
    "maximum_belief_candidate_projection_records_per_transaction": 100,
    "maximum_approval_evidence_records_per_transaction": 4,
    "minimum_independent_approvers_per_transaction": 2,
    "maximum_content_bytes_per_knowledge_version": 16384,
    "maximum_summary_bytes_per_projection": 4096,
    "maximum_metadata_bytes_per_record": 16384,
    "maximum_total_transaction_bytes": 4194304,
    "maximum_database_bytes": 1073741824,
    "maximum_backup_bytes": 1073741824,
    "maximum_backup_copies": 10,
    "maximum_query_results": 1000,
    "maximum_concurrent_readers": 4,
    "maximum_concurrent_writers": 1,
    "maximum_transaction_seconds": 30,
    "maximum_checkpoint_interval_records": 1000,
    "maximum_integrity_findings": 1000,
    "maximum_operator_review_items": 100,
    "maximum_restore_attempts_per_session": 3,
    "maximum_persistent_source_body_writes": 0,
    "maximum_persistent_source_preview_writes": 0,
    "maximum_persistent_raw_approval_payload_writes": 0,
    "maximum_confidential_content_writes": 0,
    "maximum_restricted_content_writes": 0,
    "maximum_actual_belief_creations": 0,
    "maximum_actual_belief_mutations": 0,
    "maximum_automatic_candidate_approvals": 0,
    "maximum_automatic_knowledge_promotions": 0,
    "maximum_automatic_memory_ingestions": 0,
    "maximum_engagement_learning_applications": 0,
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
FUTURE_SQLITE_POLICY = {
    "foreign_keys": "ON",
    "journal_mode": "WAL",
    "synchronous": "FULL",
    "busy_timeout": 5000,
    "trusted_schema": "OFF",
    "recursive_triggers": "OFF",
    "auto_vacuum": "NONE",
    "temp_store": "MEMORY",
    "application_id": 223224,
    "user_version": 1,
    "extension_loading": "disabled",
}
FUTURE_MODELS = [
    "LocalPersistenceAuthorizationEnvelope",
    "PersistenceApprovalEvidence",
    "PersistenceApprovalBundle",
    "ApprovedKnowledgeContentEnvelope",
    "PersistentCandidateEvidenceReceipt",
    "PersistentKnowledgeIdentity",
    "PersistentKnowledgeVersion",
    "PersistentApprovalBinding",
    "PersistentMemoryProjectionRecord",
    "PersistentBeliefProjectionCandidateRecord",
    "PersistenceLedgerEvent",
    "PersistenceTransactionRequest",
    "PersistenceTransactionReceipt",
    "LocalKnowledgeQuery",
    "LocalKnowledgeQueryResult",
    "LocalProjectionQuery",
    "LocalProjectionQueryResult",
    "LocalStoreIntegrityReport",
    "LocalStoreCheckpoint",
    "LocalStoreBackupManifest",
    "LocalStoreRestorePlan",
    "LocalStoreRestoreResult",
    "LocalPersistenceIncident",
    "LocalPersistenceOperatorReviewItem",
]
THREAT_MODEL = [
    "database path traversal",
    "symlink replacement",
    "parent-directory substitution",
    "world-writable directory",
    "store identity substitution",
    "unknown schema",
    "malicious schema object",
    "SQLite extension loading",
    "ATTACH DATABASE abuse",
    "SQL injection",
    "concurrent writer races",
    "partial transaction commit",
    "WAL truncation",
    "rollback-journal manipulation",
    "ledger-chain truncation",
    "ledger-chain reordering",
    "previous-hash substitution",
    "transaction-ID replay",
    "changed transaction replay",
    "content-envelope substitution",
    "approval replay",
    "approval-store mismatch",
    "approval-path mismatch",
    "approval-content mismatch",
    "single-actor persistence",
    "candidate-fingerprint substitution",
    "lineage substitution",
    "projection substitution",
    "version rollback",
    "version overwrite",
    "hidden update",
    "hidden delete",
    "hard deletion",
    "retraction suppression",
    "supersession suppression",
    "backup substitution",
    "restore rollback attack",
    "corrupted backup",
    "source-body leakage",
    "approval-payload leakage",
    "sensitive-content persistence",
    "belief creation through projection",
    "production-memory contamination",
    "automatic promotion",
    "background writer activation",
    "network activation",
    "source mutation",
    "Git mutation",
    "runtime approval creation",
    "production deployment",
    "authorization reuse",
]
ZERO_EFFECT_FIELDS = [
    "approval_requests_created",
    "approval_decisions_created",
    "persistent_knowledge_writes",
    "persistent_verified_knowledge_writes",
    "semantic_memory_writes",
    "episodic_memory_writes",
    "procedural_memory_writes",
    "cognitive_memory_writes",
    "belief_creations",
    "belief_mutations",
    "automatic_candidate_approvals",
    "automatic_knowledge_promotions",
    "engagement_learning_applications",
    "network_calls",
    "dns_resolutions",
    "search_provider_calls",
    "connector_calls",
    "model_provider_calls",
    "actual_tool_executions",
    "shell_executions",
    "subprocess_executions",
    "browser_actions",
    "filesystem_mutations",
    "source_mutations",
    "git_operations",
    "runtime_pull_requests",
    "runtime_approvals",
    "deployments",
    "model_weight_changes",
]


class LocalPersistenceAuthorizationError(ValueError):
    pass


def load_json(relative: str, root: Path = REPO_ROOT) -> dict[str, Any]:
    return json.loads((root / relative).read_text(encoding="utf-8"))


def _fail(message: str) -> None:
    raise LocalPersistenceAuthorizationError(message)


def _record_by_id(
    records: list[Mapping[str, Any]], authorization_id: str
) -> Mapping[str, Any]:
    for record in records:
        if record.get("authorization_transaction_id") == authorization_id:
            return record
    _fail(f"authorization record missing: {authorization_id}")


def _require_false(payload: Mapping[str, Any], keys: list[str], label: str) -> None:
    for key in keys:
        if payload.get(key) is not False:
            _fail(f"{label} expected false: {key}")


def _require_true(payload: Mapping[str, Any], keys: list[str], label: str) -> None:
    for key in keys:
        if payload.get(key) is not True:
            _fail(f"{label} expected true: {key}")


def validate_evaluation_report(root: Path = REPO_ROOT) -> dict[str, Any]:
    report = evaluation.validate_evaluation_report_file(
        root
        / "examples/governed-learning-memory/promotion-operator-evaluation-report.json"
    )
    if report["decision"] != PASS_DECISION or report["evaluation_passed"] is not True:
        _fail("AION-223 report must be exact PASS")
    if report["scenario_count"] != 28:
        _fail("AION-223 scenario count mismatch")
    if not all(item["result"] == "passed" for item in report["scenario_results"]):
        _fail("not every scenario passed")
    if not all(item["passed"] is True for item in report["hard_gate_results"].values()):
        _fail("not every hard gate passed")
    for field in ZERO_EFFECT_FIELDS:
        if report.get(field) != 0:
            _fail(f"report zero-effect mismatch: {field}")
    if (
        report.get("repository_unchanged") is not True
        or report.get("temporary_evaluation_data_cleaned") is not True
    ):
        _fail("repository cleanup evidence mismatch")
    return report


def validate_authorization_ledgers(
    root: Path = REPO_ROOT,
) -> tuple[dict[str, Any], dict[str, Any]]:
    program = load_json("docs/governed-learning-memory/program-ledger.json", root)
    auth = load_json("docs/governed-learning-memory/authorization-ledger.json", root)
    for label, payload in (("program", program), ("authorization", auth)):
        if payload.get("program_id") != PROGRAM_ID:
            _fail(f"{label} program mismatch")
        if (
            payload.get("program_state")
            != "governed_learning_memory_local_persistence_authorized_not_implemented"
        ):
            _fail(f"{label} state mismatch")
        if (
            payload.get("active_glm_implementation_authorization_count") != 1
            or payload.get("active_glm_implementation_authorization")
            != AION223_AUTHORIZATION_ID
        ):
            _fail(f"{label} active authorization mismatch")
        if (
            payload.get("active_glm_implementation_task") != AION224_TASK
            or payload.get("formal_closeout_task") != AION225_TASK
        ):
            _fail(f"{label} task mismatch")
        _require_true(
            payload,
            [
                "promotion_transaction_operator_evaluation_passed",
                "new_glm_implementation_authorization_created",
                "local_append_only_knowledge_store_authorized",
                "operator_invoked_local_persistence_authorized",
                "knowledge_promotion_transaction_core_implemented",
            ],
            label,
        )
        _require_false(
            payload,
            [
                "local_append_only_knowledge_store_implemented",
                "operator_invoked_local_persistence_available",
                "general_persistent_knowledge_write_enabled",
                "background_persistent_knowledge_write_enabled",
                "production_persistent_knowledge_write_enabled",
                "automatic_knowledge_promotion_enabled",
                "cognitive_belief_creation_enabled",
                "cognitive_belief_mutation_enabled",
                "production_exposure",
                "v02_release_ready",
                "v02_tag_created",
                "v02_release_created",
            ],
            label,
        )
        if (
            payload.get("promotion_transaction_operator_evaluation_decision")
            != PASS_DECISION
        ):
            _fail(f"{label} decision mismatch")
    if auth.get("active_authorizations") != [AION223_AUTHORIZATION_ID]:
        _fail("active_authorizations mismatch")
    records = auth.get("records")
    if not isinstance(records, list):
        _fail("authorization records missing")
    closed = _record_by_id(records, AION221_AUTHORIZATION_ID)
    new = _record_by_id(records, AION223_AUTHORIZATION_ID)
    if (
        closed.get("authorization_active") is not False
        or closed.get("authorization_consumed") is not True
        or closed.get("authorization_expired") is not True
        or closed.get("authorization_reusable") is not False
    ):
        _fail("AION-221 closeout mismatch")
    if (
        closed.get("authorization_consumed_by_task") != "AION-222"
        or closed.get("authorization_consumed_by_prs") != [138]
        or closed.get("authorization_consumed_by_feature_commits")
        != [AION222_FEATURE_COMMIT]
        or closed.get("authorization_consumed_by_merge_commits")
        != [AION222_MERGE_COMMIT]
        or closed.get("authorization_closed_by_task") != "AION-223"
    ):
        _fail("AION-221 delivery closeout mismatch")
    if closed.get("evaluation_used_as_persistence_approval") is not False:
        _fail("evaluation cannot be persistence approval")
    expected = {
        "program_id": PROGRAM_ID,
        "authorization_transaction_id": AION223_AUTHORIZATION_ID,
        "approval_record_id": AION223_AUTHORIZATION_ID,
        "parent_authorization_transaction_id": AION221_AUTHORIZATION_ID,
        "parent_evaluation_id": "AION-GLMPE-001",
        "parent_evaluation_decision": PASS_DECISION,
        "candidate_id": "operator-approved-local-append-only-knowledge-persistence-core",
        "workstream": "governed-learning-memory-local-persistence",
        "implementation_task": AION224_TASK,
        "formal_closeout_task": AION225_TASK,
        "authorization_scope": AION224_AUTHORIZATION_SCOPE,
    }
    for k, v in expected.items():
        if new.get(k) != v:
            _fail(f"new authorization {k} mismatch")
    _require_true(
        new,
        [
            "authorization_transaction_approved",
            "explicit_approval_record_approval",
            "implementation_authorization_approved",
            "implementation_go_status",
            "authorization_active",
        ],
        "new authorization",
    )
    _require_false(
        new,
        [
            "implementation_no_go_status",
            "authorization_consumed",
            "authorization_expired",
            "authorization_reusable",
            "evaluation_used_as_persistence_approval",
            "individual_transaction_persistence_approved",
        ],
        "new authorization",
    )
    if set(new.get("authorized_capabilities", {})) != set(
        AION224_APPROVED_CAPABILITIES
    ):
        _fail("approved capability key mismatch")
    if set(new.get("prohibited_capabilities", {})) != set(
        AION224_PROHIBITED_CAPABILITIES
    ):
        _fail("prohibited capability key mismatch")
    if any(v is not True for v in new["authorized_capabilities"].values()) or any(
        v is not False for v in new["prohibited_capabilities"].values()
    ):
        _fail("capability value mismatch")
    if (
        new.get("resource_limits") != AION224_RESOURCE_LIMITS
        or new.get("authorized_source_scope") != AION224_SOURCE_SCOPE
    ):
        _fail("future limits or source scope mismatch")
    return program, auth


def validate_delivery_reconciliation(root: Path = REPO_ROOT) -> None:
    delivery = load_json("docs/governed-learning-memory/program-ledger.json", root).get(
        "aion_222_delivery", {}
    )
    expected = {
        "task_id": "AION-222",
        "branch": "phase/governed-learning-memory-promotion-transaction-core",
        "feature_commits": [AION222_FEATURE_COMMIT],
        "pull_requests": [138],
        "merge_commits": [AION222_MERGE_COMMIT],
        "ci_result": "pass",
        "completion_timestamp": AION222_MERGED_AT,
        "authorization_transaction": AION221_AUTHORIZATION_ID,
        "authorization_state": "consumed_by_AION-222_closed_by_AION-223",
        "next_task": "AION-223",
        "runtime_state": "promotion_transaction_core_implemented_dry_run_in_memory_write_disabled",
        "evaluation_id": "AION-GLMPE-001",
        "evaluation_decision": PASS_DECISION,
    }
    for k, v in expected.items():
        if delivery.get(k) != v:
            _fail(f"AION-222 delivery {k} mismatch")


def validate_future_policy(root: Path = REPO_ROOT) -> None:
    record = _record_by_id(
        load_json("docs/governed-learning-memory/authorization-ledger.json", root)[
            "records"
        ],
        AION223_AUTHORIZATION_ID,
    )
    if record["approval_policy"]["minimum_independent_approvers"] != 2:
        _fail("dual approval missing")
    if (
        record["approval_policy"]["plan_approval_can_authorize_persistence"]
        is not False
    ):
        _fail("plan approval reuse must be rejected")
    if (
        record["content_policy"]["confidential_content_allowed"] is not False
        or record["content_policy"]["raw_source_body_allowed"] is not False
    ):
        _fail("content policy mismatch")
    if (
        record["sqlite_policy"] != FUTURE_SQLITE_POLICY
        or len(record["threat_model"]) < 50
    ):
        _fail("sqlite or threat model mismatch")


def validate_no_aion224_source(root: Path = REPO_ROOT) -> None:
    for rel in AION224_SOURCE_SCOPE:
        if rel.endswith("__init__.py"):
            continue
        if (root / rel).exists():
            _fail(f"AION-224 source exists before implementation: {rel}")
    for pattern in ("*.db", "*.sqlite", "*.sqlite3", "*.jsonl", "*.state", "*.sql"):
        for p in root.rglob(pattern):
            rel = p.relative_to(root).as_posix()
            if "governed-learning-memory" in rel or "governed_learning_memory" in rel:
                _fail(f"persistent state artifact exists: {rel}")


def validate_local_persistence_authorization(root: Path = REPO_ROOT) -> None:
    validate_evaluation_report(root)
    validate_authorization_ledgers(root)
    validate_delivery_reconciliation(root)
    validate_future_policy(root)
    validate_no_aion224_source(root)


def main() -> int:
    try:
        validate_local_persistence_authorization()
    except LocalPersistenceAuthorizationError as exc:
        print(f"ERROR: {exc}")
        return 1
    print("governed learning memory local persistence authorization validator PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
