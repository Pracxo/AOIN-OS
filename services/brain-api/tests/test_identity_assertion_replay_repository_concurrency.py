from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from aion_brain.production_auth.identity_assertion_replay_repository import (
    IdentityAssertionReplayRepository,
)
from tests.test_identity_assertion_replay_contracts import (
    file_engine,
    make_replay_record,
    table_count,
)


def test_concurrent_identical_claims_create_one_row(tmp_path) -> None:  # type: ignore[no-untyped-def]
    engine = file_engine(tmp_path / "replay.sqlite")
    IdentityAssertionReplayRepository(engine=engine, auto_create=True)
    record = make_replay_record(assertion_id="assertion-race-001")

    def claim_once() -> str:
        repository = IdentityAssertionReplayRepository(engine=engine)
        return repository.claim(record).outcome

    with ThreadPoolExecutor(max_workers=16) as executor:
        outcomes = list(executor.map(lambda _item: claim_once(), range(32)))

    assert outcomes.count("claimed") == 1
    assert outcomes.count("replay_detected") == 31
    assert outcomes.count("identifier_collision") == 0
    assert table_count(engine) == 1
