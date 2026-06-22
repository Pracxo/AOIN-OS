"""Module package compatibility checks."""

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.config import Settings
from aion_brain.contracts.module_developer import ModuleCompatibilityReport, ModulePackage
from aion_brain.module_developer.validator import ALLOWED_EXECUTION_MODES


class ModuleCompatibilityChecker:
    """Check a module package against AION Brain v0.1 capabilities."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def check(self, package: ModulePackage) -> ModuleCompatibilityReport:
        """Return a deterministic compatibility report."""

        warnings: list[dict[str, object]] = []
        issues: list[dict[str, object]] = []
        required_version = str(package.compatibility.get("required_aion_version") or "")
        if required_version and required_version != self._settings.version:
            warnings.append(
                {
                    "code": "aion_version_mismatch",
                    "message": "required_aion_version differs from running AION version",
                }
            )
        if package.manifest.execution_mode not in ALLOWED_EXECUTION_MODES:
            warnings.append(
                {
                    "code": "unsupported_execution_mode",
                    "execution_mode": package.manifest.execution_mode,
                }
            )
        unsupported = [
            dependency
            for dependency in list(package.compatibility.get("required_features", []))
            if dependency
            not in {
                "capability_registry",
                "runtime_gateway",
                "policy",
                "autonomy",
                "risk",
                "audit",
            }
        ]
        for dependency in unsupported:
            issues.append({"code": "unsupported_feature", "feature": dependency})
        return ModuleCompatibilityReport(
            report_id=f"module-compat-{uuid4().hex}",
            module_id=package.module_id,
            version=package.version,
            compatible=not issues,
            aion_version=self._settings.version,
            required_aion_version=required_version or None,
            issues=issues,
            warnings=warnings,
            checked_at=datetime.now(UTC),
        )
