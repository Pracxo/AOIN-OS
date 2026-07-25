from knowledge_domain_expert_mesh_test_helpers import make_case

from aion_brain.contracts.knowledge_domain_expert_mesh import ExpertPerspectiveRole
from aion_brain.knowledge_intelligence.domain_expert_routing import select_expert_panel


def test_routing_selects_required_exact_matches():
    panel = select_expert_panel(make_case())
    roles = {assignment.perspective_role for assignment in panel.assignments}
    assert ExpertPerspectiveRole.DOMAIN_ANALYST in roles
    assert ExpertPerspectiveRole.EVIDENCE_AUDITOR in roles
    assert ExpertPerspectiveRole.METHODOLOGICAL_SKEPTIC in roles
    assert ExpertPerspectiveRole.RISK_REVIEWER in roles
    assert panel.panel_size == panel.independence_group_count
