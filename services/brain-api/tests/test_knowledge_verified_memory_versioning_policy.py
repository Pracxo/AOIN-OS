from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
VALIDATOR = REPO_ROOT / "scripts/lib/knowledge_intelligence_verified_knowledge_authorization.py"
HARNESS = (
    REPO_ROOT
    / "scripts/lib/knowledge_intelligence_integrated_research_agent_operator_evaluation.py"
)


def _load_validator():
    sys.path.insert(0, str(REPO_ROOT / "scripts/lib"))
    spec = importlib.util.spec_from_file_location("verified_auth", VALIDATOR)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_json(relative: str) -> dict[str, object]:
    return json.loads((REPO_ROOT / relative).read_text(encoding="utf-8"))


def test_verified_knowledge_versioning_is_append_only_and_non_deleting() -> None:
    version = _load_json(
        "examples/knowledge-intelligence/verified-knowledge-candidate-version.json"
    )
    assert version["append_only"] is True
    assert version["prior_versions_preserved"] is True
    assert version["historical_version_mutated"] is False
    assert version["confidence_carry_forward_automatic"] is False
    assert version["runtime_effect"] is False
