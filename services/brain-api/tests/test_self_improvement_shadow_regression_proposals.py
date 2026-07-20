"""AION-178 shadow regression-proposal tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from test_self_improvement_shadow_contracts import NOW, make_observation, safe_fingerprint

from aion_brain.self_improvement.shadow_pipeline import (
    ShadowRegressionTestProposal,
    generate_shadow_hypotheses,
    generate_shadow_regression_proposals,
    mine_shadow_failure_patterns,
)


def _hypothesis():
    pattern = mine_shadow_failure_patterns(
        (make_observation(repeated_count=2),),
        maximum_patterns=100,
        created_at=NOW,
    )[0]
    return generate_shadow_hypotheses((pattern,), maximum_hypotheses=50, created_at=NOW)[0]


def test_regression_proposal_is_specification_only() -> None:
    proposal = generate_shadow_regression_proposals(
        (_hypothesis(),),
        maximum_proposals=25,
        created_at=NOW,
    )[0]

    assert proposal.review_state == "shadow_regression_proposed"
    assert proposal.suggested_test_area == "brain_api_retrieval_tests"
    assert "skip" not in " ".join(proposal.proposed_assertion_summaries).lower()


def test_regression_proposal_rejects_unknown_area_and_test_weakening() -> None:
    hypothesis = _hypothesis()
    base = generate_shadow_regression_proposals(
        (hypothesis,),
        maximum_proposals=25,
        created_at=NOW,
    )[0].model_dump(mode="python")

    with pytest.raises(ValidationError):
        ShadowRegressionTestProposal(**{**base, "suggested_test_area": "unknown"})
    with pytest.raises(ValidationError):
        ShadowRegressionTestProposal(
            **{
                **base,
                "proposed_assertion_summaries": ("Skip guarding assertion.",),
                "source_reference_fingerprints": (safe_fingerprint("source"),),
            }
        )


def test_regression_proposal_maximum_count_is_enforced() -> None:
    hypothesis = _hypothesis()

    assert (
        generate_shadow_regression_proposals((hypothesis,), maximum_proposals=0, created_at=NOW)
        == ()
    )
