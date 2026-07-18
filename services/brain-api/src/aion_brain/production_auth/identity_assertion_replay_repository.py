"""SQLAlchemy repository for persistent identity assertion replay claims."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    Column,
    DateTime,
    Index,
    MetaData,
    Table,
    Text,
    delete,
    insert,
    inspect,
    select,
)
from sqlalchemy.engine import Engine, RowMapping
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from aion_brain.contracts.identity_assertion import normalize_utc_datetime
from aion_brain.contracts.identity_assertion_replay import (
    TABLE_NAME,
    IdentityAssertionReplayRecord,
    IdentityAssertionReplayRepositoryOutcome,
    IdentityAssertionReplayRepositoryResult,
    repository_reason_codes,
)

identity_assertion_replay_metadata = MetaData()

aion_identity_assertion_replay_claims = Table(
    TABLE_NAME,
    identity_assertion_replay_metadata,
    Column("replay_key", Text, primary_key=True),
    Column("issuer_fingerprint", Text, nullable=False),
    Column("assertion_fingerprint", Text, nullable=False),
    Column("claimed_at", DateTime(timezone=True), nullable=False),
    Column("assertion_expires_at", DateTime(timezone=True), nullable=False),
    Column("retain_until", DateTime(timezone=True), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_identity_assertion_replay_retain_until", "retain_until"),
    Index("ix_aion_identity_assertion_replay_claimed_at", "claimed_at"),
    Index("ix_aion_identity_assertion_replay_assertion_expires_at", "assertion_expires_at"),
)


class IdentityAssertionReplayRepositoryError(RuntimeError):
    """Sanitized replay repository exception carrying only a reason code."""

    def __init__(self, reason_code: str) -> None:
        if reason_code not in {
            "identity_assertion_replay_repository_unavailable",
            "identity_assertion_replay_schema_unavailable",
            "identity_assertion_replay_cleanup_failed_closed",
        }:
            raise ValueError("unsupported replay repository error reason code")
        self.reason_code = reason_code
        super().__init__(reason_code)


class IdentityAssertionReplayRepository:
    """Insert-first replay claim repository with a unique replay key."""

    def __init__(self, *, engine: Engine, auto_create: bool = False) -> None:
        self._engine = engine
        if auto_create:
            identity_assertion_replay_metadata.create_all(self._engine)

    def claim(
        self,
        record: IdentityAssertionReplayRecord,
    ) -> IdentityAssertionReplayRepositoryResult:
        """Claim one replay key atomically, or fail closed with a safe result."""

        try:
            with self._engine.begin() as connection:
                connection.execute(
                    insert(aion_identity_assertion_replay_claims).values(
                        **record.model_dump(mode="python", exclude={"schema_version"})
                    )
                )
            return _result(
                outcome="claimed",
                record=record,
                existing_record=None,
                repository_available=True,
                schema_available=True,
            )
        except IntegrityError:
            existing = self._load_existing(record.replay_key)
            if existing is None:
                return _result(
                    outcome="repository_unavailable",
                    record=record,
                    existing_record=None,
                    repository_available=False,
                    schema_available=False,
                )
            outcome: IdentityAssertionReplayRepositoryOutcome
            if record.assertion_fingerprint == existing.assertion_fingerprint:
                outcome = "replay_detected"
            else:
                outcome = "identifier_collision"
            return _result(
                outcome=outcome,
                record=record,
                existing_record=existing,
                repository_available=True,
                schema_available=True,
            )
        except SQLAlchemyError:
            schema_available = self._schema_available()
            if schema_available is False:
                return _result(
                    outcome="schema_unavailable",
                    record=record,
                    existing_record=None,
                    repository_available=True,
                    schema_available=False,
                )
            return _result(
                outcome="repository_unavailable",
                record=record,
                existing_record=None,
                repository_available=False,
                schema_available=False,
            )

    def purge_expired(self, *, now: datetime, limit: int) -> int:
        """Delete expired replay records using explicit caller-driven cleanup."""

        if limit < 1 or limit > 10_000:
            raise ValueError("limit must be in 1..10000")
        cutoff = normalize_utc_datetime(now)
        try:
            statement = (
                select(aion_identity_assertion_replay_claims.c.replay_key)
                .where(aion_identity_assertion_replay_claims.c.retain_until <= cutoff)
                .order_by(
                    aion_identity_assertion_replay_claims.c.retain_until,
                    aion_identity_assertion_replay_claims.c.replay_key,
                )
                .limit(limit)
            )
            with self._engine.begin() as connection:
                replay_keys = [str(row[0]) for row in connection.execute(statement).all()]
                if not replay_keys:
                    return 0
                connection.execute(
                    delete(aion_identity_assertion_replay_claims).where(
                        aion_identity_assertion_replay_claims.c.replay_key.in_(replay_keys)
                    )
                )
                return len(replay_keys)
        except SQLAlchemyError:
            raise IdentityAssertionReplayRepositoryError(
                "identity_assertion_replay_cleanup_failed_closed"
            ) from None

    def get(self, replay_key: str) -> IdentityAssertionReplayRecord | None:
        """Return one safe replay record by replay key."""

        return self._load_existing(replay_key)

    def _load_existing(self, replay_key: str) -> IdentityAssertionReplayRecord | None:
        try:
            with self._engine.connect() as connection:
                row = (
                    connection.execute(
                        select(aion_identity_assertion_replay_claims).where(
                            aion_identity_assertion_replay_claims.c.replay_key == replay_key
                        )
                    )
                    .mappings()
                    .first()
                )
        except SQLAlchemyError:
            return None
        if row is None:
            return None
        try:
            return _row_to_record(row)
        except (TypeError, ValueError):
            return None

    def _schema_available(self) -> bool | None:
        try:
            return bool(inspect(self._engine).has_table(TABLE_NAME))
        except SQLAlchemyError:
            return None


def _result(
    *,
    outcome: IdentityAssertionReplayRepositoryOutcome,
    record: IdentityAssertionReplayRecord,
    existing_record: IdentityAssertionReplayRecord | None,
    repository_available: bool,
    schema_available: bool,
) -> IdentityAssertionReplayRepositoryResult:
    result_record = record if outcome == "claimed" else existing_record
    return IdentityAssertionReplayRepositoryResult(
        operation_id=f"identity-assertion-replay-repository-{outcome}",
        outcome=outcome,
        claim_created=outcome == "claimed",
        replay_detected=outcome == "replay_detected",
        identifier_collision=outcome == "identifier_collision",
        repository_available=repository_available,
        schema_available=schema_available,
        fail_closed=outcome != "claimed",
        existing_assertion_fingerprint_matches=outcome == "replay_detected",
        record=result_record,
        primary_reason_code=repository_reason_codes(outcome)[0],
        reason_codes=repository_reason_codes(outcome),
        created_at=record.claimed_at,
    )


def _row_to_record(row: RowMapping) -> IdentityAssertionReplayRecord:
    return IdentityAssertionReplayRecord(
        replay_key=str(row["replay_key"]),
        issuer_fingerprint=str(row["issuer_fingerprint"]),
        assertion_fingerprint=str(row["assertion_fingerprint"]),
        claimed_at=_utc_datetime(row["claimed_at"]),
        assertion_expires_at=_utc_datetime(row["assertion_expires_at"]),
        retain_until=_utc_datetime(row["retain_until"]),
        created_at=_utc_datetime(row["created_at"]),
    )


def _utc_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        converted = value if value.tzinfo else value.replace(tzinfo=UTC)
        return normalize_utc_datetime(converted)
    if isinstance(value, str):
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        converted = parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
        return normalize_utc_datetime(converted)
    raise TypeError("Expected datetime-compatible value")


__all__ = [
    "IdentityAssertionReplayRepository",
    "IdentityAssertionReplayRepositoryError",
    "aion_identity_assertion_replay_claims",
    "identity_assertion_replay_metadata",
]
