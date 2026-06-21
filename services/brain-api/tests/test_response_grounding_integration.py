from __future__ import annotations

from aion_brain.contracts.grounding import GroundingVerificationRun
from aion_brain.contracts.responses import ResponseComposeRequest
from tests.dialogue_helpers import service_bundle


class FakeCitationMap:
    citation_map_id = "citation-map-1"
    coverage_score = 1.0


class FakeCitationMapper:
    def __init__(self) -> None:
        self.calls = 0

    def map_response(
        self,
        response_id: str,
        owner_scope: list[str],
        required_source_types: list[str],
    ) -> FakeCitationMap:
        self.calls += 1
        return FakeCitationMap()


class FakeGroundingVerifier:
    def __init__(self) -> None:
        self.calls = 0

    def verify(self, request: object) -> GroundingVerificationRun:
        self.calls += 1
        return GroundingVerificationRun(
            grounding_verification_id="grounding-verification-1",
            trace_id=None,
            response_id="response-1",
            explanation_id=None,
            target_type="response",
            target_id="response-1",
            status="passed",
            owner_scope=["workspace:main"],
            grounded=True,
            checked_statement_count=1,
            supported_statement_count=1,
            unsupported_statement_count=0,
            citation_count=1,
            coverage_score=1.0,
            issues=[],
            result={},
            created_by=None,
        )


def test_response_composer_attaches_grounding_metadata_when_required() -> None:
    bundle = service_bundle()
    mapper = FakeCitationMapper()
    verifier = FakeGroundingVerifier()
    bundle.response_composer.set_grounding_services(mapper, verifier)

    response = bundle.response_composer.compose(
        ResponseComposeRequest(
            response_id="response-1",
            require_grounding=True,
            context={"evidence_refs": ["evidence-1"]},
            reasoning_result={"summary": "AION records deterministic support."},
            metadata={"owner_scope": ["workspace:main"]},
        )
    )

    assert response.metadata["citation_map_id"] == "citation-map-1"
    assert response.metadata["grounding_verification_id"] == "grounding-verification-1"
    assert mapper.calls == 1
    assert verifier.calls == 1
