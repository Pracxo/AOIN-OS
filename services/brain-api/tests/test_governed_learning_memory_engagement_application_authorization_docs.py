from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def load_json(relative: str):
    return json.loads((REPO_ROOT / relative).read_text())


def test_engagement_application_docs_exist_and_record_non_factual_boundary():
    for rel in [
        "docs/governed-learning-memory/engagement-application-architecture.md",
        "docs/governed-learning-memory/engagement-application-boundary.md",
        "docs/governed-learning-memory/engagement-application-threat-model.md",
    ]:
        text = (REPO_ROOT / rel).read_text()
        assert "AION-225-GLM-0003" in text
        assert "non-factual" in text
        assert "persistent overlay" in text
