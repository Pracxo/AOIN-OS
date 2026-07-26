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


def test_verified_knowledge_revalidation_is_explicit_and_not_background_runtime() -> None:
    runtime = _load_json("examples/knowledge-intelligence/verified-knowledge-runtime-hold.json")
    assert runtime["verified_knowledge_memory_implemented"] is False
    assert runtime["scheduled_revalidation_job_enabled"] is False
    assert runtime["background_verified_knowledge_worker_enabled"] is False
    assert runtime["persistent_verified_knowledge_write_enabled"] is False
