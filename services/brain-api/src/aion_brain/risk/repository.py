"""Risk assessment persistence."""

from datetime import UTC, datetime
from typing import Any, cast

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Float,
    Index,
    MetaData,
    Table,
    Text,
    create_engine,
    insert,
    select,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import Engine, RowMapping
from sqlalchemy.pool import QueuePool, StaticPool

from aion_brain.contracts.risk import RiskAssessment, RiskDecision, RiskLevel

risk_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_risk_assessments = Table(
    "aion_risk_assessments",
    risk_metadata,
    Column("risk_assessment_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("action_type", Text, nullable=False),
    Column("resource_type", Text, nullable=False),
    Column("resource_id", Text, nullable=True),
    Column("requested_risk_level", Text, nullable=False),
    Column("computed_risk_level", Text, nullable=False),
    Column("risk_score", Float, nullable=False),
    Column("factors", json_payload_type, nullable=False),
    Column("constraints", json_payload_type, nullable=False),
    Column("decision", Text, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_risk_assessments_trace_id", "trace_id"),
    Index("ix_aion_risk_assessments_actor_id", "actor_id"),
    Index("ix_aion_risk_assessments_workspace_id", "workspace_id"),
    Index("ix_aion_risk_assessments_action_type", "action_type"),
    Index("ix_aion_risk_assessments_resource_type", "resource_type"),
    Index("ix_aion_risk_assessments_computed_risk_level", "computed_risk_level"),
    Index("ix_aion_risk_assessments_decision", "decision"),
    Index("ix_aion_risk_assessments_created_at", "created_at"),
)


class RiskRepository:
    """Repository for risk assessment records."""

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

    def save_assessment(self, assessment: RiskAssessment) -> RiskAssessment:
        """Persist one risk assessment."""
        self._ensure_schema()
        stored = assessment.model_copy(update={"created_at": assessment.created_at or _now()})
        with self._engine.begin() as connection:
            connection.execute(
                insert(aion_risk_assessments).values(**stored.model_dump(mode="python"))
            )
        return stored

    def get_assessment(self, risk_assessment_id: str) -> RiskAssessment | None:
        """Return one risk assessment."""
        self._ensure_schema()
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    select(aion_risk_assessments).where(
                        aion_risk_assessments.c.risk_assessment_id == risk_assessment_id
                    )
                )
                .mappings()
                .first()
            )
        return _assessment_from_row(row) if row is not None else None

    def _ensure_schema(self) -> None:
        if self._schema_ready or not self._auto_create:
            return
        risk_metadata.create_all(self._engine)
        self._schema_ready = True


def _create_engine(database_url: str) -> Engine:
    if database_url.startswith("sqlite"):
        return create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    return create_engine(database_url, poolclass=QueuePool, pool_pre_ping=True)


def _assessment_from_row(row: RowMapping) -> RiskAssessment:
    return RiskAssessment(
        risk_assessment_id=str(row["risk_assessment_id"]),
        trace_id=_optional_str(row["trace_id"]),
        actor_id=_optional_str(row["actor_id"]),
        workspace_id=_optional_str(row["workspace_id"]),
        action_type=str(row["action_type"]),
        resource_type=str(row["resource_type"]),
        resource_id=_optional_str(row["resource_id"]),
        requested_risk_level=cast(RiskLevel, str(row["requested_risk_level"])),
        computed_risk_level=cast(RiskLevel, str(row["computed_risk_level"])),
        risk_score=float(row["risk_score"]),
        factors=_list_dict(row["factors"]),
        constraints=_list_str(row["constraints"]),
        decision=cast(RiskDecision, str(row["decision"])),
        metadata=_dict(row["metadata"]),
        created_at=_datetime(row["created_at"]),
    )


def _dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _list_dict(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [dict(item) for item in value if isinstance(item, dict)]
    return []


def _list_str(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    return []


def _optional_str(value: Any) -> str | None:
    return str(value) if value is not None else None


def _datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo is not None else value.replace(tzinfo=UTC)
    if isinstance(value, str):
        parsed = datetime.fromisoformat(value)
        return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)
    return _now()


def _now() -> datetime:
    return datetime.now(UTC)
