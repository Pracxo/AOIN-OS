from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from aion_brain.contracts import v02_release_qualification as c

REPO_ROOT = Path(__file__).resolve().parents[3]
HARNESS_PATH = (
    REPO_ROOT / "scripts/lib/v02_release_qualification_foundation_operator_evaluation.py"
)
REPORT_PATH = (
    REPO_ROOT
    / "examples/v02-release-qualification/foundation-operator-evaluation-report.json"
)
STAGING_AUTH_PATH = (
    REPO_ROOT / "examples/v02-release-qualification/staging-qualification-authorization.json"
)


def load_harness():
    spec = importlib.util.spec_from_file_location("aion240_eval", HARNESS_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_json(relative: str) -> dict:
    return json.loads((REPO_ROOT / relative).read_text(encoding="utf-8"))


def test_harness_executes_exact_twenty_eight_scenarios(tmp_path):
    harness = load_harness()
    report = harness.evaluate(
        repo_root=REPO_ROOT,
        evaluation_id=harness.EVALUATION_ID,
        implementation_main_commit=harness.IMPLEMENTATION_MERGE_COMMIT,
        evaluation_base_commit="test-evaluation-base",
        pilot_evidence_path=REPO_ROOT
        / "examples/v02-release-qualification/"
        "v02-production-readiness-qualification-foundation-pilot-evidence.json",
        temporary_output_directory=tmp_path,
    )

    harness.validate_report(report)
    assert report["decision"] == harness.PASS_DECISION
    assert report["evaluation_passed"] is True
    assert report["scenario_count"] == 28
    assert report["scenario_ids"] == list(harness.SCENARIO_IDS)
    assert [item["scenario_id"] for item in report["scenario_results"]] == list(
        harness.SCENARIO_IDS
    )
    assert all(item["passed"] is True for item in report["scenario_results"])
    assert all(item["passed"] is True for item in report["hard_gate_results"])


def test_pilot_evidence_and_aion_239_delivery_are_reconciled():
    harness = load_harness()
    pilot = load_json(
        "examples/v02-release-qualification/"
        "v02-production-readiness-qualification-foundation-pilot-evidence.json"
    )
    program = load_json("docs/v02-release-qualification/program-ledger.json")

    assert pilot["pilot_id"] == c.PILOT_ID
    assert pilot["authorization_id"] == "AION-238-V02RQ-0001"
    assert pilot["report_fingerprint"] == harness.EXPECTED_PILOT_FINGERPRINT
    assert harness.pilot_fingerprint_matches(c, pilot)
    assert pilot["readiness_domains_evaluated"] == 20
    assert pilot["readiness_gaps_evaluated"] == 20
    assert pilot["release_gates_evaluated"] == 24
    assert pilot["threat_scenarios_validated"] == 40
    assert pilot["v02_release_ready"] is False
    assert pilot["v02_release_candidate_created"] is False
    assert pilot["prohibited_effect_counters"] == c.PROHIBITED_EFFECT_COUNTERS
    assert program["aion_239_record"]["task_id"] == "AION-239"


def test_source_boundary_and_aion_241_source_state_is_exact():
    harness = load_harness()
    state = harness.source_scope_state(REPO_ROOT)

    assert state["missing_source_scope"] == []
    assert state["exact_runtime_source_scope"] is True
    assert state["prohibited_source_present"] == []
    assert state["aion_241_source_scope_implemented"] is True
    assert sorted(state["future_aion_241_source_present"]) == sorted(
        harness.FUTURE_AION241_SOURCE_SCOPE
    )
    assert state["aion_241_source_scope_state_valid"] is True
    assert state["uninstalled_runner_present"] is True


def test_committed_report_when_present_is_schema_valid_and_zero_effect():
    if not REPORT_PATH.exists():
        return

    harness = load_harness()
    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    harness.validate_report(report)

    assert report["evaluation_id"] == "AION-V02RQPE-001"
    assert report["decision"] == harness.PASS_DECISION
    assert report["synthetic"] is True
    assert report["read_only"] is True
    assert report["redacted"] is True
    assert report["repository_unchanged"] is True
    for key in harness.REPORT_ZERO_EFFECT_FIELDS:
        assert report[key] == 0


def test_authorization_closeout_when_present_is_consistent():
    if not STAGING_AUTH_PATH.exists():
        return

    auth = load_json("docs/v02-release-qualification/authorization-ledger.json")
    program = load_json("docs/v02-release-qualification/program-ledger.json")
    staging = json.loads(STAGING_AUTH_PATH.read_text(encoding="utf-8"))

    assert auth["authorization_transaction_id"] == "AION-240-V02RQ-0002"
    assert auth["parent_authorization_transaction_id"] == "AION-238-V02RQ-0001"
    assert auth["parent_evaluation_id"] == "AION-V02RQPE-001"
    assert auth["authorization_active"] is True
    assert auth["authorization_consumed"] is False
    assert auth["authorization_expired"] is False
    assert auth["authorization_reusable"] is False
    assert auth["implementation_task"] == "AION-241"
    assert auth["formal_closeout_task"] == "AION-242"
    assert program["active_v02_release_qualification_authorization_count"] == 1
    assert program["active_v02_release_qualification_authorization"] == "AION-240-V02RQ-0002"
    assert program["active_v02_release_qualification_task"] == "AION-241"
    assert program["v02_release_ready"] is False
    assert staging["authorization_transaction_id"] == "AION-240-V02RQ-0002"
    assert staging["staging_qualification_implemented"] is True
    assert not any(staging["prohibited_capabilities"].values())
