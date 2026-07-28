from __future__ import annotations

from test_governed_learning_memory_program_authorization import load_json


def test_resource_budgets_include_positive_planning_limits_and_zero_effect_limits() -> None:
    limits = load_json("docs/governed-learning-memory/authorization-ledger.json")[
        "resource_limits"
    ]

    assert limits["maximum_promotion_requests_per_batch"] == 100
    assert limits["maximum_candidates_per_request"] == 100
    assert limits["maximum_lineage_references_per_candidate"] == 500
    assert limits["maximum_source_references_per_candidate"] == 100
    assert limits["maximum_fixture_bytes"] == 4194304
    assert limits["maximum_concurrency"] == 4

    zero_limits = [
        "maximum_persistent_knowledge_writes",
        "maximum_persistent_verified_knowledge_writes",
        "maximum_cognitive_memory_writes",
        "maximum_semantic_memory_writes",
        "maximum_episodic_memory_writes",
        "maximum_procedural_memory_writes",
        "maximum_belief_creations",
        "maximum_belief_mutations",
        "maximum_automatic_knowledge_promotions",
        "maximum_automatic_candidate_approvals",
        "maximum_engagement_fact_promotions",
        "maximum_engagement_confidence_effects",
        "maximum_network_calls",
        "maximum_connector_calls",
        "maximum_model_provider_calls",
        "maximum_actual_tool_executions",
        "maximum_shell_commands",
        "maximum_subprocess_executions",
        "maximum_browser_actions",
        "maximum_source_mutations",
        "maximum_git_operations",
        "maximum_runtime_created_pull_requests",
        "maximum_runtime_created_approvals",
        "maximum_deployments",
        "maximum_model_weight_changes",
    ]
    for key in zero_limits:
        assert limits[key] == 0, key
