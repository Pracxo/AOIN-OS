from __future__ import annotations

from test_secure_runtime_integration_program_charter import (
    AUTH_ID,
    CLOSEOUT_TASK,
    IMPLEMENTATION_TASK,
    PROGRAM_ID,
    read_text,
)


def test_readme_records_current_program_completion_and_sri_authorization() -> None:
    readme = read_text("README.md")

    assert "Knowledge Intelligence Program is complete" in readme
    assert "Governed Learning and Memory Program is complete" in readme
    assert "AION Secure Runtime Integration Program" in readme
    assert PROGRAM_ID in readme
    assert AUTH_ID in readme
    assert IMPLEMENTATION_TASK in readme
    assert CLOSEOUT_TASK in readme
    assert "active Knowledge Intelligence implementation authorizations: `0`" in readme
    assert "active GLM implementation authorizations: `0`" in readme
    assert "repeated live-pilot authorization: `false`" in readme
    assert "production runtime authorization: `false`" in readme
    assert "v0.2 remains unreleased" in readme


def test_readme_no_longer_claims_stale_glm_current_tasks() -> None:
    readme = read_text("README.md")
    stale_current_claims = (
        "AION-222 remains unimplemented",
        "AION-225-GLM-0003 is active",
        "AION-226 is current",
        "AION-227 is next",
        "AION-228 is unauthorized",
        "AION-229 remains pending",
    )
    for claim in stale_current_claims:
        assert claim not in readme
