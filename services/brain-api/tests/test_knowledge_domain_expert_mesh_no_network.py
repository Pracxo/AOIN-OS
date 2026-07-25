from knowledge_domain_expert_mesh_test_helpers import run_sample_session


def test_mesh_accesses_no_network():
    _, _, _, session = run_sample_session()
    assert session.network_accessed is False
    assert session.diagnostics.runtime_effect is False
