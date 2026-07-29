from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_continual_learning_authorization_docs_exist() -> None:
    for relative in (
        "docs/governed-learning-memory/continual-learning-pilot-architecture.md",
        "docs/governed-learning-memory/continual-learning-pilot-boundary.md",
        "docs/governed-learning-memory/continual-learning-pilot-authorization-model.md",
        "docs/governed-learning-memory/continual-learning-cycle-state-machine.md",
        "docs/governed-learning-memory/continual-learning-threat-model.md",
        "docs/release/governed-learning-memory-continual-learning-pilot-checklist.md",
        "docs/adr/0191-engagement-shadow-application-evaluation-and-controlled-local-continual-learning-pilot-authorization.md",
    ):
        assert (REPO_ROOT / relative).is_file()
