from __future__ import annotations

from pathlib import Path


def test_claim_graph_adds_no_runtime_registration_api_cli_or_persistence_files() -> None:
    root = Path("/Users/damilaremerotiwon/KITEV2/AOIN OS")
    forbidden = (
        root / "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph_runtime.py",
        root / "services/brain-api/src/aion_brain/knowledge_intelligence/claim_truth.py",
        root / "services/brain-api/src/aion_brain/knowledge_intelligence/claim_confidence.py",
        root / "services/brain-api/src/aion_brain/api/claim_graph.py",
    )
    assert not any(path.exists() for path in forbidden)
    source_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (
            root / "services/brain-api/src/aion_brain/contracts/knowledge_claim_graph.py",
            root / "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph.py",
            root
            / "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph_evidence.py",
            root
            / "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph_repository.py",
            root / "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph_index.py",
            root
            / "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph_integrity.py",
            root
            / "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph_temporal.py",
        )
    )
    for token in ("socket", "requests", "httpx", "sqlite3", "subprocess", "github"):
        assert f"import {token}" not in source_text
        assert f"from {token}" not in source_text
