import re

from knowledge_intelligence_test_helpers import (
    CURRENT_SURFACES,
    PARENT_DECISION,
    read_json,
    read_text,
)


def test_aion_203_postmerge_evidence_is_exact():
    text = read_text("docs/cognitive-architecture/aion-203-postmerge-verification.md")
    for term in (
        "Pull request: `114`",
        "Feature commit: `24df1f990a643d013e6155f6ce32598dfa8833bd`",
        "Merge commit: `fdc38402e050ffb5beebd9d6d298f859736f0121`",
        "Merged timestamp: `2026-07-22T18:55:59Z`",
        PARENT_DECISION,
        "brain-api-quality: pass",
        "sdk-quality: pass",
    ):
        assert term in text


def test_cognitive_program_remains_complete_zero_auth_and_disabled():
    program = read_json("docs/cognitive-architecture/program-ledger.json")
    auth = read_json("docs/cognitive-architecture/authorization-ledger.json")
    assert program["program_state"] == "cognitive_architecture_program_complete"
    assert program["cognitive_architecture_program_complete"] is True
    assert program["controlled_local_offline_pilot_passed"] is True
    assert program["active_cognitive_implementation_authorization_count"] == 0
    assert auth["active_cognitive_implementation_authorization_count"] == 0
    for key in (
        "production_cognitive_runtime_enabled",
        "production_event_subscription_enabled",
        "network_access_enabled",
        "source_rewrite_runtime_enabled",
        "automatic_merge_enabled",
        "production_canary_enabled",
        "production_deployment_enabled",
        "model_weight_training_enabled",
    ):
        assert program[key] is False


def test_current_state_reconciled_without_stale_authoritative_markers():
    stale = re.compile(
        r"Current milestone:\s*AION-18[12]|"
        r"AION-181 is the next task|"
        r"AION-182.*next|"
        r"actual_controlled_shadow_activation_authorization_review|"
        r"current state remains AION-179|"
        r"current stage remains AION-179"
    )
    status = read_text("docs/project-status.md")
    milestone = (
        "AION-204 Cognitive Architecture closeout reconciliation and "
        "Knowledge Intelligence Program authorization"
    )
    next_task = "AION-205 controlled research acquisition and source-snapshot core"
    assert milestone in status
    assert next_task in status
    for relative in CURRENT_SURFACES:
        assert stale.search(read_text(relative)) is None, relative
