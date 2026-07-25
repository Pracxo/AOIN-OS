from knowledge_domain_expert_mesh_test_helpers import run_sample_session


def test_mesh_makes_no_human_identity_claims():
    _, _, _, session = run_sample_session()
    assert all(report.human_identity_claimed is False for report in session.reports)
    assert all(report.computational_profile is True for report in session.reports)
