from __future__ import annotations

import subprocess

from test_secure_runtime_integration_program_charter import (
    PROHIBITED_CAPABILITIES,
    REPO_ROOT,
    load_json,
)


def test_every_aion231_prohibited_capability_remains_false() -> None:
    program = load_json("docs/secure-runtime-integration/program-ledger.json")
    auth = load_json("docs/secure-runtime-integration/authorization-ledger.json")

    for payload in (program, auth):
        assert set(payload["prohibited_capabilities"]) == set(PROHIBITED_CAPABILITIES)
        assert all(
            payload["prohibited_capabilities"][key] is False for key in PROHIBITED_CAPABILITIES
        )


def test_static_runtime_hold_keeps_runtime_activation_disabled() -> None:
    hold = load_json(
        "operator-console-static/demo-data/secure-runtime-integration-runtime-hold.json"
    )
    boundary = load_json("examples/secure-runtime-integration/runtime-boundary.json")

    disabled_keys = (
        "production_auth_runtime_enabled",
        "external_identity_provider_enabled",
        "credential_persistence_enabled",
        "token_persistence_enabled",
        "general_network_access_enabled",
        "model_provider_call_enabled",
        "connector_execution_enabled",
        "actual_tool_execution_enabled",
        "module_activation_enabled",
        "production_write_execution_enabled",
        "source_rewrite_enabled",
        "git_mutation_enabled",
        "production_deployment_enabled",
        "model_weight_training_enabled",
        "v02_release_ready",
    )
    assert hold["runtime_hold_active"] is True
    assert hold["aion_231_runtime_source_exists"] is True
    for key in disabled_keys:
        assert hold[key] is False
        assert boundary["disabled"][key] is False


def test_no_v02_tag_exists_locally() -> None:
    result = subprocess.run(
        ["git", "tag", "--list", "v0.2*", "aion-v0.2*"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == ""
