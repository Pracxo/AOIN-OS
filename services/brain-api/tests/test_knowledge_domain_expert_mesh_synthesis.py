from knowledge_domain_expert_mesh_test_helpers import run_sample_session


def test_synthesis_is_bounded_advisory_and_non_truthful():
    _, _, _, session = run_sample_session()
    synthesis = session.synthesis
    assert synthesis.explicit_abstention is True
    assert synthesis.operator_review_required is True
    assert synthesis.truth_decision is False
    assert synthesis.claim_accepted is False
    assert synthesis.claim_rejected is False
