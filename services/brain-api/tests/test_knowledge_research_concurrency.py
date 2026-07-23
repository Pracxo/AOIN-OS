from __future__ import annotations

from aion_brain.knowledge_intelligence.research_budget import ResearchResourceBudget


def test_concurrency_is_bounded_to_four_workers():
    assert ResearchResourceBudget().maximum_concurrency == 4
