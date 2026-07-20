"""AION-176 post-merge evidence reconciliation tests."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]

AION_175_PR = 86
AION_175_FEATURE_COMMIT = "50b498e9a47a95f82c26df718e11696b9ef741b3"
AION_175_MERGE_COMMIT = "00b71a6172fb136279716103b10dae986f455968"
AION_175_MERGED_AT = "2026-07-19T06:17:29Z"

CURRENT_STATE_SURFACES = (
    "docs/project-status.md",
    "docs/self-improvement/program-ledger.json",
    "examples/self-improvement/final-readiness-report.json",
    "docs/self-improvement/aion-176-post-merge-evidence-reconciliation.md",
)

STALE_AION_176_CURRENT_STATE_MARKERS = (
    "final_closeout_pre_merge_evidence",
    "pending_pr_merge",
    "AION-164 is the next implementation task",
    "Current milestone: AION-162",
    "replay protection absent",
    "AION-163-PA-0007 active",
    "Current authorization: AION-163",
)

SENSITIVE_EVIDENCE_MARKERS = (
    "BEGIN PRIVATE KEY",
    "END PRIVATE KEY",
    "raw prompt",
    "raw_prompt",
    "hidden reasoning",
    "raw diff",
    "source generation transcript",
)


def test_aion175_program_ledger_uses_merged_postmerge_evidence() -> None:
    ledger = _json("docs/self-improvement/program-ledger.json")
    records = ledger["records"]
    by_task = {record["task_id"]: record for record in records}

    assert len(by_task) == len(records)
    for task_number in range(164, 175):
        assert f"AION-{task_number}" in by_task

    aion175 = by_task["AION-175"]
    assert aion175["branch"] == "phase/self-improvement-final-closeout"
    assert aion175["pull_requests"] == [AION_175_PR]
    assert aion175["feature_commits"] == [AION_175_FEATURE_COMMIT]
    assert aion175["merge_commits"] == [AION_175_MERGE_COMMIT]
    assert aion175["ci_result"] == "pass"
    assert aion175["next_task"] == "operator_evaluation"
    assert (
        aion175["authorization_state"]
        == "final_closeout_complete_no_new_implementation_authorization"
    )
    assert aion175["runtime_state"] == "self_improvement_platform_implemented_disabled"
    assert aion175["completion_timestamp"] == AION_175_MERGED_AT
    assert aion175["pull_requests"]
    assert aion175["feature_commits"]
    assert aion175["merge_commits"]
    assert "pending" not in aion175["ci_result"]


def test_final_readiness_report_uses_merged_evidence_and_operator_stage() -> None:
    report = _json("examples/self-improvement/final-readiness-report.json")
    aion175 = _task(report["completed_tasks"], "AION-175")

    assert report["report_state"] == "final_closeout_merged_evidence"
    assert report["current_stage"] == "operator_evaluation"
    assert report["operator_evaluation_ready"] is True
    assert report["active_implementation_task"] == "none"
    assert report["active_self_improvement_implementation_authorization_count"] == 0
    assert aion175["status"] == "merged"
    assert aion175["pull_requests"] == [AION_175_PR]
    assert aion175["feature_commits"] == [AION_175_FEATURE_COMMIT]
    assert aion175["merge_commits"] == [AION_175_MERGE_COMMIT]
    assert aion175["ci_result"] == "pass"
    assert aion175["completion_timestamp"] == AION_175_MERGED_AT
    assert report["approval_state"]["new_implementation_authorization_created"] is False
    assert (
        "AION-175 PR and merge evidence are reported live after this branch merges"
        not in report["known_limitations"]
    )
    assert report["remaining_blockers"] == [
        "operator evaluation",
        "new explicit authorization before runtime self-improvement activation",
        "new exact approval before any source-changing proposal can merge",
        "new explicit authorization before production canary or deployment",
        "separate authorization before model-weight training",
    ]


def test_runtime_safety_flags_remain_disabled() -> None:
    report = _json("examples/self-improvement/final-readiness-report.json")
    runtime = report["runtime_state"]
    safety = report["security_gates"]

    assert runtime["self_improvement_platform_implemented"] is True
    assert runtime["self_improvement_platform_state"] == "implemented_disabled"
    for key in (
        "self_improvement_runtime_enabled",
        "self_rewrite_runtime_enabled",
        "automatic_merge_enabled",
        "production_canary_enabled",
        "production_deployment_enabled",
        "model_weight_training_enabled",
    ):
        assert runtime[key] is False

    for key in (
        "direct_main_writes",
        "self_approval",
        "automatic_merge",
        "production_deployment",
        "production_canary",
        "protected_core_ordinary_modification",
        "benchmark_self_modification",
        "holdout_disclosure",
        "test_weakening_allowed",
        "runtime_self_rewrite",
        "model_weight_training",
        "v02_tag_created",
        "v02_release_created",
    ):
        assert safety[key] is False
    assert safety["aion_v010_unchanged"] is True


def test_project_status_describes_current_shadow_authorization_state() -> None:
    text = _text("docs/project-status.md")
    current_text = _project_status_current_text()

    assert "AION-178 controlled self-improvement shadow plane is implemented." in text
    assert "Current stage: Shadow mode implemented and disabled" in text
    assert "`self_improvement_platform_state=implemented_disabled`" in text
    assert "`shadow_mode_implemented=true`" in text
    assert "`shadow_mode_implementation_state=implemented_operator_invoked_disabled`" in text
    assert "`shadow_mode_runtime_enabled=false`" in text
    assert "active self-improvement implementation authorization count: 1" in text
    assert "active implementation task: `AION-178`" in text
    assert "formal closeout task: `AION-179`" in text
    assert "v02_tag_created=false" in text
    assert "v02_release_created=false" in text
    for stale_marker in STALE_AION_176_CURRENT_STATE_MARKERS:
        assert stale_marker not in current_text


def test_current_state_surfaces_are_reconciled_and_safe() -> None:
    combined = "\n".join(
        _project_status_current_text() if surface == "docs/project-status.md" else _text(surface)
        for surface in CURRENT_STATE_SURFACES
    )
    for stale_marker in STALE_AION_176_CURRENT_STATE_MARKERS:
        assert stale_marker not in combined
    ledger = _json("docs/self-improvement/program-ledger.json")
    aion178 = _task(ledger["records"], "AION-178")
    assert aion178["ci_result"] == "pending"
    assert aion178["runtime_state"] == "shadow_mode_implemented_operator_invoked_disabled"
    for marker in SENSITIVE_EVIDENCE_MARKERS:
        assert marker not in combined
    assert re.search(r"sk-[A-Za-z0-9_-]{10,}", combined) is None
    assert re.search(r"gho_[A-Za-z0-9_]{10,}", combined) is None

    reconciliation = _text("docs/self-improvement/aion-176-post-merge-evidence-reconciliation.md")
    normalized = " ".join(reconciliation.split())
    assert "AION-175 is complete and merged." in normalized
    assert "The implementation program is complete." in normalized
    assert "No new implementation authorization is created." in normalized
    assert "No runtime activation occurs." in normalized
    assert "No architecture changes occur." in normalized
    assert "No AION-177 implementation task is created." in normalized
    assert "No v0.2 tag or release is created." in normalized


def test_no_v02_tag_exists_locally() -> None:
    tags = subprocess.run(
        ["git", "tag", "--list", "v0.2*", "aion-v0.2*"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert tags.stdout.strip() == ""


def _json(relative: str) -> dict[str, Any]:
    with (ROOT / relative).open() as handle:
        payload = json.load(handle)
    assert isinstance(payload, dict)
    return payload


def _text(relative: str) -> str:
    return (ROOT / relative).read_text()


def _project_status_current_text() -> str:
    text = _text("docs/project-status.md")
    marker = "## Historical Compatibility Markers"
    assert marker in text
    return text.split(marker, 1)[0]


def _task(records: list[dict[str, Any]], task_id: str) -> dict[str, Any]:
    matches = [record for record in records if record["task_id"] == task_id]
    assert len(matches) == 1
    return matches[0]
