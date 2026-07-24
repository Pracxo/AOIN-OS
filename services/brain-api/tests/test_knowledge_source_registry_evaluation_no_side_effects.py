from __future__ import annotations

import os
import subprocess

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
        changed = {line.strip() for line in diff.stdout.splitlines() if line.strip()}
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
