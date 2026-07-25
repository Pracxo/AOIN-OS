from knowledge_domain_expert_mesh_test_helpers import run_sample_session


def test_critiques_reject_self_review_and_preserve_targets():
    _, _, _, session = run_sample_session()
    assert session.critiques
    for critique in session.critiques:
        assert critique.critic_profile_id != critique.target_profile_id
        assert critique.target_report_preserved is True
        assert critique.confidence_increased is False
