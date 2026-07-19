"""Self-improvement governance authorization chain tests."""

from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts/lib"))

from self_improvement_governance import (  # noqa: E402
    AION_172_FEATURE_COMMIT,
    AION_172_MERGE_COMMIT,
    AUTHORIZATION_ID,
    CANARY_APPROVAL_BINDING_REQUIREMENTS,
    CANARY_APPROVED_SCOPE,
    CANARY_AUTHORIZATION_ID,
    CANARY_PROHIBITED_SCOPE,
    CHANGE_BUDGET_DIMENSIONS,
    EVALUATION_AUTHORIZATION_ID,
    EXPERIMENT_AUTHORIZATION_ID,
    GOVERNANCE_FALSE_FLAGS,
    GOVERNANCE_TRUE_FLAGS,
    LIFECYCLE_STATES,
    PARENT_AUTHORIZATION_ID,
    PROTECTED_PATHS,
    RISK_LEVELS,
    ROOT_AUTHORIZATION_ID,
    SHADOW_AUTHORIZATION_ID,
    SHADOW_PROHIBITED_FLAGS,
    SHADOW_PROHIBITED_SCOPE,
    TEST_WEAKENING_CONTROLS,
    GovernanceValidationError,
    validate_authorization_ledger,
    validate_no_go,
    validate_program_ledger,
    validate_repo,
    validate_sequence,
    validate_transition,
)

AION_166_FEATURE_COMMIT = "fae49a3f913b7a3d4d18ad4e7f989ed2aca5de91"
AION_166_MERGE_COMMIT = "9a7105e31b8f6e56faf53bfb56e11eed75a01203"
AION_167_FEATURE_COMMIT = "bbc04cf57f02483e00752c20fa70b77abf95ce46"
AION_167_MERGE_COMMIT = "98a50edb5eaaf55de5babaa0ea9eb057ef5b2feb"
AION_168_FEATURE_COMMIT = "8d1402f6c122098f3aec5809cf94539992b45d10"
AION_168_MERGE_COMMIT = "74472522edffbbeabb996c6d572dce1dcb0cda48"
AION_170_FEATURE_COMMITS = [
    "2005217334301a6b4951cc3ae2a0d88de99b95e0",
    "4798459eec61e5f534c880234508815364804ee5",
]
AION_170_MERGE_COMMIT = "6e741c8327d900fa80480bce911fbccffb8b4781"


def test_self_improvement_required_files_exist_and_adrs_are_indexed() -> None:
    required = [
        "docs/self-improvement/governance-charter.md",
        "docs/self-improvement/evaluation-authorization.md",
        "docs/self-improvement/experiment-authorization.md",
        "docs/self-improvement/rewrite-authorization.md",
        "docs/self-improvement/canary-authorization.md",
        "docs/self-improvement/protected-core-boundary.md",
        "docs/self-improvement/approval-model.md",
        "docs/self-improvement/change-budget-model.md",
        "docs/self-improvement/risk-model.md",
        "docs/self-improvement/aion-164-closeout-evidence.md",
        "docs/self-improvement/authorization-ledger.json",
        "docs/self-improvement/program-ledger.json",
        "docs/adr/0156-governed-self-improvement-control-plane.md",
        "docs/adr/0157-self-improvement-evaluation-authorization.md",
        "docs/adr/0158-self-improvement-experiment-authorization.md",
        "docs/adr/0159-self-improvement-rewrite-authorization.md",
        "docs/adr/0160-self-improvement-canary-authorization.md",
    ]
    for relative in required:
        assert (ROOT / relative).is_file(), relative
    adr_index = _text("docs/adr/README.md")
    assert "0156-governed-self-improvement-control-plane.md" in adr_index
    assert "0157-self-improvement-evaluation-authorization.md" in adr_index
    assert "0158-self-improvement-experiment-authorization.md" in adr_index
    assert "0159-self-improvement-rewrite-authorization.md" in adr_index
    assert "0160-self-improvement-canary-authorization.md" in adr_index


