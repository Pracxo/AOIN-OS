from secure_runtime_aion232_test_helpers import report, scenario


def test_zero_external_and_production_effects_are_recorded() -> None:
    payload = report()
    for key in (
        "network_calls",
        "model_provider_calls",
        "connector_calls",
        "actual_tool_executions",
        "credentials_persisted",
        "tokens_persisted",
        "runtime_created_approvals",
        "production_writes",
        "production_memory_writes",
        "production_policy_mutations",
        "cognitive_memory_writes",
        "actual_belief_creations",
        "actual_belief_mutations",
        "source_mutations",
        "git_operations",
        "deployments",
        "model_weight_changes",
        "active_sessions_after_evaluation",
        "active_requests_after_evaluation",
    ):
        assert payload[key] == 0
    assert payload["repository_unchanged"] is True
    assert payload["temporary_evaluation_data_cleaned"] is True
    reqs = scenario("zero_external_and_production_effects")["requirements"]
    assert all(reqs.values())
