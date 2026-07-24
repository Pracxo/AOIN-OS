from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_claim_graph_adds_no_runtime_registration_api_cli_or_persistence_files() -> None:
    forbidden = (
        ROOT / "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph_runtime.py",
        ROOT / "services/brain-api/src/aion_brain/knowledge_intelligence/claim_truth.py",
        ROOT / "services/brain-api/src/aion_brain/knowledge_intelligence/claim_confidence.py",
        ROOT / "services/brain-api/src/aion_brain/api/claim_graph.py",
    )
    assert not any(path.exists() for path in forbidden)
    source_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (
            ROOT / "services/brain-api/src/aion_brain/contracts/knowledge_claim_graph.py",
            ROOT / "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph.py",
            ROOT
            / "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph_evidence.py",
            ROOT
            / "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph_repository.py",
            ROOT / "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph_index.py",
            ROOT
            / "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph_integrity.py",
            ROOT
            / "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph_temporal.py",
        )
    )
    for token in ("socket", "requests", "httpx", "sqlite3", "subprocess", "github"):
        assert f"import {token}" not in source_text
        assert f"from {token}" not in source_text
