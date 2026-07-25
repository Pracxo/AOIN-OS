from knowledge_domain_expert_mesh_test_helpers import run_sample_session


def test_mesh_mutates_no_beliefs():
    _, _, _, session = run_sample_session()
    assert session.belief_mutated is False
    assert session.synthesis.belief_mutated is False
    assert all(report.belief_mutated is False for report in session.reports)
