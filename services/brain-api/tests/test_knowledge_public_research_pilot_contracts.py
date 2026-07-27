from __future__ import annotations

from aion_brain.contracts.knowledge_public_research_pilot import (
    AUTHORIZATION_TRANSACTION_ID,
    PUBLIC_RESEARCH_PILOT_CONTRACT_SCHEMA_VERSION,
    PublicResearchPilotResourceBudget,
)


def test_contract_constants_and_exact_budget() -> None:
    budget = PublicResearchPilotResourceBudget()
    assert AUTHORIZATION_TRANSACTION_ID == "AION-218-KI-0008"
    assert PUBLIC_RESEARCH_PILOT_CONTRACT_SCHEMA_VERSION == "aion-public-research-pilot/v1"
    assert budget.maximum_public_https_requests_per_plan == 50
    assert budget.maximum_persistent_verified_knowledge_writes == 0
