from knowledge_domain_expert_mesh_test_helpers import run_sample_session

from aion_brain.contracts.knowledge_domain_expert_mesh import ExpertPerspectiveRole


def test_high_stakes_policy_requires_risk_reviewer_and_operator_review():
    _, _, _, session = run_sample_session()
    roles = {assignment.perspective_role for assignment in session.panel_plan.assignments}
    assert ExpertPerspectiveRole.RISK_REVIEWER in roles
    assert session.synthesis.operator_escalation_recommended is True
    assert session.operator_review_items
