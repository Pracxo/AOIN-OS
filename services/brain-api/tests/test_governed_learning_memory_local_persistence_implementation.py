from __future__ import annotations

import os
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest
from knowledge_verified_memory_test_helpers import FIXED_TIME, fp
from test_governed_learning_memory_contracts import sample_planning_components

from aion_brain.contracts import governed_learning_memory as glm
from aion_brain.contracts import governed_learning_memory_persistence as glmp
from aion_brain.contracts.approvals import ApprovalDecision, ApprovalRequest
from aion_brain.governed_learning_memory.local_persistence_policy import (
    database_path_fingerprint,
    operator_identity_fingerprint,
    store_identity_fingerprint,
    validate_database_path,
)
from aion_brain.governed_learning_memory.local_sqlite_schema import (
    APPLICATION_TABLES,
    EXPECTED_TRIGGER_NAMES,
    SQLITE_APPLICATION_ID,
    SQLITE_USER_VERSION,
)
from aion_brain.governed_learning_memory.local_sqlite_store import (
    ControlledLocalAppendOnlyPersistenceService,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
TARGETS = (
    glm.MemoryProjectionTarget.SEMANTIC_MEMORY,
    glm.MemoryProjectionTarget.EPISODIC_MEMORY,
    glm.MemoryProjectionTarget.PROCEDURAL_MEMORY,
    glm.MemoryProjectionTarget.BELIEF_CANDIDATE,
)


def _secure_dir(path: Path) -> Path:
    path.mkdir(exist_ok=True)
    os.chmod(path, 0o700)
    return path.resolve()


def _build_plan(transaction_id: str) -> SimpleNamespace:
    components = sample_planning_components(
        transaction_id=transaction_id,
        targets=TARGETS,
        risk_class=glm.PromotionRiskClass.HIGH,
        approval_pairs=2,
    )
    budget = glm.evaluate_resource_budget(
        glm.PromotionResourceUsage(
            candidates=len(components.bindings),
            approval_evidence_records=2,
        )
    )
    plan = glm._build(
        glm.PromotionTransactionPlan,
        {
            "transaction_id": components.context.request.transaction_id,
            "promotion_request": components.context.request,
            "candidate_bindings": components.bindings,
            "eligibility_snapshots": components.snapshots,
            "approval_evidence_bundle": components.approvals,
            "knowledge_identity_plans": components.identities,
            "conflict_report": components.conflicts,
            "version_plans": components.versions,
            "memory_projection_plan": components.projections,
            "rollback_plan": components.rollback,
            "compensation_plan": components.compensation,
            "resource_budget_decision": budget,
        },
        "transaction_plan_fingerprint",
    )
    return SimpleNamespace(plan=plan, result=components.context.result)


def _persistence_fixture(tmp_path: Path, transaction_id: str = "promotion-transaction-aion224"):
    store_dir = _secure_dir(tmp_path / transaction_id)
    database_path = store_dir / "store.sqlite3"
    database_fp = database_path_fingerprint(database_path)
    store_fp = store_identity_fingerprint("store-001", database_fp)
    operator_fp = operator_identity_fingerprint("operator-001")
    authorization = glmp.build_authorization_envelope(
        persistence_session_id="session-001",
        store_id="store-001",
        store_identity_fingerprint=store_fp,
        database_path_fingerprint=database_fp,
        operator_identity_fingerprint=operator_fp,
        mode=glmp.LocalPersistenceMode.SYNTHETIC_TEST,
        allowed_operations=tuple(glmp.LocalPersistenceOperation),
        created_at=datetime.now(UTC),
    )
    service = ControlledLocalAppendOnlyPersistenceService(repo_root=REPO_ROOT)
    init_report = service.initialize_store(
        database_path=database_path,
        authorization=authorization,
    )
    planned = _build_plan(transaction_id)
    plan = planned.plan
    result = planned.result
    backup_policy_fp = fp("backup-policy")
    preliminary_content = _content(plan, result, fp("placeholder"))
    content_fingerprints = (preliminary_content.content_fingerprint,)
    evidence_records = tuple(
        _approval_evidence(
            role=role,
            approver=approver,
            plan=plan,
            result=result,
            store_fp=store_fp,
            database_fp=database_fp,
            content_fingerprints=content_fingerprints,
            backup_policy_fp=backup_policy_fp,
        )
        for role, approver in (
            ("knowledge_steward", "knowledge-steward-001"),
            ("memory_operator", "memory-operator-001"),
        )
    )
    approval_bundle = glmp.build_persistence_approval_bundle(
        approval_bundle_id="persistence-approval-bundle-001",
        evidence_records=evidence_records,
    )
    content = _content(plan, result, approval_bundle.bundle_fingerprint)
    request = _request(
        authorization=authorization,
        plan=plan,
        result=result,
        approval_bundle=approval_bundle,
        content=content,
        database_fp=database_fp,
        store_fp=store_fp,
    )
    return SimpleNamespace(
        authorization=authorization,
        content=content,
        database_path=database_path,
        init_report=init_report,
        plan=plan,
        request=request,
        result=result,
        service=service,
        store_dir=store_dir,
    )


def _content(plan, result, approval_bundle_fp: str):
    identity = plan.knowledge_identity_plans[0]
    return glmp.build_content_envelope(
        content_envelope_id="content-envelope-001",
        knowledge_identity_id=identity.knowledge_identity_id,
        candidate_id=identity.candidate_id,
        candidate_fingerprint=identity.candidate_fingerprint,
        candidate_kind=identity.candidate_kind.value,
        canonical_statement="A bounded public synthetic knowledge statement for AION-224.",
        bounded_summary="A bounded public synthetic summary.",
        language_code="en",
        sensitivity="public",
        lineage_fingerprint=identity.lineage_fingerprint,
        transaction_plan_fingerprint=plan.transaction_plan_fingerprint,
        transaction_result_fingerprint=result.result_fingerprint,
        persistence_approval_bundle_fingerprint=approval_bundle_fp,
        created_at=FIXED_TIME,
    )


def _approval_evidence(
    *,
    role: str,
    approver: str,
    plan,
    result,
    store_fp: str,
    database_fp: str,
    content_fingerprints: tuple[str, ...],
    backup_policy_fp: str,
):
    action = {
        "knowledge_steward": "governed_learning_memory.persist_local_knowledge_version",
        "memory_operator": "governed_learning_memory.persist_local_memory_projection",
    }[role]
    scope = {
        "knowledge_steward": "governed-learning-memory:persist-local-knowledge",
        "memory_operator": "governed-learning-memory:persist-local-projection",
    }[role]
    payload = {
        "persistence_role": role,
        "store_identity_fingerprint": store_fp,
        "database_path_fingerprint": database_fp,
        "transaction_id": plan.transaction_id,
        "promotion_request_fingerprint": plan.promotion_request.request_fingerprint,
        "promotion_plan_fingerprint": plan.transaction_plan_fingerprint,
        "promotion_result_fingerprint": result.result_fingerprint,
        "knowledge_identity_ids": [
            item.knowledge_identity_id for item in plan.knowledge_identity_plans
        ],
        "knowledge_version_plan_fingerprints": [
            item.version_plan_fingerprint for item in plan.version_plans
        ],
        "memory_projection_fingerprints": [
            item.projection_fingerprint for item in plan.memory_projection_plan.records
        ],
        "approved_content_fingerprints": list(content_fingerprints),
        "backup_policy_fingerprint": backup_policy_fp,
    }
    request = ApprovalRequest(
        approval_request_id=f"{role}-request-001",
        actor_id="requester-001",
        requested_by="requester-001",
        assigned_to=approver,
        action_type=action,
        resource_type="promotion_transaction_result",
        resource_id=result.result_fingerprint,
        title="Approve local persistence",
        description="Approve local append-only persistence for synthetic test.",
        status="approved",
        priority="normal",
        approval_scope=[scope],
        payload=payload,
        expires_at=FIXED_TIME + timedelta(hours=2),
        created_at=FIXED_TIME,
    )
    decision = ApprovalDecision(
        approval_decision_id=f"{role}-decision-001",
        approval_request_id=request.approval_request_id,
        decided_by=approver,
        decision="approve",
        reason="Approved for local persistence synthetic test.",
        created_at=FIXED_TIME + timedelta(minutes=1),
    )
    return glmp.project_existing_persistence_approval_evidence(
        request,
        decision,
        approval_evidence_id=f"evidence-{role}",
        role=role,
        transaction_id=plan.transaction_id,
        store_identity_fingerprint=store_fp,
        database_path_fingerprint=database_fp,
        promotion_request_fingerprint=plan.promotion_request.request_fingerprint,
        promotion_plan_fingerprint=plan.transaction_plan_fingerprint,
        promotion_result_fingerprint=result.result_fingerprint,
        knowledge_identity_ids=tuple(
            item.knowledge_identity_id for item in plan.knowledge_identity_plans
        ),
        knowledge_version_plan_fingerprints=tuple(
            item.version_plan_fingerprint for item in plan.version_plans
        ),
        memory_projection_fingerprints=tuple(
            item.projection_fingerprint for item in plan.memory_projection_plan.records
        ),
        approved_content_fingerprints=content_fingerprints,
        backup_policy_fingerprint=backup_policy_fp,
        observed_at=FIXED_TIME + timedelta(minutes=2),
    )


def _request(
    *,
    authorization,
    plan,
    result,
    approval_bundle,
    content,
    database_fp,
    store_fp,
    request_id: str = "persist-request-001",
):
    return glmp.build_model(
        glmp.PersistenceTransactionRequest,
        {
            "persistence_request_id": request_id,
            "persistence_session_id": authorization.persistence_session_id,
            "store_id": authorization.store_id,
            "store_identity_fingerprint": store_fp,
            "database_path_fingerprint": database_fp,
            "local_authorization_envelope": authorization,
            "promotion_transaction_plan": plan,
            "promotion_transaction_result": result,
            "persistence_approval_bundle": approval_bundle,
            "approved_content_envelopes": (content,),
            "requested_at": FIXED_TIME,
            "expires_at": FIXED_TIME + timedelta(hours=1),
        },
        "request_fingerprint",
    )


def _cleanup_files(directory: Path) -> None:
    for path in sorted(directory.glob("*")):
        path.unlink(missing_ok=True)
    directory.rmdir()


def test_local_persistence_authorization_and_path_policy(tmp_path: Path):
    secure = _secure_dir(tmp_path / "policy")
    database_path = secure / "store.sqlite3"

    checked = validate_database_path(
        database_path,
        mode=glmp.LocalPersistenceMode.SYNTHETIC_TEST,
        operation=glmp.LocalPersistenceOperation.INITIALIZE,
        repo_root=REPO_ROOT,
    )
    assert checked.database_path_fingerprint == database_path_fingerprint(database_path)

    with pytest.raises(glmp.LocalPersistenceError):
        validate_database_path(
            REPO_ROOT / "blocked.sqlite3",
            mode=glmp.LocalPersistenceMode.SYNTHETIC_TEST,
            operation=glmp.LocalPersistenceOperation.INITIALIZE,
            repo_root=REPO_ROOT,
        )

    with pytest.raises(glmp.LocalPersistenceError):
        validate_database_path(
            database_path,
            mode=glmp.LocalPersistenceMode.OPERATOR_LOCAL,
            operation=glmp.LocalPersistenceOperation.INITIALIZE,
            repo_root=REPO_ROOT,
        )

    secure.rmdir()


def test_local_persistence_bootstrap_schema_pragmas_and_triggers(tmp_path: Path):
    fixture = _persistence_fixture(tmp_path, "promotion-transaction-bootstrap")
    try:
        assert fixture.init_report.status is glmp.LocalStoreIntegrityStatus.PASSED
        assert fixture.database_path.stat().st_mode & 0o777 == 0o600
        with sqlite3.connect(fixture.database_path) as conn:
            assert conn.execute("PRAGMA application_id").fetchone()[0] == SQLITE_APPLICATION_ID
            assert conn.execute("PRAGMA user_version").fetchone()[0] == SQLITE_USER_VERSION
            tables = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'glm_%'"
                )
            }
            triggers = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='trigger' AND name LIKE 'glm_%'"
                )
            }
        assert tables == set(APPLICATION_TABLES)
        assert triggers == set(EXPECTED_TRIGGER_NAMES)

        with pytest.raises(glmp.LocalPersistenceError):
            fixture.service.initialize_store(
                database_path=fixture.database_path,
                authorization=fixture.authorization,
            )
    finally:
        _cleanup_files(fixture.store_dir)


