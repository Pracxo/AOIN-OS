"""AION-180 / AION-181 source-scope specification tests."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from aion243_release_candidate_scope import without_aion243_allowed_paths

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts/lib"))

from knowledge_intelligence_verified_knowledge_authorization import (  # noqa: E402
    AION217_OPTIONAL_SOURCE_PATHS,
    AION217_SOURCE_PATHS,
)
from self_improvement_governance import (  # noqa: E402
    SHADOW_ACTIVATION_ALLOWED_CREATE,
    SHADOW_ACTIVATION_ALLOWED_UPDATE,
)

AION217_ALLOWED_SOURCE_PATHS = set(AION217_SOURCE_PATHS) | set(
    AION217_OPTIONAL_SOURCE_PATHS
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


def _aion239_source_paths() -> set[str]:
    program = _json("docs/v02-release-qualification/program-ledger.json")
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
    adaptive = _json("docs/adaptive-intelligence/program-ledger.json")
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


def test_aion181_runtime_source_is_present_after_authorized_implementation() -> None:
    for relative in SHADOW_ACTIVATION_ALLOWED_CREATE:
        assert (ROOT / relative).is_file(), relative


def test_aion181_source_scope_is_exactly_recorded() -> None:
    record = _json("docs/self-improvement/authorization-ledger.json")["records"][-1]
    assert tuple(record["allowed_aion181_create_paths"]) == SHADOW_ACTIVATION_ALLOWED_CREATE
    assert tuple(record["allowed_aion181_update_paths"]) == SHADOW_ACTIVATION_ALLOWED_UPDATE
    assert "services/brain-api/src/aion_brain/self_improvement/shadow_mode.py" in record[
        "aion181_must_not_modify_paths"
    ]
    assert ".github/workflows/" in record["aion181_must_not_modify_paths"]
    assert "migrations/" in record["aion181_must_not_modify_paths"]


def test_aion181_branch_modifies_only_authorized_runtime_or_package_surfaces() -> None:
    changed = without_aion243_allowed_paths(
        _changed_files(
            ".github/workflows",
            "services/brain-api/src/aion_brain",
            "services/brain-api/pyproject.toml",
            "packages/aion-sdk-python/src",
            "migrations",
        )
    )
    aion239_source_paths = _aion239_source_paths()
    aion248_source_paths = _aion248_source_paths()
    assert (
        changed
        <= set(SHADOW_ACTIVATION_ALLOWED_CREATE)
        | AION217_ALLOWED_SOURCE_PATHS
        | aion239_source_paths
        | aion248_source_paths
    )
    if changed & AION217_ALLOWED_SOURCE_PATHS:
        _assert_aion217_runtime_surfaces_absent()
    if changed & aion239_source_paths:
        _assert_aion239_runtime_surfaces_absent()
    if changed & aion248_source_paths:
        _assert_aion248_runtime_surfaces_absent()


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


def _json(relative: str) -> dict[str, Any]:
    with (ROOT / relative).open() as handle:
        payload = json.load(handle)
    assert isinstance(payload, dict)
    return payload


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
    candidates = []
    github_base_ref = os.environ.get("GITHUB_BASE_REF")
    if github_base_ref:
        candidates.extend([f"origin/{github_base_ref}", github_base_ref])
    candidates.extend(["origin/main", "main"])

    for candidate in candidates:
        if not _git_ref_exists(candidate):
            continue
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


def _changed_files(*pathspecs: str) -> set[str]:
    base = _comparison_base()
    if base is None:
        return set()

    changed = subprocess.run(
        ["git", "diff", "--name-only", base, "HEAD", "--", *pathspecs],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return {line.strip() for line in changed.stdout.splitlines() if line.strip()}
