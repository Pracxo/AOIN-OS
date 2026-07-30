from __future__ import annotations

from test_secure_runtime_integration_program_charter import (
    FUTURE_SOURCE_SCOPE,
    REPO_ROOT,
    load_json,
)


def test_aion231_source_scope_is_recorded_and_present() -> None:
    program = load_json("docs/secure-runtime-integration/program-ledger.json")

    assert program["future_source_scope"] == FUTURE_SOURCE_SCOPE
    for relative in FUTURE_SOURCE_SCOPE:
        assert (REPO_ROOT / relative).exists()


def test_aion231_branch_does_not_create_prohibited_runtime_surfaces() -> None:
    forbidden_paths = (
        "services/brain-api/src/aion_brain/api/secure_runtime.py",
        "services/brain-api/src/aion_brain/api/production_auth.py",
        "services/brain-api/src/aion_brain/secure_runtime/network.py",
        "services/brain-api/src/aion_brain/secure_runtime/model_gateway.py",
        "services/brain-api/src/aion_brain/secure_runtime/connector_runtime.py",
        "services/brain-api/src/aion_brain/secure_runtime/tool_runtime.py",
        "services/brain-api/src/aion_brain/secure_runtime/shell_runtime.py",
        "services/brain-api/src/aion_brain/secure_runtime/module_loader.py",
        "services/brain-api/src/aion_brain/secure_runtime/credential_store.py",
        "services/brain-api/src/aion_brain/secure_runtime/token_store.py",
        "services/brain-api/src/aion_brain/secure_runtime/background_worker.py",
        "services/brain-api/src/aion_brain/secure_runtime/scheduler.py",
    )
    for relative in forbidden_paths:
        assert not (REPO_ROOT / relative).exists()
