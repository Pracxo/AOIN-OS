"""Controlled Knowledge Intelligence research-acquisition package."""

from aion_brain.knowledge_intelligence.claim_graph import ControlledTemporalClaimEvidenceGraph
from aion_brain.knowledge_intelligence.domain_expert_mesh import ControlledDomainExpertMesh
from aion_brain.knowledge_intelligence.epistemic_assessment import (
    ControlledEpistemicAssessmentEngine,
)
from aion_brain.knowledge_intelligence.research import ControlledResearchAcquisitionService
from aion_brain.knowledge_intelligence.source_registry import ControlledSourceProvenanceRegistry
from aion_brain.knowledge_intelligence.tool_verification_fabric import (
    ControlledToolVerificationFabric,
)
from aion_brain.knowledge_intelligence.verified_knowledge_memory import (
    InMemoryVerifiedKnowledgeCandidateRepository,
)

__all__ = [
    "ControlledEpistemicAssessmentEngine",
    "ControlledDomainExpertMesh",
    "ControlledResearchAcquisitionService",
    "ControlledSourceProvenanceRegistry",
    "ControlledToolVerificationFabric",
    "ControlledTemporalClaimEvidenceGraph",
    "InMemoryVerifiedKnowledgeCandidateRepository",
]
