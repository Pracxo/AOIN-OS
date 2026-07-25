from knowledge_domain_expert_mesh_test_helpers import run_sample_session


def test_reports_bind_existing_evidence_references_without_new_evidence():
    _, _, _, session = run_sample_session()
    assert all("conflict-001" in report.evidence_reference_ids for report in session.reports)
    assert all(
        "domain_mesh_evidence_reference_resolved" in report.finding_codes
        for report in session.reports
        if report.perspective_role.value == "evidence_auditor"
    )
