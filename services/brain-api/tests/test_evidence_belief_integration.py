from __future__ import annotations

from types import SimpleNamespace

from aion_brain.beliefs.claim_extractor import ClaimExtractor
from aion_brain.contracts.beliefs import BeliefQuery
from tests.belief_helpers import belief_bundle
from tests.test_evidence_service import FakeEvidenceRepository, make_ingest_request, make_service


def test_evidence_ingest_extracts_claims_only_when_requested() -> None:
    belief = belief_bundle()
    repository = FakeEvidenceRepository()
    service = make_service(
        repository=repository,
        claim_extractor=ClaimExtractor(),
        belief_service=belief.service,
        settings=SimpleNamespace(belief_auto_extract_from_evidence=False),
    )

    service.ingest(make_ingest_request(content_text="The evidence layer stores text."))
    assert belief.query.query(BeliefQuery(scope=["workspace:main"])).claims == []

    service.ingest(
        make_ingest_request(
            content_text="The evidence layer extracts generic claims.",
            content_ref=None,
            source_type="text",
        ).model_copy(update={"evidence_id": "evidence-2", "metadata": {"extract_claims": True}})
    )
    claims = belief.query.query(BeliefQuery(scope=["workspace:main"])).claims
    assert len(claims) == 1


def test_evidence_ingest_extracts_supported_claim_with_evidence_ref() -> None:
    belief = belief_bundle()
    service = make_service(
        claim_extractor=ClaimExtractor(),
        belief_service=belief.service,
        settings=SimpleNamespace(belief_auto_extract_from_evidence=True),
    )

    service.ingest(make_ingest_request(content_text="The evidence layer can support claims."))

    claims = belief.query.query(BeliefQuery(scope=["workspace:main"])).claims
    assert len(claims) == 1
    assert claims[0].evidence_refs[0] == "evidence-1"
