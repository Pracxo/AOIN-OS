from __future__ import annotations

import json
from pathlib import Path

from scripts.lib import governed_learning_memory_engagement_application_authorization as engauth

REPO_ROOT = Path(__file__).resolve().parents[3]


def load_json(relative: str):
    return json.loads((REPO_ROOT / relative).read_text())


def test_engagement_application_authorization_validator_passes():
    engauth.validate_engagement_application_authorization(REPO_ROOT)
