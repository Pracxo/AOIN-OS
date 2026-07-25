from knowledge_domain_expert_mesh_test_helpers import run_sample_session

from aion_brain.contracts.knowledge_domain_expert_mesh import (
    DomainExpertMeshQuery,
    ExpertPerspectiveRole,
)


def test_queries_are_exact_and_bounded():
    mesh, _, _, session = run_sample_session()
    by_case = mesh.query(DomainExpertMeshQuery(case_id=session.case.case_id))
    by_role = mesh.query(
        DomainExpertMeshQuery(perspective_role=ExpertPerspectiveRole.DOMAIN_ANALYST)
    )
    assert by_case.session_ids == (session.session_id,)
    assert by_role.result_count == 1
    assert by_case.query.semantic_search_enabled is False
