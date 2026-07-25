from knowledge_domain_expert_mesh_test_helpers import run_sample_session


def test_critique_responses_preserve_critiques():
    _, _, _, session = run_sample_session()
    critique_ids = {critique.critique_id for critique in session.critiques}
    assert {response.critique_id for response in session.critique_responses} == critique_ids
    assert all(response.critique_preserved for response in session.critique_responses)
    assert all(response.report_rewritten is False for response in session.critique_responses)
