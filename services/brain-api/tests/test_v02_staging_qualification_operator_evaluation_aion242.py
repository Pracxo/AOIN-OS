from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from aion_brain.contracts import v02_staging_qualification as c

REPO_ROOT = Path(__file__).resolve().parents[3]
HARNESS_PATH = (
    REPO_ROOT / "scripts/lib/v02_staging_qualification_operator_evaluation.py"
)
REPORT_PATH = (
    REPO_ROOT
    / "examples/v02-release-qualification/staging-qualification-operator-evaluation-report.json"
)
AION243_EVIDENCE_PATH = (
    REPO_ROOT
    / "examples/v02-release-qualification/v02-release-candidate-artifact-build-evidence.json"
)


def load_harness():
    spec = importlib.util.spec_from_file_location("aion242_eval", HARNESS_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_json(relative: str) -> dict:
    return json.loads((REPO_ROOT / relative).read_text(encoding="utf-8"))


def test_harness_executes_exact_twenty_eight_hard_gates(tmp_path):
    harness = load_harness()
    report = harness.evaluate(
        repo_root=REPO_ROOT,
        evaluation_id=harness.EVALUATION_ID,
        implementation_main_commit=harness.IMPLEMENTATION_MERGE_COMMIT,
        evaluation_base_commit="test-evaluation-base",
        pilot_evidence_path=REPO_ROOT
        / "examples/v02-release-qualification/"
        "v02-controlled-isolated-staging-pilot-evidence.json",
        temporary_output_directory=tmp_path,
    )

    harness.validate_report(report)
    assert report["decision"] == harness.PASS_DECISION
    assert report["evaluation_passed"] is True
    assert report["scenario_count"] == 28
    assert report["hard_gate_count"] == 28
    assert report["scenario_ids"] == list(harness.SCENARIO_IDS)
    assert [item["scenario_id"] for item in report["scenario_results"]] == list(
        harness.SCENARIO_IDS
    )
    assert all(item["hard_gate"] is True for item in report["scenario_results"])
    assert all(item["passed"] is True for item in report["hard_gate_results"])


def test_aion_241_pilot_evidence_is_exact_and_recomputed():
    harness = load_harness()
    pilot = load_json(
        "examples/v02-release-qualification/"
        "v02-controlled-isolated-staging-pilot-evidence.json"
    )

    assert pilot["pilot_id"] == c.PILOT_ID
    assert pilot["authorization_id"] == "AION-240-V02RQ-0002"
    assert pilot["implementation_commit"] == harness.IMPLEMENTATION_COMMIT
    assert pilot["source_snapshot_commit"] == harness.IMPLEMENTATION_COMMIT
    assert pilot["report_fingerprint"] == harness.EXPECTED_PILOT_FINGERPRINT
    assert harness.pilot_fingerprint_matches(c, pilot)
    assert pilot["base_image_id"] == harness.EXPECTED_BASE_IMAGE_ID
    assert pilot["dependency_image_ids"] == harness.EXPECTED_DEPENDENCY_IMAGE_IDS
    assert pilot["dependency_image_fingerprints"] == (
        harness.EXPECTED_DEPENDENCY_IMAGE_FINGERPRINTS
    )
    assert pilot["staging_artifact_fingerprints"] == list(
        harness.EXPECTED_STAGING_ARTIFACT_FINGERPRINTS
    )
    assert pilot["sbom_component_count"] == 61
    assert pilot["byte_for_byte_reproducibility_confirmed"] is False
    assert pilot["prohibited_effect_counters"] == harness.EXPECTED_PROHIBITED_COUNTERS


def test_source_scope_authorization_and_release_boundary_are_strict():
    harness = load_harness()
    program = load_json("docs/v02-release-qualification/program-ledger.json")
    auth = load_json("docs/v02-release-qualification/authorization-ledger.json")
    source = harness.source_scope_state(REPO_ROOT, c)
    auth_state = harness.authorization_lineage_state(program, auth)

    assert source["missing_source_scope"] == []
    assert source["runtime_source_scope_exact"] is True
    assert source["prohibited_source_present"] == []
    final_rc1_published = (
        program["program_state"]
        == "v02_release_qualification_program_complete_rc1_prerelease_published"
    )
    if program["active_v02_release_qualification_task"] in {
        "AION-243",
        "AION-244",
    } or final_rc1_published:
        assert set(source["future_aion_243_source_present"]) == set(
            harness.FUTURE_AION243_SOURCE_SCOPE
        )
        assert source["future_aion_243_runner_present"] is True
    else:
        assert source["future_aion_243_source_present"] == []
        assert source["future_aion_243_runner_present"] is False
    assert auth_state["lineage_valid"] is True
    assert auth_state["sole_active_authorization_exact"] is True
    assert program["v02_release_ready"] is final_rc1_published
    assert program["v02_tag_created"] is final_rc1_published
    assert program["v02_release_created"] is final_rc1_published
    if final_rc1_published:
        assert program["v02_tag_name"] == "aion-v0.2.0-rc.1"
        assert program["v02_stable_tag_created"] is False
        assert program["v02_stable_release_created"] is False


def test_committed_report_when_present_is_schema_valid_and_zero_effect():
    if not REPORT_PATH.exists():
        return

    harness = load_harness()
    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    harness.validate_report(report)

    assert report["evaluation_id"] == "AION-V02RQPE-002"
    assert report["decision"] == harness.PASS_DECISION
    assert report["synthetic"] is False
    assert report["read_only"] is True
    assert report["redacted"] is True
    assert report["repository_unchanged"] is True
    for key in harness.REPORT_ZERO_EFFECT_FIELDS:
        assert report[key] == 0


def test_release_candidate_authorization_when_present_stays_non_release():
    auth = load_json("docs/v02-release-qualification/authorization-ledger.json")
    if auth["authorization_transaction_id"] != "AION-242-V02RQ-0003":
        return

    harness = load_harness()
    program = load_json("docs/v02-release-qualification/program-ledger.json")

    assert auth["parent_authorization_transaction_id"] == "AION-240-V02RQ-0002"
    assert auth["parent_evaluation_id"] == "AION-V02RQPE-002"
    assert auth["parent_evaluation_decision"] == harness.PASS_DECISION
    assert auth["implementation_task"] == "AION-243"
    assert auth["formal_closeout_task"] == "AION-244"
    assert auth["authorization_active"] is True
    assert auth["authorization_consumed"] is False
    assert auth["approved_capabilities"] == dict.fromkeys(
        harness.APPROVED_AION243_CAPABILITIES, True
    )
    assert auth["prohibited_capabilities"] == dict.fromkeys(
        harness.PROHIBITED_AION243_CAPABILITIES, False
    )
    assert auth["resource_limits"] == {
        **harness.POSITIVE_AION243_LIMITS,
        **dict.fromkeys(harness.ZERO_AION243_LIMITS, 0),
    }
    assert program["active_v02_release_qualification_authorization"] == (
        "AION-242-V02RQ-0003"
    )
    assert program["active_v02_release_qualification_task"] == "AION-243"
    assert program["release_candidate_artifact_build_authorized"] is True
    if AION243_EVIDENCE_PATH.exists():
        assert program["release_candidate_artifact_build_implemented"] is True
        assert program["release_candidate_created"] is True
        assert program["candidate_bundle_retained"] is True
        assert program["candidate_local_image_retained"] is True
    else:
        assert program["release_candidate_artifact_build_implemented"] is False
        assert program["release_candidate_created"] is False
    assert program["release_candidate_published"] is False
    assert program["production_deployment_enabled"] is False
    assert program["v02_release_ready"] is False
