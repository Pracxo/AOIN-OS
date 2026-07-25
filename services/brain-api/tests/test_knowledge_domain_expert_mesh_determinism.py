from knowledge_domain_expert_mesh_test_helpers import MESH_TEST_NOW, make_assessment, make_case

from aion_brain.knowledge_intelligence.domain_expert_mesh import ControlledDomainExpertMesh


def test_fixed_inputs_produce_identical_sessions():
    case = make_case()
    assessment = make_assessment()
    first = ControlledDomainExpertMesh(clock=lambda: MESH_TEST_NOW).run_session(
        case=case, assessments=(assessment,)
    )
    second = ControlledDomainExpertMesh(clock=lambda: MESH_TEST_NOW).run_session(
        case=case, assessments=(assessment,)
    )
    assert first.session_fingerprint == second.session_fingerprint
    assert first.panel_plan.panel_fingerprint == second.panel_plan.panel_fingerprint
