"""AION-178 shadow retention tests."""

from __future__ import annotations

from datetime import timedelta

import pytest
from pydantic import ValidationError
from test_self_improvement_shadow_contracts import NOW, make_bundle, make_manifest

from aion_brain.self_improvement.shadow_mode import EphemeralShadowStore, default_shadow_expires_at


def test_default_and_maximum_retention_are_enforced() -> None:
    assert default_shadow_expires_at(NOW) == NOW + timedelta(days=1)
    assert make_manifest(retention_seconds=604800).retention_seconds == 604800
    with pytest.raises(ValidationError):
        make_manifest(retention_seconds=604801)


def test_ephemeral_store_has_explicit_purge_only() -> None:
    store = EphemeralShadowStore()
    bundle = make_bundle()
    store.put(bundle)

    assert store.list_run_ids() == (bundle.run_id,)
    assert store.get(bundle.run_id) == bundle
    assert store.list_run_ids() == (bundle.run_id,)
    assert store.purge_expired(NOW) == ()
    assert store.purge_expired(bundle.expires_at + timedelta(seconds=1)) == (bundle.run_id,)
    assert store.get(bundle.run_id) is None


def test_duplicate_run_ids_are_rejected() -> None:
    store = EphemeralShadowStore()
    bundle = make_bundle()
    store.put(bundle)

    with pytest.raises(ValueError):
        store.put(bundle)
