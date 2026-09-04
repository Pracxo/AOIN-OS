"""AION-182 repository-boundary tests."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

from aion243_release_candidate_scope import without_aion243_allowed_paths

ROOT = Path(__file__).resolve().parents[3]
VALIDATOR = ROOT / "scripts/lib/knowledge_intelligence_verified_knowledge_authorization.py"


FORBIDDEN_DIFF_PATHS = (
    ".github/workflows",
    "services/brain-api/src/aion_brain",
    "services/brain-api/pyproject.toml",
    "packages/aion-sdk-python/src",
    "migrations",
)
AION248_SOURCE = {
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


def _load_validator():
    sys.path.insert(0, str(ROOT / "scripts/lib"))
    spec = importlib.util.spec_from_file_location("verified_auth", VALIDATOR)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _aion217_source_paths() -> set[str]:
    validator = _load_validator()
    return set(validator.AION217_SOURCE_PATHS) | set(validator.AION217_OPTIONAL_SOURCE_PATHS)


def _aion239_source_paths() -> set[str]:
    program = json.loads(
        (ROOT / "docs/v02-release-qualification/program-ledger.json").read_text()
    )
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
        return set(AION248_SOURCE)
    return set()


def _assert_aion217_runtime_surfaces_absent() -> None:
    for relative in (
        "services/brain-api/src/aion_brain/api/verified_knowledge.py",
        "services/brain-api/src/aion_brain/knowledge_intelligence/verified_knowledge_runtime.py",
        "services/brain-api/src/aion_brain/knowledge_intelligence/verified_knowledge_database.py",
        "services/brain-api/src/aion_brain/knowledge_intelligence/knowledge_promotion.py",
        "services/brain-api/src/aion_brain/knowledge_intelligence/cognitive_memory_writer.py",
        "services/brain-api/src/aion_brain/knowledge_intelligence/engagement_policy_updater.py",
    ):
        assert not (ROOT / relative).exists(), relative


def _assert_aion239_runtime_surfaces_absent() -> None:
    assert not (
        ROOT / "services/brain-api/src/aion_brain/api/v02_release_qualification.py"
    ).exists()


def _assert_aion248_runtime_surfaces_absent() -> None:
    assert not (
        ROOT / "services/brain-api/src/aion_brain/api/live_provider_pilot.py"
    ).exists()


def _git_ref_exists(ref: str) -> bool:
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
    github_base_ref = os.environ.get("GITHUB_BASE_REF")
    if github_base_ref:
        candidates.extend((f"origin/{github_base_ref}", github_base_ref))
    candidates.extend(("origin/main", "main"))
    for candidate in candidates:
        if _git_ref_exists(candidate):
            merge_base = subprocess.run(
                ["git", "merge-base", "HEAD", candidate],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            if merge_base.returncode == 0 and merge_base.stdout.strip():
                return merge_base.stdout.strip()
    if _git_ref_exists("HEAD~1"):
        return "HEAD~1"
    return None


def _changed_files() -> set[str]:
    base = _comparison_base()
    if base is None:
        return set()
    diff = subprocess.run(
        ["git", "diff", "--name-only", base, "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return {line.strip() for line in diff.stdout.splitlines() if line.strip()}


def test_aion_182_does_not_modify_protected_runtime_paths() -> None:
    changed = without_aion243_allowed_paths(_changed_files())
    aion217_paths = _aion217_source_paths()
    aion239_paths = _aion239_source_paths()
    aion248_paths = _aion248_source_paths()
    blocked = [
        path
        for path in changed
        if any(
            path == prefix or path.startswith(f"{prefix}/")
            for prefix in FORBIDDEN_DIFF_PATHS
        )
        and path not in aion217_paths
        and path not in aion239_paths
        and path not in aion248_paths
    ]
    if changed & aion217_paths:
        _assert_aion217_runtime_surfaces_absent()
    if changed & aion239_paths:
        _assert_aion239_runtime_surfaces_absent()
    if changed & aion248_paths:
        _assert_aion248_runtime_surfaces_absent()
    assert blocked == []


def test_evaluation_report_records_repository_unchanged() -> None:
    report = json.loads(
        (
            ROOT
            / (
                "examples/self-improvement/"
                "shadow-activation-control-plane-operator-evaluation-report.json"
            )
        ).read_text()
    )

    assert report["repository_digest_before"] == report["repository_digest_after"]
    assert report["repository_integrity"]["canonical_repository_untouched_by_evaluation"] is True
    assert report["repository_integrity"]["control_plane_real_pull_request_created"] is False


def test_release_tags_remain_unchanged() -> None:
    tag = subprocess.run(
        ["git", "rev-parse", "aion-v0.1.0^{}"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    v02_tags = subprocess.run(
        ["git", "tag", "--list", "v0.2*", "aion-v0.2*"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    assert tag == "105fe29348160a2218ac095cfffadcb6f234421f"
    assert set(v02_tags.splitlines()) <= {"aion-v0.2.0-rc.1"}
