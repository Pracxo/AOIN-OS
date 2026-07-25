"""AION-211 assessment request tests."""

import pytest

from aion_brain.contracts.knowledge_epistemic_assessment import EpistemicAssessmentRequest
from tests.test_knowledge_epistemic_assessment_helpers import assessment_request


def test_request_sorts_claim_ids_deterministically() -> None:
    request = assessment_request(claim_ids=("claim-0002", "claim-0001"))
    assert request.claim_ids == ("claim-0001", "claim-0002")
    assert request.read_only is True
    assert request.runtime_effect is False


def test_request_rejects_duplicate_claim_ids() -> None:
    payload = assessment_request(claim_ids=("claim-0001",)).model_dump()
    payload["claim_ids"] = ("claim-0001", "claim-0001")
    with pytest.raises(ValueError, match="duplicate claim IDs"):
        EpistemicAssessmentRequest(**payload)
