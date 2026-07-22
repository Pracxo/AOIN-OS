"""Pure continual-learning services for AION cognitive architecture."""

from aion_brain.continual_learning.core import (
    LEARNING_LEVELS,
    REQUIRED_PIPELINE,
    CandidateLearningService,
    CandidatePromotionPolicy,
    CatastrophicForgettingEvaluator,
    ExperienceReplayService,
    LearningBenchmarkEvaluator,
    LearningRollbackService,
)

__all__ = [
    "LEARNING_LEVELS",
    "REQUIRED_PIPELINE",
    "CandidateLearningService",
    "CandidatePromotionPolicy",
    "CatastrophicForgettingEvaluator",
    "ExperienceReplayService",
    "LearningBenchmarkEvaluator",
    "LearningRollbackService",
]