def test_aion171_is_consumed_and_aion173_authorization_is_exact() -> None:
    payload = _json("docs/self-improvement/authorization-ledger.json")
    validate_authorization_ledger(payload)
    (
        root_closeout,
        parent_closeout,
        evaluation_closeout,
        experiment_closeout,
        rewrite_closeout,
        canary_closeout,
        shadow_active,
    ) = payload["records"]

    assert root_closeout["authorization_transaction_id"] == ROOT_AUTHORIZATION_ID
    assert root_closeout["authorization_consumed_by_pr"] == 75

    assert parent_closeout["authorization_transaction_id"] == PARENT_AUTHORIZATION_ID
    assert parent_closeout["authorization_consumed_by_task"] == "AION-166"
    assert parent_closeout["authorization_consumed_by_pr"] == 77
    assert parent_closeout["authorization_consumed_by_feature_commits"] == [
        AION_166_FEATURE_COMMIT
    ]
    assert parent_closeout["authorization_consumed_by_merge_commit"] == AION_166_MERGE_COMMIT
    assert parent_closeout["authorization_reusable"] is False

    assert evaluation_closeout["authorization_transaction_id"] == EVALUATION_AUTHORIZATION_ID
    assert evaluation_closeout["authorization_consumed_by_task"] == "AION-168"
    assert evaluation_closeout["authorization_consumed_by_pr"] == 79
    assert evaluation_closeout["authorization_consumed_by_feature_commits"] == [
        AION_168_FEATURE_COMMIT
    ]
    assert evaluation_closeout["authorization_consumed_by_merge_commit"] == AION_168_MERGE_COMMIT
    assert evaluation_closeout["authorization_reusable"] is False

    assert experiment_closeout["authorization_transaction_id"] == EXPERIMENT_AUTHORIZATION_ID
    assert experiment_closeout["authorization_consumed_by_task"] == "AION-170"
    assert experiment_closeout["authorization_consumed_by_pr"] == 81
    assert experiment_closeout["authorization_consumed_by_feature_commits"] == (
        AION_170_FEATURE_COMMITS
    )
    assert experiment_closeout["authorization_consumed_by_merge_commit"] == AION_170_MERGE_COMMIT
    assert experiment_closeout["authorization_reusable"] is False

    assert rewrite_closeout["authorization_transaction_id"] == AUTHORIZATION_ID
    assert rewrite_closeout["authorization_consumed_by_task"] == "AION-172"
    assert rewrite_closeout["authorization_consumed_by_pr"] == 83
    assert rewrite_closeout["authorization_consumed_by_feature_commits"] == [
        AION_172_FEATURE_COMMIT
    ]
    assert rewrite_closeout["authorization_consumed_by_merge_commit"] == AION_172_MERGE_COMMIT
    assert rewrite_closeout["authorization_reusable"] is False

    assert canary_closeout["authorization_transaction_id"] == CANARY_AUTHORIZATION_ID
    assert canary_closeout["implementation_task"] == "AION-174"
    assert (
        canary_closeout["authorization_scope"]
        == "approval-bound-canary-rollback-and-adaptive-policy"
    )
    assert tuple(canary_closeout["protected_paths"]) == PROTECTED_PATHS
    assert tuple(canary_closeout["risk_levels"]) == RISK_LEVELS
    assert tuple(canary_closeout["change_budget_dimensions"]) == CHANGE_BUDGET_DIMENSIONS
    assert (
        tuple(canary_closeout["approval_binding_requirements"])
        == CANARY_APPROVAL_BINDING_REQUIREMENTS
    )
    assert tuple(canary_closeout["test_weakening_controls"]) == TEST_WEAKENING_CONTROLS
    assert tuple(canary_closeout["approved_scope"]) == CANARY_APPROVED_SCOPE
    assert tuple(canary_closeout["prohibited_scope"]) == CANARY_PROHIBITED_SCOPE
    for key in GOVERNANCE_FALSE_FLAGS:
        assert canary_closeout[key] is False
    for key in GOVERNANCE_TRUE_FLAGS:
        assert canary_closeout[key] is True

    assert shadow_active["authorization_transaction_id"] == SHADOW_AUTHORIZATION_ID
    assert shadow_active["authorization_active"] is True
    assert shadow_active["implementation_task"] == "AION-178"
    assert tuple(shadow_active["prohibited_scope"]) == SHADOW_PROHIBITED_SCOPE
    for key in SHADOW_PROHIBITED_FLAGS:
        assert shadow_active[key] is False


