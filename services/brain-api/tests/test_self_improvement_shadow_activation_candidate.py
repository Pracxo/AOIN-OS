"""AION-181 activation candidate validation tests."""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError
from test_self_improvement_shadow_activation_contracts import NOW, make_context

from aion_brain.contracts.self_improvement_shadow_activation import (
    ShadowActivationCandidate,
    validate_activation_candidate,
)


def test_candidate_lineage_and_risk_levels(tmp_path: Path) -> None:
    ctx = make_context(tmp_path)
    assert validate_activation_candidate(ctx["candidate"], now=NOW).valid is True
    payload = ctx["candidate"].model_dump(mode="python")
    payload.pop("fingerprint", None)
    payload["risk_level"] = "critical"
    assert ShadowActivationCandidate(**payload).risk_level == "critical"
    payload["risk_level"] = "medium"
    with pytest.raises(ValidationError):
        ShadowActivationCandidate(**payload)


def test_candidate_expiry_lifetime_and_flags(tmp_path: Path) -> None:
    payload = make_context(tmp_path)["candidate"].model_dump(mode="python")
    payload.pop("fingerprint", None)
    payload["expires_at"] = NOW + timedelta(days=8)
    with pytest.raises(ValidationError):
        ShadowActivationCandidate(**payload)

    payload = make_context(tmp_path)["candidate"].model_dump(mode="python")
    payload.pop("fingerprint", None)
    candidate = ShadowActivationCandidate(**payload)
    assert validate_activation_candidate(candidate, now=NOW + timedelta(days=2)).expired is True

    payload["shadow_activation_enabled"] = True
    with pytest.raises(ValidationError):
        ShadowActivationCandidate(**payload)


def test_changed_binding_changes_fingerprint(tmp_path: Path) -> None:
    payload = make_context(tmp_path)["candidate"].model_dump(mode="python")
    payload.pop("fingerprint", None)
    original = ShadowActivationCandidate(**payload)
    payload["operator_scope_fingerprint"] = "9" * 64
    changed = ShadowActivationCandidate(**payload)
    assert changed.fingerprint != original.fingerprint
