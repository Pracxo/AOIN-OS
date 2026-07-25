from knowledge_domain_expert_mesh_test_helpers import make_case

from aion_brain.knowledge_intelligence.domain_expert_mesh import decompose_domain_expert_case


def test_decomposition_is_bounded_and_deterministic():
    case = make_case()
    first = decompose_domain_expert_case(case)
    second = decompose_domain_expert_case(case)
    assert first.plan_fingerprint == second.plan_fingerprint
    assert first.subquestion_count <= 50
    assert first.model_inference_used is False
    assert first.external_research_requested is False