def test_program_ledger_records_aion164_through_aion167() -> None:
    payload = _json("docs/self-improvement/program-ledger.json")
    validate_program_ledger(payload)
    by_task = {record["task_id"]: record for record in payload["records"]}

    assert by_task["AION-164"]["pull_requests"] == [75]
    assert by_task["AION-164"]["ci_result"] == "pass"
    assert by_task["AION-164"]["completion_timestamp"] == "2026-07-18T13:14:27Z"

    assert by_task["AION-165"]["pull_requests"] == [76]
    assert by_task["AION-165"]["authorization_state"] == "consumed_by_AION-166_closed_by_AION-167"

    assert by_task["AION-166"]["branch"] == "phase/self-improvement-governance-plane"
    assert by_task["AION-166"]["feature_commits"] == [AION_166_FEATURE_COMMIT]
    assert by_task["AION-166"]["pull_requests"] == [77]
    assert by_task["AION-166"]["merge_commits"] == [AION_166_MERGE_COMMIT]
    assert by_task["AION-166"]["ci_result"] == "pass"

    assert by_task["AION-167"]["branch"] == "phase/self-improvement-evaluation-authorization"
    assert by_task["AION-167"]["feature_commits"] == [AION_167_FEATURE_COMMIT]
    assert by_task["AION-167"]["pull_requests"] == [78]
    assert by_task["AION-167"]["merge_commits"] == [AION_167_MERGE_COMMIT]
    assert by_task["AION-167"]["authorization_transaction"] == EVALUATION_AUTHORIZATION_ID
    assert by_task["AION-167"]["authorization_state"] == (
        "consumed_by_AION-168_closed_by_AION-169"
    )
    assert by_task["AION-167"]["next_task"] == "AION-168"

    assert by_task["AION-168"]["branch"] == "phase/self-improvement-evaluation-plane"
    assert by_task["AION-168"]["feature_commits"] == [AION_168_FEATURE_COMMIT]
    assert by_task["AION-168"]["pull_requests"] == [79]
    assert by_task["AION-168"]["merge_commits"] == [AION_168_MERGE_COMMIT]
    assert by_task["AION-168"]["authorization_transaction"] == EVALUATION_AUTHORIZATION_ID
    assert by_task["AION-168"]["authorization_state"] == (
        "consumed_by_AION-168_closed_by_AION-169"
    )

    assert by_task["AION-169"]["branch"] == "phase/self-improvement-experiment-authorization"
    assert by_task["AION-169"]["authorization_transaction"] == EXPERIMENT_AUTHORIZATION_ID
    assert by_task["AION-169"]["authorization_state"] == (
        "consumed_by_AION-170_closed_by_AION-171"
    )
    assert by_task["AION-169"]["next_task"] == "AION-170"

    assert by_task["AION-170"]["branch"] == "phase/self-improvement-experiment-engine"
    assert by_task["AION-170"]["feature_commits"] == AION_170_FEATURE_COMMITS
    assert by_task["AION-170"]["pull_requests"] == [81]
    assert by_task["AION-170"]["merge_commits"] == [AION_170_MERGE_COMMIT]
    assert by_task["AION-170"]["authorization_transaction"] == EXPERIMENT_AUTHORIZATION_ID
    assert by_task["AION-170"]["authorization_state"] == (
        "consumed_by_AION-170_closed_by_AION-171"
    )
    assert by_task["AION-170"]["next_task"] == "AION-171"

    assert by_task["AION-171"]["branch"] == "phase/self-improvement-rewrite-authorization"
    assert by_task["AION-171"]["authorization_transaction"] == AUTHORIZATION_ID
    assert by_task["AION-171"]["authorization_state"] == (
        "consumed_by_AION-172_closed_by_AION-173"
    )
    assert by_task["AION-171"]["next_task"] == "AION-172"

    assert by_task["AION-172"]["branch"] == "phase/self-improvement-approved-rewrite-controller"
    assert by_task["AION-172"]["feature_commits"] == [AION_172_FEATURE_COMMIT]
    assert by_task["AION-172"]["pull_requests"] == [83]
    assert by_task["AION-172"]["merge_commits"] == [AION_172_MERGE_COMMIT]
    assert by_task["AION-172"]["authorization_transaction"] == AUTHORIZATION_ID
    assert by_task["AION-172"]["authorization_state"] == (
        "consumed_by_AION-172_closed_by_AION-173"
    )
    assert by_task["AION-172"]["next_task"] == "AION-173"

    assert by_task["AION-173"]["branch"] == "phase/self-improvement-canary-authorization"
    assert by_task["AION-173"]["authorization_transaction"] == CANARY_AUTHORIZATION_ID
    assert by_task["AION-173"]["authorization_state"] == "active_until_AION-174_merge"
    assert by_task["AION-173"]["next_task"] == "AION-174"


