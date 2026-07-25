from concurrent.futures import ThreadPoolExecutor

from knowledge_domain_expert_mesh_test_helpers import MESH_TEST_NOW, make_assessment, make_case

from aion_brain.knowledge_intelligence.domain_expert_mesh import ControlledDomainExpertMesh


def test_parallel_sessions_share_no_mutable_global_state():
    def run(index: int) -> str:
        case = make_case(case_id=f"case-{index:03d}")
        assessment = make_assessment()
        mesh = ControlledDomainExpertMesh(clock=lambda: MESH_TEST_NOW)
        return mesh.run_session(case=case, assessments=(assessment,)).session_fingerprint

    with ThreadPoolExecutor(max_workers=4) as pool:
        fingerprints = tuple(pool.map(run, range(1, 5)))
    assert len(set(fingerprints)) == 4
