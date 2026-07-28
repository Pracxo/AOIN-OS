from __future__ import annotations

import json
from pathlib import Path

from scripts.lib import governed_learning_memory_local_persistence_operator_evaluation as eval225

REPO_ROOT = Path(__file__).resolve().parents[3]


def load_json(relative: str):
    return json.loads((REPO_ROOT / relative).read_text())


def test_evaluation_docs_and_release_evidence_exist():
    required = [
        "docs/governed-learning-memory/local-persistence-operator-evaluation-closeout.md",
        "docs/governed-learning-memory/local-persistence-operator-evaluation-report.md",
        "docs/governed-learning-memory/local-persistence-evaluation-scenarios.md",
        "docs/governed-learning-memory/local-persistence-evaluation-security-boundary.md",
        "docs/release/governed-learning-memory-local-persistence-evaluation-closeout.md",
    ]
    for rel in required:
        text = (REPO_ROOT / rel).read_text()
        assert "AION-GLMPE-002" in text
        assert eval225.PASS_DECISION in text
