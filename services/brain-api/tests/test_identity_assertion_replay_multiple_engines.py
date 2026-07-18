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


def test_multiple_engines_share_unique_replay_key_constraint(tmp_path) -> None:  # type: ignore[no-untyped-def]
    db_path = tmp_path / "shared-replay.sqlite"
    engine_a = file_engine(db_path)
    engine_b = file_engine(db_path)
    repo_a = IdentityAssertionReplayRepository(engine=engine_a, auto_create=True)
    repo_b = IdentityAssertionReplayRepository(engine=engine_b)
    record = make_replay_record(assertion_id="assertion-shared-engine")

    assert repo_a.claim(record).outcome == "claimed"
    assert repo_b.claim(record).outcome == "replay_detected"
    assert table_count(engine_a) == 1
    assert table_count(engine_b) == 1


def test_concurrent_changed_payloads_across_engines_do_not_create_second_row(tmp_path) -> None:  # type: ignore[no-untyped-def]
    db_path = tmp_path / "shared-collision.sqlite"
    bootstrap_engine = file_engine(db_path)
    IdentityAssertionReplayRepository(engine=bootstrap_engine, auto_create=True)
    records = [
        make_replay_record(
            assertion_id="assertion-shared-collision",
            subject=f"subject-{index}",
        )
        for index in range(32)
    ]

    def claim_record(index: int) -> str:
        engine = file_engine(db_path)
        repository = IdentityAssertionReplayRepository(engine=engine)
        return repository.claim(records[index]).outcome

    with ThreadPoolExecutor(max_workers=16) as executor:
        outcomes = list(executor.map(claim_record, range(len(records))))

    assert outcomes.count("claimed") == 1
    assert outcomes.count("identifier_collision") == 31
    assert table_count(bootstrap_engine) == 1
