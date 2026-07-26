from __future__ import annotations

from knowledge_verified_memory_test_helpers import sample_version

from aion_brain.contracts.knowledge_verified_memory import (
    VerifiedKnowledgeCandidateQuery,
    VerifiedKnowledgeLifecycleStatus,
)
from aion_brain.knowledge_intelligence.verified_knowledge_memory import (
    InMemoryVerifiedKnowledgeCandidateRepository,
)
from aion_brain.knowledge_intelligence.verified_knowledge_versioning import (
    expire_candidate_version,
)


def test_expiry_records_new_version_and_is_queryable() -> None:
    first = sample_version()
    expired = expire_candidate_version(first)
    repo = (
        InMemoryVerifiedKnowledgeCandidateRepository()
        .with_candidate_version(first)
        .with_candidate_version(expired)
    )
    result = repo.query(VerifiedKnowledgeCandidateQuery(expired=True))
    assert expired.candidate.lifecycle_status is VerifiedKnowledgeLifecycleStatus.EXPIRED
    assert result.result_count == 1
