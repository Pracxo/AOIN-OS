from __future__ import annotations

import json

import pytest
from knowledge_verified_memory_test_helpers import sample_version

from aion_brain.knowledge_intelligence.verified_knowledge_memory import (
    InMemoryVerifiedKnowledgeCandidateRepository,
    build_verified_knowledge_fixture_envelope,
)


def test_explicit_synthetic_fixture_replay_loads_outside_repository(tmp_path) -> None:
    version = sample_version()
    envelope = build_verified_knowledge_fixture_envelope(
        fixture_id="fixture-001",
        fixture_records=({"candidate_version": version.model_dump(mode="json")},),
    )
    path = tmp_path / "fixture.json"
    path.write_text(json.dumps(envelope.model_dump(mode="json")), encoding="utf-8")
    repo = InMemoryVerifiedKnowledgeCandidateRepository().replay_fixture(path)
    assert repo.snapshot().candidate_count == 1


def test_relative_fixture_path_is_rejected() -> None:
    with pytest.raises(ValueError):
        InMemoryVerifiedKnowledgeCandidateRepository().replay_fixture("fixture.json")
