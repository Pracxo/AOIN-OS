"""AION-178 shadow improvement-proposal tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from test_self_improvement_shadow_contracts import NOW, make_observation

from aion_brain.self_improvement.shadow_pipeline import (
    ShadowImprovementProposalCandidate,
    generate_shadow_hypotheses,
    generate_shadow_improvement_proposals,
    generate_shadow_regression_proposals,
    mine_shadow_failure_patterns,
)


def _proposal_payloads():
    pattern = mine_shadow_failure_patterns(
        (make_observation(repeated_count=2),),
        maximum_patterns=100,
        created_at=NOW,
    )[0]
    hypothesis = generate_shadow_hypotheses((pattern,), maximum_hypotheses=50, created_at=NOW)[0]
    regression = generate_shadow_regression_proposals(
        (hypothesis,),
        maximum_proposals=25,
        created_at=NOW,
    )[0]
    return pattern, hypothesis, regression


def test_shadow_proposal_remains_review_only_and_inert() -> None:
    pattern, hypothesis, regression = _proposal_payloads()
    proposal = generate_shadow_improvement_proposals(
        (hypothesis,),
        (regression,),
        (pattern,),
        maximum_proposals=10,
        created_at=NOW,
    )[0]

    assert proposal.review_state == "shadow_proposal_generated"
    assert proposal.operator_review_required is True
    assert proposal.implementation_authorization_created is False
    assert proposal.approval_created is False
    assert proposal.source_modified is False
    assert proposal.git_mutated is False
    assert proposal.pull_request_created is False
    assert proposal.merged is False
    assert proposal.runtime_effect is False
    assert proposal.active_learning_promoted is False


def test_shadow_proposal_rejects_side_effect_and_invalid_review_state() -> None:
    pattern, hypothesis, regression = _proposal_payloads()
    proposal = generate_shadow_improvement_proposals(
        (hypothesis,),
        (regression,),
        (pattern,),
        maximum_proposals=10,
        created_at=NOW,
    )[0]
    payload = proposal.model_dump(mode="python")

    with pytest.raises(ValidationError):
        ShadowImprovementProposalCandidate(**{**payload, "review_state": "approved"})
    with pytest.raises(ValidationError):
        ShadowImprovementProposalCandidate(**{**payload, "source_modified": True})


def test_shadow_proposal_maximum_count_is_enforced() -> None:
    pattern, hypothesis, regression = _proposal_payloads()

    assert (
        generate_shadow_improvement_proposals(
            (hypothesis,),
            (regression,),
            (pattern,),
            maximum_proposals=0,
            created_at=NOW,
        )
        == ()
    )
