from __future__ import annotations

from knowledge_verified_memory_test_helpers import sample_version

from aion_brain.knowledge_intelligence.verified_knowledge_versioning import (
    build_candidate_history,
    supersede_candidate_version,
)


def test_candidate_history_preserves_prior_versions_contiguously() -> None:
    first = sample_version()
    second = supersede_candidate_version(first)
    history = build_candidate_history((second, first))
    assert history.version_count == 2
    assert tuple(version.version_number for version in history.versions) == (1, 2)
    assert history.latest_candidate_version_id == second.candidate_version_id
