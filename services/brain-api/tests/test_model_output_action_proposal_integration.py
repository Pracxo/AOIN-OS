"""Model output governance to action proposal integration tests."""

from __future__ import annotations

from aion_brain.contracts.model_outputs import ModelOutputCreateRequest
from aion_brain.contracts.output_governance import OutputGovernanceRequest
from tests.model_outputs_fakes import governance_service


class ReviewSpy:
    """Collect review requests when auto proposal creation is enabled."""

    def __init__(self) -> None:
        self.requests: list[object] = []

    def review(self, request: object) -> None:
        self.requests.append(request)


def test_model_output_governance_does_not_auto_create_proposal_by_default() -> None:
    service, _, _, _ = governance_service()
    review_spy = ReviewSpy()
    service.set_tool_intent_review_service(review_spy)
    output = service.receive_output(
        ModelOutputCreateRequest(
            trace_id="trace-1",
            raw_output='Answer safely.\ncommand: noop {"value":"ok"}',
            output_type="mixed",
            owner_scope=["workspace:main"],
        )
    )

    run = service.govern(
        OutputGovernanceRequest(
            trace_id="trace-1",
            model_output_id=output.model_output_id,
            owner_scope=["workspace:main"],
            metadata={"review_tool_intents": True},
        )
    )

    assert run.tool_intents
    assert run.tool_intents[0].status == "blocked"
    assert review_spy.requests == []
