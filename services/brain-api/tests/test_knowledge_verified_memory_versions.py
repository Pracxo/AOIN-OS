from __future__ import annotations

from knowledge_verified_memory_test_helpers import sample_version

from aion_brain.contracts.knowledge_verified_memory import VerifiedKnowledgeVersionReason


def test_initial_candidate_version_is_immutable_and_not_persistent() -> None:
    version = sample_version()
    assert version.version_number == 1
    assert version.version_reason is VerifiedKnowledgeVersionReason.INITIAL
    assert version.previous_candidate_version_id is None
    assert version.persistent_write_applied is False
