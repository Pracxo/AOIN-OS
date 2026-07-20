"""AION-181 local evidence adapter tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from test_self_improvement_shadow_activation_contracts import make_context

from aion_brain.production_auth.canonical import canonical_json_text
from aion_brain.self_improvement.shadow_activation_policy import (
    ExplicitLocalShadowEvidenceBundleAdapter,
    InMemoryShadowActivationEvidenceAdapter,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_in_memory_and_local_exact_bundle_are_accepted(tmp_path: Path) -> None:
    ctx = make_context(tmp_path)
    assert InMemoryShadowActivationEvidenceAdapter(
        bundle=ctx["bundle"],
        expected_bundle_fingerprint=ctx["bundle_fingerprint"],
    ).load_evidence_bundle() == ctx["bundle"]

    evidence_path = tmp_path / "bundle.json"
    evidence_path.write_text(
        canonical_json_text(ctx["bundle"].model_dump(mode="python")),
        encoding="utf-8",
    )
    loaded = ExplicitLocalShadowEvidenceBundleAdapter(
        path=evidence_path,
        repository_root=REPO_ROOT,
        expected_bundle_fingerprint=ctx["bundle_fingerprint"],
    ).load_evidence_bundle()
    assert loaded.run_id == "shadow-run-181"


def test_local_adapter_rejects_bad_paths_and_payloads(tmp_path: Path) -> None:
    ctx = make_context(tmp_path)
    with pytest.raises(ValueError):
        ExplicitLocalShadowEvidenceBundleAdapter(
            path=Path("relative.json"),
            repository_root=REPO_ROOT,
            expected_bundle_fingerprint=ctx["bundle_fingerprint"],
        ).load_evidence_bundle()
    with pytest.raises(ValueError):
        ExplicitLocalShadowEvidenceBundleAdapter(
            path=REPO_ROOT / "README.md",
            repository_root=REPO_ROOT,
            expected_bundle_fingerprint=ctx["bundle_fingerprint"],
        ).load_evidence_bundle()
    hidden = tmp_path / ".hidden.json"
    hidden.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError):
        ExplicitLocalShadowEvidenceBundleAdapter(
            path=hidden,
            repository_root=REPO_ROOT,
            expected_bundle_fingerprint=ctx["bundle_fingerprint"],
        ).load_evidence_bundle()
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"observations": ["raw prompt"]}), encoding="utf-8")
    with pytest.raises(ValueError):
        ExplicitLocalShadowEvidenceBundleAdapter(
            path=bad,
            repository_root=REPO_ROOT,
            expected_bundle_fingerprint=ctx["bundle_fingerprint"],
        ).load_evidence_bundle()
    invalid = tmp_path / "invalid.json"
    invalid.write_bytes(b"\xff")
    with pytest.raises(ValueError):
        ExplicitLocalShadowEvidenceBundleAdapter(
            path=invalid,
            repository_root=REPO_ROOT,
            expected_bundle_fingerprint=ctx["bundle_fingerprint"],
        ).load_evidence_bundle()


def test_local_adapter_rejects_mismatch_directory_symlink_and_oversize(tmp_path: Path) -> None:
    ctx = make_context(tmp_path)
    evidence_path = tmp_path / "bundle.json"
    evidence_path.write_text(
        canonical_json_text(ctx["bundle"].model_dump(mode="python")),
        encoding="utf-8",
    )
    with pytest.raises(ValueError):
        ExplicitLocalShadowEvidenceBundleAdapter(
            path=evidence_path,
            repository_root=REPO_ROOT,
            expected_bundle_fingerprint="9" * 64,
        ).load_evidence_bundle()
    with pytest.raises(ValueError):
        ExplicitLocalShadowEvidenceBundleAdapter(
            path=tmp_path,
            repository_root=REPO_ROOT,
            expected_bundle_fingerprint=ctx["bundle_fingerprint"],
        ).load_evidence_bundle()
    link = tmp_path / "link.json"
    link.symlink_to(evidence_path)
    with pytest.raises(ValueError):
        ExplicitLocalShadowEvidenceBundleAdapter(
            path=link,
            repository_root=REPO_ROOT,
            expected_bundle_fingerprint=ctx["bundle_fingerprint"],
        ).load_evidence_bundle()
    with pytest.raises(ValueError):
        ExplicitLocalShadowEvidenceBundleAdapter(
            path=evidence_path,
            repository_root=REPO_ROOT,
            expected_bundle_fingerprint=ctx["bundle_fingerprint"],
            maximum_bytes=1,
        ).load_evidence_bundle()
