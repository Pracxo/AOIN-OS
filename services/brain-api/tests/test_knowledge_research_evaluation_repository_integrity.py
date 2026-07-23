from knowledge_source_registry_test_helpers import ROOT, SOURCE_RUNTIME_PATHS, changed_files


def test_aion_206_does_not_add_runtime_source_or_release_surfaces():
    changed = changed_files()
    for path in changed:
        assert not path.startswith(".github/workflows/"), path
        assert not path.startswith("services/brain-api/src/aion_brain/"), path
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
    for relative in SOURCE_RUNTIME_PATHS:
        assert not (ROOT / relative).exists(), relative
