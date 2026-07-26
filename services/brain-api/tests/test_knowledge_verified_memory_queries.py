from __future__ import annotations

from knowledge_verified_memory_test_helpers import sample_repository, sample_version

from aion_brain.contracts.knowledge_verified_memory import VerifiedKnowledgeCandidateQuery


def test_exact_query_uses_no_semantic_or_engagement_ranking() -> None:
    version = sample_version()
    repo = sample_repository()
    result = repo.query(VerifiedKnowledgeCandidateQuery(candidate_id=version.candidate_id))
    assert result.result_count == 1
    assert result.semantic_search_used is False
    assert result.engagement_ranking_used is False
    assert result.popularity_ranking_used is False
