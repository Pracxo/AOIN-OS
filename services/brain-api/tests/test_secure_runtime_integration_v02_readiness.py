from __future__ import annotations

from test_secure_runtime_integration_program_charter import (
    RELEASE_BLOCKERS,
    load_json,
    read_text,
)


def test_v02_release_readiness_remains_false_with_required_blockers() -> None:
    release = read_text("docs/release/v02-release-readiness-delta.md")
    program = load_json("docs/secure-runtime-integration/program-ledger.json")

    assert program["v02_release_ready"] is False
    assert program["v02_tag_created"] is False
    assert program["v02_release_created"] is False
    assert "AION-230 addresses only the secure local runtime foundation" in release
    assert "It does not close all v0.2 release blockers" in release
    for blocker in RELEASE_BLOCKERS:
        assert blocker in release


def test_release_evidence_keeps_secure_runtime_no_go_boundary() -> None:
    for relative in (
        "docs/release/secure-runtime-integration-program-authorization.md",
        "docs/release/secure-runtime-integration-scope.md",
        "docs/release/secure-runtime-integration-runtime-hold.md",
        "docs/release/secure-runtime-integration-no-go.md",
        "docs/release/secure-runtime-integration-checklist.md",
        "docs/release/secure-runtime-integration-evidence-matrix.md",
    ):
        content = read_text(relative)
        assert "AION-230-SRI-0001" in content
        assert "AION-231" in content
        assert "AION-232" in content
