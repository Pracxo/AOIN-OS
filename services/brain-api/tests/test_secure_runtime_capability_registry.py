from __future__ import annotations

import pytest

from aion_brain.contracts.secure_runtime import CLOSED_CAPABILITY_REGISTRY, capability_manifest_for


def test_closed_capability_registry_is_simulation_only() -> None:
    assert set(CLOSED_CAPABILITY_REGISTRY) == {
        "secure_runtime.health.read",
        "secure_runtime.observability.read",
        "secure_runtime.audit.read",
        "secure_runtime.fixture.replay",
        "brain.think.simulate",
    }
    for manifest in CLOSED_CAPABILITY_REGISTRY.values():
        assert manifest.simulation_only is True
        assert manifest.actual_execution_available is False
        assert manifest.production_effect is False
        assert manifest.side_effect_class == "none"


def test_unknown_capability_is_rejected() -> None:
    with pytest.raises(ValueError, match="unknown"):
        capability_manifest_for("tool.execute")
