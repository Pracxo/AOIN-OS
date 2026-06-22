"""Memory governance persistence."""

from datetime import UTC, datetime
from typing import Any, cast

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    Table,
    Text,
    create_engine,
    insert,
    select,
    update,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import Engine, RowMapping
from sqlalchemy.pool import QueuePool, StaticPool

from aion_brain.contracts.memory_governance import (
    ForgetStatus,
    MemoryCompactedRecord,
    MemoryCompactionRunRecord,
    MemoryCompactionStatus,
    MemoryCompactionStrategy,
    MemoryConflict,
    MemoryConflictSeverity,
    MemoryConflictStatus,
    MemoryConflictType,
    MemoryDecayRecord,
    MemoryForgettingRequestRecord,
    MemoryGovernanceAction,
    MemoryGovernanceDecision,
    MemoryGovernanceRule,
    MemoryGovernanceRuleType,
)

memory_governance_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_memory_governance_rules = Table(
    "aion_memory_governance_rules",
    memory_governance_metadata,
    Column("governance_rule_id", Text, primary_key=True),
    Column("name", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("rule_type", Text, nullable=False),
    Column("memory_types", json_payload_type, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("sensitivity_levels", json_payload_type, nullable=False),
    Column("conditions", json_payload_type, nullable=False),
    Column("action", Text, nullable=False),
    Column("priority", Integer, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("disabled_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_memory_governance_rules_name", "name"),
    Index("ix_aion_memory_governance_rules_status", "status"),
    Index("ix_aion_memory_governance_rules_rule_type", "rule_type"),
    Index("ix_aion_memory_governance_rules_action", "action"),
    Index("ix_aion_memory_governance_rules_priority", "priority"),
    Index("ix_aion_memory_governance_rules_created_at", "created_at"),
)

aion_memory_governance_decisions = Table(
    "aion_memory_governance_decisions",
    memory_governance_metadata,
    Column("governance_decision_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("memory_id", Text, nullable=True),
    Column("rule_ids", json_payload_type, nullable=False),
    Column("decision", Text, nullable=False),
    Column("reason", Text, nullable=False),
    Column("constraints", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_memory_governance_decisions_trace_id", "trace_id"),
    Index("ix_aion_memory_governance_decisions_memory_id", "memory_id"),
    Index("ix_aion_memory_governance_decisions_decision", "decision"),
    Index("ix_aion_memory_governance_decisions_created_at", "created_at"),
)

aion_memory_decay_records = Table(
    "aion_memory_decay_records",
    memory_governance_metadata,
    Column("decay_id", Text, primary_key=True),
    Column("memory_id", Text, nullable=False),
    Column("previous_score", Float, nullable=False),
    Column("new_score", Float, nullable=False),
    Column("decay_reason", Text, nullable=False),
    Column("factors", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_memory_decay_records_memory_id", "memory_id"),
    Index("ix_aion_memory_decay_records_new_score", "new_score"),
    Index("ix_aion_memory_decay_records_created_at", "created_at"),
)

aion_memory_forgetting_requests = Table(
    "aion_memory_forgetting_requests",
    memory_governance_metadata,
    Column("forget_request_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("target_type", Text, nullable=False),
    Column("target_id", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("reason", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("risk_assessment_id", Text, nullable=True),
    Column("approval_request_id", Text, nullable=True),
    Column("result", json_payload_type, nullable=False),
    Column("requested_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("resolved_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_memory_forgetting_requests_trace_id", "trace_id"),
    Index("ix_aion_memory_forgetting_requests_actor_id", "actor_id"),
    Index("ix_aion_memory_forgetting_requests_workspace_id", "workspace_id"),
    Index("ix_aion_memory_forgetting_requests_target_type", "target_type"),
    Index("ix_aion_memory_forgetting_requests_target_id", "target_id"),
    Index("ix_aion_memory_forgetting_requests_status", "status"),
    Index("ix_aion_memory_forgetting_requests_approval_request_id", "approval_request_id"),
    Index("ix_aion_memory_forgetting_requests_created_at", "created_at"),
)

aion_memory_conflicts = Table(
    "aion_memory_conflicts",
    memory_governance_metadata,
    Column("conflict_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("conflict_type", Text, nullable=False),
    Column("memory_ids", json_payload_type, nullable=False),
    Column("evidence_ids", json_payload_type, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("severity", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("detected_by", Text, nullable=False),
    Column("resolution", Text, nullable=True),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("resolved_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_memory_conflicts_trace_id", "trace_id"),
    Index("ix_aion_memory_conflicts_conflict_type", "conflict_type"),
    Index("ix_aion_memory_conflicts_severity", "severity"),
    Index("ix_aion_memory_conflicts_status", "status"),
    Index("ix_aion_memory_conflicts_detected_by", "detected_by"),
    Index("ix_aion_memory_conflicts_created_at", "created_at"),
)

aion_memory_compaction_runs = Table(
    "aion_memory_compaction_runs",
    memory_governance_metadata,
    Column("compaction_run_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("memory_types", json_payload_type, nullable=False),
    Column("status", Text, nullable=False),
    Column("input_memory_ids", json_payload_type, nullable=False),
    Column("output_memory_ids", json_payload_type, nullable=False),
    Column("strategy", Text, nullable=False),
    Column("result", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_memory_compaction_runs_trace_id", "trace_id"),
    Index("ix_aion_memory_compaction_runs_actor_id", "actor_id"),
    Index("ix_aion_memory_compaction_runs_workspace_id", "workspace_id"),
    Index("ix_aion_memory_compaction_runs_status", "status"),
    Index("ix_aion_memory_compaction_runs_strategy", "strategy"),
    Index("ix_aion_memory_compaction_runs_created_at", "created_at"),
)

aion_memory_compacted_records = Table(
    "aion_memory_compacted_records",
    memory_governance_metadata,
    Column("compacted_record_id", Text, primary_key=True),
    Column(
        "compaction_run_id",
        Text,
        ForeignKey("aion_memory_compaction_runs.compaction_run_id"),
        nullable=False,
    ),
    Column("output_memory_id", Text, nullable=False),
    Column("input_memory_ids", json_payload_type, nullable=False),
    Column("compaction_type", Text, nullable=False),
    Column("confidence", Float, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_memory_compacted_records_compaction_run_id", "compaction_run_id"),
    Index("ix_aion_memory_compacted_records_output_memory_id", "output_memory_id"),
    Index("ix_aion_memory_compacted_records_compaction_type", "compaction_type"),
    Index("ix_aion_memory_compacted_records_confidence", "confidence"),
    Index("ix_aion_memory_compacted_records_created_at", "created_at"),
)


class MemoryGovernanceRepository:
    """Repository for memory governance records."""

    def __init__(
        self,
        database_url: str | None = None,
        *,
        engine: Engine | None = None,
        auto_create: bool = True,
    ) -> None:
        if engine is None:
            if database_url is None:
                raise ValueError("database_url or engine is required")
            self._engine = _create_engine(database_url)
        else:
            self._engine = engine
        self._auto_create = auto_create
        self._schema_ready = False

    def save_rule(self, rule: MemoryGovernanceRule) -> MemoryGovernanceRule:
        """Upsert one governance rule."""
        self._ensure_schema()
        now = _now()
        stored = rule.model_copy(
            update={
                "created_at": rule.created_at or now,
                "updated_at": now,
            }
        )
        values = stored.model_dump(mode="python")
        with self._engine.begin() as connection:
            existing = connection.execute(
                select(aion_memory_governance_rules.c.governance_rule_id).where(
                    aion_memory_governance_rules.c.governance_rule_id == stored.governance_rule_id
                )
            ).first()
            if existing is None:
                connection.execute(insert(aion_memory_governance_rules).values(**values))
            else:
                connection.execute(
                    update(aion_memory_governance_rules)
                    .where(
                        aion_memory_governance_rules.c.governance_rule_id
                        == stored.governance_rule_id
                    )
                    .values(**values)
                )
        return stored

    def get_rule(self, governance_rule_id: str) -> MemoryGovernanceRule | None:
        """Return one governance rule."""
        self._ensure_schema()
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(aion_memory_governance_rules).where(
                        aion_memory_governance_rules.c.governance_rule_id == governance_rule_id
                    )
                )
                .mappings()
                .first()
            )
        return _rule_from_row(row) if row is not None else None

    def list_rules(
        self,
        *,
        status: str | None = None,
        rule_type: str | None = None,
    ) -> list[MemoryGovernanceRule]:
        """List governance rules."""
        self._ensure_schema()
        statement = select(aion_memory_governance_rules)
        if status is not None:
            statement = statement.where(aion_memory_governance_rules.c.status == status)
        if rule_type is not None:
            statement = statement.where(aion_memory_governance_rules.c.rule_type == rule_type)
        statement = statement.order_by(
            aion_memory_governance_rules.c.priority.asc(),
            aion_memory_governance_rules.c.created_at.asc(),
        )
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [_rule_from_row(row) for row in rows]

    def save_decision(self, decision: MemoryGovernanceDecision) -> MemoryGovernanceDecision:
        """Persist one governance decision."""
        self._ensure_schema()
        stored = decision.model_copy(update={"created_at": decision.created_at or _now()})
        with self._engine.begin() as connection:
            connection.execute(
                insert(aion_memory_governance_decisions).values(**stored.model_dump(mode="python"))
            )
        return stored

    def save_decay_record(self, record: MemoryDecayRecord) -> MemoryDecayRecord:
        """Persist one decay record."""
        self._ensure_schema()
        stored = record.model_copy(update={"created_at": record.created_at or _now()})
        with self._engine.begin() as connection:
            connection.execute(
                insert(aion_memory_decay_records).values(**stored.model_dump(mode="python"))
            )
        return stored

    def save_forgetting_request(
        self,
        request: MemoryForgettingRequestRecord,
    ) -> MemoryForgettingRequestRecord:
        """Upsert one forgetting request."""
        self._ensure_schema()
        stored = request.model_copy(update={"created_at": request.created_at or _now()})
        values = stored.model_dump(mode="python")
        with self._engine.begin() as connection:
            existing = connection.execute(
                select(aion_memory_forgetting_requests.c.forget_request_id).where(
                    aion_memory_forgetting_requests.c.forget_request_id == stored.forget_request_id
                )
            ).first()
            if existing is None:
                connection.execute(insert(aion_memory_forgetting_requests).values(**values))
            else:
                connection.execute(
                    update(aion_memory_forgetting_requests)
                    .where(
                        aion_memory_forgetting_requests.c.forget_request_id
                        == stored.forget_request_id
                    )
                    .values(**values)
                )
        return stored

    def get_forgetting_request(
        self,
        forget_request_id: str,
    ) -> MemoryForgettingRequestRecord | None:
        """Return one forgetting request."""
        self._ensure_schema()
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(aion_memory_forgetting_requests).where(
                        aion_memory_forgetting_requests.c.forget_request_id == forget_request_id
                    )
                )
                .mappings()
                .first()
            )
        return _forget_request_from_row(row) if row is not None else None

    def save_conflict(self, conflict: MemoryConflict) -> MemoryConflict:
        """Upsert one conflict."""
        self._ensure_schema()
        stored = conflict.model_copy(update={"created_at": conflict.created_at or _now()})
        values = stored.model_dump(mode="python")
        with self._engine.begin() as connection:
            existing = connection.execute(
                select(aion_memory_conflicts.c.conflict_id).where(
                    aion_memory_conflicts.c.conflict_id == stored.conflict_id
                )
            ).first()
            if existing is None:
                connection.execute(insert(aion_memory_conflicts).values(**values))
            else:
                connection.execute(
                    update(aion_memory_conflicts)
                    .where(aion_memory_conflicts.c.conflict_id == stored.conflict_id)
                    .values(**values)
                )
        return stored

    def get_conflict(self, conflict_id: str) -> MemoryConflict | None:
        """Return one conflict."""
        self._ensure_schema()
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(aion_memory_conflicts).where(
                        aion_memory_conflicts.c.conflict_id == conflict_id
                    )
                )
                .mappings()
                .first()
            )
        return _conflict_from_row(row) if row is not None else None

    def list_conflicts(
        self,
        scope: list[str],
        *,
        status: str | None = None,
        limit: int = 100,
    ) -> list[MemoryConflict]:
        """List conflicts visible to scope."""
        self._ensure_schema()
        statement = select(aion_memory_conflicts).order_by(
            aion_memory_conflicts.c.created_at.desc()
        )
        if status is not None:
            statement = statement.where(aion_memory_conflicts.c.status == status)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [
            conflict
            for conflict in (_conflict_from_row(row) for row in rows)
            if _scope_matches(conflict.owner_scope, scope)
        ][:limit]

    def save_compaction_run(
        self,
        run: MemoryCompactionRunRecord,
    ) -> MemoryCompactionRunRecord:
        """Upsert one compaction run."""
        self._ensure_schema()
        stored = run.model_copy(update={"created_at": run.created_at or _now()})
        values = stored.model_dump(mode="python")
        with self._engine.begin() as connection:
            existing = connection.execute(
                select(aion_memory_compaction_runs.c.compaction_run_id).where(
                    aion_memory_compaction_runs.c.compaction_run_id == stored.compaction_run_id
                )
            ).first()
            if existing is None:
                connection.execute(insert(aion_memory_compaction_runs).values(**values))
            else:
                connection.execute(
                    update(aion_memory_compaction_runs)
                    .where(
                        aion_memory_compaction_runs.c.compaction_run_id == stored.compaction_run_id
                    )
                    .values(**values)
                )
        return stored

    def get_compaction_run(self, compaction_run_id: str) -> MemoryCompactionRunRecord | None:
        """Return one compaction run."""
        self._ensure_schema()
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(aion_memory_compaction_runs).where(
                        aion_memory_compaction_runs.c.compaction_run_id == compaction_run_id
                    )
                )
                .mappings()
                .first()
            )
        return _compaction_run_from_row(row) if row is not None else None

    def save_compacted_record(self, record: MemoryCompactedRecord) -> MemoryCompactedRecord:
        """Persist one compacted relation."""
        self._ensure_schema()
        stored = record.model_copy(update={"created_at": record.created_at or _now()})
        with self._engine.begin() as connection:
            connection.execute(
                insert(aion_memory_compacted_records).values(**stored.model_dump(mode="python"))
            )
        return stored

    def _ensure_schema(self) -> None:
        if self._schema_ready or not self._auto_create:
            return
        memory_governance_metadata.create_all(self._engine)
        self._schema_ready = True


def _create_engine(database_url: str) -> Engine:
    if database_url.startswith("sqlite"):
        return create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    return create_engine(database_url, poolclass=QueuePool, pool_pre_ping=True)


def _rule_from_row(row: RowMapping) -> MemoryGovernanceRule:
    return MemoryGovernanceRule(
        governance_rule_id=str(row["governance_rule_id"]),
        name=str(row["name"]),
        description=str(row["description"]),
        status=cast(Any, str(row["status"])),
        rule_type=cast(MemoryGovernanceRuleType, str(row["rule_type"])),
        memory_types=cast(Any, _list_str(row["memory_types"])),
        owner_scope=_list_str(row["owner_scope"]),
        sensitivity_levels=cast(Any, _list_str(row["sensitivity_levels"])),
        conditions=_dict(row["conditions"]),
        action=cast(MemoryGovernanceAction, str(row["action"])),
        priority=int(row["priority"]),
        metadata=_dict(row["metadata"]),
        created_by=_optional_str(row["created_by"]),
        created_at=_optional_datetime(row["created_at"]),
        updated_at=_optional_datetime(row["updated_at"]),
        disabled_at=_optional_datetime(row["disabled_at"]),
    )


def _decision_from_row(row: RowMapping) -> MemoryGovernanceDecision:
    return MemoryGovernanceDecision(
        governance_decision_id=str(row["governance_decision_id"]),
        trace_id=_optional_str(row["trace_id"]),
        memory_id=_optional_str(row["memory_id"]),
        rule_ids=_list_str(row["rule_ids"]),
        decision=cast(MemoryGovernanceAction, str(row["decision"])),
        reason=str(row["reason"]),
        constraints=_list_str(row["constraints"]),
        metadata=_dict(row["metadata"]),
        created_at=_optional_datetime(row["created_at"]),
    )


def _forget_request_from_row(row: RowMapping) -> MemoryForgettingRequestRecord:
    return MemoryForgettingRequestRecord(
        forget_request_id=str(row["forget_request_id"]),
        trace_id=_optional_str(row["trace_id"]),
        actor_id=_optional_str(row["actor_id"]),
        workspace_id=_optional_str(row["workspace_id"]),
        target_type=cast(Any, str(row["target_type"])),
        target_id=str(row["target_id"]),
        owner_scope=_list_str(row["owner_scope"]),
        reason=str(row["reason"]),
        status=cast(ForgetStatus, str(row["status"])),
        risk_assessment_id=_optional_str(row["risk_assessment_id"]),
        approval_request_id=_optional_str(row["approval_request_id"]),
        result=_dict(row["result"]),
        requested_by=_optional_str(row["requested_by"]),
        created_at=_optional_datetime(row["created_at"]),
        resolved_at=_optional_datetime(row["resolved_at"]),
    )


def _conflict_from_row(row: RowMapping) -> MemoryConflict:
    return MemoryConflict(
        conflict_id=str(row["conflict_id"]),
        trace_id=_optional_str(row["trace_id"]),
        conflict_type=cast(MemoryConflictType, str(row["conflict_type"])),
        memory_ids=_list_str(row["memory_ids"]),
        evidence_ids=_list_str(row["evidence_ids"]),
        owner_scope=_list_str(row["owner_scope"]),
        severity=cast(MemoryConflictSeverity, str(row["severity"])),
        status=cast(MemoryConflictStatus, str(row["status"])),
        description=str(row["description"]),
        detected_by=str(row["detected_by"]),
        resolution=_optional_str(row["resolution"]),
        metadata=_dict(row["metadata"]),
        created_at=_optional_datetime(row["created_at"]),
        resolved_at=_optional_datetime(row["resolved_at"]),
    )


def _compaction_run_from_row(row: RowMapping) -> MemoryCompactionRunRecord:
    return MemoryCompactionRunRecord(
        compaction_run_id=str(row["compaction_run_id"]),
        trace_id=_optional_str(row["trace_id"]),
        actor_id=_optional_str(row["actor_id"]),
        workspace_id=_optional_str(row["workspace_id"]),
        owner_scope=_list_str(row["owner_scope"]),
        memory_types=_list_str(row["memory_types"]),
        status=cast(MemoryCompactionStatus, str(row["status"])),
        input_memory_ids=_list_str(row["input_memory_ids"]),
        output_memory_ids=_list_str(row["output_memory_ids"]),
        strategy=cast(MemoryCompactionStrategy, str(row["strategy"])),
        result=_dict(row["result"]),
        created_by=_optional_str(row["created_by"]),
        created_at=_optional_datetime(row["created_at"]),
        completed_at=_optional_datetime(row["completed_at"]),
    )


def _dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _list_str(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    return []


def _optional_str(value: Any) -> str | None:
    return str(value) if value is not None else None


def _optional_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo is not None else value.replace(tzinfo=UTC)
    if isinstance(value, str):
        parsed = datetime.fromisoformat(value)
        return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)
    return None


def _scope_matches(owner_scope: list[str], requested_scope: list[str]) -> bool:
    return bool(set(owner_scope) & set(requested_scope))


def _now() -> datetime:
    return datetime.now(UTC)
