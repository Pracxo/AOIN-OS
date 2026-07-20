"""AION-178 runtime-influence boundary tests."""

from __future__ import annotations

from pathlib import Path

from test_self_improvement_shadow_contracts import ROOT, make_bundle


def test_bundle_flags_have_no_runtime_influence_or_side_effects() -> None:
    bundle = make_bundle()

    assert bundle.shadow_mode_runtime_enabled is False
    assert bundle.implementation_authorization_created is False
    assert bundle.approval_created is False
    assert bundle.source_modified is False
    assert bundle.git_mutated is False
    assert bundle.pull_request_created is False
    assert bundle.merged is False
    assert bundle.active_learning_promoted is False
    assert bundle.runtime_effect is False
    assert bundle.diagnostics.background_loop is False
    assert bundle.diagnostics.production_event_subscription is False


def test_shadow_plane_is_not_registered_in_runtime_surfaces() -> None:
    protected_paths = (
        ROOT / "services/brain-api/src/aion_brain/kernel",
        ROOT / "services/brain-api/src/aion_brain/api",
        ROOT / "services/brain-api/src/aion_brain/api_support",
        ROOT / "services/brain-api/src/aion_brain/config.py",
    )
    for path in protected_paths:
        if path.is_file():
            text = path.read_text()
        else:
            text = "\n".join(item.read_text() for item in Path(path).rglob("*.py"))
        assert "shadow_mode" not in text
        assert "ControlledShadowModeRunner" not in text
