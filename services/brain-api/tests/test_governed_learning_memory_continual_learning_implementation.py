from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest
from pydantic import ValidationError

from aion_brain.contracts.governed_continual_learning import (
    AUTHORIZATION_TRANSACTION_ID,
    CONTINUAL_LEARNING_QUERY_SCHEMA_VERSION,
    RESOURCE_LIMITS,
    ContinualLearningCycleState,
    ContinualLearningError,
    ContinualLearningPilotMode,
    ContinualLearningResourceUsage,
    build_record,
    continual_fingerprint,
    evaluate_resource_budget,
)
from aion_brain.governed_learning_memory.continual_learning_cycle import (
    ControlledLocalContinualLearningPilotService,
    build_cycle_plan,
    build_deterministic_evidence_bundle,
    build_stage_command,
    deterministic_three_cycle_session,
)
from aion_brain.governed_learning_memory.continual_learning_research import (
    ControlledContinualLearningResearchAdapter,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
AION228_SOURCE = (
    REPO_ROOT
    / "services"
    / "brain-api"
    / "src"
    / "aion_brain"
    / "governed_learning_memory"
)


def test_contract_constants_and_resource_limits_are_exact() -> None:
    assert AUTHORIZATION_TRANSACTION_ID == "AION-227-GLM-0004"
    assert CONTINUAL_LEARNING_QUERY_SCHEMA_VERSION == "aion-glm-continual-learning-query/v1"
    assert RESOURCE_LIMITS["maximum_cycles_per_live_pilot"] == 3
    assert RESOURCE_LIMITS["maximum_background_cycles"] == 0
    assert RESOURCE_LIMITS["maximum_automatic_knowledge_promotions"] == 0
    assert RESOURCE_LIMITS["maximum_production_memory_writes"] == 0


def test_strict_contracts_reject_extra_and_protected_material() -> None:
    with pytest.raises(ValidationError):
        build_record(
            type(build_deterministic_evidence_bundle()),
            {
                "schema_version": "aion-glm-continual-learning-evidence/v1",
                "evidence_bundle_id": "bad-evidence",
                "session_id": "bad-session",
                "authorization_transaction_id": AUTHORIZATION_TRANSACTION_ID,
                "session_result_fingerprint": "0" * 64,
                "integrity_report_fingerprint": "0" * 64,
                "operator_review_item_fingerprints": (),
                "created_at": __import__("datetime").datetime.now(
                    __import__("datetime").UTC
                ),
                "raw_source_body": "raw source body",
            },
            "evidence_bundle_fingerprint",
        )


def test_deterministic_session_receipts_and_outcomes_are_closed() -> None:
    result, receipts = deterministic_three_cycle_session()
    assert result.cycle_count == 3
    assert result.completed_cycle_count == 2
    assert result.abstained_cycle_count == 1
    assert result.stage_receipt_count == len(receipts) == 33
    assert all(receipt.operator_invoked for receipt in receipts)
    assert all(not receipt.background_execution for receipt in receipts)
    assert all(not receipt.production_effect for receipt in receipts)
    assert result.production_memory_writes == 0
    assert result.production_policy_mutations == 0
    assert result.actual_belief_creations == 0


def test_stage_skip_and_expired_command_fail_closed() -> None:
    service = ControlledLocalContinualLearningPilotService()
    plan = build_cycle_plan(
        session_id="aion-228-test-session",
        cycle_id="aion-228-test-cycle",
        cycle_kind=__import__(
            "aion_brain.contracts.governed_continual_learning",
            fromlist=["ContinualLearningCycleKind"],
        ).ContinualLearningCycleKind.EVIDENCE_ACQUISITION_AND_TEMPORARY_CONTINUITY,
        cycle_sequence=1,
        terminal_outcome=__import__(
            "aion_brain.contracts.governed_continual_learning",
            fromlist=["ContinualLearningCycleOutcomeStatus"],
        ).ContinualLearningCycleOutcomeStatus.COMPLETED,
        required_stages=(
            ContinualLearningCycleState.DRAFTED,
            ContinualLearningCycleState.AUTHORIZED,
            ContinualLearningCycleState.CYCLE_COMPLETED,
        ),
    )
    with pytest.raises(ValidationError):
        build_stage_command(
            stage_command_id="aion-228-skip-command",
            session_id=plan.session_id,
            cycle_id=plan.cycle_id,
            expected_current_state=ContinualLearningCycleState.DRAFTED,
            requested_next_state=ContinualLearningCycleState.CYCLE_COMPLETED,
            cycle_plan_fingerprint=plan.cycle_plan_fingerprint,
            operator_identity_fingerprint=continual_fingerprint({"operator": "test"}),
        )
    command = build_stage_command(
        stage_command_id="aion-228-valid-command",
        session_id=plan.session_id,
        cycle_id=plan.cycle_id,
        expected_current_state=ContinualLearningCycleState.DRAFTED,
        requested_next_state=ContinualLearningCycleState.AUTHORIZED,
        cycle_plan_fingerprint=plan.cycle_plan_fingerprint,
        operator_identity_fingerprint=continual_fingerprint({"operator": "test"}),
    )
    with pytest.raises(ContinualLearningError):
        service.validate_stage_command(
            command=command,
            cycle_plan=plan,
            current_state=ContinualLearningCycleState.AUTHORIZED,
        )


def test_in_memory_research_adapter_uses_no_public_network() -> None:
    adapter = ControlledContinualLearningResearchAdapter(
        mode=ContinualLearningPilotMode.DETERMINISTIC_SIMULATION
    )
    urls = (
        "https://example.org/research.txt",
        "https://iana.org/research.txt",
        "https://w3.org/research.txt",
    )
    plan = adapter.plan_research(
        session_id="aion-228-deterministic-session",
        cycle_id="aion-228-deterministic-session-cycle-001",
        claim_fingerprint=continual_fingerprint({"claim": "json-data-interchange"}),
        explicit_source_urls=urls,
        exact_domains=("example.org", "iana.org", "w3.org"),
        source_control_groups=("example", "iana", "w3c"),
    )
    binding = adapter.acquire_research(
        plan=plan,
        explicit_source_urls=urls,
        source_control_groups=("example", "iana", "w3c"),
    )
    assert binding.source_fetch_count == 3
    assert binding.public_https_request_count == 6
    assert binding.source_body_purge_count == 3
    assert binding.source_bodies_retained == 0
    assert binding.automatic_source_discoveries == 0


def test_aion228_source_has_no_direct_transport_or_runtime_mutation_imports() -> None:
    forbidden = (
        "import socket",
        "import ssl",
        "import http.client",
        "import requests",
        "import httpx",
        "import aiohttp",
        "urllib.request",
        "ApprovalService",
        "ApprovalRepository",
        "MemoryRepository",
    )
    for path in AION228_SOURCE.glob("continual_learning_*.py"):
        text = path.read_text(encoding="utf-8")
        for marker in forbidden:
            assert marker not in text, (path, marker)


def test_resource_budget_fails_closed_on_one_over_limit() -> None:
    usage = ContinualLearningResourceUsage(cycles=4)
    decision = evaluate_resource_budget(usage)
    assert decision.passed is False
    assert decision.violations == ("maximum_cycles_per_live_pilot",)


def test_uninstalled_runner_writes_new_redacted_output(tmp_path: Path) -> None:
    temporary_root = tmp_path / "pilot"
    temporary_root.mkdir()
    os.chmod(temporary_root, 0o700)
    output = tmp_path / "runner-output.json"
    session_plan = tmp_path / "session-plan.json"
    runner = (
        REPO_ROOT
        / "scripts"
        / "governed-learning-memory-controlled-local-continual-learning-run.py"
    )
    command = [
        str(runner),
        "plan-session",
        "--authorization",
        AUTHORIZATION_TRANSACTION_ID,
        "--session-plan",
        str(session_plan),
        "--temporary-root",
        str(temporary_root),
        "--output",
        str(output),
        "--mode",
        "deterministic-simulation",
    ]
    subprocess.run(command, cwd=REPO_ROOT, check=True)
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["action"] == "plan-session"
    assert payload["redacted"] is True
    assert payload["runtime_effect"] is False
