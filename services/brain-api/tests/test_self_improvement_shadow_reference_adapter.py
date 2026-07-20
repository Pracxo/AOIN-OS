"""AION-178 shadow reference-adapter tests."""

from __future__ import annotations

import pytest
from test_self_improvement_shadow_contracts import make_reference, make_snapshot, safe_fingerprint

from aion_brain.self_improvement.shadow_observation import (
    DisabledShadowReferenceAdapter,
    InMemoryShadowReferenceAdapter,
    ShadowReferenceResolutionError,
)


def test_in_memory_adapter_resolves_exact_snapshot() -> None:
    reference = make_reference()
    snapshot = make_snapshot(reference=reference)
    adapter = InMemoryShadowReferenceAdapter((snapshot,))

    assert adapter.resolve(reference) == snapshot


def test_missing_and_mismatched_references_fail_closed() -> None:
    reference = make_reference()
    adapter = InMemoryShadowReferenceAdapter((make_snapshot(reference=reference),))

    with pytest.raises(ShadowReferenceResolutionError, match="shadow_reference_unavailable"):
        adapter.resolve(make_reference("missing-ref"))
    mismatched = make_reference(reference_fingerprint=safe_fingerprint("other"))
    with pytest.raises(
        ShadowReferenceResolutionError,
        match="shadow_reference_fingerprint_mismatch",
    ):
        adapter.resolve(mismatched)


def test_duplicate_snapshot_registration_is_rejected() -> None:
    snapshot = make_snapshot()

    with pytest.raises(ValueError):
        InMemoryShadowReferenceAdapter((snapshot, snapshot))


def test_disabled_adapter_has_no_fallback() -> None:
    with pytest.raises(ShadowReferenceResolutionError, match="shadow_reference_adapter_disabled"):
        DisabledShadowReferenceAdapter().resolve(make_reference())
