"""Feature registry tests."""

from __future__ import annotations

import pytest

from aion_brain.api_support.errors import AIONPolicyDeniedException
from aion_brain.versioning.features import FeatureRegistryService
from tests.versioning_fakes import SCOPE, AllowPolicy, DenyPolicy, repository


def test_seed_defaults_dry_run_lists_generic_features() -> None:
    service = FeatureRegistryService(repository(), AllowPolicy())

    result = service.seed_defaults(SCOPE, dry_run=True)

    assert result["dry_run"] is True
    assert "kernel.container" in result["feature_keys"]
    assert all("finance" not in key for key in result["feature_keys"])


def test_seed_defaults_apply_persists_features() -> None:
    repo = repository()
    service = FeatureRegistryService(repo, AllowPolicy())

    service.seed_defaults(SCOPE, dry_run=False)

    assert repo.get_feature("kernel.container") is not None


def test_deprecate_feature_marks_default_feature_deprecated() -> None:
    service = FeatureRegistryService(repository(), AllowPolicy())

    entry = service.deprecate_feature(
        "kernel.container",
        SCOPE,
        actor_id="tester",
        reason="covered by release policy",
    )

    assert entry.status == "deprecated"
    assert entry.deprecated_at is not None


def test_policy_deny_blocks_feature_create() -> None:
    service = FeatureRegistryService(repository(), DenyPolicy())

    with pytest.raises(AIONPolicyDeniedException):
        service.seed_defaults(SCOPE)
