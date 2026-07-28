"""SQLite-backed isolated local append-only GLM persistence service."""

from __future__ import annotations

import json
import os
import sqlite3
from collections import defaultdict
from collections.abc import Mapping
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from aion_brain.contracts.governed_learning_memory import (
    PromotionRequestKind,
)
from aion_brain.contracts.governed_learning_memory_persistence import (
    APPROVAL_RECORD_ID,
    AUTHORIZATION_TRANSACTION_ID,
    LOCAL_PERSISTENCE_CONTRACT_SCHEMA_VERSION,
    SQLITE_APPLICATION_ID,
    SQLITE_USER_VERSION,
    ZERO_HASH,
    LocalBackupStatus,
    LocalKnowledgeQuery,
    LocalKnowledgeQueryResult,
    LocalPersistenceAuthorizationEnvelope,
    LocalPersistenceError,
    LocalPersistenceMode,
    LocalPersistenceOperation,
    LocalProjectionQuery,
    LocalProjectionQueryResult,
    LocalRestoreStatus,
    LocalStoreBackupManifest,
    LocalStoreCheckpoint,
    LocalStoreIntegrityFinding,
    LocalStoreIntegrityReport,
    LocalStoreIntegrityStatus,
    LocalStoreRestorePlan,
    LocalStoreRestoreResult,
    PersistenceApprovalBundle,
    PersistenceLedgerEvent,
    PersistenceTransactionReceipt,
    PersistenceTransactionRequest,
    PersistentApprovalBinding,
    PersistentBeliefProjectionCandidateRecord,
    PersistentCandidateEvidenceReceipt,
    PersistentKnowledgeEventType,
    PersistentKnowledgeIdentity,
    PersistentKnowledgeVersion,
    PersistentMemoryProjectionRecord,
    PersistentProjectionType,
    build_model,
    model_fingerprint,
    persistence_fingerprint,
    target_to_projection_type,
)
from aion_brain.governed_learning_memory.local_persistence_policy import (
    ValidatedLocalStorePath,
    database_path_fingerprint,
    validate_database_path,
)
from aion_brain.governed_learning_memory.local_sqlite_schema import (
    APPLICATION_TABLES,
    CREATE_SCHEMA_SQL,
    EXPECTED_INDEX_NAMES,
    EXPECTED_SQLITE_PRAGMAS,
    EXPECTED_TRIGGER_NAMES,
    SCHEMA_FINGERPRINT,
)

MAXIMUM_DATABASE_BYTES = 1_073_741_824
MAXIMUM_BACKUP_BYTES = 1_073_741_824


