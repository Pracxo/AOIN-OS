from __future__ import annotations

import subprocess
from pathlib import Path

from knowledge_claim_graph_evaluation_test_helpers import ROOT, evaluation_report


def test_claim_graph_evaluation_repository_integrity_zero_totals():
    integrity = evaluation_report()["repository_integrity"]
    for key in (
        "source_body_bytes",
        "persistent_graph_writes",
        "live_network_requests",
        "live_dns_requests",
        "claim_verifications",
        "truth_decisions",
        "confidence_calculations",
        "contradiction_resolutions",
        "knowledge_promotions",
        "belief_mutations",
        "source_mutations",
        "git_operations",
        "runtime_pull_requests",
        "runtime_approvals",
        "runtime_merges",
        "deployments",
        "model_weight_changes",
    ):
        assert integrity[key] == 0, key
    assert integrity["repository_unchanged"] is True
    assert integrity["temporary_evaluation_data_cleaned"] is True


def test_no_tracked_claim_or_assessment_persistence_files_exist():
    tracked = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True).splitlines()
    offenders = [
        path
        for path in tracked
        if Path(path).suffix.lower() in {".db", ".sqlite", ".sqlite3", ".jsonl"}
        or path.endswith("claim-graph-state.jsonl")
        or path.endswith("epistemic-assessment-state.jsonl")
    ]
    assert offenders == []
