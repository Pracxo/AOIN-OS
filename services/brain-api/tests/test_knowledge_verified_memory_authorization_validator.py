from __future__ import annotations

import importlib.util
import json
import os
import subprocess
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


def test_verified_knowledge_authorization_validator_and_scripts_pass() -> None:
    validator = _load_validator()
    validator.validate_authorization_files(REPO_ROOT)
    validator.validate_runtime_hold(REPO_ROOT)
    env = {**os.environ, "PYTEST_CURRENT_TEST": "AION-216 verified knowledge authorization"}
    for script in (
        "scripts/knowledge-intelligence-verified-knowledge-authorization-no-go-regression.sh",
        "scripts/knowledge-intelligence-verified-knowledge-authorization-check.sh",
        "scripts/knowledge-intelligence-verified-knowledge-runtime-hold.sh",
    ):
        subprocess.run([str(REPO_ROOT / script)], cwd=REPO_ROOT, env=env, check=True)
