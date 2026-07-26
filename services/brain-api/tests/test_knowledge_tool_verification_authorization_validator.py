from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
VALIDATOR = REPO_ROOT / "scripts/lib/knowledge_intelligence_tool_verification_authorization.py"


def _load_validator():
    spec = importlib.util.spec_from_file_location("tool_auth", VALIDATOR)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_tool_verification_authorization_validator_passes_repository_files() -> None:
    validator = _load_validator()
    validator.validate_authorization_files(REPO_ROOT)
    validator.validate_runtime_hold(REPO_ROOT)


def test_tool_verification_authorization_scripts_pass_under_pytest() -> None:
    env = {**os.environ, "PYTEST_CURRENT_TEST": "AION-214 tool verification validator"}
    for script in (
        "scripts/knowledge-intelligence-tool-verification-authorization-no-go-regression.sh",
        "scripts/knowledge-intelligence-tool-verification-authorization-check.sh",
        "scripts/knowledge-intelligence-tool-verification-runtime-hold.sh",
    ):
        subprocess.run([str(REPO_ROOT / script)], cwd=REPO_ROOT, env=env, check=True)