def test_local_persistence_rejects_bad_pragmas(tmp_path: Path):
    fixture = _persistence_fixture(tmp_path, "promotion-transaction-bad-pragma")
    try:
        with sqlite3.connect(fixture.database_path) as conn:
            conn.execute("PRAGMA user_version=2")
        assert (
            fixture.service.audit_store(database_path=fixture.database_path).status
            is glmp.LocalStoreIntegrityStatus.FAILED
        )
    finally:
        _cleanup_files(fixture.store_dir)


def test_local_persistence_transaction_queries_idempotency_and_triggers(tmp_path: Path):
    fixture = _persistence_fixture(tmp_path, "promotion-transaction-write")
    try:
        receipt = fixture.service.persist_transaction(
            database_path=fixture.database_path,
            request=fixture.request,
        )
        assert receipt.integrity_status is glmp.LocalStoreIntegrityStatus.PASSED
        assert receipt.isolated_local_persistence_applied is True
        assert receipt.production_memory_written is False
        assert receipt.actual_belief_created is False
        assert receipt.row_counts == {
            "approval_bindings": 2,
            "candidate_evidence_receipts": 1,
            "knowledge_identities": 1,
            "knowledge_versions": 1,
            "memory_projection_records": 3,
            "belief_projection_candidates": 1,
            "ledger_events": 11,
        }

        query = glmp.build_model(
            glmp.LocalKnowledgeQuery,
            {
                "store_id": fixture.authorization.store_id,
                "candidate_id": fixture.plan.version_plans[0].candidate_id,
                "limit": 10,
            },
            "query_fingerprint",
        )
        knowledge = fixture.service.query_knowledge(
            database_path=fixture.database_path,
            query=query,
        )
        assert knowledge.result_count == 1
        assert knowledge.records[0].candidate_id == fixture.plan.version_plans[0].candidate_id

        projection_query = glmp.build_model(
            glmp.LocalProjectionQuery,
            {"limit": 10},
            "query_fingerprint",
        )
        projections = fixture.service.query_projections(
            database_path=fixture.database_path,
            query=projection_query,
        )
        assert projections.result_count == 4
        assert len(projections.memory_projection_records) == 3
        assert len(projections.belief_candidate_records) == 1

        replay = fixture.service.persist_transaction(
            database_path=fixture.database_path,
            request=fixture.request,
        )
        assert replay.idempotent_replay is True
        assert replay.row_counts["ledger_events"] == 0

        changed_request = _request(
            authorization=fixture.authorization,
            plan=fixture.plan,
            result=fixture.result,
            approval_bundle=fixture.request.persistence_approval_bundle,
            content=fixture.content,
            database_fp=fixture.authorization.database_path_fingerprint,
            store_fp=fixture.authorization.store_identity_fingerprint,
            request_id="persist-request-changed",
        )
        with pytest.raises(glmp.LocalPersistenceError):
            fixture.service.persist_transaction(
                database_path=fixture.database_path,
                request=changed_request,
            )

        with sqlite3.connect(fixture.database_path) as conn:
            with pytest.raises(sqlite3.DatabaseError, match="append-only"):
                conn.execute("UPDATE glm_knowledge_versions SET bounded_summary='blocked'")
            with pytest.raises(sqlite3.DatabaseError, match="append-only"):
                conn.execute("DELETE FROM glm_knowledge_versions")

        assert (
            fixture.service.audit_store(database_path=fixture.database_path).status
            is glmp.LocalStoreIntegrityStatus.PASSED
        )
    finally:
        _cleanup_files(fixture.store_dir)


