from __future__ import annotations

from pathlib import Path


def test_aion_217_does_not_add_runtime_api_or_cli_registration() -> None:
    repo = Path(__file__).resolve().parents[3]
    forbidden = (
        "services/brain-api/src/aion_brain/api/verified_knowledge.py",
        "services/brain-api/src/aion_brain/knowledge_intelligence/verified_knowledge_runtime.py",
        "services/brain-api/src/aion_brain/knowledge_intelligence/verified_knowledge_database.py",
    )
    assert all(not (repo / relative).exists() for relative in forbidden)
