"""Source tree manifest builder for local release packages."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aion_brain.release_package.checksums import root_checksum, sha256_file

INCLUDE_PATHS = (
    "services/brain-api/src",
    "services/brain-api/pyproject.toml",
    "packages/aion-sdk-python/src",
    "packages/aion-sdk-python/pyproject.toml",
    "README.md",
    "AGENTS.md",
    "CHANGELOG.md",
    "VERSION",
    "RELEASE_NOTES.md",
    "docs",
    "scripts",
    "docker-compose.yml",
    ".github/workflows",
)
EXCLUDE_NAMES = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".aion_objects",
    ".aion_indexes",
    "node_modules",
    "venv",
    ".venv",
    "dist",
    "build",
}
SECRET_NAME_PARTS = {
    "api_key",
    "apikey",
    "authorization",
    "bearer",
    "client_secret",
    "credential",
    "password",
    "private_key",
    "secret",
    "token",
}


class SourceManifestService:
    """Build a deterministic local source manifest without external calls."""

    def __init__(self, *, max_file_size_mb: int = 10) -> None:
        self._max_file_size_bytes = max_file_size_mb * 1024 * 1024

    def build(self, root: Path) -> dict[str, Any]:
        """Build a source manifest from release-owned paths."""
        root = root.resolve()
        files: list[dict[str, Any]] = []
        excluded: list[dict[str, Any]] = []
        for relative in INCLUDE_PATHS:
            candidate = root / relative
            if not candidate.exists():
                excluded.append({"file_path": relative, "reason": "missing"})
                continue
            if candidate.is_file():
                self._append_file(root, candidate, files, excluded)
            else:
                for path in sorted(candidate.rglob("*")):
                    if path.is_dir():
                        continue
                    if _has_excluded_part(path.relative_to(root)):
                        excluded.append(
                            {"file_path": path.relative_to(root).as_posix(), "reason": "cache_dir"}
                        )
                        continue
                    self._append_file(root, path, files, excluded)
        checksums = {
            str(file["file_path"]): str(file["sha256"])
            for file in files
            if bool(file.get("included", True))
        }
        total_size = sum(int(file["size_bytes"]) for file in files)
        return {
            "generated_at": datetime.now(UTC).isoformat(),
            "include_paths": list(INCLUDE_PATHS),
            "files": files,
            "excluded_artifacts": excluded,
            "forbidden_files": [
                item for item in excluded if item.get("reason") in {"env_file", "secret_name"}
            ],
            "oversized_files": [item for item in excluded if item.get("reason") == "oversized"],
            "file_count": len(files),
            "total_size_bytes": total_size,
            "root_checksum": root_checksum(checksums),
        }

    def _append_file(
        self,
        root: Path,
        path: Path,
        files: list[dict[str, Any]],
        excluded: list[dict[str, Any]],
    ) -> None:
        relative = path.relative_to(root)
        relative_text = relative.as_posix()
        if _is_env_file(relative):
            excluded.append({"file_path": relative_text, "reason": "env_file"})
            return
        if _secret_like_name(path.name):
            excluded.append({"file_path": relative_text, "reason": "secret_name"})
            return
        size = path.stat().st_size
        if size > self._max_file_size_bytes:
            excluded.append({"file_path": relative_text, "reason": "oversized", "size_bytes": size})
            return
        files.append(
            {
                "file_path": relative_text,
                "artifact_type": _artifact_type(relative_text),
                "size_bytes": size,
                "sha256": sha256_file(path),
                "included": True,
                "reason": None,
            }
        )


def _has_excluded_part(path: Path) -> bool:
    return any(part in EXCLUDE_NAMES for part in path.parts)


def _is_env_file(path: Path) -> bool:
    name = path.name
    return name == ".env" or (name.startswith(".env.") and name != ".env.example")


def _secret_like_name(name: str) -> bool:
    lowered = name.lower().replace("-", "_")
    return any(part in lowered for part in SECRET_NAME_PARTS)


def _artifact_type(relative: str) -> str:
    if relative.startswith("services/brain-api/src"):
        return "source"
    if relative.startswith("packages/aion-sdk-python"):
        return "sdk"
    if relative == "RELEASE_NOTES.md" or relative.startswith("docs/release-notes"):
        return "release_notes"
    if relative.startswith("docs"):
        return "docs"
    if relative.startswith("scripts"):
        return "script"
    if relative.startswith(".github"):
        return "config"
    if relative.startswith("infra/postgres/migrations"):
        return "migration"
    if relative == "docker-compose.yml":
        return "docker"
    if relative == "CHANGELOG.md":
        return "changelog"
    return "manifest"
