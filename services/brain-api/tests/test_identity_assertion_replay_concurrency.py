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


def test_concurrent_changed_payload_reuse_classifies_without_state_leak(tmp_path) -> None:  # type: ignore[no-untyped-def]
    engine = file_engine(tmp_path / "changed-payload-race.sqlite")
    IdentityAssertionReplayRepository(engine=engine, auto_create=True)
    records = [
        make_replay_record(assertion_id="same-id", subject=f"subject-{index}")
        for index in range(32)
    ]

    def claim(index: int) -> str:
        repository = IdentityAssertionReplayRepository(engine=engine)
        return repository.claim(records[index]).outcome

    with ThreadPoolExecutor(max_workers=16) as executor:
        outcomes = list(executor.map(claim, range(32)))

    assert outcomes.count("claimed") == 1
    assert outcomes.count("identifier_collision") == 31
    assert outcomes.count("replay_detected") == 0
    assert table_count(engine) == 1
