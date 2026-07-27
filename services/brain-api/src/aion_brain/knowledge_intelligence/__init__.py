"""Controlled Knowledge Intelligence research-acquisition package."""

from aion_brain.knowledge_intelligence.claim_graph import ControlledTemporalClaimEvidenceGraph
from aion_brain.knowledge_intelligence.domain_expert_mesh import ControlledDomainExpertMesh
from aion_brain.knowledge_intelligence.epistemic_assessment import (
    ControlledEpistemicAssessmentEngine,
)
from aion_brain.knowledge_intelligence.public_research_dns import (
    DisabledPublicResearchDnsBackend,
    InMemoryPublicResearchDnsBackend,
    SystemPublicResearchDnsBackend,
)
from aion_brain.knowledge_intelligence.public_research_http_transport import (
    DisabledPublicResearchConnectionBackend,
    InMemoryPinnedHttpsBackend,
    SystemPinnedHttpsBackend,
)
from aion_brain.knowledge_intelligence.public_research_pilot import (
    ControlledPublicResearchPilot,
)
from aion_brain.knowledge_intelligence.public_research_session import (
    PublicResearchPilotKillSwitch,
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
    "ControlledPublicResearchPilot",
    "ControlledEpistemicAssessmentEngine",
    "ControlledDomainExpertMesh",
    "ControlledResearchAcquisitionService",
    "ControlledSourceProvenanceRegistry",
    "ControlledToolVerificationFabric",
    "ControlledTemporalClaimEvidenceGraph",
    "DisabledPublicResearchConnectionBackend",
    "DisabledPublicResearchDnsBackend",
    "InMemoryPinnedHttpsBackend",
    "InMemoryPublicResearchDnsBackend",
    "InMemoryVerifiedKnowledgeCandidateRepository",
    "PublicResearchPilotKillSwitch",
    "SystemPinnedHttpsBackend",
    "SystemPublicResearchDnsBackend",
]
