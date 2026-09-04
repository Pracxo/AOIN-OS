from __future__ import annotations

import json
import os
import subprocess

from aion243_release_candidate_scope import without_aion243_allowed_paths
from knowledge_source_registry_test_helpers import ROOT, read_json

PROTECTED_PATHS = (
    ".github/workflows",
    "services/brain-api/src/aion_brain",
    "services/brain-api/pyproject.toml",
    "packages/aion-sdk-python/src",
    "migrations",
)
CLAIM_GRAPH_SOURCE_PATHS = {
    "services/brain-api/src/aion_brain/contracts/knowledge_claim_graph.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/__init__.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph_evidence.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph_index.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph_integrity.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph_repository.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph_temporal.py",
}
AION217_SOURCE_PATHS = {
    "services/brain-api/src/aion_brain/contracts/knowledge_verified_memory.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/__init__.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/engagement_learning_candidates.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/engagement_signal_policy.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/verified_knowledge_candidates.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/verified_knowledge_evidence.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/verified_knowledge_integrity.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/verified_knowledge_lineage.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/verified_knowledge_memory.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/verified_knowledge_revalidation.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/verified_knowledge_versioning.py",
}
AION248_SOURCE_PATHS = {
    "services/brain-api/src/aion_brain/contracts/live_provider_pilot.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/__init__.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/authorization.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/component_binding.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/provider_selection.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/operator_approval.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/credential_boundary.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/endpoint_policy.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/request_projection.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/response_projection.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/usage_budget.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/retention_policy.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/transport.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/openai_responses_adapter.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/trust.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/redaction.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/replay.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/audit.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/observability.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/integrity.py",
    "services/brain-api/src/aion_brain/live_provider_pilot/evidence.py",
}
AION239_PROGRAM_LEDGER = "docs/v02-release-qualification/program-ledger.json"
CLAIM_GRAPH_FORBIDDEN_RUNTIME_PATHS = (
    "services/brain-api/src/aion_brain/api/claim_graph.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph_runtime.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/claim_truth.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/claim_confidence.py",
)


def _ref_exists(ref: str) -> bool:
    return (
        subprocess.run(
            ["git", "rev-parse", "--verify", "--quiet", ref],
            cwd=ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        ).returncode
        == 0
    )


