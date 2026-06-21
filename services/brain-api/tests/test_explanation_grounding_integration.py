from __future__ import annotations

from types import SimpleNamespace

from aion_brain.contracts.explanations import ExplanationRequest
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.explanations.builder import ExplanationBuilder
from aion_brain.explanations.repository import ExplanationRepository


class AllowPolicy:
    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        return PolicyDecision(
            decision_id=f"decision-{request.request_id}",
            trace_id=request.trace_id or "",
            allow=True,
            approval_required=False,
            reason="allowed",
            constraints=[],
            audit_level="standard",
        )


class FakeCitationMapper:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def map_text(self, **kwargs: object) -> object:
        self.calls.append(kwargs)
        return SimpleNamespace(citation_map_id="citation-map-1")


class FakeGroundingVerifier:
    def __init__(self) -> None:
        self.calls: list[object] = []

    def verify(self, request: object) -> object:
        self.calls.append(request)
        return SimpleNamespace(
            grounding_verification_id="grounding-verification-1",
            status="passed",
        )


def test_explanation_builder_uses_grounding_services_when_evidence_requested() -> None:
    citation_mapper = FakeCitationMapper()
    grounding_verifier = FakeGroundingVerifier()
    builder = ExplanationBuilder(
        ExplanationRepository(),
        AllowPolicy(),
        citation_mapper=citation_mapper,
        grounding_verifier=grounding_verifier,
    )

    explanation = builder.explain(
        ExplanationRequest(
            trace_id="trace-1",
            explanation_type="generic",
            target_type="trace",
            target_id="trace-1",
            owner_scope=["workspace:main"],
            require_grounding=True,
        )
    )

    assert citation_mapper.calls
    assert grounding_verifier.calls
    assert explanation.metadata["citation_map_id"] == "citation-map-1"
    assert explanation.metadata["grounding_verification_id"] == "grounding-verification-1"
