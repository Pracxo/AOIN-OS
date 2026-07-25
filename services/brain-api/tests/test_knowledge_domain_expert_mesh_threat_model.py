from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_domain_expert_mesh_threat_model_names_core_no_go_risks():
    text = (
        (REPO_ROOT / "docs/knowledge-intelligence/domain-expert-threat-model.md")
        .read_text()
        .lower()
    )
    for phrase in (
        "impersonation",
        "credential claims",
        "dissent suppression",
        "confidence amplification",
        "network access",
        "model calls",
        "tool execution",
        "persistence",
    ):
        assert phrase in text


def test_domain_expert_mesh_runtime_hold_keeps_prohibited_capabilities_disabled():
    runtime = json.loads(
        (
            REPO_ROOT / "examples/knowledge-intelligence/domain-expert-mesh-runtime-hold.json"
        ).read_text()
    )
    for key in (
        "human_expert_identity_claim_enabled",
        "professional_credential_claim_enabled",
        "model_provider_integration_enabled",
        "tool_execution_enabled",
        "network_access_enabled",
        "persistent_mesh_write_enabled",
        "automatic_real_world_action_enabled",
        "knowledge_promotion_enabled",
        "belief_mutation_enabled",
        "runtime_effect",
    ):
        assert runtime[key] is False
