from __future__ import annotations

import json

import pytest
from knowledge_source_registry_implementation_helpers import fixture_payload, valid_batch

from aion_brain.knowledge_intelligence.source_registry_repository import (
    ExplicitLocalSourceRegistryFixtureReplay,
)


def test_source_registry_fixture_replay_accepts_explicit_synthetic_fixture(tmp_path):
    payload = fixture_payload(valid_batch().records)
    path = tmp_path / "source-registry-fixture.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    repository = ExplicitLocalSourceRegistryFixtureReplay().replay(
        path,
        repository_root="/Users/damilaremerotiwon/KITEV2/AOIN OS",
    )
    assert repository.record_count() == 6


def test_source_registry_fixture_replay_rejects_bad_paths(tmp_path):
    replay = ExplicitLocalSourceRegistryFixtureReplay(maximum_fixture_bytes=32)
    directory = tmp_path / "fixture-dir"
    directory.mkdir()
    hidden = tmp_path / ".hidden-fixture.json"
    hidden.write_text("{}", encoding="utf-8")
    target = tmp_path / "target.json"
    target.write_text("{}", encoding="utf-8")
    symlink = tmp_path / "link.json"
    symlink.symlink_to(target)
    for path in (
        "relative.json",
        "https://example.invalid/fixture.json",
        str(hidden),
        str(symlink),
        str(directory),
        str(tmp_path / "missing.json"),
        "/Users/damilaremerotiwon/KITEV2/AOIN OS/README.md",
    ):
        with pytest.raises(ValueError):
            replay.replay(path, repository_root="/Users/damilaremerotiwon/KITEV2/AOIN OS")


def test_source_registry_fixture_replay_rejects_invalid_payloads(tmp_path):
    replay = ExplicitLocalSourceRegistryFixtureReplay()
    payload = fixture_payload(valid_batch().records)
    cases = [
        {**payload, "extra": "rejected"},
        {**payload, "synthetic": False},
        {**payload, "records": []},
        {**payload, "records": [{**payload["records"][0], "source_body_bytes": 1}]},
    ]
    for index, bad_payload in enumerate(cases, start=1):
        path = tmp_path / f"bad-fixture-{index}.json"
        path.write_text(json.dumps(bad_payload), encoding="utf-8")
        with pytest.raises(ValueError):
            replay.replay(path, repository_root="/Users/damilaremerotiwon/KITEV2/AOIN OS")


def test_source_registry_fixture_replay_rejects_sequence_gap_and_broken_chain(tmp_path):
    replay = ExplicitLocalSourceRegistryFixtureReplay()
    records = list(valid_batch().records)
    gap_record = records[1].model_copy(update={"sequence_number": 99})
    broken_record = records[1].model_copy(update={"previous_record_fingerprint": "c" * 64})
    for index, changed_records in enumerate(
        ((records[0], gap_record), (records[0], broken_record)),
        start=1,
    ):
        path = tmp_path / f"broken-fixture-{index}.json"
        path.write_text(json.dumps(fixture_payload(tuple(changed_records))), encoding="utf-8")
        with pytest.raises(ValueError):
            replay.replay(path, repository_root="/Users/damilaremerotiwon/KITEV2/AOIN OS")
