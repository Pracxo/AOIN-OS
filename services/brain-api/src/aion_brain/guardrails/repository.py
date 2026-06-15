"""Guardrail rule and decision persistence."""

from datetime import UTC, datetime
from typing import Any, cast

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Index,
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

from aion_brain.contracts.guardrails import (
    GuardrailDecision,
    GuardrailEffect,
    GuardrailRule,
    GuardrailSeverity,
    GuardrailStatus,
)
from aion_brain.contracts.risk import RiskLevel

guardrail_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_guardrail_rules = Table(
    "aion_guardrail_rules",
    guardrail_metadata,
    Column("guardrail_id", Text, primary_key=True),
    Column("name", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("scope", json_payload_type, nullable=False),
    Column("action_types", json_payload_type, nullable=False),
    Column("resource_types", json_payload_type, nullable=False),
    Column("risk_levels", json_payload_type, nullable=False),
    Column("conditions", json_payload_type, nullable=False),
    Column("effect", Text, nullable=False),
    Column("severity", Text, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("disabled_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_guardrail_rules_name", "name"),
    Index("ix_aion_guardrail_rules_status", "status"),
    Index("ix_aion_guardrail_rules_effect", "effect"),
    Index("ix_aion_guardrail_rules_severity", "severity"),
    Index("ix_aion_guardrail_rules_created_at", "created_at"),
)

aion_guardrail_decisions = Table(
    "aion_guardrail_decisions",
    guardrail_metadata,
    Column("guardrail_decision_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("risk_assessment_id", Text, nullable=True),
    Column("action_type", Text, nullable=False),
    Column("resource_type", Text, nullable=False),
    Column("resource_id", Text, nullable=True),
    Column("matched_guardrails", json_payload_type, nullable=False),
    Column("allow", Boolean, nullable=False),
    Column("approval_required", Boolean, nullable=False),
    Column("blocked", Boolean, nullable=False),
    Column("severity", Text, nullable=False),
    Column("reason", Text, nullable=False),
    Column("constraints", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_guardrail_decisions_trace_id", "trace_id"),
    Index("ix_aion_guardrail_decisions_risk_assessment_id", "risk_assessment_id"),
    Index("ix_aion_guardrail_decisions_action_type", "action_type"),
    Index("ix_aion_guardrail_decisions_resource_type", "resource_type"),
    Index("ix_aion_guardrail_decisions_allow", "allow"),
    Index("ix_aion_guardrail_decisions_approval_required", "approval_required"),
    Index("ix_aion_guardrail_decisions_blocked", "blocked"),
    Index("ix_aion_guardrail_decisions_severity", "severity"),
    Index("ix_aion_guardrail_decisions_created_at", "created_at"),
)


class GuardrailRepository:
    """Repository for guardrail rules and evaluation decisions."""

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

    def save_rule(self, rule: GuardrailRule) -> GuardrailRule:
        """Upsert one guardrail rule."""
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
                select(aion_guardrail_rules.c.guardrail_id).where(
                    aion_guardrail_rules.c.guardrail_id == stored.guardrail_id
                )
            ).first()
            if existing is None:
                connection.execute(insert(aion_guardrail_rules).values(**values))
            else:
                connection.execute(
                    update(aion_guardrail_rules)
                    .where(aion_guardrail_rules.c.guardrail_id == stored.guardrail_id)
                    .values(**values)
                )
        return stored

    def get_rule(self, guardrail_id: str) -> GuardrailRule | None:
        """Return one guardrail rule."""
        self._ensure_schema()
        with self._engine.connect() as connection:
            row = connection.execute(
                select(aion_guardrail_rules).where(
                    aion_guardrail_rules.c.guardrail_id == guardrail_id
                )
            ).mappings().first()
        return _rule_from_row(row) if row is not None else None

    def list_rules(self, status: str | None = None) -> list[GuardrailRule]:
        """List guardrail rules."""
        self._ensure_schema()
        statement = select(aion_guardrail_rules).order_by(aion_guardrail_rules.c.created_at)
        if status is not None:
            statement = statement.where(aion_guardrail_rules.c.status == status)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [_rule_from_row(row) for row in rows]

    def save_decision(self, decision: GuardrailDecision) -> GuardrailDecision:
        """Persist one guardrail decision."""
        self._ensure_schema()
        stored = decision.model_copy(update={"created_at": decision.created_at or _now()})
        with self._engine.begin() as connection:
            connection.execute(
                insert(aion_guardrail_decisions).values(**stored.model_dump(mode="python"))
            )
        return stored

    def _ensure_schema(self) -> None:
        if self._schema_ready or not self._auto_create:
            return
        guardrail_metadata.create_all(self._engine)
        self._schema_ready = True


def _create_engine(database_url: str) -> Engine:
    if database_url.startswith("sqlite"):
        return create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    return create_engine(database_url, poolclass=QueuePool, pool_pre_ping=True)


def _rule_from_row(row: RowMapping) -> GuardrailRule:
    return GuardrailRule(
        guardrail_id=str(row["guardrail_id"]),
        name=str(row["name"]),
        description=str(row["description"]),
        status=cast(GuardrailStatus, str(row["status"])),
        scope=_list_str(row["scope"]),
        action_types=_list_str(row["action_types"]),
        resource_types=_list_str(row["resource_types"]),
        risk_levels=[cast(RiskLevel, item) for item in _list_str(row["risk_levels"])],
        conditions=_dict(row["conditions"]),
        effect=cast(GuardrailEffect, str(row["effect"])),
        severity=cast(GuardrailSeverity, str(row["severity"])),
        metadata=_dict(row["metadata"]),
        created_by=_optional_str(row["created_by"]),
        created_at=_optional_datetime(row["created_at"]),
        updated_at=_optional_datetime(row["updated_at"]),
        disabled_at=_optional_datetime(row["disabled_at"]),
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


def _now() -> datetime:
    return datetime.now(UTC)
