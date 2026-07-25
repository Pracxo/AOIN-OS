from knowledge_domain_expert_mesh_test_helpers import run_sample_session


def test_reports_bind_existing_epistemic_assessments():
    _, _, assessment, session = run_sample_session()
    assert all(report.assessment_ids == (assessment.assessment_id,) for report in session.reports)
    assert all(
        "domain_mesh_assessment_reference_resolved" in report.finding_codes
        for report in session.reports
    )
