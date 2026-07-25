from knowledge_domain_expert_mesh_test_helpers import run_sample_session


def test_ci_safe_performance_smoke_executes_complete_pipeline():
    _, _, _, session = run_sample_session()
    assert session.subquestion_plan.subquestion_count > 0
    assert session.panel_plan.panel_size > 0
    assert len(session.reports) == session.panel_plan.panel_size
    assert len(session.critique_responses) == len(session.critiques)
    assert session.integrity_report.finding_count == 0
