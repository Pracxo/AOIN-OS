from __future__ import annotations

from sqlalchemy import inspect

from aion_brain.contracts.identity_assertion_replay import TABLE_NAME
from aion_brain.production_auth.identity_assertion_replay_repository import (
    IdentityAssertionReplayRepository,
)
from tests.test_identity_assertion_replay_contracts import make_replay_record, memory_engine


def test_auto_create_false_does_not_create_schema_and_fails_closed() -> None:
    engine = memory_engine()
    repository = IdentityAssertionReplayRepository(engine=engine)

    result = repository.claim(make_replay_record())

    assert result.outcome == "schema_unavailable"
    assert result.claim_created is False
    assert result.schema_available is False
    assert result.fail_closed is True
    assert inspect(engine).has_table(TABLE_NAME) is False


def test_auto_create_true_creates_only_replay_table() -> None:
    engine = memory_engine()
    IdentityAssertionReplayRepository(engine=engine, auto_create=True)

    inspector = inspect(engine)
    assert inspector.get_table_names() == [TABLE_NAME]
    assert {index["name"] for index in inspector.get_indexes(TABLE_NAME)} == {
        "ix_aion_identity_assertion_replay_retain_until",
        "ix_aion_identity_assertion_replay_claimed_at",
        "ix_aion_identity_assertion_replay_assertion_expires_at",
    }


def test_sqlite_naive_row_conversion_is_treated_as_utc() -> None:
    engine = memory_engine()
    repository = IdentityAssertionReplayRepository(engine=engine, auto_create=True)
    record = make_replay_record()
    assert repository.claim(record).outcome == "claimed"

    loaded = repository.get(record.replay_key)

    assert loaded is not None
    assert loaded.claimed_at.tzinfo is not None
    assert loaded.claimed_at.utcoffset().total_seconds() == 0
