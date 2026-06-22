"""Persistence boundary for AION model gateway records."""

from datetime import UTC, datetime
from typing import Any

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
    create_engine,
    delete,
    insert,
    select,
    update,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import Engine, RowMapping
from sqlalchemy.pool import QueuePool, StaticPool

from aion_brain.contracts.model_gateway import (
    ModelBudgetRecord,
    ModelProfile,
    ModelProvider,
    ModelUsageRecord,
    PromptRedactionRecord,
)

model_gateway_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_model_providers = Table(
    "aion_model_providers",
    model_gateway_metadata,
    Column("provider_id", Text, primary_key=True),
    Column("provider_type", Text, nullable=False),
    Column("display_name", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("endpoint_ref", Text, nullable=True),
    Column("config", json_payload_type, nullable=False),
    Column("health_status", Text, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("last_health_check_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_model_providers_provider_type", "provider_type"),
    Index("ix_aion_model_providers_status", "status"),
    Index("ix_aion_model_providers_health_status", "health_status"),
    Index("ix_aion_model_providers_created_at", "created_at"),
)

aion_model_profiles = Table(
    "aion_model_profiles",
    model_gateway_metadata,
    Column("model_profile_id", Text, primary_key=True),
    Column("provider_id", Text, nullable=False),
    Column("model_name", Text, nullable=False),
    Column("mode", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("privacy_level", Text, nullable=False),
    Column("risk_level", Text, nullable=False),
    Column("max_input_tokens", Integer, nullable=False),
    Column("max_output_tokens", Integer, nullable=False),
    Column("cost_per_1k_input_tokens", Float, nullable=True),
    Column("cost_per_1k_output_tokens", Float, nullable=True),
    Column("latency_class", Text, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_model_profiles_provider_id", "provider_id"),
    Index("ix_aion_model_profiles_model_name", "model_name"),
    Index("ix_aion_model_profiles_mode", "mode"),
    Index("ix_aion_model_profiles_status", "status"),
    Index("ix_aion_model_profiles_privacy_level", "privacy_level"),
    Index("ix_aion_model_profiles_risk_level", "risk_level"),
    Index("ix_aion_model_profiles_latency_class", "latency_class"),
    Index("ix_aion_model_profiles_created_at", "created_at"),
)

aion_model_budget_records = Table(
    "aion_model_budget_records",
    model_gateway_metadata,
    Column("budget_id", Text, primary_key=True),
    Column("workspace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("scope", json_payload_type, nullable=False),
    Column("budget_type", Text, nullable=False),
    Column("limit_amount", Float, nullable=False),
    Column("used_amount", Float, nullable=False),
    Column("currency", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("resets_at", DateTime(timezone=True), nullable=True),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_model_budget_records_workspace_id", "workspace_id"),
    Index("ix_aion_model_budget_records_actor_id", "actor_id"),
    Index("ix_aion_model_budget_records_budget_type", "budget_type"),
    Index("ix_aion_model_budget_records_status", "status"),
    Index("ix_aion_model_budget_records_resets_at", "resets_at"),
    Index("ix_aion_model_budget_records_created_at", "created_at"),
)

aion_model_usage_records = Table(
    "aion_model_usage_records",
    model_gateway_metadata,
    Column("usage_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("reasoning_id", Text, nullable=True),
    Column("model_call_id", Text, nullable=True),
    Column("provider_id", Text, nullable=False),
    Column("model_profile_id", Text, nullable=True),
    Column("model_name", Text, nullable=False),
    Column("mode", Text, nullable=False),
    Column("input_token_estimate", Integer, nullable=False),
    Column("output_token_estimate", Integer, nullable=False),
    Column("cost_estimate", Float, nullable=False),
    Column("latency_ms", Integer, nullable=True),
    Column("status", Text, nullable=False),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_model_usage_records_trace_id", "trace_id"),
    Index("ix_aion_model_usage_records_reasoning_id", "reasoning_id"),
    Index("ix_aion_model_usage_records_model_call_id", "model_call_id"),
    Index("ix_aion_model_usage_records_provider_id", "provider_id"),
    Index("ix_aion_model_usage_records_model_profile_id", "model_profile_id"),
    Index("ix_aion_model_usage_records_model_name", "model_name"),
    Index("ix_aion_model_usage_records_mode", "mode"),
    Index("ix_aion_model_usage_records_status", "status"),
    Index("ix_aion_model_usage_records_actor_id", "actor_id"),
    Index("ix_aion_model_usage_records_workspace_id", "workspace_id"),
    Index("ix_aion_model_usage_records_created_at", "created_at"),
)

aion_prompt_redaction_records = Table(
    "aion_prompt_redaction_records",
    model_gateway_metadata,
    Column("redaction_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("reasoning_id", Text, nullable=True),
    Column("prompt_id", Text, nullable=True),
    Column("redaction_count", Integer, nullable=False),
    Column("redaction_types", json_payload_type, nullable=False),
    Column("blocked", Boolean, nullable=False),
    Column("reason", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_prompt_redaction_records_trace_id", "trace_id"),
    Index("ix_aion_prompt_redaction_records_reasoning_id", "reasoning_id"),
    Index("ix_aion_prompt_redaction_records_prompt_id", "prompt_id"),
    Index("ix_aion_prompt_redaction_records_blocked", "blocked"),
    Index("ix_aion_prompt_redaction_records_created_at", "created_at"),
)


class ModelGatewayRepository:
    """Repository for model providers, profiles, budgets, usage, and redactions."""

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
            if database_url.startswith("sqlite") and ":memory:" in database_url:
                self._engine = create_engine(
                    database_url,
                    connect_args={"check_same_thread": False},
                    poolclass=StaticPool,
                )
            else:
                self._engine = create_engine(database_url, poolclass=QueuePool, pool_pre_ping=True)
        else:
            self._engine = engine
        self._auto_create = auto_create
        self._schema_ready = False

    def save_provider(self, provider: ModelProvider) -> ModelProvider:
        """Persist a model provider."""
        self._ensure_schema()
        now = datetime.now(UTC)
        record = provider.model_copy(
            update={
                "created_at": provider.created_at or now,
                "updated_at": now,
            }
        )
        with self._engine.begin() as connection:
            connection.execute(
                delete(aion_model_providers).where(
                    aion_model_providers.c.provider_id == record.provider_id
                )
            )
            connection.execute(
                insert(aion_model_providers).values(**record.model_dump(mode="python"))
            )
        return record

    def get_provider(self, provider_id: str) -> ModelProvider | None:
        """Return one provider by ID."""
        self._ensure_schema()
        statement = select(aion_model_providers).where(
            aion_model_providers.c.provider_id == provider_id
        )
        with self._engine.connect() as connection:
            row = connection.execute(statement).mappings().first()
        return _row_to_provider(row) if row is not None else None

    def list_providers(self, status: str | None = None) -> list[ModelProvider]:
        """List providers, optionally filtered by status."""
        self._ensure_schema()
        statement = select(aion_model_providers)
        if status is not None:
            statement = statement.where(aion_model_providers.c.status == status)
        statement = statement.order_by(aion_model_providers.c.created_at)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [_row_to_provider(row) for row in rows]

    def save_profile(self, profile: ModelProfile) -> ModelProfile:
        """Persist a model profile."""
        self._ensure_schema()
        now = datetime.now(UTC)
        record = profile.model_copy(
            update={
                "created_at": profile.created_at or now,
                "updated_at": now,
            }
        )
        with self._engine.begin() as connection:
            connection.execute(
                delete(aion_model_profiles).where(
                    aion_model_profiles.c.model_profile_id == record.model_profile_id
                )
            )
            connection.execute(
                insert(aion_model_profiles).values(**record.model_dump(mode="python"))
            )
        return record

    def get_profile(self, model_profile_id: str) -> ModelProfile | None:
        """Return one profile by ID."""
        self._ensure_schema()
        statement = select(aion_model_profiles).where(
            aion_model_profiles.c.model_profile_id == model_profile_id
        )
        with self._engine.connect() as connection:
            row = connection.execute(statement).mappings().first()
        return _row_to_profile(row) if row is not None else None

    def list_profiles(
        self,
        *,
        provider_id: str | None = None,
        mode: str | None = None,
        status: str | None = None,
    ) -> list[ModelProfile]:
        """List profiles, optionally filtered by provider, mode, and status."""
        self._ensure_schema()
        statement = select(aion_model_profiles)
        if provider_id is not None:
            statement = statement.where(aion_model_profiles.c.provider_id == provider_id)
        if mode is not None:
            statement = statement.where(aion_model_profiles.c.mode == mode)
        if status is not None:
            statement = statement.where(aion_model_profiles.c.status == status)
        statement = statement.order_by(aion_model_profiles.c.created_at)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [_row_to_profile(row) for row in rows]

    def save_budget(self, budget: ModelBudgetRecord) -> ModelBudgetRecord:
        """Persist a model budget record."""
        self._ensure_schema()
        now = datetime.now(UTC)
        record = budget.model_copy(
            update={
                "created_at": budget.created_at or now,
                "updated_at": now,
            }
        )
        with self._engine.begin() as connection:
            connection.execute(
                delete(aion_model_budget_records).where(
                    aion_model_budget_records.c.budget_id == record.budget_id
                )
            )
            connection.execute(
                insert(aion_model_budget_records).values(**record.model_dump(mode="python"))
            )
        return record

    def list_budgets(
        self,
        *,
        workspace_id: str | None = None,
        actor_id: str | None = None,
        status: str | None = None,
    ) -> list[ModelBudgetRecord]:
        """List budget records."""
        self._ensure_schema()
        statement = select(aion_model_budget_records)
        if workspace_id is not None:
            statement = statement.where(aion_model_budget_records.c.workspace_id == workspace_id)
        if actor_id is not None:
            statement = statement.where(aion_model_budget_records.c.actor_id == actor_id)
        if status is not None:
            statement = statement.where(aion_model_budget_records.c.status == status)
        statement = statement.order_by(aion_model_budget_records.c.created_at)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [_row_to_budget(row) for row in rows]

    def increment_budget_usage(self, budget_id: str, amount: float) -> ModelBudgetRecord | None:
        """Increment a budget's used amount and return the updated record."""
        self._ensure_schema()
        existing = self.get_budget(budget_id)
        if existing is None:
            return None
        updated = existing.model_copy(
            update={
                "used_amount": existing.used_amount + amount,
                "updated_at": datetime.now(UTC),
            }
        )
        with self._engine.begin() as connection:
            connection.execute(
                update(aion_model_budget_records)
                .where(aion_model_budget_records.c.budget_id == budget_id)
                .values(
                    used_amount=updated.used_amount,
                    updated_at=updated.updated_at,
                    status=updated.status,
                )
            )
        return updated

    def get_budget(self, budget_id: str) -> ModelBudgetRecord | None:
        """Return one budget by ID."""
        self._ensure_schema()
        statement = select(aion_model_budget_records).where(
            aion_model_budget_records.c.budget_id == budget_id
        )
        with self._engine.connect() as connection:
            row = connection.execute(statement).mappings().first()
        return _row_to_budget(row) if row is not None else None

    def save_usage(self, usage: ModelUsageRecord) -> ModelUsageRecord:
        """Persist a model usage record."""
        self._ensure_schema()
        record = usage.model_copy(update={"created_at": usage.created_at or datetime.now(UTC)})
        with self._engine.begin() as connection:
            connection.execute(
                delete(aion_model_usage_records).where(
                    aion_model_usage_records.c.usage_id == record.usage_id
                )
            )
            connection.execute(
                insert(aion_model_usage_records).values(**record.model_dump(mode="python"))
            )
        return record

    def list_usage(
        self,
        *,
        trace_id: str | None = None,
        reasoning_id: str | None = None,
        provider_id: str | None = None,
        workspace_id: str | None = None,
        limit: int = 100,
    ) -> list[ModelUsageRecord]:
        """List usage records."""
        self._ensure_schema()
        statement = select(aion_model_usage_records)
        if trace_id is not None:
            statement = statement.where(aion_model_usage_records.c.trace_id == trace_id)
        if reasoning_id is not None:
            statement = statement.where(aion_model_usage_records.c.reasoning_id == reasoning_id)
        if provider_id is not None:
            statement = statement.where(aion_model_usage_records.c.provider_id == provider_id)
        if workspace_id is not None:
            statement = statement.where(aion_model_usage_records.c.workspace_id == workspace_id)
        statement = statement.order_by(aion_model_usage_records.c.created_at.desc()).limit(limit)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [_row_to_usage(row) for row in rows]

    def save_redaction(self, redaction: PromptRedactionRecord) -> PromptRedactionRecord:
        """Persist a prompt redaction record."""
        self._ensure_schema()
        record = redaction.model_copy(
            update={"created_at": redaction.created_at or datetime.now(UTC)}
        )
        with self._engine.begin() as connection:
            connection.execute(
                delete(aion_prompt_redaction_records).where(
                    aion_prompt_redaction_records.c.redaction_id == record.redaction_id
                )
            )
            connection.execute(
                insert(aion_prompt_redaction_records).values(**record.model_dump(mode="python"))
            )
        return record

    def _ensure_schema(self) -> None:
        if self._schema_ready or not self._auto_create:
            return
        model_gateway_metadata.create_all(self._engine)
        self._schema_ready = True


def _row_to_provider(row: RowMapping) -> ModelProvider:
    return ModelProvider(
        provider_id=str(row["provider_id"]),
        provider_type=row["provider_type"],
        display_name=str(row["display_name"]),
        status=row["status"],
        endpoint_ref=_optional_str(row["endpoint_ref"]),
        config=dict(row["config"]),
        health_status=row["health_status"],
        created_at=_optional_datetime(row["created_at"]),
        updated_at=_optional_datetime(row["updated_at"]),
        last_health_check_at=_optional_datetime(row["last_health_check_at"]),
    )


def _row_to_profile(row: RowMapping) -> ModelProfile:
    return ModelProfile(
        model_profile_id=str(row["model_profile_id"]),
        provider_id=str(row["provider_id"]),
        model_name=str(row["model_name"]),
        mode=row["mode"],
        status=row["status"],
        privacy_level=row["privacy_level"],
        risk_level=row["risk_level"],
        max_input_tokens=int(row["max_input_tokens"]),
        max_output_tokens=int(row["max_output_tokens"]),
        cost_per_1k_input_tokens=_optional_float(row["cost_per_1k_input_tokens"]),
        cost_per_1k_output_tokens=_optional_float(row["cost_per_1k_output_tokens"]),
        latency_class=row["latency_class"],
        metadata=dict(row["metadata"]),
        created_at=_optional_datetime(row["created_at"]),
        updated_at=_optional_datetime(row["updated_at"]),
    )


def _row_to_budget(row: RowMapping) -> ModelBudgetRecord:
    return ModelBudgetRecord(
        budget_id=str(row["budget_id"]),
        workspace_id=_optional_str(row["workspace_id"]),
        actor_id=_optional_str(row["actor_id"]),
        scope=list(row["scope"]),
        budget_type=row["budget_type"],
        limit_amount=float(row["limit_amount"]),
        used_amount=float(row["used_amount"]),
        currency=str(row["currency"]),
        status=row["status"],
        resets_at=_optional_datetime(row["resets_at"]),
        metadata=dict(row["metadata"]),
        created_at=_optional_datetime(row["created_at"]),
        updated_at=_optional_datetime(row["updated_at"]),
    )


def _row_to_usage(row: RowMapping) -> ModelUsageRecord:
    return ModelUsageRecord(
        usage_id=str(row["usage_id"]),
        trace_id=_optional_str(row["trace_id"]),
        reasoning_id=_optional_str(row["reasoning_id"]),
        model_call_id=_optional_str(row["model_call_id"]),
        provider_id=str(row["provider_id"]),
        model_profile_id=_optional_str(row["model_profile_id"]),
        model_name=str(row["model_name"]),
        mode=row["mode"],
        input_token_estimate=int(row["input_token_estimate"]),
        output_token_estimate=int(row["output_token_estimate"]),
        cost_estimate=float(row["cost_estimate"]),
        latency_ms=_optional_int(row["latency_ms"]),
        status=row["status"],
        actor_id=_optional_str(row["actor_id"]),
        workspace_id=_optional_str(row["workspace_id"]),
        created_at=_optional_datetime(row["created_at"]),
    )


def _optional_str(value: Any) -> str | None:
    return None if value is None else str(value)


def _optional_int(value: Any) -> int | None:
    return None if value is None else int(value)


def _optional_float(value: Any) -> float | None:
    return None if value is None else float(value)


def _optional_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo is not None else value.replace(tzinfo=UTC)
    if isinstance(value, str):
        parsed = datetime.fromisoformat(value)
        return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)
    raise TypeError(f"Expected datetime-compatible value, got {type(value)!r}")
