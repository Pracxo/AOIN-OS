from knowledge_domain_expert_mesh_test_helpers import run_sample_session


def test_mesh_does_not_override_truth_or_claim_state():
    _, _, _, session = run_sample_session()
    assert session.synthesis.truth_decision is False
    assert session.synthesis.claim_accepted is False
    assert session.synthesis.claim_rejected is False
    assert all(report.truth_decision is False for report in session.reports)
