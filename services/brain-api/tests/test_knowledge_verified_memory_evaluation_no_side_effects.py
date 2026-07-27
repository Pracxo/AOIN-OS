from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def load_json(relative: str) -> dict[str, object]:
    return json.loads((REPO_ROOT / relative).read_text(encoding="utf-8"))


def report() -> dict[str, object]:
    return load_json(
        "examples/knowledge-intelligence/verified-memory-operator-evaluation-report.json"
    )


def test_evaluation_zero_side_effect_fields() -> None:
    data = report()
    for key in (
        "public_network_requests",
        "dns_resolutions",
        "search_provider_calls",
        "connector_calls",
        "model_provider_calls",
        "actual_tool_executions",
        "shell_executions",
        "subprocess_executions",
        "browser_actions",
        "filesystem_mutations",
        "source_mutations",
        "git_operations",
        "runtime_pull_requests",
        "runtime_approvals",
        "deployments",
        "model_weight_changes",
        "persistent_verified_knowledge_writes",
        "automatic_knowledge_promotions",
        "cognitive_memory_writes",
        "belief_mutations",
        "engagement_fact_promotions",
        "engagement_confidence_effects",
    ):
        assert data[key] == 0, key
    assert data["repository_unchanged"] is True
    assert data["temporary_evaluation_data_cleaned"] is True
