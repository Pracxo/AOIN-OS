from knowledge_domain_expert_mesh_test_helpers import run_sample_session


def test_mesh_never_calls_model_provider():
    _, _, _, session = run_sample_session()
    assert session.model_provider_called is False
    assert all(report.runtime_effect is False for report in session.reports)
