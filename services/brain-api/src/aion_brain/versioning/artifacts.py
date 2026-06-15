"""Release artifact manifest service."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast
from uuid import uuid4

from aion_brain.api_support.errors import AIONPolicyDeniedException
from aion_brain.contracts.compatibility import ReleaseArtifactManifest
from aion_brain.contracts.policy import PolicyRequest
from aion_brain.policy.base import PolicyAdapter
from aion_brain.versioning.compatibility import emit_versioning_telemetry
from aion_brain.versioning.manifest import stable_hash
from aion_brain.versioning.repository import VersioningRepository

RELEASE_ARTIFACT_FILES = (
    "README.md",
    "AGENTS.md",
    "CHANGELOG.md",
    "docs/versioning.md",
    "docs/upgrade-policy.md",
    "docs/deprecation-policy.md",
    "docs/release-notes/v0.1.0.md",
    "docker-compose.yml",
    "packages/aion-sdk-python/pyproject.toml",
)


class ReleaseArtifactService:
    """Generate metadata-only release artifact manifests."""

    def __init__(
        self,
        repository: VersioningRepository,
        policy_adapter: PolicyAdapter,
        *,
        root_dir: Path,
        contract_export_service: object | None = None,
        telemetry_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._root_dir = root_dir
        self._contract_export_service = contract_export_service
        self._telemetry_service = telemetry_service

    def generate(
        self,
        version: str,
        created_by: str | None,
        scope: list[str],
    ) -> ReleaseArtifactManifest:
        """Generate and persist an artifact manifest without packaging files."""
        self._authorize(
            "release.artifact.generate",
            scope,
            actor_id=created_by,
            risk_level="medium",
            context={"version": version},
        )
        checksums = _file_checksums(self._root_dir)
        artifacts: dict[str, Any] = {
            "files": sorted(checksums),
            "contract_export_hash": self._contract_export_hash(),
            "openapi_hash": self._contract_export_hash(openapi_only=True),
            "sdk_package_metadata": _safe_file_text(
                self._root_dir / "packages/aion-sdk-python/pyproject.toml"
            ),
            "docker_compose_config_hash": checksums.get("docker-compose.yml"),
            "migration_baseline_hash": _directory_hash(
                self._root_dir / "infra/postgres/migrations"
            ),
            "policy_bundle_hash": _directory_hash(self._root_dir / "infra/opa/policies"),
            "release_baseline_report_id": None,
        }
        missing = [path for path in RELEASE_ARTIFACT_FILES if path not in checksums]
        status = "failed" if missing else "complete"
        manifest = ReleaseArtifactManifest(
            release_artifact_id=f"release-artifact-{uuid4().hex}",
            version=version,
            status=cast(Any, status),
            artifacts=artifacts,
            checksums=checksums,
            report={
                "missing_files": missing,
                "packaged": False,
                "uploaded": False,
                "external_calls": False,
            },
            created_by=created_by,
            created_at=datetime.now(UTC),
        )
        saved = self._repository.save_release_artifact(manifest)
        emit_versioning_telemetry(
            self._telemetry_service,
            event_type="release_artifact_manifest_generated",
            node_type="release_artifact",
            node_id=saved.release_artifact_id,
            intensity=0.8 if saved.status == "complete" else 1.0,
            scope=scope,
            payload={"version": version, "status": saved.status},
        )
        return saved

    def _authorize(
        self,
        action_type: str,
        scope: list[str],
        *,
        actor_id: str | None = None,
        risk_level: str = "low",
        context: dict[str, Any] | None = None,
    ) -> None:
        decision = self._policy_adapter.authorize(
            PolicyRequest(
                request_id=f"{action_type}-{uuid4().hex}",
                trace_id=None,
                actor_id=actor_id,
                workspace_id=None,
                action_type=action_type,
                resource_type="release_artifact",
                resource_id=None,
                risk_level=risk_level,
                approval_present=True,
                requested_permissions=[action_type],
                security_scope=scope,
                context=context or {},
            )
        )
        if not decision.allow:
            raise AIONPolicyDeniedException(decision.reason)

    def _contract_export_hash(self, *, openapi_only: bool = False) -> str | None:
        export_contracts = getattr(self._contract_export_service, "export_contracts", None)
        if not callable(export_contracts):
            return None
        try:
            return stable_hash(
                {"contract_export_service": "available", "openapi_only": openapi_only}
            )
        except Exception:
            return None

def _file_checksums(root_dir: Path) -> dict[str, str]:
    checksums: dict[str, str] = {}
    for relative in RELEASE_ARTIFACT_FILES:
        path = root_dir / relative
        if path.is_file():
            checksums[relative] = _file_hash(path)
    return checksums


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _directory_hash(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    for child in sorted(item for item in path.rglob("*") if item.is_file()):
        digest.update(child.relative_to(path).as_posix().encode())
        digest.update(b"\0")
        digest.update(child.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _safe_file_text(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"present": False}
    data: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("name =") or line.startswith("version ="):
            key, value = line.split("=", 1)
            data[key.strip()] = value.strip().strip('"')
    return {"present": True, **json.loads(json.dumps(data, sort_keys=True))}