class ControlledLocalAppendOnlyPersistenceService:
    """Explicit operator-invoked local store controller."""

    def __init__(self, *, repo_root: Path) -> None:
        self.repo_root = repo_root.resolve()

    def initialize_store(
        self,
        *,
        database_path: str | Path,
        authorization: LocalPersistenceAuthorizationEnvelope,
        created_at: datetime | None = None,
    ) -> LocalStoreIntegrityReport:
        checked = self.validate_store_path(
            database_path,
            mode=authorization.mode,
            operation=LocalPersistenceOperation.INITIALIZE,
        )
        self.validate_authorization(authorization, checked)
        fd = os.open(
            checked.absolute_path,
            os.O_CREAT | os.O_EXCL | os.O_WRONLY,
            0o600,
        )
        os.close(fd)
        try:
            with closing(
                self._connect(checked.absolute_path, read_only=False, bootstrap=True)
            ) as conn:
                self._apply_bootstrap_pragmas(conn)
                conn.executescript(CREATE_SCHEMA_SQL)
                now = _timestamp(created_at)
                metadata_fingerprint = persistence_fingerprint(
                    {
                        "store_id": authorization.store_id,
                        "store_identity_fingerprint": authorization.store_identity_fingerprint,
                        "schema_version": LOCAL_PERSISTENCE_CONTRACT_SCHEMA_VERSION,
                        "schema_fingerprint": SCHEMA_FINGERPRINT,
                        "application_id": SQLITE_APPLICATION_ID,
                        "authorization_transaction_id": AUTHORIZATION_TRANSACTION_ID,
                        "created_at": now,
                    }
                )
                conn.execute(
                    """
                    INSERT INTO glm_store_metadata (
                      store_id,
                      store_identity_fingerprint,
                      schema_version,
                      schema_fingerprint,
                      application_id,
                      authorization_transaction_id,
                      created_at,
                      status,
                      metadata_fingerprint
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        authorization.store_id,
                        authorization.store_identity_fingerprint,
                        LOCAL_PERSISTENCE_CONTRACT_SCHEMA_VERSION,
                        SCHEMA_FINGERPRINT,
                        SQLITE_APPLICATION_ID,
                        AUTHORIZATION_TRANSACTION_ID,
                        now,
                        "ready",
                        metadata_fingerprint,
                    ),
                )
                self._validate_open_store(conn)
                conn.commit()
            os.chmod(checked.absolute_path, 0o600)
        except Exception:
            try:
                checked.absolute_path.unlink(missing_ok=True)
                checked.absolute_path.with_suffix(checked.absolute_path.suffix + "-wal").unlink(
                    missing_ok=True
                )
                checked.absolute_path.with_suffix(checked.absolute_path.suffix + "-shm").unlink(
                    missing_ok=True
                )
            finally:
                raise
        return self.audit_store(database_path=checked.absolute_path, mode=authorization.mode)

    def open_store(
        self,
        *,
        database_path: str | Path,
        mode: LocalPersistenceMode = LocalPersistenceMode.SYNTHETIC_TEST,
    ) -> LocalStoreIntegrityReport:
        return self.audit_store(database_path=database_path, mode=mode)

    def validate_store_path(
        self,
        database_path: str | Path,
        *,
        mode: LocalPersistenceMode,
        operation: LocalPersistenceOperation,
    ) -> ValidatedLocalStorePath:
        return validate_database_path(
            database_path,
            mode=mode,
            operation=operation,
            repo_root=self.repo_root,
        )

    def validate_authorization(
        self,
        authorization: LocalPersistenceAuthorizationEnvelope,
        path: ValidatedLocalStorePath,
    ) -> None:
        if authorization.authorization_transaction_id != AUTHORIZATION_TRANSACTION_ID:
            raise LocalPersistenceError("local persistence authorization mismatch")
        if authorization.approval_record_id != APPROVAL_RECORD_ID:
            raise LocalPersistenceError("local persistence approval record mismatch")
        if path.database_path_fingerprint != authorization.database_path_fingerprint:
            raise LocalPersistenceError("database path fingerprint mismatch")
        if authorization.mode is not path.mode:
            raise LocalPersistenceError("authorization mode mismatch")
        now = datetime.now(UTC)
        if authorization.expires_at <= now:
            raise LocalPersistenceError("local persistence authorization expired")

    def validate_persistence_approvals(
        self,
        approval_bundle: PersistenceApprovalBundle,
    ) -> None:
        if approval_bundle.approval_status != "valid":
            raise LocalPersistenceError("persistence approval bundle is invalid")
        if approval_bundle.independent_approver_count < 2:
            raise LocalPersistenceError("dual persistence approval is required")
        if not approval_bundle.separation_of_duties_passed:
            raise LocalPersistenceError("approval separation of duties failed")

    def validate_transaction(self, request: PersistenceTransactionRequest) -> None:
        self.validate_persistence_approvals(request.persistence_approval_bundle)
        request.model_validate(request.model_dump(mode="python"))

    def persist_transaction(
        self,
        *,
        database_path: str | Path,
        request: PersistenceTransactionRequest,
        mode: LocalPersistenceMode = LocalPersistenceMode.SYNTHETIC_TEST,
        created_at: datetime | None = None,
    ) -> PersistenceTransactionReceipt:
        checked = self.validate_store_path(
            database_path,
            mode=mode,
            operation=LocalPersistenceOperation.PERSIST,
        )
        self.validate_authorization(request.local_authorization_envelope, checked)
        self.validate_transaction(request)
        now = _timestamp(created_at)
        with closing(self._connect(checked.absolute_path, read_only=False)) as conn:
            self._validate_open_store(conn)
            existing = conn.execute(
                """
                SELECT request_fingerprint
                FROM glm_persistence_transactions
                WHERE transaction_id = ?
                """,
                (request.promotion_transaction_plan.transaction_id,),
            ).fetchone()
            if existing is not None:
                if existing["request_fingerprint"] != request.request_fingerprint:
                    raise LocalPersistenceError("changed transaction replay rejected")
                return self._existing_receipt(conn, request, idempotent=True)
            promotion_result_reuse = conn.execute(
                """
                SELECT transaction_id
                FROM glm_persistence_transactions
                WHERE promotion_result_fingerprint = ?
                """,
                (request.promotion_transaction_result.result_fingerprint,),
            ).fetchone()
            if promotion_result_reuse is not None:
                raise LocalPersistenceError("promotion result replay requires new approvals")

            try:
                conn.execute("BEGIN IMMEDIATE")
                if conn.execute(
                    "SELECT 1 FROM glm_persistence_transactions WHERE transaction_id = ?",
                    (request.promotion_transaction_plan.transaction_id,),
                ).fetchone():
                    return self._existing_receipt(conn, request, idempotent=True)
                rows = self._build_persistent_rows(request)
                ledger_head_before, last_sequence = self._ledger_head(conn)
                events = self._build_ledger_events(
                    request=request,
                    rows=rows,
                    ledger_head_before=ledger_head_before,
                    start_sequence=last_sequence + 1,
                    created_at=now,
                )
                self._insert_transaction(conn, request, rows, events, now, ledger_head_before)
                self._insert_rows(conn, rows)
                self._insert_events(conn, events)
                receipt = self._receipt_from_rows(
                    request=request,
                    rows=rows,
                    events=events,
                    ledger_head_before=ledger_head_before,
                    idempotent=False,
                    created_at=now,
                )
                self._verify_read_after_write(conn, receipt)
                conn.commit()
            except Exception:
                conn.rollback()
                raise
        with closing(self._connect(checked.absolute_path, read_only=True)) as read_conn:
            self._validate_open_store(read_conn)
            self._verify_read_after_write(read_conn, receipt)
        return receipt

    def query_knowledge(
        self,
        *,
        database_path: str | Path,
        query: LocalKnowledgeQuery,
        mode: LocalPersistenceMode = LocalPersistenceMode.SYNTHETIC_TEST,
    ) -> LocalKnowledgeQueryResult:
        checked = self.validate_store_path(
            database_path,
            mode=mode,
            operation=LocalPersistenceOperation.QUERY,
        )
        with closing(self._connect(checked.absolute_path, read_only=True)) as conn:
            if query.store_id is not None and query.store_id != self._store_id(conn):
                versions: tuple[PersistentKnowledgeVersion, ...] = ()
            else:
                where, params = _knowledge_filters(query)
                records = conn.execute(
                    f"""
                    SELECT payload_json
                    FROM glm_knowledge_versions
                    {where}
                    ORDER BY knowledge_identity_id, version_number, knowledge_version_id
                    LIMIT ?
                    """,
                    (*params, query.limit),
                ).fetchall()
                versions = tuple(
                    PersistentKnowledgeVersion.model_validate_json(row["payload_json"])
                    for row in records
                )
        return build_model(
            LocalKnowledgeQueryResult,
            {
                "query_fingerprint": query.query_fingerprint,
                "records": versions,
                "result_count": len(versions),
            },
            "result_fingerprint",
        )

    def query_projections(
        self,
        *,
        database_path: str | Path,
        query: LocalProjectionQuery,
        mode: LocalPersistenceMode = LocalPersistenceMode.SYNTHETIC_TEST,
    ) -> LocalProjectionQueryResult:
        checked = self.validate_store_path(
            database_path,
            mode=mode,
            operation=LocalPersistenceOperation.QUERY,
        )
        with closing(self._connect(checked.absolute_path, read_only=True)) as conn:
            where, params = _projection_filters(query, belief=False)
            memory_rows = conn.execute(
                f"""
                SELECT payload_json
                FROM glm_memory_projection_records
                {where}
                ORDER BY projection_type, projection_record_id
                LIMIT ?
                """,
                (*params, query.limit),
            ).fetchall()
            belief_where, belief_params = _projection_filters(query, belief=True)
            belief_rows = conn.execute(
                f"""
                SELECT payload_json
                FROM glm_belief_projection_candidates
                {belief_where}
                ORDER BY belief_candidate_id
                LIMIT ?
                """,
                (*belief_params, query.limit),
            ).fetchall()
            memory_records = tuple(
                PersistentMemoryProjectionRecord.model_validate_json(row["payload_json"])
                for row in memory_rows
            )
            belief_records = tuple(
                PersistentBeliefProjectionCandidateRecord.model_validate_json(row["payload_json"])
                for row in belief_rows
            )
        total = len(memory_records) + len(belief_records)
        if total > query.limit:
            memory_records = memory_records[: query.limit]
            belief_records = belief_records[: max(0, query.limit - len(memory_records))]
            total = len(memory_records) + len(belief_records)
        return build_model(
            LocalProjectionQueryResult,
            {
                "query_fingerprint": query.query_fingerprint,
                "memory_projection_records": memory_records,
                "belief_candidate_records": belief_records,
                "result_count": total,
            },
            "result_fingerprint",
        )

    def audit_store(
        self,
        *,
        database_path: str | Path,
        mode: LocalPersistenceMode = LocalPersistenceMode.SYNTHETIC_TEST,
    ) -> LocalStoreIntegrityReport:
        checked = self.validate_store_path(
            database_path,
            mode=mode,
            operation=LocalPersistenceOperation.AUDIT,
        )
        findings: list[LocalStoreIntegrityFinding] = []
        global_ok = False
        tx_ok = False
        triggers_ok = False
        content_ok = True
        production_ok = True
        belief_ok = True
        automatic_ok = True
        try:
            with closing(self._connect(checked.absolute_path, read_only=True)) as conn:
                self._validate_open_store(conn)
                triggers_ok = self._expected_triggers_present(conn)
                global_ok, tx_ok = self._validate_hash_chains(conn)
                content_ok, production_ok, belief_ok, automatic_ok = (
                    self._validate_no_prohibited_markers(conn)
                )
                self._add_finding(
                    findings,
                    "schema-and-pragmas",
                    True,
                    ("schema_bootstrap_passed",),
                    (),
                    (SCHEMA_FINGERPRINT,),
                )
                self._add_finding(
                    findings,
                    "append-only-triggers",
                    triggers_ok,
                    ("append_only_enforced",),
                    (),
                    (),
                )
                self._add_finding(
                    findings,
                    "global-hash-chain",
                    global_ok,
                    ("global_hash_chain_passed",),
                    (),
                    (),
                )
                self._add_finding(
                    findings,
                    "transaction-hash-chain",
                    tx_ok,
                    ("transaction_hash_chain_passed",),
                    (),
                    (),
                )
        except Exception:
            self._add_finding(
                findings,
                "integrity-exception",
                False,
                ("integrity_failed",),
                (),
                (),
            )
        return build_model(
            LocalStoreIntegrityReport,
            {
                "report_id": "local-store-integrity",
                "store_id": self._store_id_or_unknown(database_path),
                "status": LocalStoreIntegrityStatus.PASSED
                if all(f.status is LocalStoreIntegrityStatus.PASSED for f in findings)
                and triggers_ok
                and global_ok
                and tx_ok
                and content_ok
                and production_ok
                and belief_ok
                and automatic_ok
                else LocalStoreIntegrityStatus.FAILED,
                "findings": tuple(findings),
                "finding_count": len(findings),
                "global_hash_chain_passed": global_ok,
                "transaction_hash_chain_passed": tx_ok,
                "append_only_triggers_present": triggers_ok,
                "no_prohibited_content": content_ok,
                "no_production_memory_markers": production_ok,
                "no_actual_belief_markers": belief_ok,
                "no_automatic_promotion_markers": automatic_ok,
            },
            "report_fingerprint",
        )

    def checkpoint_store(
        self,
        *,
        database_path: str | Path,
        mode: LocalPersistenceMode = LocalPersistenceMode.SYNTHETIC_TEST,
        created_at: datetime | None = None,
    ) -> LocalStoreCheckpoint:
        checked = self.validate_store_path(
            database_path,
            mode=mode,
            operation=LocalPersistenceOperation.CHECKPOINT,
        )
        with closing(self._connect(checked.absolute_path, read_only=False)) as conn:
            self._validate_open_store(conn)
            result = conn.execute("PRAGMA wal_checkpoint(FULL)").fetchone()
            ledger_head, sequence = self._ledger_head(conn)
            store_id = self._store_id(conn)
        return build_model(
            LocalStoreCheckpoint,
            {
                "checkpoint_id": f"checkpoint-{sequence}",
                "store_id": store_id,
                "ledger_head": ledger_head,
                "last_ledger_sequence": sequence,
                "checkpoint_mode": "FULL",
                "sqlite_checkpoint_result": tuple(result or (0, 0, 0)),
                "database_fingerprint": self._file_fingerprint(checked.absolute_path),
                "created_at": _dt(created_at),
            },
            "checkpoint_fingerprint",
        )

    def backup_store(
        self,
        *,
        database_path: str | Path,
        backup_path: str | Path,
        manifest_path: str | Path,
        mode: LocalPersistenceMode = LocalPersistenceMode.SYNTHETIC_TEST,
        created_at: datetime | None = None,
    ) -> LocalStoreBackupManifest:
        source = self.validate_store_path(
            database_path,
            mode=mode,
            operation=LocalPersistenceOperation.BACKUP
            if not Path(database_path).exists()
            else LocalPersistenceOperation.AUDIT,
        )
        backup = self.validate_store_path(
            backup_path,
            mode=mode,
            operation=LocalPersistenceOperation.BACKUP,
        )
        manifest = self.validate_store_path(
            manifest_path,
            mode=mode,
            operation=LocalPersistenceOperation.BACKUP,
        )
        source_report = self.audit_store(database_path=source.absolute_path, mode=mode)
        if source_report.status is not LocalStoreIntegrityStatus.PASSED:
            raise LocalPersistenceError("source integrity failed before backup")
        with closing(self._connect(source.absolute_path, read_only=True)) as src:
            store_id = self._store_id(src)
            store_identity_fp = self._store_identity_fingerprint(src)
            ledger_head, sequence = self._ledger_head(src)
            with closing(self._connect(backup.absolute_path, read_only=False, uri=False)) as dst:
                src.backup(dst)
        os.chmod(backup.absolute_path, 0o600)
        if backup.absolute_path.stat().st_size > MAXIMUM_BACKUP_BYTES:
            raise LocalPersistenceError("backup exceeds size limit")
        backup_report = self.audit_store(database_path=backup.absolute_path, mode=mode)
        if backup_report.status is not LocalStoreIntegrityStatus.PASSED:
            raise LocalPersistenceError("backup integrity failed")
        manifest_model = build_model(
            LocalStoreBackupManifest,
            {
                "backup_manifest_id": f"backup-{sequence}",
                "store_id": store_id,
                "store_identity_fingerprint": store_identity_fp,
                "schema_version_value": LOCAL_PERSISTENCE_CONTRACT_SCHEMA_VERSION,
                "application_id": SQLITE_APPLICATION_ID,
                "last_ledger_sequence": sequence,
                "ledger_head_hash": ledger_head,
                "source_database_fingerprint": self._file_fingerprint(source.absolute_path),
                "backup_database_fingerprint": self._file_fingerprint(backup.absolute_path),
                "backup_path_fingerprint": database_path_fingerprint(backup.absolute_path),
                "backup_size": backup.absolute_path.stat().st_size,
                "created_at": _dt(created_at),
                "integrity_status": LocalBackupStatus.CREATED,
            },
            "manifest_fingerprint",
        )
        _write_private_json(manifest.absolute_path, manifest_model)
        return manifest_model

    def plan_restore(
        self,
        *,
        backup_manifest: LocalStoreBackupManifest,
        destination_path: str | Path,
        mode: LocalPersistenceMode = LocalPersistenceMode.SYNTHETIC_TEST,
        created_at: datetime | None = None,
    ) -> LocalStoreRestorePlan:
        destination = self.validate_store_path(
            destination_path,
            mode=mode,
            operation=LocalPersistenceOperation.RESTORE,
        )
        return build_model(
            LocalStoreRestorePlan,
            {
                "restore_plan_id": f"restore-{backup_manifest.backup_manifest_id}",
                "backup_manifest_id": backup_manifest.backup_manifest_id,
                "backup_database_fingerprint": backup_manifest.backup_database_fingerprint,
                "backup_path_fingerprint": backup_manifest.backup_path_fingerprint,
                "destination_path_fingerprint": destination.database_path_fingerprint,
                "created_at": _dt(created_at),
            },
            "plan_fingerprint",
        )

    def restore_to_new_store(
        self,
        *,
        backup_path: str | Path,
        restore_plan: LocalStoreRestorePlan,
        destination_path: str | Path,
        backup_manifest: LocalStoreBackupManifest,
        mode: LocalPersistenceMode = LocalPersistenceMode.SYNTHETIC_TEST,
        created_at: datetime | None = None,
    ) -> LocalStoreRestoreResult:
        backup = self.validate_store_path(
            backup_path,
            mode=mode,
            operation=LocalPersistenceOperation.AUDIT,
        )
        destination = self.validate_store_path(
            destination_path,
            mode=mode,
            operation=LocalPersistenceOperation.RESTORE,
        )
        if database_path_fingerprint(backup.absolute_path) != restore_plan.backup_path_fingerprint:
            raise LocalPersistenceError("restore backup path fingerprint mismatch")
        if (
            self._file_fingerprint(backup.absolute_path)
            != backup_manifest.backup_database_fingerprint
        ):
            raise LocalPersistenceError("restore backup fingerprint mismatch")
        with closing(self._connect(backup.absolute_path, read_only=True)) as src:
            with closing(
                self._connect(destination.absolute_path, read_only=False, uri=False)
            ) as dst:
                src.backup(dst)
        os.chmod(destination.absolute_path, 0o600)
        report = self.audit_store(database_path=destination.absolute_path, mode=mode)
        with closing(self._connect(destination.absolute_path, read_only=True)) as conn:
            store_id = self._store_id(conn)
            ledger_head, sequence = self._ledger_head(conn)
        return build_model(
            LocalStoreRestoreResult,
            {
                "restore_result_id": f"restore-result-{restore_plan.restore_plan_id}",
                "restore_plan_id": restore_plan.restore_plan_id,
                "store_id": store_id,
                "status": LocalRestoreStatus.RESTORED_TO_NEW_STORE,
                "source_manifest_fingerprint": backup_manifest.manifest_fingerprint,
                "restored_database_fingerprint": self._file_fingerprint(destination.absolute_path),
                "restored_path_fingerprint": destination.database_path_fingerprint,
                "restored_ledger_head_hash": ledger_head,
                "restored_last_ledger_sequence": sequence,
                "integrity_status": report.status,
                "created_at": _dt(created_at),
            },
            "result_fingerprint",
        )

    def close(self) -> None:
        return None

    def _connect(
        self,
        path: Path,
        *,
        read_only: bool,
        bootstrap: bool = False,
        uri: bool = True,
    ) -> sqlite3.Connection:
        target = f"file:{path.as_posix()}?mode=ro" if read_only and uri else path.as_posix()
        conn = sqlite3.connect(target, uri=read_only and uri, isolation_level=None)
        conn.row_factory = sqlite3.Row
        if hasattr(conn, "enable_load_extension"):
            conn.enable_load_extension(False)
        self._apply_runtime_pragmas(conn, read_only=read_only)
        if not bootstrap:
            self._install_authorizer(conn, read_only=read_only)
        return conn

    def _apply_bootstrap_pragmas(self, conn: sqlite3.Connection) -> None:
        self._apply_runtime_pragmas(conn, read_only=False)
        conn.execute(f"PRAGMA application_id={SQLITE_APPLICATION_ID}")
        conn.execute(f"PRAGMA user_version={SQLITE_USER_VERSION}")

    def _apply_runtime_pragmas(self, conn: sqlite3.Connection, *, read_only: bool) -> None:
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=FULL")
        conn.execute("PRAGMA busy_timeout=5000")
        conn.execute("PRAGMA trusted_schema=OFF")
        conn.execute("PRAGMA recursive_triggers=OFF")
        conn.execute("PRAGMA auto_vacuum=NONE")
        conn.execute("PRAGMA temp_store=MEMORY")
        if read_only:
            conn.execute("PRAGMA query_only=ON")

    def _install_authorizer(self, conn: sqlite3.Connection, *, read_only: bool) -> None:
        denied = {
            getattr(sqlite3, "SQLITE_ATTACH", -1),
            getattr(sqlite3, "SQLITE_DETACH", -1),
            getattr(sqlite3, "SQLITE_ALTER_TABLE", -1),
            getattr(sqlite3, "SQLITE_DROP_TABLE", -1),
            getattr(sqlite3, "SQLITE_DROP_INDEX", -1),
            getattr(sqlite3, "SQLITE_DROP_TRIGGER", -1),
            getattr(sqlite3, "SQLITE_DROP_VIEW", -1),
            getattr(sqlite3, "SQLITE_CREATE_TABLE", -1),
            getattr(sqlite3, "SQLITE_CREATE_TRIGGER", -1),
            getattr(sqlite3, "SQLITE_CREATE_VIEW", -1),
            getattr(sqlite3, "SQLITE_CREATE_INDEX", -1),
        }
        read_denied = {
            getattr(sqlite3, "SQLITE_INSERT", -1),
            getattr(sqlite3, "SQLITE_UPDATE", -1),
            getattr(sqlite3, "SQLITE_DELETE", -1),
        }
        allowed_pragmas = {
            "foreign_keys",
            "journal_mode",
            "synchronous",
            "busy_timeout",
            "trusted_schema",
            "recursive_triggers",
            "auto_vacuum",
            "temp_store",
            "application_id",
            "user_version",
            "integrity_check",
            "foreign_key_check",
            "query_only",
            "wal_checkpoint",
        }

        def authorizer(action: int, arg1: str | None, _arg2: str | None, *_: Any) -> int:
            if action in denied:
                return sqlite3.SQLITE_DENY
            if read_only and action in read_denied:
                return sqlite3.SQLITE_DENY
            if action == getattr(sqlite3, "SQLITE_PRAGMA", -2):
                pragma = (arg1 or "").lower()
                if pragma not in allowed_pragmas:
                    return sqlite3.SQLITE_DENY
            return sqlite3.SQLITE_OK

        conn.set_authorizer(authorizer)

    def _validate_open_store(self, conn: sqlite3.Connection) -> None:
        if conn.execute("PRAGMA application_id").fetchone()[0] != SQLITE_APPLICATION_ID:
            raise LocalPersistenceError("SQLite application_id mismatch")
        if conn.execute("PRAGMA user_version").fetchone()[0] != SQLITE_USER_VERSION:
            raise LocalPersistenceError("SQLite user_version mismatch")
        for name, expected in EXPECTED_SQLITE_PRAGMAS.items():
            actual = conn.execute(f"PRAGMA {name}").fetchone()[0]
            if isinstance(expected, str):
                if str(actual).lower() != expected:
                    raise LocalPersistenceError(f"SQLite pragma mismatch: {name}")
            elif actual != expected:
                raise LocalPersistenceError(f"SQLite pragma mismatch: {name}")
        table_rows = conn.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type='table' AND name LIKE 'glm_%'
            ORDER BY name
            """
        ).fetchall()
        tables = tuple(row["name"] for row in table_rows)
        if tables != tuple(sorted(APPLICATION_TABLES)):
            raise LocalPersistenceError("SQLite application table set mismatch")
        trigger_rows = conn.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type='trigger' AND name LIKE 'glm_%'
            ORDER BY name
            """
        ).fetchall()
        if tuple(row["name"] for row in trigger_rows) != tuple(sorted(EXPECTED_TRIGGER_NAMES)):
            raise LocalPersistenceError("SQLite trigger set mismatch")
        index_rows = conn.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type='index' AND name LIKE 'idx_glm_%'
            ORDER BY name
            """
        ).fetchall()
        if tuple(row["name"] for row in index_rows) != tuple(sorted(EXPECTED_INDEX_NAMES)):
            raise LocalPersistenceError("SQLite index set mismatch")
        metadata = conn.execute("SELECT * FROM glm_store_metadata").fetchall()
        if len(metadata) != 1:
            raise LocalPersistenceError("store metadata mismatch")
        if metadata[0]["schema_fingerprint"] != SCHEMA_FINGERPRINT:
            raise LocalPersistenceError("schema fingerprint mismatch")
        if conn.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise LocalPersistenceError("SQLite integrity check failed")
        if conn.execute("PRAGMA foreign_key_check").fetchall():
            raise LocalPersistenceError("SQLite foreign key check failed")

    def _build_persistent_rows(
        self,
        request: PersistenceTransactionRequest,
    ) -> dict[str, tuple[BaseModel, ...]]:
        plan = request.promotion_transaction_plan
        result = request.promotion_transaction_result
        approval_bundle_fp = request.persistence_approval_bundle.bundle_fingerprint
        content_by_identity = {
            item.knowledge_identity_id: item for item in request.approved_content_envelopes
        }
        snapshots_by_candidate = {item.candidate_id: item for item in plan.eligibility_snapshots}
        version_by_identity = {item.knowledge_identity_id: item for item in plan.version_plans}
        knowledge_versions: list[PersistentKnowledgeVersion] = []
        identities: list[PersistentKnowledgeIdentity] = []
        receipts: list[PersistentCandidateEvidenceReceipt] = []
        for identity_plan in plan.knowledge_identity_plans:
            identities.append(
                build_model(
                    PersistentKnowledgeIdentity,
                    {
                        "knowledge_identity_id": identity_plan.knowledge_identity_id,
                        "claim_identity_fingerprint": identity_plan.claim_identity_fingerprint,
                        "valid_time_fingerprint": identity_plan.target_valid_time_fingerprint,
                        "jurisdiction_fingerprint": identity_plan.jurisdiction_scope_fingerprint,
                        "version_scope_fingerprint": identity_plan.version_scope_fingerprint,
                        "created_transaction_id": plan.transaction_id,
                    },
                    "identity_fingerprint",
                )
            )
            snapshot = snapshots_by_candidate[identity_plan.candidate_id]
            receipts.append(
                build_model(
                    PersistentCandidateEvidenceReceipt,
                    {
                        "candidate_receipt_id": f"receipt-{identity_plan.candidate_id}",
                        "transaction_id": plan.transaction_id,
                        "candidate_id": identity_plan.candidate_id,
                        "candidate_fingerprint": identity_plan.candidate_fingerprint,
                        "lineage_fingerprint": identity_plan.lineage_fingerprint,
                        "eligibility_fingerprint": snapshot.snapshot_fingerprint,
                        "candidate_integrity_fingerprint": snapshot.candidate_integrity_fingerprint,
                        "promotion_plan_fingerprint": plan.transaction_plan_fingerprint,
                        "promotion_result_fingerprint": result.result_fingerprint,
                    },
                    "receipt_fingerprint",
                )
            )
            version_plan = version_by_identity[identity_plan.knowledge_identity_id]
            content = content_by_identity[identity_plan.knowledge_identity_id]
            knowledge_versions.append(
                build_model(
                    PersistentKnowledgeVersion,
                    {
                        "knowledge_version_id": _knowledge_version_id(version_plan),
                        "knowledge_identity_id": version_plan.knowledge_identity_id,
                        "version_number": version_plan.planned_version_number,
                        "event_type": _event_type(version_plan.request_kind),
                        "candidate_posture": version_plan.candidate_kind.value,
                        "candidate_id": version_plan.candidate_id,
                        "approved_bounded_statement": content.canonical_statement,
                        "bounded_summary": content.bounded_summary,
                        "language_code": content.language_code,
                        "sensitivity": content.sensitivity,
                        "content_fingerprint": content.content_fingerprint,
                        "candidate_fingerprint": version_plan.candidate_fingerprint,
                        "lineage_fingerprint": version_plan.lineage_fingerprint,
                        "approval_bundle_fingerprint": approval_bundle_fp,
                        "promotion_plan_fingerprint": plan.transaction_plan_fingerprint,
                        "promotion_result_fingerprint": result.result_fingerprint,
                        "confidence_cap": version_plan.candidate_confidence_cap,
                        "valid_from": version_plan.effective_from,
                        "valid_to": version_plan.effective_to,
                        "supersedes_version_id": version_plan.supersedes_version_id,
                        "retracts_version_id": version_plan.retracts_version_id,
                        "expires_version_id": version_plan.expires_version_id,
                        "created_transaction_id": plan.transaction_id,
                    },
                    "version_fingerprint",
                )
            )
        version_id_by_identity = {
            item.knowledge_identity_id: item.knowledge_version_id for item in knowledge_versions
        }
        approval_bindings = tuple(
            build_model(
                PersistentApprovalBinding,
                {
                    "binding_id": f"binding-{record.approval_evidence_id}",
                    "transaction_id": plan.transaction_id,
                    "role": record.role,
                    "action_type": record.action_type,
                    "approval_scope_fingerprint": record.approval_scope_fingerprint,
                    "request_fingerprint": record.request_fingerprint,
                    "decision_fingerprint": record.decision_fingerprint,
                    "approver_identity_fingerprint": record.approver_identity_fingerprint,
                    "transaction_binding_fingerprint": record.transaction_binding_fingerprint,
                },
                "binding_fingerprint",
            )
            for record in request.persistence_approval_bundle.evidence_records
        )
        projections: list[PersistentMemoryProjectionRecord] = []
        belief_candidates: list[PersistentBeliefProjectionCandidateRecord] = []
        for record in plan.memory_projection_plan.records:
            projection_type = target_to_projection_type(record.target)
            version_id = version_id_by_identity[record.knowledge_identity_id]
            if projection_type is PersistentProjectionType.BELIEF_CANDIDATE:
                belief_candidates.append(
                    build_model(
                        PersistentBeliefProjectionCandidateRecord,
                        {
                            "belief_candidate_id": f"belief-candidate-{record.planned_record_id}",
                            "transaction_id": plan.transaction_id,
                            "knowledge_identity_id": record.knowledge_identity_id,
                            "knowledge_version_id": version_id,
                            "proposed_posture": "belief_candidate_only",
                            "confidence_cap": record.confidence_cap,
                            "uncertainty_fingerprint": persistence_fingerprint(
                                {
                                    "projection": record.projection_fingerprint,
                                    "field": "uncertainty",
                                }
                            ),
                            "contradiction_fingerprint": persistence_fingerprint(
                                {
                                    "projection": record.projection_fingerprint,
                                    "field": "contradiction",
                                }
                            ),
                            "provenance_fingerprints": tuple(
                                sorted(record.evidence_reference_fingerprints)
                            ),
                            "candidate_fingerprint": record.projection_fingerprint,
                        },
                        "candidate_fingerprint",
                    )
                )
                continue
            projections.append(
                build_model(
                    PersistentMemoryProjectionRecord,
                    {
                        "projection_record_id": record.planned_record_id,
                        "projection_type": projection_type.value,
                        "transaction_id": plan.transaction_id,
                        "knowledge_identity_id": record.knowledge_identity_id,
                        "knowledge_version_id": version_id,
                        "content_reference_fingerprint": record.content_reference_fingerprint,
                        "summary": f"redacted {projection_type.value} projection",
                        "confidence_cap": record.confidence_cap,
                        "sensitivity": "internal"
                        if _enum_value(record.sensitivity) == "internal"
                        else "public",
                        "owner_scope_fingerprints": tuple(sorted(record.owner_scope_fingerprints)),
                        "provenance_fingerprints": tuple(
                            sorted(record.evidence_reference_fingerprints)
                        ),
                        "created_transaction_id": plan.transaction_id,
                    },
                    "projection_fingerprint",
                )
            )
        memory_projection_rows: tuple[PersistentMemoryProjectionRecord, ...] = tuple(
            sorted(
                projections,
                key=lambda item: (item.projection_type, item.projection_record_id),
            )
        )
        return {
            "approval_bindings": approval_bindings,
            "candidate_receipts": tuple(receipts),
            "knowledge_identities": tuple(identities),
            "knowledge_versions": tuple(knowledge_versions),
            "memory_projections": memory_projection_rows,
            "belief_candidates": tuple(belief_candidates),
        }

    def _build_ledger_events(
        self,
        *,
        request: PersistenceTransactionRequest,
        rows: Mapping[str, tuple[BaseModel, ...]],
        ledger_head_before: str,
        start_sequence: int,
        created_at: str,
    ) -> tuple[PersistenceLedgerEvent, ...]:
        tx_id = request.promotion_transaction_plan.transaction_id
        transaction_fp = self._transaction_fingerprint(request, rows)
        event_specs: list[tuple[str, str, str, str]] = [
            ("transaction_opened", "glm_persistence_transactions", tx_id, transaction_fp),
        ]
        for key, event_type, record_type in (
            ("approval_bindings", "approval_binding_persisted", "glm_approval_bindings"),
            (
                "candidate_receipts",
                "candidate_evidence_receipt_persisted",
                "glm_candidate_evidence_receipts",
            ),
            (
                "knowledge_identities",
                "knowledge_identity_persisted",
                "glm_knowledge_identities",
            ),
            (
                "knowledge_versions",
                "knowledge_version_persisted",
                "glm_knowledge_versions",
            ),
            (
                "memory_projections",
                "memory_projection_record_persisted",
                "glm_memory_projection_records",
            ),
            (
                "belief_candidates",
                "belief_candidate_record_persisted",
                "glm_belief_projection_candidates",
            ),
        ):
            for model in rows[key]:
                event_specs.append(
                    (
                        event_type,
                        record_type,
                        _model_record_id(model),
                        _model_record_fingerprint(model),
                    )
                )
        event_specs.append(
            ("transaction_committed", "glm_persistence_transactions", tx_id, transaction_fp)
        )
        global_previous = ledger_head_before
        transaction_previous = ZERO_HASH
        events: list[PersistenceLedgerEvent] = []
        for index, (event_type, record_type, record_id, record_fp) in enumerate(
            event_specs,
            start=1,
        ):
            global_sequence = start_sequence + index - 1
            global_hash = persistence_fingerprint(
                {
                    "store_id": request.store_id,
                    "global_sequence": global_sequence,
                    "transaction_id": tx_id,
                    "transaction_sequence": index,
                    "event_type": event_type,
                    "record_type": record_type,
                    "record_id": record_id,
                    "record_fingerprint": record_fp,
                    "previous_global_hash": global_previous,
                    "previous_transaction_hash": transaction_previous,
                    "created_at": created_at,
                }
            )
            tx_hash = persistence_fingerprint(
                {
                    "transaction_id": tx_id,
                    "transaction_sequence": index,
                    "event_type": event_type,
                    "record_type": record_type,
                    "record_id": record_id,
                    "record_fingerprint": record_fp,
                    "previous_transaction_hash": transaction_previous,
                    "created_at": created_at,
                }
            )
            event = PersistenceLedgerEvent(
                global_sequence=global_sequence,
                transaction_id=tx_id,
                transaction_sequence=index,
                event_type=event_type,
                record_type=record_type,
                record_id=record_id,
                record_fingerprint=record_fp,
                previous_global_hash=global_previous,
                global_event_hash=global_hash,
                previous_transaction_hash=transaction_previous,
                transaction_event_hash=tx_hash,
                created_at=_parse_ts(created_at),
            )
            events.append(event)
            global_previous = global_hash
            transaction_previous = tx_hash
        return tuple(events)

    def _insert_transaction(
        self,
        conn: sqlite3.Connection,
        request: PersistenceTransactionRequest,
        rows: Mapping[str, tuple[BaseModel, ...]],
        events: tuple[PersistenceLedgerEvent, ...],
        created_at: str,
        ledger_head_before: str,
    ) -> None:
        plan = request.promotion_transaction_plan
        result = request.promotion_transaction_result
        transaction_fp = self._transaction_fingerprint(request, rows)
        conn.execute(
            """
            INSERT INTO glm_persistence_transactions (
              transaction_id,
              store_id,
              request_fingerprint,
              promotion_plan_fingerprint,
              promotion_result_fingerprint,
              persistence_authorization_fingerprint,
              approval_bundle_fingerprint,
              transaction_fingerprint,
              status,
              started_at,
              committed_at,
              ledger_start_sequence,
              ledger_end_sequence,
              ledger_head_before,
              ledger_head_after,
              transaction_chain_head,
              knowledge_identity_count,
              knowledge_version_count,
              projection_count,
              belief_candidate_count,
              candidate_receipt_count,
              payload_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                plan.transaction_id,
                request.store_id,
                request.request_fingerprint,
                plan.transaction_plan_fingerprint,
                result.result_fingerprint,
                request.local_authorization_envelope.envelope_fingerprint,
                request.persistence_approval_bundle.bundle_fingerprint,
                transaction_fp,
                "committed",
                created_at,
                created_at,
                events[0].global_sequence,
                events[-1].global_sequence,
                ledger_head_before,
                events[-1].global_event_hash,
                events[-1].transaction_event_hash,
                len(rows["knowledge_identities"]),
                len(rows["knowledge_versions"]),
                len(rows["memory_projections"]),
                len(rows["belief_candidates"]),
                len(rows["candidate_receipts"]),
                _json_dumps({"request_fingerprint": request.request_fingerprint}),
            ),
        )

    def _insert_rows(
        self,
        conn: sqlite3.Connection,
        rows: Mapping[str, tuple[BaseModel, ...]],
    ) -> None:
        for item in rows["approval_bindings"]:
            assert isinstance(item, PersistentApprovalBinding)
            conn.execute(
                """
                INSERT INTO glm_approval_bindings VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.binding_id,
                    item.transaction_id,
                    item.role,
                    item.action_type,
                    item.approval_scope_fingerprint,
                    item.request_fingerprint,
                    item.decision_fingerprint,
                    item.approver_identity_fingerprint,
                    item.transaction_binding_fingerprint,
                    0,
                    item.binding_fingerprint,
                    _model_json(item),
                ),
            )
        for item in rows["candidate_receipts"]:
            assert isinstance(item, PersistentCandidateEvidenceReceipt)
            conn.execute(
                """
                INSERT INTO glm_candidate_evidence_receipts VALUES (
                  ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
                """,
                (
                    item.candidate_receipt_id,
                    item.transaction_id,
                    item.candidate_id,
                    item.candidate_fingerprint,
                    item.lineage_fingerprint,
                    item.eligibility_fingerprint,
                    item.candidate_integrity_fingerprint,
                    item.promotion_plan_fingerprint,
                    item.promotion_result_fingerprint,
                    0,
                    item.receipt_fingerprint,
                    _model_json(item),
                ),
            )
        for item in rows["knowledge_identities"]:
            assert isinstance(item, PersistentKnowledgeIdentity)
            existing = conn.execute(
                """
                SELECT identity_fingerprint
                FROM glm_knowledge_identities
                WHERE knowledge_identity_id = ?
                """,
                (item.knowledge_identity_id,),
            ).fetchone()
            if existing and existing["identity_fingerprint"] != item.identity_fingerprint:
                raise LocalPersistenceError("knowledge identity collision rejected")
            if not existing:
                conn.execute(
                    """
                    INSERT INTO glm_knowledge_identities VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        item.knowledge_identity_id,
                        item.claim_identity_fingerprint,
                        item.valid_time_fingerprint,
                        item.jurisdiction_fingerprint,
                        item.version_scope_fingerprint,
                        item.created_transaction_id,
                        item.identity_fingerprint,
                        _model_json(item),
                    ),
                )
        for item in rows["knowledge_versions"]:
            assert isinstance(item, PersistentKnowledgeVersion)
            conn.execute(
                """
                INSERT INTO glm_knowledge_versions VALUES (
                  ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
                """,
                (
                    item.knowledge_version_id,
                    item.knowledge_identity_id,
                    item.version_number,
                    item.event_type.value,
                    item.candidate_posture,
                    item.candidate_id,
                    item.approved_bounded_statement,
                    item.bounded_summary,
                    item.language_code,
                    item.sensitivity,
                    item.content_fingerprint,
                    item.candidate_fingerprint,
                    item.lineage_fingerprint,
                    item.approval_bundle_fingerprint,
                    item.promotion_plan_fingerprint,
                    item.promotion_result_fingerprint,
                    f"{item.confidence_cap:.6f}",
                    _timestamp(item.valid_from),
                    _timestamp(item.valid_to) if item.valid_to else None,
                    item.supersedes_version_id,
                    item.retracts_version_id,
                    item.expires_version_id,
                    item.created_transaction_id,
                    item.version_fingerprint,
                    _model_json(item),
                ),
            )
        for item in rows["memory_projections"]:
            assert isinstance(item, PersistentMemoryProjectionRecord)
            conn.execute(
                """
                INSERT INTO glm_memory_projection_records VALUES (
                  ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
                """,
                (
                    item.projection_record_id,
                    item.projection_type,
                    item.transaction_id,
                    item.knowledge_identity_id,
                    item.knowledge_version_id,
                    item.content_reference_fingerprint,
                    item.summary,
                    f"{item.confidence_cap:.6f}",
                    item.sensitivity,
                    _json_dumps(item.owner_scope_fingerprints),
                    _json_dumps(item.provenance_fingerprints),
                    item.projection_fingerprint,
                    item.created_transaction_id,
                    0,
                    _model_json(item),
                ),
            )
        for item in rows["belief_candidates"]:
            assert isinstance(item, PersistentBeliefProjectionCandidateRecord)
            conn.execute(
                """
                INSERT INTO glm_belief_projection_candidates VALUES (
                  ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
                """,
                (
                    item.belief_candidate_id,
                    item.transaction_id,
                    item.knowledge_identity_id,
                    item.knowledge_version_id,
                    item.proposed_posture,
                    f"{item.confidence_cap:.6f}",
                    item.uncertainty_fingerprint,
                    item.contradiction_fingerprint,
                    _json_dumps(item.provenance_fingerprints),
                    item.candidate_fingerprint,
                    0,
                    0,
                    _model_json(item),
                ),
            )

    def _insert_events(
        self,
        conn: sqlite3.Connection,
        events: tuple[PersistenceLedgerEvent, ...],
    ) -> None:
        for event in events:
            conn.execute(
                """
                INSERT INTO glm_ledger_events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.global_sequence,
                    event.transaction_id,
                    event.transaction_sequence,
                    event.event_type,
                    event.record_type,
                    event.record_id,
                    event.record_fingerprint,
                    event.previous_global_hash,
                    event.global_event_hash,
                    event.previous_transaction_hash,
                    event.transaction_event_hash,
                    _timestamp(event.created_at),
                    _model_json(event),
                ),
            )

    def _receipt_from_rows(
        self,
        *,
        request: PersistenceTransactionRequest,
        rows: Mapping[str, tuple[BaseModel, ...]],
        events: tuple[PersistenceLedgerEvent, ...],
        ledger_head_before: str,
        idempotent: bool,
        created_at: str,
    ) -> PersistenceTransactionReceipt:
        plan = request.promotion_transaction_plan
        result = request.promotion_transaction_result
        approval_bundle_fp = request.persistence_approval_bundle.bundle_fingerprint
        projection_ids = tuple(_model_record_id(item) for item in rows["memory_projections"])
        belief_ids = tuple(_model_record_id(item) for item in rows["belief_candidates"])
        knowledge_identity_ids = tuple(
            _model_record_id(item) for item in rows["knowledge_identities"]
        )
        knowledge_version_ids = tuple(_model_record_id(item) for item in rows["knowledge_versions"])
        candidate_receipt_ids = tuple(_model_record_id(item) for item in rows["candidate_receipts"])
        approval_binding_ids = tuple(_model_record_id(item) for item in rows["approval_bindings"])
        row_counts = {
            "approval_bindings": len(approval_binding_ids),
            "candidate_evidence_receipts": len(candidate_receipt_ids),
            "knowledge_identities": len(knowledge_identity_ids),
            "knowledge_versions": len(knowledge_version_ids),
            "memory_projection_records": len(projection_ids),
            "belief_projection_candidates": len(belief_ids),
            "ledger_events": 0 if idempotent else len(events),
        }
        return build_model(
            PersistenceTransactionReceipt,
            {
                "receipt_id": f"receipt-{plan.transaction_id}",
                "store_id": request.store_id,
                "store_identity_fingerprint": request.store_identity_fingerprint,
                "database_path_fingerprint": request.database_path_fingerprint,
                "transaction_id": plan.transaction_id,
                "promotion_request_fingerprint": plan.promotion_request.request_fingerprint,
                "promotion_plan_fingerprint": plan.transaction_plan_fingerprint,
                "promotion_result_fingerprint": result.result_fingerprint,
                "persistence_approval_bundle_fingerprint": approval_bundle_fp,
                "knowledge_identity_ids": knowledge_identity_ids,
                "knowledge_version_ids": knowledge_version_ids,
                "projection_record_ids": projection_ids,
                "belief_candidate_record_ids": belief_ids,
                "candidate_receipt_ids": candidate_receipt_ids,
                "approval_binding_ids": approval_binding_ids,
                "row_counts": row_counts,
                "ledger_start_sequence": 0 if idempotent else events[0].global_sequence,
                "ledger_end_sequence": 0 if idempotent else events[-1].global_sequence,
                "ledger_head_before": ledger_head_before,
                "ledger_head_after": ledger_head_before
                if idempotent
                else events[-1].global_event_hash,
                "transaction_chain_head": ledger_head_before
                if idempotent
                else events[-1].transaction_event_hash,
                "idempotent_replay": idempotent,
                "isolated_local_persistence_applied": not idempotent,
                "read_after_write_verified": True,
                "integrity_status": LocalStoreIntegrityStatus.PASSED,
                "created_at": _parse_ts(created_at),
            },
            "receipt_fingerprint",
        )

    def _existing_receipt(
        self,
        conn: sqlite3.Connection,
        request: PersistenceTransactionRequest,
        *,
        idempotent: bool,
    ) -> PersistenceTransactionReceipt:
        rows = self._load_rows_for_transaction(
            conn,
            request.promotion_transaction_plan.transaction_id,
        )
        ledger_head, _ = self._ledger_head(conn)
        return self._receipt_from_rows(
            request=request,
            rows=rows,
            events=(),
            ledger_head_before=ledger_head,
            idempotent=idempotent,
            created_at=_timestamp(),
        )

    def _load_rows_for_transaction(
        self,
        conn: sqlite3.Connection,
        transaction_id: str,
    ) -> dict[str, tuple[BaseModel, ...]]:
        return {
            "approval_bindings": tuple(
                PersistentApprovalBinding.model_validate_json(row["payload_json"])
                for row in conn.execute(
                    """
                    SELECT payload_json FROM glm_approval_bindings
                    WHERE transaction_id=? ORDER BY binding_id
                    """,
                    (transaction_id,),
                )
            ),
            "candidate_receipts": tuple(
                PersistentCandidateEvidenceReceipt.model_validate_json(row["payload_json"])
                for row in conn.execute(
                    """
                    SELECT payload_json FROM glm_candidate_evidence_receipts
                    WHERE transaction_id=? ORDER BY candidate_receipt_id
                    """,
                    (transaction_id,),
                )
            ),
            "knowledge_identities": tuple(
                PersistentKnowledgeIdentity.model_validate_json(row["payload_json"])
                for row in conn.execute(
                    """
                    SELECT payload_json FROM glm_knowledge_identities
                    WHERE created_transaction_id=? ORDER BY knowledge_identity_id
                    """,
                    (transaction_id,),
                )
            ),
            "knowledge_versions": tuple(
                PersistentKnowledgeVersion.model_validate_json(row["payload_json"])
                for row in conn.execute(
                    """
                    SELECT payload_json FROM glm_knowledge_versions
                    WHERE created_transaction_id=? ORDER BY knowledge_identity_id, version_number
                    """,
                    (transaction_id,),
                )
            ),
            "memory_projections": tuple(
                PersistentMemoryProjectionRecord.model_validate_json(row["payload_json"])
                for row in conn.execute(
                    """
                    SELECT payload_json FROM glm_memory_projection_records
                    WHERE transaction_id=? ORDER BY projection_type, projection_record_id
                    """,
                    (transaction_id,),
                )
            ),
            "belief_candidates": tuple(
                PersistentBeliefProjectionCandidateRecord.model_validate_json(row["payload_json"])
                for row in conn.execute(
                    """
                    SELECT payload_json FROM glm_belief_projection_candidates
                    WHERE transaction_id=? ORDER BY belief_candidate_id
                    """,
                    (transaction_id,),
                )
            ),
        }

    def _transaction_fingerprint(
        self,
        request: PersistenceTransactionRequest,
        rows: Mapping[str, tuple[BaseModel, ...]],
    ) -> str:
        plan = request.promotion_transaction_plan
        result = request.promotion_transaction_result
        authorization = request.local_authorization_envelope
        approval_bundle = request.persistence_approval_bundle
        return persistence_fingerprint(
            {
                "transaction_id": plan.transaction_id,
                "request_fingerprint": request.request_fingerprint,
                "promotion_plan_fingerprint": plan.transaction_plan_fingerprint,
                "promotion_result_fingerprint": result.result_fingerprint,
                "authorization_fingerprint": authorization.envelope_fingerprint,
                "approval_bundle_fingerprint": approval_bundle.bundle_fingerprint,
                "row_fingerprints": {
                    key: tuple(_model_record_fingerprint(item) for item in value)
                    for key, value in sorted(rows.items())
                },
            }
        )

    def _verify_read_after_write(
        self,
        conn: sqlite3.Connection,
        receipt: PersistenceTransactionReceipt,
    ) -> None:
        row = conn.execute(
            """
            SELECT ledger_head_after
            FROM glm_persistence_transactions
            WHERE transaction_id = ?
            """,
            (receipt.transaction_id,),
        ).fetchone()
        if row is None:
            raise LocalPersistenceError("read-after-write transaction missing")
        if not receipt.idempotent_replay and row["ledger_head_after"] != receipt.ledger_head_after:
            raise LocalPersistenceError("read-after-write ledger mismatch")

    def _ledger_head(self, conn: sqlite3.Connection) -> tuple[str, int]:
        row = conn.execute(
            """
            SELECT global_sequence, global_event_hash
            FROM glm_ledger_events
            ORDER BY global_sequence DESC
            LIMIT 1
            """
        ).fetchone()
        if row is None:
            return ZERO_HASH, 0
        return row["global_event_hash"], int(row["global_sequence"])

    def _validate_hash_chains(self, conn: sqlite3.Connection) -> tuple[bool, bool]:
        rows = conn.execute(
            """
            SELECT payload_json
            FROM glm_ledger_events
            ORDER BY global_sequence
            """
        ).fetchall()
        previous_global = ZERO_HASH
        previous_by_transaction: dict[str, str] = defaultdict(lambda: ZERO_HASH)
        expected_sequence = 1
        global_ok = True
        tx_ok = True
        for row in rows:
            event = PersistenceLedgerEvent.model_validate_json(row["payload_json"])
            if event.global_sequence != expected_sequence:
                global_ok = False
            if event.previous_global_hash != previous_global:
                global_ok = False
            expected_global = persistence_fingerprint(
                {
                    "store_id": self._store_id(conn),
                    "global_sequence": event.global_sequence,
                    "transaction_id": event.transaction_id,
                    "transaction_sequence": event.transaction_sequence,
                    "event_type": event.event_type,
                    "record_type": event.record_type,
                    "record_id": event.record_id,
                    "record_fingerprint": event.record_fingerprint,
                    "previous_global_hash": event.previous_global_hash,
                    "previous_transaction_hash": event.previous_transaction_hash,
                    "created_at": _timestamp(event.created_at),
                }
            )
            if expected_global != event.global_event_hash:
                global_ok = False
            tx_previous = previous_by_transaction[event.transaction_id]
            if event.previous_transaction_hash != tx_previous:
                tx_ok = False
            expected_tx = persistence_fingerprint(
                {
                    "transaction_id": event.transaction_id,
                    "transaction_sequence": event.transaction_sequence,
                    "event_type": event.event_type,
                    "record_type": event.record_type,
                    "record_id": event.record_id,
                    "record_fingerprint": event.record_fingerprint,
                    "previous_transaction_hash": event.previous_transaction_hash,
                    "created_at": _timestamp(event.created_at),
                }
            )
            if expected_tx != event.transaction_event_hash:
                tx_ok = False
            previous_global = event.global_event_hash
            previous_by_transaction[event.transaction_id] = event.transaction_event_hash
            expected_sequence += 1
        return global_ok, tx_ok

    def _validate_no_prohibited_markers(
        self,
        conn: sqlite3.Connection,
    ) -> tuple[bool, bool, bool, bool]:
        payload_tables = tuple(
            table for table in APPLICATION_TABLES if table != "glm_store_metadata"
        )
        text = "\n".join(
            row["payload_json"]
            for table in payload_tables
            for row in conn.execute(f"SELECT payload_json FROM {table}")
        )
        lowered = text.lower()
        return (
            all(marker not in lowered for marker in ("source_body", "raw_prompt", "secret")),
            'production_memory_written":true' not in lowered,
            'actual_belief_created":true' not in lowered
            and 'actual_belief_mutated":true' not in lowered,
            'automatic_promotion_applied":true' not in lowered,
        )

    def _expected_triggers_present(self, conn: sqlite3.Connection) -> bool:
        rows = conn.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type='trigger' AND name LIKE 'glm_%'
            ORDER BY name
            """
        ).fetchall()
        return tuple(row["name"] for row in rows) == tuple(sorted(EXPECTED_TRIGGER_NAMES))

    def _add_finding(
        self,
        findings: list[LocalStoreIntegrityFinding],
        finding_id: str,
        passed: bool,
        reasons: tuple[str, ...],
        safe_ids: tuple[str, ...],
        fingerprints: tuple[str, ...],
    ) -> None:
        findings.append(
            build_model(
                LocalStoreIntegrityFinding,
                {
                    "finding_id": finding_id,
                    "status": LocalStoreIntegrityStatus.PASSED
                    if passed
                    else LocalStoreIntegrityStatus.FAILED,
                    "reason_codes": reasons if passed else ("integrity_failed",),
                    "safe_ids": safe_ids,
                    "fingerprints": fingerprints,
                    "bounded_count": len(safe_ids) + len(fingerprints),
                },
                "finding_fingerprint",
            )
        )

    def _store_id(self, conn: sqlite3.Connection) -> str:
        row = conn.execute("SELECT store_id FROM glm_store_metadata").fetchone()
        if row is None:
            raise LocalPersistenceError("local store metadata is missing")
        return str(row["store_id"])

    def _store_identity_fingerprint(self, conn: sqlite3.Connection) -> str:
        row = conn.execute("SELECT store_identity_fingerprint FROM glm_store_metadata").fetchone()
        if row is None:
            raise LocalPersistenceError("local store metadata is missing")
        return str(row["store_identity_fingerprint"])

    def _store_id_or_unknown(self, database_path: str | Path) -> str:
        try:
            with closing(self._connect(Path(database_path), read_only=True)) as conn:
                return self._store_id(conn)
        except Exception:
            return "unknown-store"

    def _file_fingerprint(self, path: Path) -> str:
        return persistence_fingerprint({"file_bytes": path.read_bytes().hex()})


def _knowledge_filters(query: LocalKnowledgeQuery) -> tuple[str, tuple[Any, ...]]:
    clauses: list[str] = []
    params: list[Any] = []
    mapping = {
        "created_transaction_id": query.transaction_id,
        "knowledge_identity_id": query.knowledge_identity_id,
        "knowledge_version_id": query.knowledge_version_id,
        "version_number": query.version_number,
        "candidate_id": query.candidate_id,
        "candidate_fingerprint": query.candidate_fingerprint,
        "candidate_posture": query.candidate_posture,
        "content_fingerprint": query.content_fingerprint,
    }
    for column, value in mapping.items():
        if value is not None:
            clauses.append(f"{column} = ?")
            params.append(value.value if hasattr(value, "value") else value)
    if query.event_type is not None:
        clauses.append("event_type = ?")
        params.append(query.event_type.value)
    if query.created_from is not None:
        clauses.append("valid_from >= ?")
        params.append(_timestamp(query.created_from))
    if query.created_to is not None:
        clauses.append("valid_from <= ?")
        params.append(_timestamp(query.created_to))
    return ("WHERE " + " AND ".join(clauses) if clauses else "", tuple(params))


def _projection_filters(
    query: LocalProjectionQuery,
    *,
    belief: bool,
) -> tuple[str, tuple[Any, ...]]:
    clauses: list[str] = []
    params: list[Any] = []
    if query.transaction_id is not None:
        clauses.append("transaction_id = ?")
        params.append(query.transaction_id)
    if query.knowledge_identity_id is not None:
        clauses.append("knowledge_identity_id = ?")
        params.append(query.knowledge_identity_id)
    if query.knowledge_version_id is not None:
        clauses.append("knowledge_version_id = ?")
        params.append(query.knowledge_version_id)
    if query.projection_record_id is not None:
        clauses.append("belief_candidate_id = ?" if belief else "projection_record_id = ?")
        params.append(query.projection_record_id)
    if query.projection_fingerprint is not None:
        column = "candidate_fingerprint" if belief else "projection_fingerprint"
        clauses.append(f"{column} = ?")
        params.append(query.projection_fingerprint)
    if query.projection_type is not None:
        if belief and query.projection_type is not PersistentProjectionType.BELIEF_CANDIDATE:
            clauses.append("1 = 0")
        if not belief:
            if query.projection_type is PersistentProjectionType.BELIEF_CANDIDATE:
                clauses.append("1 = 0")
            else:
                clauses.append("projection_type = ?")
                params.append(query.projection_type.value)
    return ("WHERE " + " AND ".join(clauses) if clauses else "", tuple(params))


def _event_type(kind: PromotionRequestKind) -> PersistentKnowledgeEventType:
    return {
        PromotionRequestKind.INITIAL_VERSION: PersistentKnowledgeEventType.INITIAL_VERSION,
        PromotionRequestKind.NEW_VERSION: PersistentKnowledgeEventType.NEW_VERSION,
        PromotionRequestKind.SUPERSESSION: PersistentKnowledgeEventType.SUPERSESSION_MARKER,
        PromotionRequestKind.RETRACTION: PersistentKnowledgeEventType.RETRACTION_MARKER,
        PromotionRequestKind.EXPIRY: PersistentKnowledgeEventType.EXPIRY_MARKER,
        PromotionRequestKind.REVALIDATION_ONLY: PersistentKnowledgeEventType.NEW_VERSION,
    }.get(kind, PersistentKnowledgeEventType.NEW_VERSION)


def _knowledge_version_id(version_plan: Any) -> str:
    return f"{version_plan.knowledge_identity_id}-v{version_plan.planned_version_number:06d}"


def _model_json(model: BaseModel) -> str:
    return model.model_dump_json()


def _model_record_id(model: BaseModel) -> str:
    for field in (
        "binding_id",
        "candidate_receipt_id",
        "knowledge_identity_id",
        "knowledge_version_id",
        "projection_record_id",
        "belief_candidate_id",
        "transaction_id",
    ):
        if hasattr(model, field):
            return str(getattr(model, field))
    raise LocalPersistenceError("record ID field missing")


def _model_record_fingerprint(model: BaseModel) -> str:
    for field in (
        "binding_fingerprint",
        "receipt_fingerprint",
        "identity_fingerprint",
        "version_fingerprint",
        "projection_fingerprint",
        "candidate_fingerprint",
        "transaction_fingerprint",
    ):
        if hasattr(model, field):
            return str(getattr(model, field))
    return model_fingerprint(model, set())


def _timestamp(value: datetime | None = None) -> str:
    return _dt(value).isoformat().replace("+00:00", "Z")


def _parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _dt(value: datetime | None = None) -> datetime:
    if value is None:
        return datetime.now(UTC)
    if value.tzinfo is None or value.utcoffset() is None:
        raise LocalPersistenceError("timestamp must be UTC-aware")
    return value.astimezone(UTC)


def _json_dumps(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _enum_value(value: Any) -> str:
    return str(value.value if hasattr(value, "value") else value)


def _write_private_json(path: Path, model: BaseModel) -> None:
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(model.model_dump_json(indent=2))
            handle.write("\n")
    except Exception:
        path.unlink(missing_ok=True)
        raise
