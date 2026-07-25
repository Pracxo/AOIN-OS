from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_domain_expert_mesh_scope_authorizes_computational_profiles_only():
    profile = json.loads(
        (REPO_ROOT / "examples/knowledge-intelligence/domain-expert-profile.json").read_text()
    )
    assert profile["computational_profile"] is True
    assert profile["human_identity_claimed"] is False
    assert profile["professional_credential_claimed"] is False
    assert profile["model_provider_required"] is False
    assert profile["tool_execution_required"] is False
    assert profile["runtime_effect"] is False


def test_domain_taxonomy_requires_explicit_safe_deterministic_nodes():
    taxonomy = json.loads(
        (REPO_ROOT / "examples/knowledge-intelligence/domain-taxonomy-node.json").read_text()
    )
    assert taxonomy["domain_id"] == "domain-regulatory-001"
    assert taxonomy["specialty_ids"] == ["specialty-policy-001"]
    assert taxonomy["explicit_safe_ids"] is True
    assert taxonomy["deterministic_hierarchy"] is True
    assert taxonomy["network_ontology_lookup_enabled"] is False
    assert taxonomy["model_generated_domain"] is False
    assert taxonomy["universal_wildcard_domain"] is False
