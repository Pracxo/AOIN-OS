from __future__ import annotations

from knowledge_research_test_helpers import NOW, valid_plan, valid_response

from aion_brain.knowledge_intelligence.research import ControlledResearchAcquisitionService
from aion_brain.knowledge_intelligence.research_adapters import InMemoryResearchFetchAdapter
from aion_brain.knowledge_intelligence.research_policy import InMemoryResearchDestinationResolver


def test_fixed_inputs_produce_deterministic_result_fingerprint():
    plan = valid_plan()
    response = valid_response(request_id="research-fetch-request-0001")
    kwargs = {
        "fetch_adapter": InMemoryResearchFetchAdapter({("GET", response.response_url): response}),
        "destination_resolver": InMemoryResearchDestinationResolver(
            {"research.example.invalid": ("93.184.216.34",)},
            NOW,
        ),
        "clock": lambda: NOW,
    }
    assert ControlledResearchAcquisitionService(**kwargs).run(plan).fingerprint == (
        ControlledResearchAcquisitionService(**kwargs).run(plan).fingerprint
    )
