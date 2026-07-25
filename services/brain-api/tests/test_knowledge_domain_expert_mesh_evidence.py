from knowledge_domain_expert_mesh_test_helpers import run_sample_session


def test_evidence_bundle_is_redacted_and_operator_safe():
    _, _, _, session = run_sample_session()
    bundle = session.evidence_bundle
    assert bundle.authorization_transaction_id == "AION-212-KI-0005"
    assert bundle.domain_expert_mesh_runtime_enabled is False
    assert bundle.persistent_expert_mesh_write_enabled is False
    assert bundle.runtime_effect is False
