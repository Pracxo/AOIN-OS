from __future__ import annotations

from scripts.lib.governed_learning_memory_local_persistence_authorization import (
    AION224_RESOURCE_LIMITS,
)
from test_governed_learning_memory_program_authorization import load_json


def test_resource_budgets_include_positive_planning_limits_and_zero_effect_limits() -> None:
    limits = load_json("docs/governed-learning-memory/authorization-ledger.json")["resource_limits"]

    assert limits == AION224_RESOURCE_LIMITS
    assert limits["maximum_persistence_sessions"] == 10
    assert limits["maximum_transactions_per_session"] == 100
    assert limits["maximum_knowledge_versions_per_transaction"] == 100
    assert limits["maximum_projection_records_per_transaction"] == 100
    assert limits["minimum_independent_approvers_per_transaction"] == 2
    assert limits["maximum_total_transaction_bytes"] == 4194304
    assert limits["maximum_database_bytes"] == 1073741824
    assert limits["maximum_concurrent_readers"] == 4
    assert limits["maximum_concurrent_writers"] == 1

    zero_limits = [
        "maximum_persistent_source_body_writes",
        "maximum_persistent_source_preview_writes",
        "maximum_persistent_raw_approval_payload_writes",
        "maximum_confidential_content_writes",
        "maximum_restricted_content_writes",
        "maximum_actual_belief_creations",
        "maximum_actual_belief_mutations",
        "maximum_automatic_knowledge_promotions",
        "maximum_automatic_candidate_approvals",
        "maximum_automatic_memory_ingestions",
        "maximum_engagement_learning_applications",
        "maximum_network_calls",
        "maximum_search_provider_calls",
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
