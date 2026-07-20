"""AION-178 shadow redaction tests."""

from __future__ import annotations

import pytest

from aion_brain.self_improvement.shadow_redaction import (
    redact_shadow_summary,
    shadow_safe_fingerprint,
    validate_shadow_safe_value,
)


@pytest.mark.parametrize(
    "value",
    (
        "raw prompt",
        "hidden reasoning",
        "chain of thought",
        "raw user message",
        "credential",
        "access token",
        "cookie",
        "authorization header",
        "private key",
        "provider payload",
        "source patch",
        "raw diff",
        "personal data",
        "email address",
        "https://example.invalid",
        "www.example.invalid",
        "./run-this",
        {"nested": {"source_patch": "redacted value"}},
        {"ｐａｓｓｗｏｒｄ": "redacted value"},
    ),
)
def test_forbidden_shadow_material_is_rejected(value: object) -> None:
    with pytest.raises(ValueError) as exc:
        validate_shadow_safe_value(value)

    assert "redacted value" not in str(exc.value)


def test_safe_values_are_normalized_and_deterministic() -> None:
    left = {"Scope Label": ["Retrieval ranking", {"Metric": 0.4}]}
    right = {"scope label": ("Retrieval ranking", {"metric": 0.4})}

    assert validate_shadow_safe_value(left) == validate_shadow_safe_value(right)
    assert shadow_safe_fingerprint(left) == shadow_safe_fingerprint(right)


def test_redacted_summary_does_not_return_nested_raw_value() -> None:
    summary = redact_shadow_summary({"metric": "Retrieval precision trailed target."})

    assert summary.startswith("redacted shadow evidence ")
    assert "Retrieval precision" not in summary


def test_rejects_bytes_callables_exceptions_non_finite_and_recursive_values() -> None:
    values: list[object] = [b"abc", lambda: None, RuntimeError("boom"), float("inf")]
    recursive: list[object] = []
    recursive.append(recursive)
    values.append(recursive)

    for value in values:
        with pytest.raises(ValueError):
            validate_shadow_safe_value(value)
