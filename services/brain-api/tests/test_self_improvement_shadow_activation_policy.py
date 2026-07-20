"""AION-181 policy service tests."""

from __future__ import annotations

from pathlib import Path

from test_self_improvement_shadow_activation_contracts import NOW, make_context

from aion_brain.self_improvement.shadow_activation_policy import (
    InMemoryShadowActivationEvidenceAdapter,
    ShadowActivationPolicyService,
)


def test_policy_requires_approval_then_accepts_exact_external_approval(tmp_path: Path) -> None:
    ctx = make_context(tmp_path)
    adapter = InMemoryShadowActivationEvidenceAdapter(
        bundle=ctx["bundle"],
        expected_bundle_fingerprint=ctx["bundle_fingerprint"],
    )
    service = ShadowActivationPolicyService(
        evidence_adapter=adapter,
        repository_root=Path.cwd(),
        clock=lambda: NOW,
    )
    without_approval = service.evaluate(candidate=ctx["candidate"], request=ctx["request"])
    assert without_approval.decision_outcome == "approval_required"
    with_approval = service.evaluate(
        candidate=ctx["candidate"],
        request=ctx["request"],
        approval=ctx["approval"],
        current_facts=ctx["facts"],
        resource_usage=ctx["usage"],
        health_snapshot=ctx["snapshot"],
    )
    assert with_approval.decision_outcome == "simulation_ready"
    assert with_approval.shadow_activation_enabled is False
    assert with_approval.runtime_effect is False


def test_policy_rejects_invalid_approval(tmp_path: Path) -> None:
    ctx = make_context(tmp_path)
    payload = ctx["approval"].model_dump(mode="python")
    payload.pop("fingerprint", None)
    payload["candidate_commit_sha"] = "8" * 40
    approval = type(ctx["approval"])(**payload)
    adapter = InMemoryShadowActivationEvidenceAdapter(
        bundle=ctx["bundle"],
        expected_bundle_fingerprint=ctx["bundle_fingerprint"],
    )
    service = ShadowActivationPolicyService(
        evidence_adapter=adapter,
        repository_root=Path.cwd(),
        clock=lambda: NOW,
    )
    result = service.evaluate(
        candidate=ctx["candidate"],
        request=ctx["request"],
        approval=approval,
        current_facts=ctx["facts"],
    )
    assert result.decision_outcome == "approval_invalid"
