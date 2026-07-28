"""Knowledge identity derivation and conflict planning helpers."""

from aion_brain.contracts.governed_learning_memory import (
    ExistingKnowledgeVersionReference,
    KnowledgeConflictFinding,
    KnowledgeConflictKind,
    KnowledgeConflictReport,
    KnowledgeIdentityDisposition,
    KnowledgeIdentityPlan,
    derive_knowledge_identity_plan,
    detect_knowledge_duplicates_and_conflicts,
)

__all__ = [
    "ExistingKnowledgeVersionReference",
    "KnowledgeConflictFinding",
    "KnowledgeConflictKind",
    "KnowledgeConflictReport",
    "KnowledgeIdentityDisposition",
    "KnowledgeIdentityPlan",
    "derive_knowledge_identity_plan",
    "detect_knowledge_duplicates_and_conflicts",
]