def _comparison_base() -> str | None:
    candidates: list[str] = []
    github_base = os.environ.get("GITHUB_BASE_REF")
    if github_base:
        candidates.extend([f"origin/{github_base}", github_base])
    candidates.extend(["origin/main", "main"])
    for candidate in candidates:
        if _ref_exists(candidate):
            merge_base = subprocess.run(
                ["git", "merge-base", "HEAD", candidate],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            if merge_base.returncode == 0 and merge_base.stdout.strip():
                return merge_base.stdout.strip()
    return "HEAD~1" if _ref_exists("HEAD~1") else None


def _claim_graph_source_present() -> bool:
    return any((ROOT / relative).exists() for relative in CLAIM_GRAPH_SOURCE_PATHS)


def _claim_graph_context(changed: set[str]) -> bool:
    if any(
        os.environ.get(key) == "1"
        for key in (
            "AION_CLAIM_GRAPH_IMPLEMENTATION_CONTEXT",
            "AION_AGGREGATE_GATE_RUNNING",
            "AION_CHECK_RUNNING",
        )
    ):
        return True
    return bool(changed and changed <= CLAIM_GRAPH_SOURCE_PATHS) or _claim_graph_source_present()


def _assert_claim_graph_boundaries(changed: set[str]) -> None:
    assert changed <= CLAIM_GRAPH_SOURCE_PATHS
    for relative in CLAIM_GRAPH_FORBIDDEN_RUNTIME_PATHS:
        assert not (ROOT / relative).exists(), relative


def _assert_aion217_boundaries(changed: set[str]) -> None:
    assert changed <= AION217_SOURCE_PATHS
    for relative in CLAIM_GRAPH_FORBIDDEN_RUNTIME_PATHS:
        assert not (ROOT / relative).exists(), relative
    for relative in (
        "services/brain-api/src/aion_brain/api/verified_knowledge.py",
        "services/brain-api/src/aion_brain/knowledge_intelligence/verified_knowledge_runtime.py",
        "services/brain-api/src/aion_brain/knowledge_intelligence/verified_knowledge_database.py",
        "services/brain-api/src/aion_brain/knowledge_intelligence/knowledge_promotion.py",
        "services/brain-api/src/aion_brain/knowledge_intelligence/cognitive_memory_writer.py",
        "services/brain-api/src/aion_brain/knowledge_intelligence/engagement_policy_updater.py",
    ):
        assert not (ROOT / relative).exists(), relative


def _aion248_source_paths() -> set[str]:
    adaptive = json.loads(
        (ROOT / "docs/adaptive-intelligence/program-ledger.json").read_text()
    )
    record = adaptive.get("aion_248_record", {})
    if (
        isinstance(record, dict)
        and adaptive.get("live_provider_pilot_authorized") is True
        and adaptive.get("active_adaptive_intelligence_authorization")
        == "AION-247-AI-0002"
        and adaptive.get("active_adaptive_intelligence_task") == "AION-248"
        and adaptive.get("formal_closeout_task") == "AION-249"
        and record.get("task_id") == "AION-248"
        and record.get("branch") == "phase/v03-openai-live-provider-pilot"
        and record.get("authorization_transaction") == "AION-247-AI-0002"
        and record.get("next_task") == "AION-249"
        and record.get("runtime_state")
        in {
            "single_openai_responses_api_live_provider_pilot_implementation_ready_live_execution_pending",
            "single_openai_responses_api_synthetic_live_provider_pilot_complete",
        }
    ):
        return set(AION248_SOURCE_PATHS)
    return set()


def _assert_aion248_boundaries(changed: set[str]) -> None:
    assert changed <= _aion248_source_paths()
    assert not (
        ROOT / "services/brain-api/src/aion_brain/api/live_provider_pilot.py"
    ).exists()


def _aion239_source_paths() -> set[str]:
    program = json.loads((ROOT / AION239_PROGRAM_LEDGER).read_text())
    if (
        program.get("active_v02_release_qualification_task") not in {"AION-239", "AION-241"}
        or program.get("v02_release_qualification_foundation_implemented") is not True
        or program.get("foundation_runtime_state")
        != "implemented_disabled_design_only_local_simulation"
    ):
        return set()
    source_scope = program.get("implemented_source_scope")
    assert isinstance(source_scope, list)
    return {str(path) for path in source_scope}


def _assert_aion239_boundaries(changed: set[str]) -> None:
    assert changed <= _aion239_source_paths()
    assert not (
        ROOT / "services/brain-api/src/aion_brain/api/v02_release_qualification.py"
    ).exists()


def test_aion_208_does_not_change_runtime_or_package_surfaces():
    base = _comparison_base()
    changed: set[str] = set()
    if base:
        diff = subprocess.run(
            ["git", "diff", "--name-only", base, "HEAD", "--", *PROTECTED_PATHS],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        changed = without_aion243_allowed_paths(
            {line.strip() for line in diff.stdout.splitlines() if line.strip()}
        )
    if changed and changed <= AION217_SOURCE_PATHS:
        _assert_aion217_boundaries(changed)
        return
    aion239_source_paths = _aion239_source_paths()
    if changed and changed <= aion239_source_paths:
        _assert_aion239_boundaries(changed)
        return
    if changed and changed <= _aion248_source_paths():
        _assert_aion248_boundaries(changed)
        return
    if _claim_graph_context(changed):
        _assert_claim_graph_boundaries(changed)
        return
    assert changed == set()
    for relative in (
        "services/brain-api/src/aion_brain/contracts/knowledge_claim_graph.py",
        "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph.py",
        "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph_repository.py",
        "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph_index.py",
        "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph_integrity.py",
        "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph_temporal.py",
        "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph_evidence.py",
    ):
        assert not (ROOT / relative).exists(), relative


def test_evaluation_report_records_no_runtime_effects():
    report = read_json(
        "examples/knowledge-intelligence/source-registry-operator-evaluation-report.json"
    )
    assert report["source_modified"] is False
    assert report["git_mutated"] is False
    assert report["pull_request_created"] is False
    assert report["approval_created"] is False
    assert report["merged"] is False
    assert report["runtime_effect"] is False
