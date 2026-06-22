"""Release handoff report builder."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast

from aion_brain.contracts.release_package import ReleaseHandoffReport, ReleasePackageValidation

KNOWN_LIMITS = [
    "local-first only",
    "no production auth",
    "no cloud deployment",
    "no full autonomy by default",
    "no domain modules",
    "optional adapters disabled by default",
    "no untrusted code execution",
    "no raw secret storage",
]
LOCAL_VERIFICATION_COMMANDS = [
    "scripts/check.sh",
    "scripts/release-candidate-check.sh",
    "scripts/package-release.sh",
    "scripts/verify-release-package.sh",
    "scripts/docker-up-core.sh",
    "scripts/kernel-self-test.sh",
    "aionctl smoke run",
    "aionctl release-baseline run --version 0.1.0",
    "aionctl freeze run --version 0.1.0",
]


class ReleaseHandoffService:
    """Build final local handoff reports."""

    def build(
        self,
        version: str,
        validation: ReleasePackageValidation,
        reports: dict[str, Any],
    ) -> ReleaseHandoffReport:
        """Build a handoff report from validation and included reports."""
        if validation.status == "failed":
            status = "blocked"
            summary = "AION local release package is blocked by validation failures."
        elif validation.status == "warning":
            status = "warning"
            summary = "AION local release package is ready with warnings."
        else:
            status = "ready"
            summary = "AION local release package is ready for local handoff."
        return ReleaseHandoffReport(
            version=version,
            status=cast(Any, status),
            summary=summary,
            included_reports=_summarize_reports(reports),
            local_verification_commands=list(LOCAL_VERIFICATION_COMMANDS),
            known_limits=list(KNOWN_LIMITS),
            next_steps=[
                "Inspect release-package-manifest.json.",
                "Verify checksums with scripts/verify-release-package.sh.",
                "Run release baseline and freeze gate before module work.",
                "Keep future domain modules outside Brain core.",
            ],
            generated_at=datetime.now(UTC),
        )


def _summarize_reports(reports: dict[str, Any]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for key, value in reports.items():
        if hasattr(value, "model_dump"):
            payload = value.model_dump(mode="json")
        else:
            payload = value
        if isinstance(payload, dict):
            summary[key] = {
                "present": True,
                "status": payload.get("status"),
                "id": _first_id(payload),
            }
        else:
            summary[key] = {"present": True}
    return summary


def _first_id(payload: dict[str, Any]) -> object | None:
    for key, value in payload.items():
        if key.endswith("_id"):
            return cast(object, value)
    return None
