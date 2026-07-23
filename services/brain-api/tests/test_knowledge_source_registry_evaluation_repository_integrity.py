from __future__ import annotations

import subprocess
from pathlib import Path

from knowledge_source_registry_test_helpers import ROOT, read_json


def test_source_registry_evaluation_repository_integrity_zero_totals():
    report = read_json(
        "examples/knowledge-intelligence/source-registry-operator-evaluation-report.json"
    )
    integrity = report["repository_integrity"]
    for key in (
        "source_body_bytes_persisted",
        "persistent_registry_writes",
        "live_network_requests",
        "live_dns_requests",
        "registry_created_pull_requests",
        "registry_git_operations",
        "registry_source_mutations",
        "registry_approvals_created",
        "registry_authorizations_created",
        "claim_verifications",
        "truth_decisions",
        "confidence_calculations",
        "knowledge_promotions",
        "belief_mutations",
    ):
        assert integrity[key] == 0, key
    assert integrity["canonical_repository_untouched_by_evaluation"] is True
    assert integrity["temporary_evaluation_data_cleaned"] is True


def test_no_tracked_registry_or_graph_persistence_files_exist():
    tracked = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True).splitlines()
    offenders = [
        path
        for path in tracked
        if Path(path).suffix.lower() in {".db", ".sqlite", ".sqlite3", ".jsonl"}
    ]
    assert offenders == []
