from __future__ import annotations

from datetime import timedelta

from aion_brain.production_auth.identity_assertion_replay_repository import (
    IdentityAssertionReplayRepository,
)
from tests.test_identity_assertion_replay_contracts import (
    NOW,
    make_replay_record,
    memory_engine,
    table_count,
)


def test_cleanup_purges_only_expired_rows_and_respects_limit() -> None:
    engine = memory_engine()
    repository = IdentityAssertionReplayRepository(engine=engine, auto_create=True)
    expired_one = make_replay_record(
        assertion_id="cleanup-1",
        claimed_at=NOW - timedelta(days=2),
        assertion_expires_at=NOW - timedelta(days=2, minutes=-5),
        retain_until=NOW - timedelta(seconds=2),
    )
    expired_two = make_replay_record(
        assertion_id="cleanup-2",
        claimed_at=NOW - timedelta(days=2),
        assertion_expires_at=NOW - timedelta(days=2, minutes=-5),
        retain_until=NOW - timedelta(seconds=1),
    )
    active = make_replay_record(assertion_id="cleanup-active")
    for record in (expired_one, expired_two, active):
        assert repository.claim(record).outcome == "claimed"

    assert repository.purge_expired(now=NOW, limit=1) == 1
    assert table_count(engine) == 2
    assert repository.get(expired_one.replay_key) is None
    assert repository.get(expired_two.replay_key) is not None
    assert repository.get(active.replay_key) is not None


def test_cleanup_equal_to_now_is_purged_future_is_retained() -> None:
    engine = memory_engine()
    repository = IdentityAssertionReplayRepository(engine=engine, auto_create=True)
    due = make_replay_record(
        assertion_id="cleanup-due",
        claimed_at=NOW - timedelta(days=2),
        assertion_expires_at=NOW - timedelta(days=2, minutes=-5),
        retain_until=NOW,
    )
    future = make_replay_record(assertion_id="cleanup-future")
    assert repository.claim(due).outcome == "claimed"
    assert repository.claim(future).outcome == "claimed"

    assert repository.purge_expired(now=NOW, limit=10) == 1

    assert repository.get(due.replay_key) is None
    assert repository.get(future.replay_key) is not None
