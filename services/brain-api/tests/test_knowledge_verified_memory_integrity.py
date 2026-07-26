from __future__ import annotations

from knowledge_verified_memory_test_helpers import (
    sample_candidate,
    sample_repository,
    sample_version,
)

from aion_brain.contracts.knowledge_verified_memory import VerifiedKnowledgeIntegrityStatus
from aion_brain.knowledge_intelligence.verified_knowledge_integrity import (
    audit_verified_knowledge_candidate,
    audit_verified_knowledge_candidate_history,
    audit_verified_knowledge_candidate_version,
    audit_verified_knowledge_repository,
)
from aion_brain.knowledge_intelligence.verified_knowledge_versioning import (
    build_candidate_history,
)


def test_integrity_audits_pass_for_candidate_version_history_and_repository() -> None:
    candidate = sample_candidate()
    version = sample_version()
    history = build_candidate_history((version,))
    repo = sample_repository()
    assert audit_verified_knowledge_candidate(candidate).status is (
        VerifiedKnowledgeIntegrityStatus.PASSED
    )
    assert audit_verified_knowledge_candidate_version(version).status is (
        VerifiedKnowledgeIntegrityStatus.PASSED
    )
    assert audit_verified_knowledge_candidate_history(history).status is (
        VerifiedKnowledgeIntegrityStatus.PASSED
    )
    assert audit_verified_knowledge_repository(repo).status is (
        VerifiedKnowledgeIntegrityStatus.PASSED
    )
