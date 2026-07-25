from knowledge_domain_expert_mesh_test_helpers import run_sample_session

from aion_brain.contracts.knowledge_domain_expert_mesh import MeshSessionOutcome


def test_mesh_rejects_persistent_write():
    mesh, _, _, session = run_sample_session()
    assert session.persistent_write_applied is False
    assert (
        mesh.reject_persistent_write({"session_id": session.session_id})
        == MeshSessionOutcome.PERSISTENT_WRITE_DISABLED
    )
