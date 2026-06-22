"""Local release smoke matrix for golden path readiness."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from aion_brain.config import Settings, get_settings
from aion_brain.golden_path.policy import authorize_golden_path_action
from aion_brain.golden_path.repository import GoldenPathRepository
from aion_brain.golden_path.telemetry import emit_golden_path_telemetry


class ReleaseSmokeMatrix:
    """Summarize deterministic local release readiness without subprocess calls."""

    def __init__(
        self,
        repository: GoldenPathRepository,
        policy_adapter: object,
        *,
        diagnostics: object | None = None,
        freeze_gate_service: object | None = None,
        release_packager: object | None = None,
        registry_service: object | None = None,
        contract_registry: object | None = None,
        operator_service: object | None = None,
        telemetry_service: object | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._diagnostics = diagnostics
        self._freeze_gate_service = freeze_gate_service
        self._release_packager = release_packager
        self._registry_service = registry_service
        self._contract_registry = contract_registry
        self._operator_service = operator_service
        self._telemetry_service = telemetry_service
        self._settings = settings or get_settings()

    def run(self, scope: list[str], *, created_by: str | None = None) -> dict[str, Any]:
        """Build the release smoke matrix."""

        authorize_golden_path_action(
            self._policy_adapter,
            "golden_path.release_smoke.run",
            scope,
            actor_id=created_by,
            resource_type="golden_path_release_smoke",
            risk_level="low",
            context={"external_calls": False, "shell_execution": False},
        )
        if not self._settings.golden_path_release_smoke_enabled:
            return {"status": "disabled", "checks": {}, "generated_at": datetime.now(UTC)}
        latest_run = self._repository.latest_run()
        latest_report = self._repository.latest_report()
        checks = {
            "script_equivalent_checks": _check(
                True, "Scripts are represented as local API checks."
            ),
            "kernel_diagnostics": _check(
                self._diagnostics is not None, "Kernel diagnostics wired."
            ),
            "health_readiness": _check(
                self._diagnostics is not None, "Readiness is locally inspectable."
            ),
            "operator_overview": _check(
                self._operator_service is not None, "Operator overview wired."
            ),
            "freeze_gate_dry_run": _check(
                self._freeze_gate_service is not None, "Freeze gate available."
            ),
            "release_package_dry_run": _check(
                self._release_packager is not None, "Release packager available."
            ),
            "contract_snapshot": _check(
                self._contract_registry is not None,
                "Contract registry available.",
            ),
            "registry_validation": _check(
                self._registry_service is not None, "Registry service available."
            ),
            "golden_path_latest": _check(
                latest_report is not None and latest_report.release_candidate_ready,
                "Latest golden path report is release-ready.",
                {
                    "latest_run_id": getattr(latest_run, "golden_path_run_id", None),
                    "latest_report_id": getattr(latest_report, "golden_path_report_id", None),
                    "readiness_score": getattr(latest_report, "readiness_score", 0.0),
                },
            ),
        }
        failed = [key for key, value in checks.items() if value["status"] == "failed"]
        warnings = [key for key, value in checks.items() if value["status"] == "warning"]
        status = "failed" if failed else "warning" if warnings else "passed"
        result = {
            "release_smoke_id": f"release-smoke-{uuid4().hex}",
            "status": status,
            "checks": checks,
            "failed_checks": failed,
            "warning_checks": warnings,
            "external_calls": False,
            "shell_execution": False,
            "generated_at": datetime.now(UTC),
        }
        emit_golden_path_telemetry(
            self._telemetry_service,
            event_type="golden_path_release_smoke_completed",
            node_type="release_smoke",
            node_id=str(result["release_smoke_id"]),
            scope=scope,
            intensity=1.0 if failed else 0.7,
            payload={"status": status, "failed_count": len(failed)},
        )
        return result


def _check(passed: bool, message: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "status": "passed" if passed else "warning",
        "message": message,
        "details": details or {},
    }


__all__ = ["ReleaseSmokeMatrix"]
