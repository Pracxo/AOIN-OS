"""AION-181 activation request boundary tests."""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError
from test_self_improvement_shadow_activation_contracts import NOW, make_context

from aion_brain.contracts.self_improvement_shadow_activation import ShadowActivationRequest


def test_request_accepts_only_local_offline_synthetic_or_redacted(tmp_path: Path) -> None:
    payload = make_context(tmp_path)["request"].model_dump(mode="python")
    payload.pop("fingerprint", None)
    assert (
        ShadowActivationRequest(**payload).requested_environment
        == "local_offline_operator_evaluation"
    )
    payload["data_classification"] = "redacted"
    assert ShadowActivationRequest(**payload).data_classification == "redacted"
    for environment in ("production", "network_connected", "user_traffic", "kernel_runtime"):
        bad = dict(payload, requested_environment=environment)
        with pytest.raises(ValidationError):
            ShadowActivationRequest(**bad)
    bad = dict(payload, data_classification="production")
    with pytest.raises(ValidationError):
        ShadowActivationRequest(**bad)


def test_request_rejects_unknown_adapter_window_runs_and_runtime(tmp_path: Path) -> None:
    payload = make_context(tmp_path)["request"].model_dump(mode="python")
    payload.pop("fingerprint", None)
    with pytest.raises(ValidationError):
        ShadowActivationRequest(**dict(payload, approved_adapter_types=("http_adapter",)))
    with pytest.raises(ValidationError):
        ShadowActivationRequest(**dict(payload, maximum_runs=11))
    with pytest.raises(ValidationError):
        ShadowActivationRequest(
            **dict(payload, activation_window_end=NOW + timedelta(seconds=3601))
        )
    with pytest.raises(ValidationError):
        ShadowActivationRequest(**dict(payload, runtime_activation_requested=True))
    with pytest.raises(ValidationError):
        ShadowActivationRequest(**dict(payload, operator_review_required=False))
