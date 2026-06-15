"""Validation for local release packages."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import PurePosixPath
from typing import Any, cast

from aion_brain.contracts.release_package import (
    ReleasePackageFile,
    ReleasePackageRequest,
    ReleasePackageValidation,
)
from aion_brain.contracts.versioning import reject_secret_like_keys

CACHE_PARTS = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".venv", "venv"}


class ReleasePackageValidator:
    """Validate local release package contents and reports."""

    def __init__(self, *, max_file_size_mb: int = 10) -> None:
        self._max_file_size_bytes = max_file_size_mb * 1024 * 1024

    def validate(
        self,
        request: ReleasePackageRequest,
        files: list[ReleasePackageFile],
        reports: dict[str, Any],
    ) -> ReleasePackageValidation:
        """Validate package files and generated reports."""
        checks: list[dict[str, Any]] = []
        failures: list[dict[str, Any]] = []
        warnings: list[dict[str, Any]] = []

        def check(
            name: str,
            passed: bool,
            *,
            severity: str = "critical",
            details: dict[str, Any] | None = None,
        ) -> None:
            payload = {
                "name": name,
                "status": "passed" if passed else "failed",
                "severity": severity,
                "details": details or {},
            }
            checks.append(payload)
            if not passed:
                (warnings if severity == "warning" else failures).append(payload)

        included_paths = {file.file_path for file in files if file.included}
        artifact_types = {file.artifact_type for file in files if file.included}
        report_keys = set(reports)

        check("version_present", bool(request.version.strip()))
        check("output_dir_safe", _path_safe(request.output_dir))
        env_files = [path for path in included_paths if _is_env_path(path)]
        check("no_env_included", not env_files, details={"matches": env_files})
        cache_files = [path for path in included_paths if _has_cache_part(path)]
        check("no_cache_dirs_included", not cache_files, details={"matches": cache_files})
        oversized = [
            file.file_path
            for file in files
            if file.included and file.size_bytes > self._max_file_size_bytes
        ]
        check("no_source_file_exceeds_max_size", not oversized, details={"matches": oversized})
        check("readme_included", "README.md" in included_paths)
        check("agents_included", "AGENTS.md" in included_paths)
        check("changelog_included", "CHANGELOG.md" in included_paths)
        check(
            "release_notes_included",
            any(path.startswith("docs/release-notes/") for path in included_paths),
        )
        if request.include_contracts:
            check(
                "contract_export_included",
                "contract_export" in report_keys or "contract" in artifact_types,
            )
        if request.include_freeze_gate:
            check("freeze_gate_included", "freeze_gate" in report_keys)
        if request.include_release_baseline:
            check("release_baseline_included", "release_baseline" in report_keys)
        if request.include_migration_baseline:
            check("migration_baseline_included", "migration_baseline" in report_keys)
        if request.include_policy_bundle:
            check(
                "policy_bundle_included",
                "policy_bundle" in report_keys or "policy" in artifact_types,
                severity="warning",
            )
        if request.include_sbom_placeholder:
            check("sbom_placeholder_included", "sbom" in report_keys or "sbom" in artifact_types)
        domain_report = reports.get("no_domain_drift")
        if isinstance(domain_report, dict) and "status" in domain_report:
            check("no_domain_drift_passed", domain_report.get("status") == "passed")
        autonomy_report = reports.get("autonomy_defaults")
        if isinstance(autonomy_report, dict):
            check(
                "no_full_autonomy_default_warning",
                not bool(autonomy_report.get("full_autonomy_enabled", False)),
            )
        compatibility = reports.get("compatibility_matrix")
        if isinstance(compatibility, dict):
            optional = compatibility.get("optional_adapters", {})
            required_optional = [
                name
                for name, value in optional.items()
                if isinstance(value, dict) and value.get("required") is True
            ]
            check(
                "optional_adapters_remain_optional",
                not required_optional,
                details={"required_optional": required_optional},
            )
        hardening_gate = reports.get("hardening_gate")
        if hardening_gate is not None:
            hardening_payload = _model_or_dict(hardening_gate)
            if isinstance(hardening_payload, dict):
                check(
                    "hardening_gate_report_included",
                    bool(hardening_payload),
                    severity="warning",
                )
                check(
                    "hardening_gate_not_failed",
                    hardening_payload.get("status") != "failed",
                    details={"status": hardening_payload.get("status")},
                )
                secret_findings = _secret_high_findings(hardening_payload)
                check(
                    "no_high_secret_scan_findings",
                    not secret_findings,
                    details={"matches": secret_findings},
                )
        check("metadata_has_no_raw_secrets", _metadata_safe(request.metadata))

        status = "failed" if failures else ("warning" if warnings else "passed")
        return ReleasePackageValidation(
            status=cast(Any, status),
            checks=checks,
            failures=failures,
            warnings=warnings,
            generated_at=datetime.now(UTC),
        )


def _path_safe(path: str) -> bool:
    pure = PurePosixPath(path.replace("\\", "/"))
    return bool(path.strip()) and not pure.is_absolute() and ".." not in pure.parts


def _is_env_path(path: str) -> bool:
    name = PurePosixPath(path).name
    return name == ".env" or (name.startswith(".env.") and name != ".env.example")


def _has_cache_part(path: str) -> bool:
    return any(part in CACHE_PARTS for part in PurePosixPath(path).parts)


def _metadata_safe(metadata: dict[str, Any]) -> bool:
    try:
        reject_secret_like_keys(metadata)
    except ValueError:
        return False
    return True


def _model_or_dict(value: object) -> object:
    dump = getattr(value, "model_dump", None)
    if callable(dump):
        return dump(mode="json")
    return value


def _secret_high_findings(report: dict[str, Any]) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    for check in report.get("checks", []):
        if not isinstance(check, dict):
            continue
        if check.get("name") != "local_secret_scan":
            continue
        details = check.get("details", {})
        if isinstance(details, dict) and int(details.get("high_or_critical_findings", 0)) > 0:
            matches.append({"check": "local_secret_scan", "status": check.get("status")})
    return matches
