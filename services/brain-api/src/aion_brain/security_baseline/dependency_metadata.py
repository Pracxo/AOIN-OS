"""Local dependency metadata scanner."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path
from typing import Any

from aion_brain.contracts.security_baseline import DependencyMetadataFinding

CORE_PROVIDER_SDKS = {
    "openai",
    "anthropic",
    "google-generativeai",
    "cohere",
    "litellm",
}
CLOUD_SDKS = {"boto3", "botocore", "google-cloud", "azure-", "pulumi", "terraform"}
DOMAIN_SDK_TERMS = {
    "finance",
    "trading",
    "legal",
    "healthcare",
    "medical",
    "payments",
    "procurement",
}
SECRET_MANAGER_SDKS = {"hvac", "aws-secretsmanager", "google-cloud-secret-manager"}
DOCKER_SDKS = {"docker"}


class DependencyMetadataScanner:
    """Read local pyproject metadata without network access."""

    def __init__(self, *, root_dir: Path | None = None) -> None:
        self._root_dir = root_dir or Path(__file__).parents[5]

    def scan(self, pyproject_paths: list[Path] | None = None) -> list[DependencyMetadataFinding]:
        """Return dependency metadata findings for local pyproject files."""
        paths = pyproject_paths or [
            self._root_dir / "services/brain-api/pyproject.toml",
            self._root_dir / "packages/aion-sdk-python/pyproject.toml",
        ]
        findings: list[DependencyMetadataFinding] = []
        for path in paths:
            findings.extend(self._scan_pyproject(path))
        return findings

    def check(self) -> list[dict[str, Any]]:
        """Return hardening check payloads derived from dependency metadata."""
        findings = self.scan()
        required_provider = [
            finding.model_dump(mode="json")
            for finding in findings
            if finding.category in {"provider_sdk_required", "cloud_sdk_required"}
        ]
        domain = [
            finding.model_dump(mode="json")
            for finding in findings
            if finding.category == "domain_specific_dependency"
        ]
        docker = [
            finding.model_dump(mode="json")
            for finding in findings
            if finding.category == "docker_sdk_required"
        ]
        secret_managers = [
            finding.model_dump(mode="json")
            for finding in findings
            if finding.category == "secret_manager_sdk_required"
        ]
        return [
            _check(
                "no_provider_sdk_in_core_required_dependencies",
                not required_provider,
                required_provider,
            ),
            _check("no_domain_specific_sdk_dependency", not domain, domain),
            _check("no_docker_sdk_required_dependency", not docker, docker),
            _check(
                "no_secret_manager_sdk_required_dependency",
                not secret_managers,
                secret_managers,
            ),
            _check("dependency_metadata_read_without_network", True, []),
        ]

    def _scan_pyproject(self, path: Path) -> list[DependencyMetadataFinding]:
        if not path.exists():
            return [
                DependencyMetadataFinding(
                    dependency_name=path.name,
                    source=path.as_posix(),
                    declared_version=None,
                    optional=False,
                    category="metadata_missing",
                    notes=["pyproject file missing"],
                )
            ]
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        source = _relative(path, self._root_dir)
        project = data.get("project", {})
        required = [str(item) for item in project.get("dependencies", [])]
        optional_payload = project.get("optional-dependencies", {})
        optional = [
            str(item)
            for values in optional_payload.values()
            if isinstance(values, list)
            for item in values
        ]
        findings: list[DependencyMetadataFinding] = []
        for dependency in required:
            name = _dependency_name(dependency)
            category = _category_for_required(name)
            if category:
                findings.append(
                    DependencyMetadataFinding(
                        dependency_name=name,
                        source=source,
                        declared_version=dependency,
                        optional=False,
                        category=category,
                        notes=["required dependency should remain optional or adapter-local"],
                    )
                )
        for dependency in optional:
            name = _dependency_name(dependency)
            if name in CORE_PROVIDER_SDKS or name in {
                "mcp",
                "temporalio",
                "turbovec",
                "graphiti-core",
            }:
                findings.append(
                    DependencyMetadataFinding(
                        dependency_name=name,
                        source=source,
                        declared_version=dependency,
                        optional=True,
                        category="optional_adapter_dependency",
                        notes=["adapter dependency remains optional"],
                    )
                )
        return findings


def _category_for_required(name: str) -> str | None:
    if name in CORE_PROVIDER_SDKS:
        return "provider_sdk_required"
    if any(name.startswith(term) for term in CLOUD_SDKS):
        return "cloud_sdk_required"
    if name in DOCKER_SDKS:
        return "docker_sdk_required"
    if name in SECRET_MANAGER_SDKS:
        return "secret_manager_sdk_required"
    if any(term in name for term in DOMAIN_SDK_TERMS):
        return "domain_specific_dependency"
    return None


def _dependency_name(value: str) -> str:
    name = re.split(r"[<>=!~;\[]", value, maxsplit=1)[0].strip().lower()
    return name


def _check(name: str, passed: bool, findings: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "name": name,
        "category": "dependency",
        "status": "passed" if passed else "failed",
        "severity": "high",
        "message": f"{name} {'passed' if passed else 'failed'}.",
        "details": {"findings": findings},
    }


def _relative(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()
