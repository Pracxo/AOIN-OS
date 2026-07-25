from knowledge_domain_expert_mesh_test_helpers import run_sample_session


def test_mesh_executes_no_tools():
    _, _, _, session = run_sample_session()
    assert session.tool_executed is False
    assert session.evidence_bundle.runtime_effect is False
