import importlib.util
import json
import sys

from aion243_release_candidate_scope import is_aion243_allowed_path
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


def _aion239_source_paths() -> set[str]:
    program = json.loads(
        (ROOT / "docs/v02-release-qualification/program-ledger.json").read_text()
    )
    if (
        program.get("active_v02_release_qualification_task") not in {"AION-239", "AION-241"}
        or program.get("v02_release_qualification_foundation_implemented") is not True
        or program.get("foundation_runtime_state")
        != "implemented_disabled_design_only_local_simulation"
    ):
        return set()
    source_scope = program.get("implemented_source_scope")
    assert isinstance(source_scope, list)
    return {str(path) for path in source_scope}


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


def _assert_aion239_boundaries() -> None:
    assert not (
        ROOT / "services/brain-api/src/aion_brain/api/v02_release_qualification.py"
    ).exists()


def test_aion_206_does_not_add_runtime_source_or_release_surfaces():
    changed = changed_files()
    aion217_source_paths = _aion217_source_paths()
    aion239_source_paths = _aion239_source_paths()
    for path in changed:
        if is_aion243_allowed_path(path):
            continue
        assert not path.startswith(".github/workflows/"), path
        if path.startswith("services/brain-api/src/aion_brain/"):
            assert (
                path in SOURCE_RUNTIME_PATHS
                or path in aion217_source_paths
                or path in aion239_source_paths
            ), path
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
    if changed & aion239_source_paths:
        changed_source_paths = {
            path
            for path in changed
            if path.startswith("services/brain-api/src/aion_brain/")
        }
        assert (
            changed_source_paths
            <= set(SOURCE_RUNTIME_PATHS) | aion217_source_paths | aion239_source_paths
        )
        _assert_aion239_boundaries()
    for relative in PROHIBITED_SOURCE_RUNTIME_PATHS:
        assert not (ROOT / relative).exists(), relative
