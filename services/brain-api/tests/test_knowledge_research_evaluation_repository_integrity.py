import importlib.util
import sys

from knowledge_source_registry_test_helpers import (
    PROHIBITED_SOURCE_RUNTIME_PATHS,
    ROOT,
    SOURCE_RUNTIME_PATHS,
    changed_files,
)

VALIDATOR = ROOT / "scripts/lib/knowledge_intelligence_verified_knowledge_authorization.py"


def _load_validator():
    sys.path.insert(0, str(ROOT / "scripts/lib"))
    spec = importlib.util.spec_from_file_location("verified_auth", VALIDATOR)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _aion217_source_paths() -> set[str]:
    validator = _load_validator()
    return set(validator.AION217_SOURCE_PATHS) | set(validator.AION217_OPTIONAL_SOURCE_PATHS)


def _assert_aion217_boundaries() -> None:
    for relative in (
        "services/brain-api/src/aion_brain/api/verified_knowledge.py",
        "services/brain-api/src/aion_brain/knowledge_intelligence/verified_knowledge_runtime.py",
        "services/brain-api/src/aion_brain/knowledge_intelligence/verified_knowledge_database.py",
        "services/brain-api/src/aion_brain/knowledge_intelligence/knowledge_promotion.py",
        "services/brain-api/src/aion_brain/knowledge_intelligence/cognitive_memory_writer.py",
        "services/brain-api/src/aion_brain/knowledge_intelligence/engagement_policy_updater.py",
    ):
        assert not (ROOT / relative).exists(), relative


def test_aion_206_does_not_add_runtime_source_or_release_surfaces():
    changed = changed_files()
    aion217_source_paths = _aion217_source_paths()
    for path in changed:
        assert not path.startswith(".github/workflows/"), path
        if path.startswith("services/brain-api/src/aion_brain/"):
            assert path in SOURCE_RUNTIME_PATHS or path in aion217_source_paths, path
        assert not path.startswith("packages/aion-sdk-python/src/"), path
        assert "migrations/" not in path, path
        assert not path.endswith((
            "package.json",
            "package-lock.json",
            "pnpm-lock.yaml",
            "yarn.lock",
            "poetry.lock",
            "uv.lock",
        )), path
    if changed & aion217_source_paths:
        changed_source_paths = {
            path
            for path in changed
            if path.startswith("services/brain-api/src/aion_brain/")
        }
        assert changed_source_paths <= set(SOURCE_RUNTIME_PATHS) | aion217_source_paths
        _assert_aion217_boundaries()
    for relative in PROHIBITED_SOURCE_RUNTIME_PATHS:
        assert not (ROOT / relative).exists(), relative