def test_local_persistence_checkpoint_backup_and_restore(tmp_path: Path):
    fixture = _persistence_fixture(tmp_path, "promotion-transaction-backup")
    try:
        fixture.service.persist_transaction(
            database_path=fixture.database_path,
            request=fixture.request,
        )
        checkpoint = fixture.service.checkpoint_store(database_path=fixture.database_path)
        assert checkpoint.last_ledger_sequence == 11

        backup_path = fixture.store_dir / "backup.sqlite3"
        manifest_path = fixture.store_dir / "backup-manifest.json"
        manifest = fixture.service.backup_store(
            database_path=fixture.database_path,
            backup_path=backup_path,
            manifest_path=manifest_path,
        )
        assert manifest.integrity_status is glmp.LocalBackupStatus.CREATED
        assert manifest_path.stat().st_mode & 0o777 == 0o600

        restored_path = fixture.store_dir / "restored.sqlite3"
        plan = fixture.service.plan_restore(
            backup_manifest=manifest,
            destination_path=restored_path,
        )
        restore = fixture.service.restore_to_new_store(
            backup_path=backup_path,
            backup_manifest=manifest,
            destination_path=restored_path,
            restore_plan=plan,
        )
        assert restore.status is glmp.LocalRestoreStatus.RESTORED_TO_NEW_STORE
        assert restore.active_store_switched is False
        assert restore.restored_ledger_head_hash == manifest.ledger_head_hash
        assert (
            fixture.service.audit_store(database_path=restored_path).status
            is glmp.LocalStoreIntegrityStatus.PASSED
        )
    finally:
        _cleanup_files(fixture.store_dir)


