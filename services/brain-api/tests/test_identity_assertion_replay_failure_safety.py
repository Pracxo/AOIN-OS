from __future__ import annotations

from datetime import timedelta

import pytest

from aion_brain.production_auth.identity_assertion_replay_repository import (
    IdentityAssertionReplayRepository,
    IdentityAssertionReplayRepositoryError,
    aion_identity_assertion_replay_claims,
)
from tests.test_identity_assertion_replay_contracts import (
    NOW,
    make_replay_record,
    memory_engine,
)


class MissingExistingRepository(IdentityAssertionReplayRepository):
    def _load_existing(self, replay_key: str):  # type: ignore[no-untyped-def]
        return None


def test_schema_absent_fails_closed_without_sql_text() -> None:
    result = IdentityAssertionReplayRepository(engine=memory_engine()).claim(make_replay_record())
    evidence = str(result.model_dump(mode="json"))
    assert result.outcome == "schema_unavailable"
    assert result.fail_closed is True
    assert "SELECT" not in evidence
    assert "INSERT" not in evidence
    assert "no such table" not in evidence


def test_integrity_error_without_retrievable_row_fails_closed() -> None:
    engine = memory_engine()
    bootstrap = IdentityAssertionReplayRepository(engine=engine, auto_create=True)
    record = make_replay_record(assertion_id="missing-existing")
    assert bootstrap.claim(record).outcome == "claimed"

    result = MissingExistingRepository(engine=engine).claim(record)

    assert result.outcome == "repository_unavailable"
    assert result.fail_closed is True
    assert result.record is None


def test_malformed_database_row_fails_closed_after_duplicate() -> None:
    engine = memory_engine()
    IdentityAssertionReplayRepository(engine=engine, auto_create=True)
    record = make_replay_record(assertion_id="malformed-row")
    with engine.begin() as connection:
        connection.execute(
            aion_identity_assertion_replay_claims.insert().values(
                replay_key=record.replay_key,
                issuer_fingerprint=record.issuer_fingerprint,
                assertion_fingerprint="bad",
                claimed_at=record.claimed_at,
                assertion_expires_at=record.assertion_expires_at,
                retain_until=record.retain_until,
                created_at=record.created_at,
            )
        )

    result = IdentityAssertionReplayRepository(engine=engine).claim(record)

    assert result.outcome == "repository_unavailable"
    assert result.fail_closed is True


def test_cleanup_failure_raises_sanitized_reason_code() -> None:
    repository = IdentityAssertionReplayRepository(engine=memory_engine())
    with pytest.raises(IdentityAssertionReplayRepositoryError) as exc_info:
        repository.purge_expired(now=NOW + timedelta(days=1), limit=10)
    assert exc_info.value.reason_code == "identity_assertion_replay_cleanup_failed_closed"
    assert str(exc_info.value) == "identity_assertion_replay_cleanup_failed_closed"
