from __future__ import annotations

import os

import pytest
from test_knowledge_claim_graph_helpers import graph_repository, write_fixture

from aion_brain.knowledge_intelligence.claim_graph_repository import (
    ExplicitLocalClaimGraphFixtureReplay,
)


def test_fixture_replay_accepts_external_synthetic_fixture(tmp_path) -> None:
    repository = graph_repository()
    fixture = write_fixture(tmp_path / "claim-graph-fixture.json", repository.records())
    replayed = ExplicitLocalClaimGraphFixtureReplay().replay(
        fixture,
        repository_root="/Users/damilaremerotiwon/KITEV2/AOIN OS",
    )
    assert replayed.record_count() == repository.record_count()


def test_fixture_replay_rejects_relative_hidden_symlink_directory_and_missing_paths(
    tmp_path,
) -> None:
    replayer = ExplicitLocalClaimGraphFixtureReplay()
    with pytest.raises(ValueError):
        replayer.replay("relative.json", repository_root=tmp_path)
    hidden = tmp_path / ".hidden.json"
    hidden.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError):
        replayer.replay(hidden, repository_root="/Users/damilaremerotiwon/KITEV2/AOIN OS")
    target = tmp_path / "target.json"
    target.write_text("{}", encoding="utf-8")
    link = tmp_path / "link.json"
    os.symlink(target, link)
    with pytest.raises(ValueError):
        replayer.replay(link, repository_root="/Users/damilaremerotiwon/KITEV2/AOIN OS")
    with pytest.raises(ValueError):
        replayer.replay(tmp_path, repository_root="/Users/damilaremerotiwon/KITEV2/AOIN OS")
    with pytest.raises(ValueError):
        replayer.replay(
            tmp_path / "missing.json", repository_root="/Users/damilaremerotiwon/KITEV2/AOIN OS"
        )
