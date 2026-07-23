from __future__ import annotations

from knowledge_research_test_helpers import NOW, valid_plan, valid_response

from aion_brain.knowledge_intelligence.research import ControlledResearchAcquisitionService
from aion_brain.knowledge_intelligence.research_adapters import InMemoryResearchFetchAdapter
from aion_brain.knowledge_intelligence.research_policy import InMemoryResearchDestinationResolver


def test_controlled_research_service_returns_redacted_operator_review_evidence():
    plan = valid_plan()
    response = valid_response(request_id="research-fetch-request-0001")
    service = ControlledResearchAcquisitionService(
        fetch_adapter=InMemoryResearchFetchAdapter({("GET", response.response_url): response}),
        destination_resolver=InMemoryResearchDestinationResolver(
            {"research.example.invalid": ("93.184.216.34",)},
            NOW,
        ),
        clock=lambda: NOW,
    )
    result = service.run(plan)
    assert result.outcome == "completed"
    assert result.evidence_bundle is not None
    assert result.evidence_bundle.snapshots[0].verified_fact is False
    assert result.evidence_bundle.operator_review_items[0].claim_verification_required is True
    assert result.knowledge_candidate_created is False
