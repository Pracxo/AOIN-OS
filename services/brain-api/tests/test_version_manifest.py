"""Version manifest service tests."""

from __future__ import annotations

import pytest

from aion_brain.api_support.errors import AIONConflictException
from aion_brain.versioning.features import FeatureRegistryService
from aion_brain.versioning.manifest import VersionManifestService, stable_hash
from tests.versioning_fakes import SCOPE, AllowPolicy, freeze_gate_run, repository, settings


def test_create_manifest_contains_feature_flags_and_contract_hash() -> None:
    repo = repository()
    features = FeatureRegistryService(repo, AllowPolicy())
    service = VersionManifestService(repo, features, AllowPolicy(), settings=settings())

    manifest = service.create_manifest("0.1.0", "tester", SCOPE)

    assert manifest.version == "0.1.0"
    assert manifest.feature_flags["kernel.container"] is True
    assert manifest.contract_hash


def test_stable_hash_is_deterministic() -> None:
    assert stable_hash({"b": 2, "a": 1}) == stable_hash({"a": 1, "b": 2})


def test_freeze_manifest_requires_passed_freeze_gate() -> None:
    repo = repository()
    features = FeatureRegistryService(repo, AllowPolicy())
    service = VersionManifestService(repo, features, AllowPolicy(), settings=settings())
    service.create_manifest("0.1.0", "tester", SCOPE)

    with pytest.raises(AIONConflictException):
        service.freeze_manifest("0.1.0", "tester", "not ready", SCOPE)


def test_freeze_manifest_marks_manifest_frozen_after_gate() -> None:
    repo = repository()
    features = FeatureRegistryService(repo, AllowPolicy())
    service = VersionManifestService(repo, features, AllowPolicy(), settings=settings())
    service.create_manifest("0.1.0", "tester", SCOPE)
    repo.save_freeze_gate(freeze_gate_run("passed"))

    manifest = service.freeze_manifest("0.1.0", "tester", "ready", SCOPE)

    assert manifest.status == "frozen"
