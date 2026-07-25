from knowledge_domain_expert_mesh_test_helpers import run_sample_session


def test_mesh_promotes_no_knowledge():
    _, _, _, session = run_sample_session()
    assert session.knowledge_promoted is False
    assert session.synthesis.knowledge_promoted is False
    assert all(report.knowledge_promoted is False for report in session.reports)
