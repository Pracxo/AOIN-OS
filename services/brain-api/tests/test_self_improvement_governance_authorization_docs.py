"""AION-165 self-improvement governance authorization tests."""

from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts/lib"))

from self_improvement_governance import (  # noqa: E402
    AUTHORIZATION_ID,
    CHANGE_BUDGET_DIMENSIONS,
    GOVERNANCE_FALSE_FLAGS,
    GOVERNANCE_TRUE_FLAGS,
    LIFECYCLE_STATES,
    PARENT_AUTHORIZATION_ID,
    PROTECTED_PATHS,
    RISK_LEVELS,
    GovernanceValidationError,
    validate_authorization_ledger,
    validate_no_go,
    validate_program_ledger,
    validate_repo,
    validate_sequence,
    validate_transition,
)


def test_aion165_required_files_exist_and_adr_is_indexed() -> None:
    required = [
        "docs/self-improvement/governance-charter.md",
        "docs/self-improvement/protected-core-boundary.md",
        "docs/self-improvement/approval-model.md",
        "docs/self-improvement/change-budget-model.md",
        "docs/self-improvement/risk-model.md",
        "docs/self-improvement/aion-164-closeout-evidence.md",
        "docs/self-improvement/authorization-ledger.json",
        "docs/self-improvement/program-ledger.json",
        "docs/adr/0156-governed-self-improvement-control-plane.md",
    ]
    for relative in required:
        assert (ROOT / relative).is_file(), relative
    assert "0156-governed-self-improvement-control-plane.md" in _text("docs/adr/README.md")


def test_aion164_closeout_and_aion165_authorization_are_exact() -> None:
    payload = _json("docs/self-improvement/authorization-ledger.json")
    validate_authorization_ledger(payload)
    closeout, active = payload["records"]
    assert closeout["authorization_transaction_id"] == PARENT_AUTHORIZATION_ID
    assert closeout["authorization_consumed_by_pr"] == 75
    assert (
        closeout["authorization_consumed_by_merge_commit"]
        == "8b2938a8995a9109b677f240d82da3b4bdc5d73c"
    )
    assert active["authorization_transaction_id"] == AUTHORIZATION_ID
    assert active["implementation_task"] == "AION-166"
    assert active["authorization_scope"] == "governed-self-improvement-control-plane"
    assert tuple(active["protected_paths"]) == PROTECTED_PATHS
    assert tuple(active["risk_levels"]) == RISK_LEVELS
    assert tuple(active["change_budget_dimensions"]) == CHANGE_BUDGET_DIMENSIONS
    for key in GOVERNANCE_FALSE_FLAGS:
        assert active[key] is False
    for key in GOVERNANCE_TRUE_FLAGS:
        assert active[key] is True


def test_program_ledger_records_aion164_and_aion165() -> None:
    payload = _json("docs/self-improvement/program-ledger.json")
    validate_program_ledger(payload)
    by_task = {record["task_id"]: record for record in payload["records"]}
    assert by_task["AION-164"]["pull_requests"] == [75]
    assert by_task["AION-164"]["ci_result"] == "pass"
    assert by_task["AION-164"]["completion_timestamp"] == "2026-07-18T13:14:27Z"
    assert by_task["AION-165"]["branch"] == "phase/self-improvement-governance-authorization"
    assert by_task["AION-165"]["authorization_state"] == "active_until_AION-166_merge"
    assert by_task["AION-165"]["next_task"] == "AION-166"


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
    mutated["records"][1]["self_rewrite_runtime_enabled"] = True
    with pytest.raises(GovernanceValidationError, match="self_rewrite_runtime_enabled"):
        validate_authorization_ledger(mutated)


def test_governance_docs_do_not_store_private_material() -> None:
    validate_repo(ROOT)
    combined = "\n".join(
        _text(relative)
        for relative in [
            "docs/self-improvement/governance-charter.md",
            "docs/self-improvement/approval-model.md",
            "docs/self-improvement/program-ledger.json",
            "docs/self-improvement/authorization-ledger.json",
        ]
    ).lower()
    for marker in ["hidden reasoning", "raw prompt", "chain-of-thought", "access_token"]:
        assert marker not in combined


def test_aion165_scripts_are_executable_and_pass() -> None:
    scripts = [
        "scripts/self-improvement-governance-no-go-regression.sh",
        "scripts/self-improvement-governance-authorization-check.sh",
    ]
    for relative in scripts:
        mode = (ROOT / relative).stat().st_mode
        assert mode & stat.S_IXUSR, relative
        subprocess.run([str(ROOT / relative)], cwd=ROOT, check=True, env=_nested_env())


def _json(relative: str) -> dict[str, object]:
    with (ROOT / relative).open() as handle:
        payload = json.load(handle)
    assert isinstance(payload, dict)
    return payload


def _text(relative: str) -> str:
    return (ROOT / relative).read_text()


def _nested_env() -> dict[str, str]:
    env = os.environ.copy()
    env["AION_AGGREGATE_GATE_RUNNING"] = "1"
    return env
