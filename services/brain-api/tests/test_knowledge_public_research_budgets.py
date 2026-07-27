from __future__ import annotations

from aion_brain.contracts.knowledge_public_research_pilot import (
    PublicResearchPilotResourceUsage,
    budget_decision_for_usage,
)


def test_budget_overage_fails_closed() -> None:
    usage = PublicResearchPilotResourceUsage(public_https_requests=51)
    decision = budget_decision_for_usage(usage)
    assert decision.within_budget is False
