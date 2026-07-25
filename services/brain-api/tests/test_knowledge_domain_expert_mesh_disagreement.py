from knowledge_domain_expert_mesh_test_helpers import run_sample_session

from aion_brain.contracts.knowledge_domain_expert_mesh import DisagreementType


def test_disagreement_matrix_is_bounded_and_preserves_reports():
    _, _, _, session = run_sample_session()
    assert session.disagreement_matrix.disagreement_count <= 100
    assert set(session.disagreement_matrix.preserved_report_ids) == {
        report.report_id for report in session.reports
    }
    assert all(
        item.disagreement_type in set(DisagreementType)
        for item in session.disagreement_matrix.disagreements
    )
