from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_tool_verification_threat_model_covers_runtime_and_approval_confusion() -> None:
    payload = json.loads(
        (REPO_ROOT / "examples/knowledge-intelligence/tool-verification-authorization.json")
        .read_text(encoding="utf-8")
    )
    threats = set(payload["threat_model"])
    for threat in (
        "malicious_tool_manifest",
        "simulation_treated_as_execution",
        "verification_treated_as_approval",
        "tool_output_treated_as_knowledge",
        "shell_execution",
        "subprocess_execution",
        "network_access",
        "connector_call",
        "model_provider_call",
        "persistent_tool_state_write",
        "authorization_reuse",
        "evaluation_evidence_used_as_approval",
    ):
        assert threat in threats
