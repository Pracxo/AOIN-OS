from knowledge_domain_expert_mesh_test_helpers import run_sample_session


def test_reports_are_computational_and_advisory_only():
    _, _, assessment, session = run_sample_session()
    assert session.reports
    for report in session.reports:
        assert report.assessment_ids == (assessment.assessment_id,)
        assert report.computational_profile is True
        assert report.human_authored is False
        assert report.truth_decision is False
        assert report.report_confidence_cap <= report.underlying_assessment_confidence_cap
