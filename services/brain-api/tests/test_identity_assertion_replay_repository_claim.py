from __future__ import annotations

import inspect

from aion_brain.production_auth.identity_assertion_replay_repository import (
    IdentityAssertionReplayRepository,
)
from tests.test_identity_assertion_replay_contracts import (
    make_replay_record,
    memory_engine,
    table_count,
)


def test_first_claim_creates_record_and_duplicate_detects_replay() -> None:
    engine = memory_engine()
    repository = IdentityAssertionReplayRepository(engine=engine, auto_create=True)
    record = make_replay_record()

    first = repository.claim(record)
    second = repository.claim(record)

    assert first.outcome == "claimed"
    assert first.claim_created is True
    assert first.fail_closed is False
    assert second.outcome == "replay_detected"
    assert second.replay_detected is True
    assert second.existing_assertion_fingerprint_matches is True
    assert second.fail_closed is True
    assert table_count(engine) == 1


def test_same_replay_key_with_changed_payload_is_identifier_collision() -> None:
    engine = memory_engine()
    repository = IdentityAssertionReplayRepository(engine=engine, auto_create=True)
    first_record = make_replay_record(assertion_id="assertion-777", subject="subject-a")
    changed_record = make_replay_record(assertion_id="assertion-777", subject="subject-b")

    assert repository.claim(first_record).outcome == "claimed"
    collision = repository.claim(changed_record)

    assert collision.outcome == "identifier_collision"
    assert collision.identifier_collision is True
    assert collision.existing_assertion_fingerprint_matches is False
    assert collision.fail_closed is True
    assert table_count(engine) == 1


def test_claim_source_uses_insert_before_duplicate_select() -> None:
    source = inspect.getsource(IdentityAssertionReplayRepository.claim)
    insert_position = source.index("insert(")
    load_existing_position = source.index("_load_existing")
    assert insert_position < load_existing_position
    assert ".get(" not in source[:insert_position]
    assert "select(" not in source[:insert_position]
