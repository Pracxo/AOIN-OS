from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
REPORT = (
    REPO_ROOT
    / "examples/knowledge-intelligence/epistemic-assessment-operator-evaluation-report.json"
)


def test_operator_evaluation_records_zero_runtime_side_effects():
    payload = json.loads(REPORT.read_text())
    integrity = payload["repository_integrity"]
    zero_keys = (
        "source_body_bytes",
        "persistent_writes",
        "absolute_truth_decisions",
        "claim_true_assignments",
        "claim_false_assignments",
        "automatic_acceptances",
        "automatic_rejections",
        "contradiction_resolutions",
        "knowledge_promotions",
        "belief_creations",
        "belief_mutations",
        "network_calls",
        "model_provider_calls",
        "connector_calls",
        "tool_executions",
        "source_mutations",
        "git_operations",
        "runtime_pull_requests",
        "runtime_approvals",
        "deployments",
        "model_weight_changes",
    )
    for key in zero_keys:
        assert integrity[key] == 0, key
    assert integrity["repository_unchanged"] is True
    assert integrity["temporary_evaluation_data_cleaned"] is True
    assert payload["runtime_effect"] is False


def test_report_is_synthetic_read_only_redacted_and_not_approval():
    payload = json.loads(REPORT.read_text())
    assert payload["synthetic"] is True
    assert payload["read_only"] is True
    assert payload["redacted"] is True
    assert payload["report_is_approval"] is False
    assert payload["report_reusable"] is False
    rendered = json.dumps(payload).lower()
    for marker in ("source body", "raw prompt", "hidden reasoning", "authorization header"):
        assert marker not in rendered
