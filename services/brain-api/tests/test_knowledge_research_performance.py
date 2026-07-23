from __future__ import annotations

from aion_brain.knowledge_intelligence.research_budget import (
    ResearchResourceBudget,
    ResearchResourceUsage,
    evaluate_research_budget,
)
from aion_brain.knowledge_intelligence.research_policy import (
    canonicalize_research_url,
    validate_public_destination_address,
)


def test_ci_safe_performance_smoke_for_hot_policy_paths():
    for index in range(250):
        canonicalize_research_url(f"https://research.example.invalid/source-{index}.txt")
        validate_public_destination_address("93.184.216.34")
        evaluate_research_budget(ResearchResourceUsage(query_count=1), ResearchResourceBudget())
