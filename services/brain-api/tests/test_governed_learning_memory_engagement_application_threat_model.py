from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def load_json(relative: str):
    return json.loads((REPO_ROOT / relative).read_text())


def test_engagement_threat_model_records_core_abuse_cases():
    text = (
        REPO_ROOT / "docs/governed-learning-memory/engagement-application-threat-model.md"
    ).read_text()
    for phrase in [
        "Engagement-learning candidates remain non-factual",
        "production policy",
        "persistent overlay",
        "belief mutation",
    ]:
        assert phrase in text
