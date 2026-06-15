"""Local metadata-only SBOM placeholder."""

from __future__ import annotations

import tomllib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from aion_brain.contracts.release_package import SBOMPlaceholder

SBOM_LIMITATIONS = [
    "This is a local metadata SBOM placeholder.",
    "It does not resolve transitive dependencies.",
    "It does not query package registries.",
]


class SBOMPlaceholderService:
    """Generate a local SBOM placeholder from Python project metadata."""

    def __init__(self, root_dir: Path) -> None:
        self._root_dir = root_dir

    def generate(self, version: str) -> SBOMPlaceholder:
        """Generate a metadata-only SBOM placeholder without network calls."""
        packages = [
            _read_project(self._root_dir / "services/brain-api/pyproject.toml"),
            _read_project(self._root_dir / "packages/aion-sdk-python/pyproject.toml"),
        ]
        return SBOMPlaceholder(
            sbom_id=f"sbom-placeholder-{uuid4().hex}",
            version=version,
            format="aion-local-json-placeholder",
            packages=packages,
            generated_by="aion-local-release-packager",
            generated_at=datetime.now(UTC),
            limitations=SBOM_LIMITATIONS,
        )


def _read_project(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"path": path.as_posix(), "present": False}
    parsed = tomllib.loads(path.read_text(encoding="utf-8"))
    project = parsed.get("project", {})
    return {
        "path": path.as_posix(),
        "present": True,
        "name": project.get("name"),
        "version": project.get("version"),
        "dependencies": list(project.get("dependencies", [])),
        "optional_dependencies": dict(project.get("optional-dependencies", {})),
    }
