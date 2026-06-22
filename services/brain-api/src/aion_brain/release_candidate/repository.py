"""Persistent repository for release candidate records."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    MetaData,
    Table,
    Text,
    UniqueConstraint,
    create_engine,
    insert,
    select,
    update,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import RowMapping
from sqlalchemy.pool import QueuePool, StaticPool

from aion_brain.contracts.release_candidate import (
    RCEvidencePack,
    RCFinding,
    RCGateRun,
    RCReport,
    ReleaseCandidate,
)
from aion_brain.contracts.verification_matrix import VerificationCheck, VerificationMatrix

rc_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")


aion_release_candidates = Table(
    "aion_release_candidates",
    rc_metadata,
    Column("release_candidate_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("rc_key", Text, nullable=False),
    Column("version", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("source_ref", Text, nullable=True),
    Column("commit_ref", Text, nullable=True),
    Column("tag_ref", Text, nullable=True),
    Column("verification_matrix_id", Text, nullable=True),
    Column("rc_run_id", Text, nullable=True),
    Column("rc_report_id", Text, nullable=True),
    Column("freeze_gate_id", Text, nullable=True),
    Column("release_package_id", Text, nullable=True),
    Column("readiness_score", Float, nullable=False),
    Column("release_ready", Boolean, nullable=False),
    Column("blocker_count", Integer, nullable=False),
    Column("warning_count", Integer, nullable=False),
    Column("evidence_pack_ref", Text, nullable=True),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("archived_at", DateTime(timezone=True), nullable=True),
    Column("deleted_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_release_candidates_key", "rc_key"),
    Index("ix_aion_release_candidates_version", "version"),
    Index("ix_aion_release_candidates_status", "status"),
    Index("ix_aion_release_candidates_trace", "trace_id"),
    Index("ix_aion_release_candidates_score", "readiness_score"),
    Index("ix_aion_release_candidates_ready", "release_ready"),
    Index("ix_aion_release_candidates_blockers", "blocker_count"),
    Index("ix_aion_release_candidates_created_at", "created_at"),
    Index("ix_aion_release_candidates_deleted_at", "deleted_at"),
)

aion_rc_verification_checks = Table(
    "aion_rc_verification_checks",
    rc_metadata,
    Column("verification_check_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("rc_run_id", Text, nullable=True),
    Column("check_key", Text, nullable=False),
    Column("check_type", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("severity", Text, nullable=False),
    Column("required", Boolean, nullable=False),
    Column("passed", Boolean, nullable=False),
    Column("title", Text, nullable=False),
    Column("summary", Text, nullable=False),
    Column("command_hint", Text, nullable=True),
    Column("evidence", json_payload_type, nullable=False),
    Column("duration_ms", Integer, nullable=True),
    Column("error", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_rc_checks_trace", "trace_id"),
    Index("ix_aion_rc_checks_run", "rc_run_id"),
    Index("ix_aion_rc_checks_key", "check_key"),
    Index("ix_aion_rc_checks_type", "check_type"),
    Index("ix_aion_rc_checks_status", "status"),
    Index("ix_aion_rc_checks_severity", "severity"),
    Index("ix_aion_rc_checks_required", "required"),
    Index("ix_aion_rc_checks_passed", "passed"),
    Index("ix_aion_rc_checks_created_at", "created_at"),
)

aion_rc_verification_matrices = Table(
    "aion_rc_verification_matrices",
    rc_metadata,
    Column("verification_matrix_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("matrix_key", Text, nullable=False),
    Column("version", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("required_checks", json_payload_type, nullable=False),
    Column("optional_checks", json_payload_type, nullable=False),
    Column("required_threshold", Float, nullable=False),
    Column("release_ready_threshold", Float, nullable=False),
    Column("fail_on_critical", Boolean, nullable=False),
    Column("fail_on_missing_required", Boolean, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("disabled_at", DateTime(timezone=True), nullable=True),
    UniqueConstraint("matrix_key", "version", name="uq_aion_rc_matrix_key_version"),
    Index("ix_aion_rc_matrices_key", "matrix_key"),
    Index("ix_aion_rc_matrices_version", "version"),
    Index("ix_aion_rc_matrices_status", "status"),
    Index("ix_aion_rc_matrices_required_threshold", "required_threshold"),
    Index("ix_aion_rc_matrices_release_threshold", "release_ready_threshold"),
    Index("ix_aion_rc_matrices_created_at", "created_at"),
)

aion_rc_gate_runs = Table(
    "aion_rc_gate_runs",
    rc_metadata,
    Column("rc_run_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("release_candidate_id", Text, nullable=True),
    Column("verification_matrix_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("mode", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("started_at", DateTime(timezone=True), nullable=False),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Column("checks_total", Integer, nullable=False),
    Column("checks_passed", Integer, nullable=False),
    Column("checks_failed", Integer, nullable=False),
    Column("checks_warning", Integer, nullable=False),
    Column("checks_skipped", Integer, nullable=False),
    Column("blocker_count", Integer, nullable=False),
    Column("readiness_score", Float, nullable=False),
    Column("release_ready", Boolean, nullable=False),
    Column("verification_check_ids", json_payload_type, nullable=False),
    Column("finding_ids", json_payload_type, nullable=False),
    Column("evidence_pack_id", Text, nullable=True),
    Column("warnings", json_payload_type, nullable=False),
    Column("failures", json_payload_type, nullable=False),
    Column("result", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_rc_runs_trace", "trace_id"),
    Index("ix_aion_rc_runs_actor", "actor_id"),
    Index("ix_aion_rc_runs_workspace", "workspace_id"),
    Index("ix_aion_rc_runs_candidate", "release_candidate_id"),
    Index("ix_aion_rc_runs_matrix", "verification_matrix_id"),
    Index("ix_aion_rc_runs_status", "status"),
    Index("ix_aion_rc_runs_mode", "mode"),
    Index("ix_aion_rc_runs_score", "readiness_score"),
    Index("ix_aion_rc_runs_ready", "release_ready"),
    Index("ix_aion_rc_runs_blockers", "blocker_count"),
    Index("ix_aion_rc_runs_created_at", "created_at"),
)

aion_rc_findings = Table(
    "aion_rc_findings",
    rc_metadata,
    Column("rc_finding_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("rc_run_id", Text, nullable=True),
    Column("release_candidate_id", Text, nullable=True),
    Column("finding_type", Text, nullable=False),
    Column("severity", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("blocking", Boolean, nullable=False),
    Column("title", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("check_key", Text, nullable=True),
    Column("source_type", Text, nullable=True),
    Column("source_id", Text, nullable=True),
    Column("recommended_action", Text, nullable=False),
    Column("evidence_refs", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("resolved_at", DateTime(timezone=True), nullable=True),
    Column("dismissed_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_rc_findings_trace", "trace_id"),
    Index("ix_aion_rc_findings_run", "rc_run_id"),
    Index("ix_aion_rc_findings_candidate", "release_candidate_id"),
    Index("ix_aion_rc_findings_type", "finding_type"),
    Index("ix_aion_rc_findings_severity", "severity"),
    Index("ix_aion_rc_findings_status", "status"),
    Index("ix_aion_rc_findings_blocking", "blocking"),
    Index("ix_aion_rc_findings_check_key", "check_key"),
    Index("ix_aion_rc_findings_created_at", "created_at"),
)

aion_rc_evidence_packs = Table(
    "aion_rc_evidence_packs",
    rc_metadata,
    Column("evidence_pack_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("rc_run_id", Text, nullable=True),
    Column("release_candidate_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("pack_type", Text, nullable=False),
    Column("title", Text, nullable=False),
    Column("summary", Text, nullable=False),
    Column("evidence_refs", json_payload_type, nullable=False),
    Column("check_summaries", json_payload_type, nullable=False),
    Column("artifact_refs", json_payload_type, nullable=False),
    Column("report_hash", Text, nullable=False),
    Column("redacted_report", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_rc_packs_trace", "trace_id"),
    Index("ix_aion_rc_packs_run", "rc_run_id"),
    Index("ix_aion_rc_packs_candidate", "release_candidate_id"),
    Index("ix_aion_rc_packs_status", "status"),
    Index("ix_aion_rc_packs_type", "pack_type"),
    Index("ix_aion_rc_packs_hash", "report_hash"),
    Index("ix_aion_rc_packs_created_at", "created_at"),
)

aion_rc_reports = Table(
    "aion_rc_reports",
    rc_metadata,
    Column("rc_report_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("release_candidate_id", Text, nullable=True),
    Column("rc_run_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("version", Text, nullable=False),
    Column("readiness_score", Float, nullable=False),
    Column("release_ready", Boolean, nullable=False),
    Column("blocker_count", Integer, nullable=False),
    Column("warning_count", Integer, nullable=False),
    Column("passed_checks", json_payload_type, nullable=False),
    Column("failed_checks", json_payload_type, nullable=False),
    Column("warning_checks", json_payload_type, nullable=False),
    Column("findings", json_payload_type, nullable=False),
    Column("recommendations", json_payload_type, nullable=False),
    Column("report", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_rc_reports_trace", "trace_id"),
    Index("ix_aion_rc_reports_candidate", "release_candidate_id"),
    Index("ix_aion_rc_reports_run", "rc_run_id"),
    Index("ix_aion_rc_reports_status", "status"),
    Index("ix_aion_rc_reports_version", "version"),
    Index("ix_aion_rc_reports_score", "readiness_score"),
    Index("ix_aion_rc_reports_ready", "release_ready"),
    Index("ix_aion_rc_reports_blockers", "blocker_count"),
    Index("ix_aion_rc_reports_created_at", "created_at"),
)


class ReleaseCandidateRepository:
    """SQLAlchemy-backed repository for RC-owned records."""

    def __init__(self, database_url: str, *, auto_create: bool = True) -> None:
        connect_args: dict[str, Any] = {}
        poolclass: type[StaticPool] | type[QueuePool] = QueuePool
        if database_url.startswith("sqlite"):
            connect_args = {"check_same_thread": False}
            poolclass = StaticPool
        self._engine = create_engine(database_url, connect_args=connect_args, poolclass=poolclass)
        self._auto_create = auto_create
        self._schema_ready = False

    def save_candidate(self, candidate: ReleaseCandidate) -> ReleaseCandidate:
        self._ensure_schema()
        stored = _with_timestamps(candidate, created=True, updated=True)
        with self._engine.begin() as conn:
            _upsert(
                conn,
                aion_release_candidates,
                "release_candidate_id",
                stored.release_candidate_id,
                _values(aion_release_candidates, stored),
            )
        return stored

    def get_candidate(self, release_candidate_id: str) -> ReleaseCandidate | None:
        self._ensure_schema()
        with self._engine.begin() as conn:
            row = (
                conn.execute(
                    select(aion_release_candidates).where(
                        aion_release_candidates.c.release_candidate_id == release_candidate_id
                    )
                )
                .mappings()
                .first()
            )
        return _model_or_none(ReleaseCandidate, row)

    def get_candidate_by_key(self, rc_key: str) -> ReleaseCandidate | None:
        self._ensure_schema()
        with self._engine.begin() as conn:
            row = (
                conn.execute(
                    select(aion_release_candidates)
                    .where(aion_release_candidates.c.rc_key == rc_key)
                    .where(aion_release_candidates.c.deleted_at.is_(None))
                    .order_by(aion_release_candidates.c.created_at.desc())
                    .limit(1)
                )
                .mappings()
                .first()
            )
        return _model_or_none(ReleaseCandidate, row)

    def list_candidates(
        self,
        *,
        status: str | None = None,
        version: str | None = None,
        release_ready: bool | None = None,
        limit: int = 100,
    ) -> list[ReleaseCandidate]:
        self._ensure_schema()
        query = (
            select(aion_release_candidates)
            .where(aion_release_candidates.c.deleted_at.is_(None))
            .order_by(aion_release_candidates.c.created_at.desc())
            .limit(limit)
        )
        if status is not None:
            query = query.where(aion_release_candidates.c.status == status)
        if version is not None:
            query = query.where(aion_release_candidates.c.version == version)
        if release_ready is not None:
            query = query.where(aion_release_candidates.c.release_ready == release_ready)
        with self._engine.begin() as conn:
            rows = conn.execute(query).mappings().all()
        return [_model(ReleaseCandidate, row) for row in rows]

    def archive_candidate(self, release_candidate_id: str, reason: str) -> ReleaseCandidate | None:
        self._ensure_schema()
        now = datetime.now(UTC)
        candidate = self.get_candidate(release_candidate_id)
        metadata = dict(candidate.metadata) if candidate is not None else {}
        metadata["archive_reason"] = reason
        with self._engine.begin() as conn:
            conn.execute(
                update(aion_release_candidates)
                .where(aion_release_candidates.c.release_candidate_id == release_candidate_id)
                .values(status="archived", archived_at=now, updated_at=now, metadata=metadata)
            )
        return self.get_candidate(release_candidate_id)

    def save_matrix(self, matrix: VerificationMatrix) -> VerificationMatrix:
        self._ensure_schema()
        stored = _with_timestamps(matrix, created=True, updated=True)
        with self._engine.begin() as conn:
            _upsert(
                conn,
                aion_rc_verification_matrices,
                "verification_matrix_id",
                stored.verification_matrix_id,
                _values(aion_rc_verification_matrices, stored),
            )
        return stored

    def get_matrix(self, verification_matrix_id: str) -> VerificationMatrix | None:
        self._ensure_schema()
        with self._engine.begin() as conn:
            row = (
                conn.execute(
                    select(aion_rc_verification_matrices).where(
                        aion_rc_verification_matrices.c.verification_matrix_id
                        == verification_matrix_id
                    )
                )
                .mappings()
                .first()
            )
        return _model_or_none(VerificationMatrix, row)

    def get_matrix_by_key(
        self, matrix_key: str, version: str | None = None
    ) -> VerificationMatrix | None:
        self._ensure_schema()
        query = (
            select(aion_rc_verification_matrices)
            .where(aion_rc_verification_matrices.c.matrix_key == matrix_key)
            .order_by(aion_rc_verification_matrices.c.created_at.desc())
            .limit(1)
        )
        if version is not None:
            query = query.where(aion_rc_verification_matrices.c.version == version)
        with self._engine.begin() as conn:
            row = conn.execute(query).mappings().first()
        return _model_or_none(VerificationMatrix, row)

    def list_matrices(
        self, *, status: str | None = None, limit: int = 100
    ) -> list[VerificationMatrix]:
        self._ensure_schema()
        query = (
            select(aion_rc_verification_matrices)
            .order_by(aion_rc_verification_matrices.c.created_at.desc())
            .limit(limit)
        )
        if status is not None:
            query = query.where(aion_rc_verification_matrices.c.status == status)
        with self._engine.begin() as conn:
            rows = conn.execute(query).mappings().all()
        return [_model(VerificationMatrix, row) for row in rows]

    def save_check(self, check: VerificationCheck) -> VerificationCheck:
        self._ensure_schema()
        stored = _with_timestamps(check, created=True)
        with self._engine.begin() as conn:
            _upsert(
                conn,
                aion_rc_verification_checks,
                "verification_check_id",
                stored.verification_check_id,
                _values(aion_rc_verification_checks, stored),
            )
        return stored

    def get_check(self, verification_check_id: str) -> VerificationCheck | None:
        self._ensure_schema()
        with self._engine.begin() as conn:
            row = (
                conn.execute(
                    select(aion_rc_verification_checks).where(
                        aion_rc_verification_checks.c.verification_check_id == verification_check_id
                    )
                )
                .mappings()
                .first()
            )
        return _model_or_none(VerificationCheck, row)

    def list_checks(
        self, *, rc_run_id: str | None = None, limit: int = 500
    ) -> list[VerificationCheck]:
        self._ensure_schema()
        query = (
            select(aion_rc_verification_checks)
            .order_by(aion_rc_verification_checks.c.created_at.asc())
            .limit(limit)
        )
        if rc_run_id is not None:
            query = query.where(aion_rc_verification_checks.c.rc_run_id == rc_run_id)
        with self._engine.begin() as conn:
            rows = conn.execute(query).mappings().all()
        return [_model(VerificationCheck, row) for row in rows]

    def save_run(self, run: RCGateRun) -> RCGateRun:
        self._ensure_schema()
        stored = _with_timestamps(run, created=True, completed=True)
        with self._engine.begin() as conn:
            _upsert(
                conn,
                aion_rc_gate_runs,
                "rc_run_id",
                stored.rc_run_id,
                _run_values(stored),
            )
        return stored

    def get_run(self, rc_run_id: str) -> RCGateRun | None:
        self._ensure_schema()
        with self._engine.begin() as conn:
            row = (
                conn.execute(
                    select(aion_rc_gate_runs).where(aion_rc_gate_runs.c.rc_run_id == rc_run_id)
                )
                .mappings()
                .first()
            )
        return self._run_or_none(row)

    def latest_run(self) -> RCGateRun | None:
        self._ensure_schema()
        with self._engine.begin() as conn:
            row = (
                conn.execute(
                    select(aion_rc_gate_runs)
                    .order_by(aion_rc_gate_runs.c.created_at.desc())
                    .limit(1)
                )
                .mappings()
                .first()
            )
        return self._run_or_none(row)

    def list_runs(self, *, status: str | None = None, limit: int = 100) -> list[RCGateRun]:
        self._ensure_schema()
        query = (
            select(aion_rc_gate_runs).order_by(aion_rc_gate_runs.c.created_at.desc()).limit(limit)
        )
        if status is not None:
            query = query.where(aion_rc_gate_runs.c.status == status)
        with self._engine.begin() as conn:
            rows = conn.execute(query).mappings().all()
        return [item for row in rows if (item := self._run_or_none(row)) is not None]

    def save_finding(self, finding: RCFinding) -> RCFinding:
        self._ensure_schema()
        stored = _with_timestamps(finding, created=True)
        with self._engine.begin() as conn:
            _upsert(
                conn,
                aion_rc_findings,
                "rc_finding_id",
                stored.rc_finding_id,
                _values(aion_rc_findings, stored),
            )
        return stored

    def get_finding(self, rc_finding_id: str) -> RCFinding | None:
        self._ensure_schema()
        with self._engine.begin() as conn:
            row = (
                conn.execute(
                    select(aion_rc_findings).where(
                        aion_rc_findings.c.rc_finding_id == rc_finding_id
                    )
                )
                .mappings()
                .first()
            )
        return _model_or_none(RCFinding, row)

    def list_findings(
        self,
        *,
        status: str | None = None,
        severity: str | None = None,
        blocking: bool | None = None,
        limit: int = 100,
    ) -> list[RCFinding]:
        self._ensure_schema()
        query = select(aion_rc_findings).order_by(aion_rc_findings.c.created_at.desc()).limit(limit)
        if status is not None:
            query = query.where(aion_rc_findings.c.status == status)
        if severity is not None:
            query = query.where(aion_rc_findings.c.severity == severity)
        if blocking is not None:
            query = query.where(aion_rc_findings.c.blocking == blocking)
        with self._engine.begin() as conn:
            rows = conn.execute(query).mappings().all()
        return [_model(RCFinding, row) for row in rows]

    def dismiss_finding(self, rc_finding_id: str, reason: str) -> RCFinding | None:
        self._ensure_schema()
        now = datetime.now(UTC)
        finding = self.get_finding(rc_finding_id)
        metadata = dict(finding.metadata) if finding is not None else {}
        metadata["dismiss_reason"] = reason
        with self._engine.begin() as conn:
            conn.execute(
                update(aion_rc_findings)
                .where(aion_rc_findings.c.rc_finding_id == rc_finding_id)
                .values(status="dismissed", dismissed_at=now, metadata=metadata)
            )
        return self.get_finding(rc_finding_id)

    def save_evidence_pack(self, pack: RCEvidencePack) -> RCEvidencePack:
        self._ensure_schema()
        stored = _with_timestamps(pack, created=True)
        with self._engine.begin() as conn:
            _upsert(
                conn,
                aion_rc_evidence_packs,
                "evidence_pack_id",
                stored.evidence_pack_id,
                _values(aion_rc_evidence_packs, stored),
            )
        return stored

    def get_evidence_pack(self, evidence_pack_id: str) -> RCEvidencePack | None:
        self._ensure_schema()
        with self._engine.begin() as conn:
            row = (
                conn.execute(
                    select(aion_rc_evidence_packs).where(
                        aion_rc_evidence_packs.c.evidence_pack_id == evidence_pack_id
                    )
                )
                .mappings()
                .first()
            )
        return _model_or_none(RCEvidencePack, row)

    def list_evidence_packs(
        self, *, status: str | None = None, limit: int = 50
    ) -> list[RCEvidencePack]:
        self._ensure_schema()
        query = (
            select(aion_rc_evidence_packs)
            .order_by(aion_rc_evidence_packs.c.created_at.desc())
            .limit(limit)
        )
        if status is not None:
            query = query.where(aion_rc_evidence_packs.c.status == status)
        with self._engine.begin() as conn:
            rows = conn.execute(query).mappings().all()
        return [_model(RCEvidencePack, row) for row in rows]

    def latest_evidence_pack(self) -> RCEvidencePack | None:
        self._ensure_schema()
        with self._engine.begin() as conn:
            row = (
                conn.execute(
                    select(aion_rc_evidence_packs)
                    .order_by(aion_rc_evidence_packs.c.created_at.desc())
                    .limit(1)
                )
                .mappings()
                .first()
            )
        return _model_or_none(RCEvidencePack, row)

    def save_report(self, report: RCReport) -> RCReport:
        self._ensure_schema()
        stored = _with_timestamps(report, created=True)
        with self._engine.begin() as conn:
            _upsert(
                conn,
                aion_rc_reports,
                "rc_report_id",
                stored.rc_report_id,
                _values(aion_rc_reports, stored),
            )
        return stored

    def get_report(self, rc_report_id: str) -> RCReport | None:
        self._ensure_schema()
        with self._engine.begin() as conn:
            row = (
                conn.execute(
                    select(aion_rc_reports).where(aion_rc_reports.c.rc_report_id == rc_report_id)
                )
                .mappings()
                .first()
            )
        return _model_or_none(RCReport, row)

    def list_reports(
        self,
        *,
        status: str | None = None,
        version: str | None = None,
        limit: int = 50,
    ) -> list[RCReport]:
        self._ensure_schema()
        query = select(aion_rc_reports).order_by(aion_rc_reports.c.created_at.desc()).limit(limit)
        if status is not None:
            query = query.where(aion_rc_reports.c.status == status)
        if version is not None:
            query = query.where(aion_rc_reports.c.version == version)
        with self._engine.begin() as conn:
            rows = conn.execute(query).mappings().all()
        return [_model(RCReport, row) for row in rows]

    def latest_report(self) -> RCReport | None:
        self._ensure_schema()
        with self._engine.begin() as conn:
            row = (
                conn.execute(
                    select(aion_rc_reports).order_by(aion_rc_reports.c.created_at.desc()).limit(1)
                )
                .mappings()
                .first()
            )
        return _model_or_none(RCReport, row)

    def status(self, scope: list[str] | None = None) -> dict[str, Any]:
        latest = self.latest_report()
        latest_run = self.latest_run()
        return {
            "status": getattr(latest, "status", "not_run"),
            "release_ready": bool(getattr(latest, "release_ready", False)),
            "readiness_score": float(getattr(latest, "readiness_score", 0.0)),
            "blocker_count": int(getattr(latest, "blocker_count", 0)),
            "latest_run_id": getattr(latest_run, "rc_run_id", None),
            "latest_report_id": getattr(latest, "rc_report_id", None),
            "scope": scope or [],
        }

    def list_registry_records(self) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        for candidate in self.list_candidates(limit=500):
            records.append(
                _registry_record(
                    "release_candidate",
                    candidate.release_candidate_id,
                    candidate.rc_key,
                    candidate.owner_scope,
                )
            )
        for run in self.list_runs(limit=500):
            records.append(
                _registry_record("rc_gate_run", run.rc_run_id, run.status, run.owner_scope)
            )
        for report in self.list_reports(limit=500):
            records.append(
                _registry_record(
                    "rc_report", report.rc_report_id, report.status, report.owner_scope
                )
            )
        for pack in self.list_evidence_packs(limit=500):
            records.append(
                _registry_record(
                    "rc_evidence_pack", pack.evidence_pack_id, pack.status, pack.owner_scope
                )
            )
        for finding in self.list_findings(limit=500):
            records.append(
                _registry_record(
                    "rc_finding",
                    finding.rc_finding_id,
                    finding.title,
                    ["workspace:main"],
                )
            )
        return records

    def _ensure_schema(self) -> None:
        if self._schema_ready or not self._auto_create:
            return
        rc_metadata.create_all(self._engine)
        self._schema_ready = True

    def _run_or_none(self, row: RowMapping | None) -> RCGateRun | None:
        if row is None:
            return None
        checks: list[VerificationCheck] = []
        for check_id in row.get("verification_check_ids", []):
            check = self.get_check(str(check_id))
            if check is not None:
                checks.append(check)
        findings: list[RCFinding] = []
        for finding_id in row.get("finding_ids", []):
            finding = self.get_finding(str(finding_id))
            if finding is not None:
                findings.append(finding)
        payload = dict(row)
        payload["verification_checks"] = checks
        payload["findings"] = findings
        payload.pop("verification_check_ids", None)
        payload.pop("finding_ids", None)
        return RCGateRun.model_validate(payload)


def _model[TModel: BaseModel](model: type[TModel], row: RowMapping) -> TModel:
    return model.model_validate(dict(row))


def _model_or_none[TModel: BaseModel](model: type[TModel], row: RowMapping | None) -> TModel | None:
    if row is None:
        return None
    return _model(model, row)


def _with_timestamps[TModel: BaseModel](
    model: TModel,
    *,
    created: bool = False,
    completed: bool = False,
    updated: bool = False,
) -> TModel:
    now = datetime.now(UTC)
    updates: dict[str, Any] = {}
    if created and getattr(model, "created_at", None) is None:
        updates["created_at"] = now
    if updated and hasattr(model, "updated_at"):
        updates["updated_at"] = now
    if (
        completed
        and hasattr(model, "completed_at")
        and getattr(model, "completed_at", None) is None
    ):
        updates["completed_at"] = now
    if not updates:
        return model
    return model.model_copy(update=updates)


def _upsert(conn: Any, table: Table, id_column: str, id_value: str, values: dict[str, Any]) -> None:
    existing = conn.execute(
        select(table.c[id_column]).where(table.c[id_column] == id_value)
    ).first()
    if existing is None:
        conn.execute(insert(table).values(**values))
    else:
        conn.execute(update(table).where(table.c[id_column] == id_value).values(**values))


def _values(table: Table, model: BaseModel) -> dict[str, Any]:
    python_payload = model.model_dump(mode="python")
    json_payload = model.model_dump(mode="json")
    return {column.name: _column_value(column, python_payload, json_payload) for column in table.c}


def _run_values(run: RCGateRun) -> dict[str, Any]:
    python_payload = run.model_dump(mode="python")
    json_payload = run.model_dump(mode="json")
    payload = {
        column.name: _column_value(column, python_payload, json_payload)
        for column in aion_rc_gate_runs.c
    }
    payload["verification_check_ids"] = [
        item.verification_check_id for item in run.verification_checks
    ]
    payload["finding_ids"] = [item.rc_finding_id for item in run.findings]
    return payload


def _column_value(column: Any, python_payload: dict[str, Any], json_payload: dict[str, Any]) -> Any:
    if isinstance(column.type, JSON):
        return json_payload.get(column.name)
    return python_payload.get(column.name)


def _registry_record(
    resource_type: str,
    resource_id: str,
    title: str,
    owner_scope: list[str],
) -> dict[str, Any]:
    return {
        "resource_uri": f"aion://{resource_type}/{resource_id}",
        "resource_type": resource_type,
        "resource_id": resource_id,
        "source_system": "release_candidate",
        "status": "active",
        "visibility": "operator",
        "sensitivity": "internal",
        "title": title,
        "summary": f"Release candidate {resource_type} record.",
        "owner_scope": owner_scope,
        "tags": ["release_candidate", "local_verification"],
        "refs": [],
        "metadata": {"source": "release_candidate"},
    }


__all__ = [
    "ReleaseCandidateRepository",
    "aion_release_candidates",
    "aion_rc_evidence_packs",
    "aion_rc_findings",
    "aion_rc_gate_runs",
    "aion_rc_reports",
    "aion_rc_verification_checks",
    "aion_rc_verification_matrices",
    "rc_metadata",
]
