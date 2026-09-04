"""Immutable model tag/digest binding for local provider requests."""
from __future__ import annotations

MODEL_TAG = "gpt-oss:20b"


def require_model_binding(*, model_tag: str, model_digest: str, frozen_digest: str) -> None:
    if model_tag != MODEL_TAG or not model_digest or model_digest != frozen_digest:
        raise ValueError("local model tag or digest does not match the frozen binding")
