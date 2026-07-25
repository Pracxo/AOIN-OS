from decimal import Decimal

from knowledge_domain_expert_mesh_test_helpers import run_sample_session


def test_confidence_caps_are_propagated_without_amplification():
    _, _, assessment, session = run_sample_session()
    assert all(report.report_confidence_cap <= assessment.confidence for report in session.reports)
    assert session.synthesis.synthesis_confidence_cap <= assessment.confidence
    assert session.synthesis.synthesis_confidence_cap <= Decimal("0.650000")
