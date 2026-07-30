from __future__ import annotations

from test_secure_runtime_integration_program_charter import (
    FUTURE_SOURCE_SCOPE,
    REPO_ROOT,
    load_json,
)


def test_aion231_future_source_scope_is_recorded_but_absent() -> None:
    program = load_json("docs/secure-runtime-integration/program-ledger.json")

    assert program["future_source_scope"] == FUTURE_SOURCE_SCOPE
    for relative in FUTURE_SOURCE_SCOPE:
        assert not (REPO_ROOT / relative).exists()
    assert not (
        REPO_ROOT / "services/brain-api/src/aion_brain/secure_runtime"
    ).exists()


def test_aion230_branch_does_not_create_runtime_activation_surfaces() -> None:
    forbidden_paths = (
        "services/brain-api/src/aion_brain/api/secure_runtime.py",
        "services/brain-api/src/aion_brain/api/production_auth.py",
        "services/brain-api/src/aion_brain/secure_runtime",
        "services/brain-api/src/aion_brain/contracts/secure_runtime.py",
    )
    for relative in forbidden_paths:
        assert not (REPO_ROOT / relative).exists()
