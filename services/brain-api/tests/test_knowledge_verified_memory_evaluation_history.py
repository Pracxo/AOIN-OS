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


def test_versioning_history_revalidation_and_repository_gates_passed() -> None:
    gates = report()["hard_gate_results"]
    for gate in (
        "versioning_passed",
        "history_preservation_passed",
        "revalidation_passed",
        "repository_immutability_passed",
        "repository_integrity_passed",
    ):
        assert gates[gate] is True