def test_local_persistence_rejects_persistence_approval_misuse(tmp_path: Path):
    fixture = _persistence_fixture(tmp_path, "promotion-transaction-approval-misuse")
    try:
        approval = ApprovalRequest(
            approval_request_id="bad-plan-approval",
            actor_id="requester-001",
            requested_by="requester-001",
            assigned_to="knowledge-steward-001",
            action_type="governed_learning_memory.promotion_plan",
            resource_type="verified_knowledge_candidate",
            resource_id=fixture.plan.knowledge_identity_plans[0].candidate_id,
            title="Wrong approval",
            description="This is only a promotion-plan approval.",
            status="approved",
            priority="normal",
            approval_scope=["governed-learning-memory:promotion-plan"],
            payload={},
            expires_at=FIXED_TIME + timedelta(hours=2),
            created_at=FIXED_TIME,
        )
        decision = ApprovalDecision(
            approval_decision_id="bad-plan-decision",
            approval_request_id=approval.approval_request_id,
            decided_by="knowledge-steward-001",
            decision="approve",
            reason="Wrong approval type.",
            created_at=FIXED_TIME + timedelta(minutes=1),
        )
        with pytest.raises(ValueError, match="action type"):
            glmp.project_existing_persistence_approval_evidence(
                approval,
                decision,
                approval_evidence_id="bad-evidence",
                role="knowledge_steward",
                transaction_id=fixture.plan.transaction_id,
                store_identity_fingerprint=fixture.authorization.store_identity_fingerprint,
                database_path_fingerprint=fixture.authorization.database_path_fingerprint,
                promotion_request_fingerprint=fixture.plan.promotion_request.request_fingerprint,
                promotion_plan_fingerprint=fixture.plan.transaction_plan_fingerprint,
                promotion_result_fingerprint=fixture.result.result_fingerprint,
                knowledge_identity_ids=tuple(
                    item.knowledge_identity_id for item in fixture.plan.knowledge_identity_plans
                ),
                knowledge_version_plan_fingerprints=tuple(
                    item.version_plan_fingerprint for item in fixture.plan.version_plans
                ),
                memory_projection_fingerprints=tuple(
                    item.projection_fingerprint
                    for item in fixture.plan.memory_projection_plan.records
                ),
                approved_content_fingerprints=(fixture.content.content_fingerprint,),
                backup_policy_fingerprint=fp("backup-policy"),
                observed_at=FIXED_TIME + timedelta(minutes=2),
            )
    finally:
        _cleanup_files(fixture.store_dir)


