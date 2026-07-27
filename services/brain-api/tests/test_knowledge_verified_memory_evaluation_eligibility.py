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


def test_support_refutation_and_blocking_scenarios_passed() -> None:
    data = report()
    passed = {item["scenario_id"] for item in data["scenario_results"] if item["passed"]}
    for scenario in (
        "valid_support_candidate",
        "valid_refutation_candidate",
        "coverage_and_provenance_requirements",
        "stale_evidence_blocking",
        "retraction_blocking",
        "supersession_policy",
        "scope_mismatch_blocking",
        "unresolved_contradiction_blocking",
        "material_dissent_blocking",
        "upstream_abstention",
    ):
        assert scenario in passed
    assert data["hard_gate_results"]["support_eligibility_passed"] is True
    assert data["hard_gate_results"]["refutation_eligibility_passed"] is True
