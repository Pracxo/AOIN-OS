from __future__ import annotations

import re
from pathlib import Path


def test_aion_217_source_has_no_network_runtime_imports() -> None:
    root = Path(__file__).resolve().parents[1]
    sources = (
        root / "src/aion_brain/contracts/knowledge_verified_memory.py",
        root / "src/aion_brain/knowledge_intelligence/verified_knowledge_memory.py",
        root / "src/aion_brain/knowledge_intelligence/verified_knowledge_candidates.py",
        root / "src/aion_brain/knowledge_intelligence/engagement_signal_policy.py",
        root / "src/aion_brain/knowledge_intelligence/engagement_learning_candidates.py",
    )
    pattern = re.compile(
        r"^\s*(import|from)\s+"
        r"(subprocess|socket|requests|httpx|aiohttp|urllib[.]request)\b",
        re.MULTILINE,
    )
    assert not pattern.search("\n".join(path.read_text(encoding="utf-8") for path in sources))