def test_local_persistence_rejects_protected_or_confidential_content():
    with pytest.raises(ValueError):
        glmp.build_content_envelope(
            content_envelope_id="content-secret",
            knowledge_identity_id="knowledge-secret",
            candidate_id="candidate-secret",
            candidate_fingerprint=fp("candidate-secret"),
            candidate_kind="support_candidate",
            canonical_statement="contains token: secret",
            bounded_summary="safe summary",
            language_code="en",
            sensitivity="public",
            lineage_fingerprint=fp("lineage-secret"),
            transaction_plan_fingerprint=fp("plan-secret"),
            transaction_result_fingerprint=fp("result-secret"),
            persistence_approval_bundle_fingerprint=fp("bundle-secret"),
            created_at=FIXED_TIME,
        )

    with pytest.raises(ValueError):
        glmp.ApprovedKnowledgeContentEnvelope.model_validate(
            {
                "content_envelope_id": "content-confidential",
                "knowledge_identity_id": "knowledge-confidential",
                "candidate_id": "candidate-confidential",
                "candidate_fingerprint": fp("candidate-confidential"),
                "candidate_kind": "support_candidate",
                "canonical_statement": "bounded",
                "bounded_summary": "bounded",
                "language_code": "en",
                "sensitivity": "confidential",
                "content_fingerprint": fp("content-confidential"),
                "lineage_fingerprint": fp("lineage-confidential"),
                "transaction_plan_fingerprint": fp("plan-confidential"),
                "transaction_result_fingerprint": fp("result-confidential"),
                "persistence_approval_bundle_fingerprint": fp("bundle-confidential"),
                "created_at": FIXED_TIME,
                "expires_at": FIXED_TIME + timedelta(hours=1),
                "envelope_fingerprint": fp("envelope-confidential"),
            }
        )
