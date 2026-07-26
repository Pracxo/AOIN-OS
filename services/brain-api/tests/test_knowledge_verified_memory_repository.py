from __future__ import annotations

from knowledge_verified_memory_test_helpers import sample_version

from aion_brain.contracts.knowledge_verified_memory import (
    VerifiedKnowledgePersistentWriteOutcome,
)
from aion_brain.knowledge_intelligence.verified_knowledge_memory import (
    InMemoryVerifiedKnowledgeCandidateRepository,
)


def test_repository_is_copy_on_write_and_rejects_persistent_writes() -> None:
    empty = InMemoryVerifiedKnowledgeCandidateRepository()
    version = sample_version()
    updated = empty.with_candidate_version(version)
    assert empty.snapshot().candidate_count == 0
    assert updated.snapshot().candidate_count == 1
    assert updated.reject_persistent_write({}) is (
        VerifiedKnowledgePersistentWriteOutcome.PERSISTENT_WRITE_DISABLED
    )
