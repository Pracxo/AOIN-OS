"""Pure memory-consolidation services for AION cognitive architecture."""

from aion_brain.memory_consolidation.core import (
    REQUIRED_PIPELINE,
    ConsolidationService,
    ContradictionResolver,
    EpisodicReplayPlanner,
    ForgettingPolicyEvaluator,
    MemoryCompactor,
    ProceduralCandidateSynthesizer,
    ReplaySelector,
    SemanticConsolidator,
)

__all__ = [
    "REQUIRED_PIPELINE",
    "ConsolidationService",
    "ContradictionResolver",
    "EpisodicReplayPlanner",
    "ForgettingPolicyEvaluator",
    "MemoryCompactor",
    "ProceduralCandidateSynthesizer",
    "ReplaySelector",
    "SemanticConsolidator",
]
