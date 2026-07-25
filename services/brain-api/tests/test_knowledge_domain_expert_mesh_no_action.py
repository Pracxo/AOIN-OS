from knowledge_domain_expert_mesh_test_helpers import run_sample_session


def test_mesh_authorizes_no_action():
    _, _, _, session = run_sample_session()
    assert session.automatic_action is False
    assert session.synthesis.automatic_action is False
    assert all(report.automatic_action is False for report in session.reports)
