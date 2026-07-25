from knowledge_domain_expert_mesh_test_helpers import run_sample_session


def test_explicit_abstention_is_required_for_high_stakes_case():
    _, _, _, session = run_sample_session()
    assert session.synthesis.explicit_abstention is True
    assert session.outcome.value == "completed_with_abstention"
