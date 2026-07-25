from knowledge_domain_expert_mesh_test_helpers import run_sample_session


def test_required_assignments_use_distinct_independence_groups():
    _, _, _, session = run_sample_session()
    groups = [assignment.independence_group_id for assignment in session.panel_plan.assignments]
    assert len(groups) == len(set(groups))
