from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PUBLIC_AUTH_VALIDATOR = (
    REPO_ROOT / "scripts/lib/knowledge_intelligence_public_research_pilot_authorization.py"
)


def load_json(relative: str) -> dict[str, object]:
    return json.loads((REPO_ROOT / relative).read_text(encoding="utf-8"))


def load_public_auth():
    spec = importlib.util.spec_from_file_location("public_auth", PUBLIC_AUTH_VALIDATOR)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def public_auth() -> dict[str, object]:
    return load_json("examples/knowledge-intelligence/public-research-pilot-authorization.json")


def test_public_research_pilot_resource_limits_are_exact() -> None:
    validator = load_public_auth()
    auth = public_auth()
    assert auth["resource_limits"] == validator.RESOURCE_LIMITS
    assert auth["resource_limits"]["maximum_public_https_requests_per_plan"] == 50
    assert auth["resource_limits"]["maximum_dns_resolutions_per_plan"] == 100
    assert auth["resource_limits"]["maximum_persistent_verified_knowledge_writes"] == 0
    assert auth["resource_limits"]["maximum_automatic_knowledge_promotions"] == 0
    assert auth["resource_limits"]["maximum_cognitive_memory_writes"] == 0
