from knowledge_domain_expert_mesh_test_helpers import run_sample_session


def test_dissent_and_minority_reports_are_not_deleted():
    _, _, _, session = run_sample_session()
    assert session.disagreement_matrix.dissent_preserved is True
    assert set(session.synthesis.report_ids) == {report.report_id for report in session.reports}
    assert session.synthesis.knowledge_promoted is False
