from knowledge_domain_expert_mesh_test_helpers import run_sample_session


def test_panel_policy_preserves_independence_and_abstention():
    _, _, _, session = run_sample_session()
    assert session.panel_plan.panel_size <= session.panel_plan.maximum_panel_size
    assert session.panel_plan.independence_group_count == session.panel_plan.panel_size
    assert session.panel_plan.panel_size_confidence_amplification_enabled is False
    assert session.panel_plan.majority_alignment_establishes_truth is False
    assert session.panel_plan.explicit_abstention_required is True