def test_lifecycle_validator_accepts_known_path_and_rejects_unknowns() -> None:
    assert LIFECYCLE_STATES[0] == "observed"
    assert LIFECYCLE_STATES[-1] == "archived"
    decisions = validate_sequence(
        (
            "observed",
            "hypothesized",
            "test_created",
            "experiment_ready",
            "patch_created",
            "sandbox_running",
            "sandbox_passed",
            "approval_pending",
            "approved",
            "pr_created",
            "merged",
            "canary",
            "rolled_back",
            "archived",
        )
    )
    assert all(decision.allowed for decision in decisions)
    assert validate_transition("observed", "approved").allowed is False
    assert validate_transition("unknown", "approved").reason == "unknown current state"
    assert validate_transition("observed", "unknown").reason == "unknown next state"
    with pytest.raises(GovernanceValidationError, match="unknown lifecycle transition"):
        validate_sequence(("observed", "approved"))


def test_governance_validator_blocks_runtime_enablement() -> None:
    payload = _json("docs/self-improvement/authorization-ledger.json")
    validate_no_go(ROOT)
    mutated = json.loads(json.dumps(payload))
    mutated["records"][5]["source_mutation_enabled"] = True
    with pytest.raises(GovernanceValidationError, match="source_mutation_enabled"):
        validate_authorization_ledger(mutated)


def test_governance_docs_do_not_store_private_material() -> None:
    validate_repo(ROOT)
    combined = "\n".join(
        _safe_text_for_private_material_check(relative)
        for relative in [
            "docs/self-improvement/governance-charter.md",
            "docs/self-improvement/evaluation-authorization.md",
            "docs/self-improvement/experiment-authorization.md",
            "docs/self-improvement/rewrite-authorization.md",
            "docs/self-improvement/canary-authorization.md",
            "docs/self-improvement/program-ledger.json",
            "docs/self-improvement/authorization-ledger.json",
        ]
    ).lower()
    for marker in ["hidden reasoning", "raw prompt", "chain-of-thought", "access_token"]:
        assert marker not in combined


def test_self_improvement_authorization_scripts_are_executable_and_pass() -> None:
    scripts = [
        "scripts/self-improvement-governance-no-go-regression.sh",
        "scripts/self-improvement-governance-authorization-check.sh",
        "scripts/self-improvement-evaluation-no-go-regression.sh",
        "scripts/self-improvement-evaluation-authorization-check.sh",
        "scripts/self-improvement-experiment-no-go-regression.sh",
        "scripts/self-improvement-experiment-authorization-check.sh",
        "scripts/self-improvement-rewrite-no-go-regression.sh",
        "scripts/self-improvement-rewrite-authorization-check.sh",
        "scripts/self-improvement-canary-no-go-regression.sh",
        "scripts/self-improvement-canary-authorization-check.sh",
    ]
    for relative in scripts:
        mode = (ROOT / relative).stat().st_mode
        assert mode & stat.S_IXUSR, relative
        subprocess.run([str(ROOT / relative)], cwd=ROOT, check=True, env=_nested_env())


def _json(relative: str) -> dict[str, Any]:
    with (ROOT / relative).open() as handle:
        payload = json.load(handle)
    assert isinstance(payload, dict)
    return payload


def _text(relative: str) -> str:
    return (ROOT / relative).read_text()


def _safe_text_for_private_material_check(relative: str) -> str:
    if relative != "docs/self-improvement/authorization-ledger.json":
        return _text(relative)
    payload = _json(relative)
    payload["records"] = [_redact_formal_no_go_labels(record) for record in payload["records"]]
    return json.dumps(payload)


def _redact_formal_no_go_labels(value: Any) -> Any:
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, item in value.items():
            if key in SHADOW_PROHIBITED_FLAGS or key in {
                "disallowed_inputs",
                "prohibited_scope",
                "prohibited_additions_for_AION_178",
            }:
                continue
            redacted[key] = _redact_formal_no_go_labels(item)
        return redacted
    if isinstance(value, list):
        return [_redact_formal_no_go_labels(item) for item in value]
    return value


def _nested_env() -> dict[str, str]:
    env = os.environ.copy()
    env["AION_AGGREGATE_GATE_RUNNING"] = "1"
    return env
