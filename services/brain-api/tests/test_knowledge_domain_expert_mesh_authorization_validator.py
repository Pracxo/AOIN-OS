from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
VALIDATOR = REPO_ROOT / "scripts/lib/knowledge_intelligence_domain_expert_mesh_authorization.py"


def _load_validator():
    spec = importlib.util.spec_from_file_location("mesh_auth", VALIDATOR)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_domain_expert_mesh_authorization_validator_passes_repository_files():
    validator = _load_validator()
    validator.validate_authorization_files(REPO_ROOT)
    validator.validate_runtime_hold(REPO_ROOT)


def test_domain_expert_mesh_authorization_scripts_pass_under_pytest():
    env = {**os.environ, "PYTEST_CURRENT_TEST": "AION-212 domain expert mesh validator"}
    for script in (
        "scripts/knowledge-intelligence-domain-expert-mesh-authorization-no-go-regression.sh",
        "scripts/knowledge-intelligence-domain-expert-mesh-authorization-check.sh",
    ):
        subprocess.run([str(REPO_ROOT / script)], cwd=REPO_ROOT, env=env, check=True)
