from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

from aion_brain.production_auth.identity_assertion_replay_repository import (
    IdentityAssertionReplayRepository,
)
from tests.test_identity_assertion_replay_contracts import (
    NOW,
    file_engine,
    make_replay_record,
    replay_fixture,
    table_count,
)


def test_expired_retained_row_blocks_until_explicit_cleanup(tmp_path) -> None:  # type: ignore[no-untyped-def]
    engine = file_engine(tmp_path / "expired-retained.sqlite")
    repository = IdentityAssertionReplayRepository(engine=engine, auto_create=True)
    record = make_replay_record(
        assertion_id="expired-retained",
        claimed_at=NOW - timedelta(days=2),
        assertion_expires_at=NOW - timedelta(days=2, minutes=-5),
        retain_until=NOW,
    )
    assert repository.claim(record).outcome == "claimed"
    assert repository.claim(record).outcome == "replay_detected"
    assert repository.purge_expired(now=NOW, limit=10) == 1
    assert repository.claim(record).outcome == "claimed"


def test_cleanup_is_not_called_automatically_from_service_or_pipeline() -> None:
    fixture = replay_fixture()
    fixture.service.protect(
        envelope=fixture.envelope,
        verification_bundle=fixture.verification_bundle,
    )
    assert table_count(fixture.engine) == 1


def test_cleanup_and_claim_race_keeps_one_successful_claim(tmp_path) -> None:  # type: ignore[no-untyped-def]
    engine = file_engine(tmp_path / "cleanup-race.sqlite")
    IdentityAssertionReplayRepository(engine=engine, auto_create=True)
    record = make_replay_record(assertion_id="cleanup-race")

    def claim_once() -> str:
        return IdentityAssertionReplayRepository(engine=engine).claim(record).outcome

    def cleanup_once() -> str:
        IdentityAssertionReplayRepository(engine=engine).purge_expired(now=NOW, limit=10)
        return "cleanup"

    with ThreadPoolExecutor(max_workers=16) as executor:
        outcomes = list(
            executor.map(lambda index: claim_once() if index else cleanup_once(), range(32))
        )

    assert outcomes.count("claimed") == 1
    assert table_count(engine) == 1
