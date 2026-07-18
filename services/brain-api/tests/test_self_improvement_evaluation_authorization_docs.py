"""AION-167 immutable evaluation authorization tests."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts/lib"))

from self_improvement_governance import (  # noqa: E402
    AUTHORIZATION_ID,
    EVALUATION_APPROVED_SCOPE,
    EVALUATION_PROHIBITED_SCOPE,
    GovernanceValidationError,
    validate_authorization_ledger,
    validate_no_go,
)


def test_aion167_authorizes_only_immutable_evaluation_plane() -> None:
    payload = _authorization()
    validate_authorization_ledger(payload)
    active = payload["records"][2]

    assert active["authorization_transaction_id"] == AUTHORIZATION_ID
    assert active["implementation_task"] == "AION-168"
    assert active["authorization_scope"] == "immutable-self-improvement-evaluation-plane"
    assert tuple(active["approved_scope"]) == EVALUATION_APPROVED_SCOPE
    assert tuple(active["prohibited_scope"]) == EVALUATION_PROHIBITED_SCOPE


def test_aion167_blocks_rewrite_pr_approval_deploy_and_training_flags() -> None:
    validate_no_go(ROOT)
    prohibited_flags = [
        "source_rewriting_enabled",
        "pull_request_creation_enabled",
        "automatic_approval_enabled",
        "benchmark_mutation_by_candidate_enabled",
        "holdout_disclosure_to_patch_generators_enabled",
        "production_deployment_enabled",
        "model_weight_training_enabled",
    ]
    for flag in prohibited_flags:
        payload = _authorization()
        payload["records"][2][flag] = True
        with pytest.raises(GovernanceValidationError, match=flag):
            validate_authorization_ledger(payload)


def test_aion167_requires_hard_safety_and_immutable_holdout_controls() -> None:
    payload = _authorization()
    active = payload["records"][2]
    assert active["hard_safety_gates_authorized"] is True
    assert active["immutable_benchmark_manifests_required"] is True
    assert active["hidden_holdout_required"] is True
    assert active["holdout_disclosure_to_patch_generators_enabled"] is False
    assert "holdout disclosure to patch generators" in active["prohibited_scope"]

    active["prohibited_scope"] = [
        item
        for item in active["prohibited_scope"]
        if item != "holdout disclosure to patch generators"
    ]
    with pytest.raises(GovernanceValidationError, match="prohibited evaluation scope"):
        validate_authorization_ledger(payload)


def _authorization() -> dict[str, Any]:
    with (ROOT / "docs/self-improvement/authorization-ledger.json").open() as handle:
        payload = json.load(handle)
    assert isinstance(payload, dict)
    return payload
