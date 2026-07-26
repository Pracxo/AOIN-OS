from __future__ import annotations

from knowledge_verified_memory_test_helpers import sample_repository

from aion_brain.contracts.knowledge_verified_memory import (
    VerifiedKnowledgePersistentWriteOutcome,
)


def test_zero_record_persistent_write_request_is_rejected() -> None:
    assert sample_repository().reject_persistent_write(None) is (
        VerifiedKnowledgePersistentWriteOutcome.PERSISTENT_WRITE_DISABLED
    )
