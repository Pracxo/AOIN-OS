"""Capability certification harness for module packages."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.config import Settings
from aion_brain.contracts.autonomy import AutonomyDecisionRequest
from aion_brain.contracts.effects import ObservedEffectCreateRequest
from aion_brain.contracts.module_developer import (
    CapabilityCertification,
    CapabilityCertificationCheck,
    CertificationStatus,
    ModuleCertificationRequest,
    ModuleCertificationRun,
    ModulePackage,
    ModulePackageCreateRequest,
)
from aion_brain.contracts.outcomes import OutcomeCreateRequest
from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.risk import RiskAssessmentRequest
from aion_brain.contracts.telemetry import VisualTelemetryEvent
from aion_brain.module_developer.repository import ModuleDeveloperRepository
from aion_brain.module_developer.validator import ModulePackageValidator


class ModuleCertifier:
    """Submit and certify module packages without executing module code."""

    def __init__(
        self,
        *,
        repository: ModuleDeveloperRepository,
        validator: ModulePackageValidator,
        capability_service: object,
        runtime_gateway: object,
        policy_adapter: object,
        autonomy_governor: object,
        risk_engine: object,
        telemetry_service: object | None,
        settings: Settings,
        sandbox_service: object | None = None,
        observed_effect_collector: object | None = None,
        outcome_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._validator = validator
        self._capability_service = capability_service
        self._runtime_gateway = runtime_gateway
        self._policy_adapter = policy_adapter
        self._autonomy_governor = autonomy_governor
        self._risk_engine = risk_engine
        self._telemetry_service = telemetry_service
        self._settings = settings
        self._sandbox_service = sandbox_service
        self._observed_effect_collector = observed_effect_collector
        self._outcome_service = outcome_service

    def submit_package(self, request: ModulePackageCreateRequest) -> ModulePackage:
        """Validate and persist a module package."""

        self._authorize(
            action_type="module.package.submit",
            resource_id=request.module_package_id or request.module_id,
            risk_level="medium",
            actor_id=request.created_by,
            workspace_id=None,
            owner_scope=request.manifest.memory_read_scopes or ["workspace:main"],
            context={"module_id": request.module_id, "version": request.version},
        )
        checks = self._validator.validate_package(request)
        critical_failed = _has_required_failure(checks)
        now = datetime.now(UTC)
        package = ModulePackage(
            module_package_id=request.module_package_id or f"module-package-{uuid4().hex}",
            module_id=request.module_id,
            version=request.version,
            package_name=request.package_name,
            display_name=request.display_name,
            description=request.description,
            status="rejected" if critical_failed else ("submitted" if request.submit else "draft"),
            manifest=request.manifest,
            compatibility=request.compatibility,
            metadata={
                **request.metadata,
                "validation": {
                    "total_checks": len(checks),
                    "failed_checks": sum(check.status == "failed" for check in checks),
                },
            },
            created_by=request.created_by,
            created_at=now,
            updated_at=now,
            disabled_at=None,
        )
        stored = self._repository.save_package(package)
        self._emit(
            "module_package_submitted",
            "module_package",
            stored.module_package_id,
            0.5,
            {"status": stored.status, "module_id": stored.module_id},
        )
        return stored

    def certify(self, request: ModuleCertificationRequest) -> ModuleCertificationRun:
        """Run deterministic certification for a module package."""

        self._authorize(
            action_type="module.package.certify",
            resource_id=request.module_package_id,
            risk_level="medium",
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            owner_scope=request.owner_scope,
            context={"dry_run": request.dry_run},
        )
        package = self._repository.get_package(request.module_package_id)
        if package is None:
            raise ValueError("module_package_not_found")
        run_id = f"module-cert-{uuid4().hex}"
        self._emit(
            "module_certification_started",
            "certification",
            run_id,
            0.5,
            {"module_package_id": package.module_package_id},
        )
        checks = self._validator.validate_manifest(package.manifest)
        capability_certifications: list[CapabilityCertification] = []
        for capability in package.manifest.capabilities:
            capability_checks = self._validator.validate_capability(capability)
            capability_checks.extend(self._certification_checks(package, capability, request))
            checks.extend(capability_checks)
            certification = _capability_certification(
                package,
                capability,
                capability_checks,
                certified_by=request.actor_id,
            )
            capability_certifications.append(self._repository.save_certification(certification))
        status = _status(checks)
        now = datetime.now(UTC)
        run = ModuleCertificationRun(
            certification_run_id=run_id,
            module_package_id=package.module_package_id,
            module_id=package.module_id,
            version=package.version,
            status=status,
            total_checks=len(checks),
            passed_checks=sum(check.status == "passed" for check in checks),
            failed_checks=sum(check.status == "failed" for check in checks),
            warning_checks=sum(check.status == "warning" for check in checks),
            score=_score(checks),
            report={
                "dry_run": request.dry_run,
                "module_code_executed": False,
                "capability_certifications": [
                    certification.certification_id for certification in capability_certifications
                ],
                "checks": [check.model_dump(mode="json") for check in checks],
            },
            created_by=request.actor_id,
            created_at=now,
            completed_at=now,
        )
        stored = self._repository.save_certification_run(run)
        if status == "passed" and not request.dry_run:
            self._repository.save_package(
                package.model_copy(update={"status": "certified", "updated_at": now})
            )
        self._record_certification_outcome(stored, request)
        self._emit(
            "module_certification_completed",
            "certification",
            run_id,
            {"passed": 0.9, "warning": 0.7, "failed": 1.0}[status],
            {"status": status, "score": stored.score},
        )
        return stored

    def _record_certification_outcome(
        self,
        run: ModuleCertificationRun,
        request: ModuleCertificationRequest,
    ) -> None:
        if not getattr(self._settings, "outcomes_enabled", True):
            return
        if self._observed_effect_collector is None or self._outcome_service is None:
            return
        try:
            create_observed = cast(
                Any,
                self._observed_effect_collector,
            ).create_observed_effect
            observed = create_observed(
                ObservedEffectCreateRequest(
                    trace_id=None,
                    source_type="generic",
                    source_id=run.certification_run_id,
                    effect_type="status_change",
                    subject_ref=run.module_package_id,
                    predicate="certification_status",
                    observed_value={
                        "status": run.status,
                        "score": run.score,
                        "module_code_executed": False,
                    },
                    observation_source_type="system",
                    observation_source_id=run.certification_run_id,
                    confidence=0.8,
                    owner_scope=request.owner_scope,
                    observed_at=run.completed_at,
                    metadata={"source": "module_certification"},
                )
            )
            create_once = cast(Any, self._outcome_service).create_outcome_once_for_source
            create_once(
                OutcomeCreateRequest(
                    trace_id=None,
                    actor_id=request.actor_id,
                    workspace_id=request.workspace_id,
                    source_type="module_certification",
                    source_id=run.certification_run_id,
                    outcome_type="generic",
                    title="Module certification completed",
                    summary=f"Certification finished with status {run.status}.",
                    owner_scope=request.owner_scope,
                    observed_effects=[observed.observed_effect_id],
                    confidence=0.8,
                    score=run.score,
                    metadata={
                        "module_package_id": run.module_package_id,
                        "module_id": run.module_id,
                        "module_code_executed": False,
                    },
                    observed_at=run.completed_at,
                    created_by=request.actor_id,
                )
            )
        except Exception:
            return

    def get_package(self, module_package_id: str) -> ModulePackage | None:
        """Return a package."""

        return self._repository.get_package(module_package_id)

    def list_packages(
        self,
        status: str | None = None,
        module_id: str | None = None,
    ) -> list[ModulePackage]:
        """List packages."""

        return self._repository.list_packages(status=status, module_id=module_id)

    def disable_package(
        self,
        module_package_id: str,
        actor_id: str | None,
        reason: str,
    ) -> ModulePackage:
        """Disable one module package."""

        package = self._repository.get_package(module_package_id)
        if package is None:
            raise ValueError("module_package_not_found")
        self._authorize(
            action_type="module.package.disable",
            resource_id=module_package_id,
            risk_level="medium",
            actor_id=actor_id,
            workspace_id=None,
            owner_scope=["workspace:main"],
            context={"reason": reason},
        )
        disabled = self._repository.save_package(
            package.model_copy(
                update={
                    "status": "disabled",
                    "disabled_at": datetime.now(UTC),
                    "metadata": {**package.metadata, "disable_reason": reason},
                }
            )
        )
        self._emit(
            "module_package_disabled",
            "module_package",
            module_package_id,
            0.8,
            {"reason": reason},
        )
        return disabled

    def get_certification_run(
        self,
        certification_run_id: str,
    ) -> ModuleCertificationRun | None:
        """Return one certification run."""

        return self._repository.get_certification_run(certification_run_id)

    def list_certification_runs(
        self,
        module_package_id: str | None = None,
    ) -> list[ModuleCertificationRun]:
        """List certification runs."""

        return self._repository.list_certification_runs(module_package_id=module_package_id)

    def _certification_checks(
        self,
        package: ModulePackage,
        capability: dict[str, Any],
        request: ModuleCertificationRequest,
    ) -> list[CapabilityCertificationCheck]:
        capability_id = str(capability.get("capability_id") or capability.get("name") or "")
        checks = [
            _check(
                f"{capability_id}_audit_requirement",
                "audit",
                bool(capability.get("audit_level")),
                "audit metadata present",
                "audit metadata missing",
                "high",
            )
        ]
        if request.include_policy_check:
            checks.append(self._policy_check(package, capability, request))
        if request.include_autonomy_check:
            checks.append(self._autonomy_check(package, capability, request))
        if request.include_runtime_check:
            checks.append(self._risk_check(package, capability, request))
        if request.include_dry_run_invocation:
            checks.append(self._dry_run_check(capability))
        checks.extend(self._sandbox_checks(capability))
        return checks

    def _policy_check(
        self,
        package: ModulePackage,
        capability: dict[str, Any],
        request: ModuleCertificationRequest,
    ) -> CapabilityCertificationCheck:
        decision = self._authorize(
            action_type="capability.invoke",
            resource_id=str(capability.get("capability_id") or ""),
            risk_level=str(capability.get("risk_level") or "low"),
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            owner_scope=request.owner_scope,
            context={"module_id": package.module_id, "mode": "dry_run"},
            raise_on_deny=False,
        )
        return _check(
            f"{capability.get('capability_id', 'capability')}_policy_dry_authorization",
            "policy",
            bool(getattr(decision, "allow", False))
            or bool(getattr(decision, "approval_required", False)),
            "policy dry authorization completed",
            f"policy denied dry authorization: {getattr(decision, 'reason', 'unknown')}",
            "high",
        )

    def _autonomy_check(
        self,
        package: ModulePackage,
        capability: dict[str, Any],
        request: ModuleCertificationRequest,
    ) -> CapabilityCertificationCheck:
        decide = getattr(self._autonomy_governor, "decide", None)
        if not callable(decide):
            return _warning(
                f"{capability.get('capability_id', 'capability')}_autonomy_check",
                "autonomy",
                "autonomy governor unavailable for dry check",
            )
        decision = decide(
            AutonomyDecisionRequest(
                trace_id=None,
                actor_id=request.actor_id,
                workspace_id=request.workspace_id,
                requested_mode="dry_run",
                action_type="capability.invoke",
                resource_type="capability",
                resource_id=str(capability.get("capability_id") or ""),
                risk_level=cast(Any, str(capability.get("risk_level") or "low")),
                approval_present=False,
                context={"security_scope": request.owner_scope, "module_id": package.module_id},
            )
        )
        return _check(
            f"{capability.get('capability_id', 'capability')}_autonomy_dry_decision",
            "autonomy",
            bool(getattr(decision, "allow", False)),
            "autonomy dry decision allowed",
            f"autonomy blocked dry decision: {getattr(decision, 'reason', 'unknown')}",
            "high",
        )

    def _risk_check(
        self,
        package: ModulePackage,
        capability: dict[str, Any],
        request: ModuleCertificationRequest,
    ) -> CapabilityCertificationCheck:
        assess = getattr(self._risk_engine, "assess", None)
        if not callable(assess):
            return _warning(
                f"{capability.get('capability_id', 'capability')}_risk_check",
                "risk",
                "risk engine unavailable for dry check",
            )
        assessment = assess(
            RiskAssessmentRequest(
                trace_id=None,
                actor_id=request.actor_id,
                workspace_id=request.workspace_id,
                action_type="capability.invoke",
                resource_type="capability",
                resource_id=str(capability.get("capability_id") or ""),
                requested_risk_level=cast(Any, str(capability.get("risk_level") or "low")),
                payload={},
                context={
                    "security_scope": request.owner_scope,
                    "dry_run": True,
                    "module_id": package.module_id,
                },
            )
        )
        return _check(
            f"{capability.get('capability_id', 'capability')}_risk_metadata",
            "risk",
            getattr(assessment, "decision", "allow") != "block",
            "risk engine completed dry assessment",
            "risk engine blocked capability",
            "high",
        )

    def _dry_run_check(self, capability: dict[str, Any]) -> CapabilityCertificationCheck:
        dry_run = getattr(self._runtime_gateway, "certify_dry_run", None)
        if not callable(dry_run):
            return _warning(
                f"{capability.get('capability_id', 'capability')}_dry_run_invocation",
                "dry_run",
                "runtime gateway dry-run certification unavailable",
            )
        result = dry_run(str(capability.get("capability_id") or ""))
        return _check(
            f"{capability.get('capability_id', 'capability')}_dry_run_invocation",
            "dry_run",
            not bool(result.get("module_code_executed", False)),
            "dry-run invocation certification did not execute module code",
            "dry-run invocation attempted to execute module code",
            "critical",
            details=result,
        )

    def _sandbox_checks(self, capability: dict[str, Any]) -> list[CapabilityCertificationCheck]:
        metadata = capability.get("metadata", {})
        if not isinstance(metadata, dict):
            metadata = {}
        capability_id = str(capability.get("capability_id", "capability"))
        secret_refs = capability.get("secret_refs", metadata.get("secret_refs", []))
        connector_refs = capability.get("connector_refs", metadata.get("connector_refs", []))
        egress_rules = capability.get("egress_rules", metadata.get("egress_rules", []))
        runtime_permissions = capability.get(
            "runtime_permissions",
            metadata.get("runtime_permissions", []),
        )
        process_spawn = bool(
            capability.get("process_spawn_enabled") or metadata.get("process_spawn_enabled")
        )
        filesystem_write = bool(
            capability.get("filesystem_write_enabled") or metadata.get("filesystem_write_enabled")
        )
        return [
            _check(
                f"{capability_id}_sandbox_profile_declared",
                "runtime",
                bool(metadata.get("sandbox_profile_id"))
                or capability.get("execution_mode") == "sync",
                "sandbox profile declaration is acceptable",
                "non-local runtime capabilities require sandbox_profile_id",
                "medium",
            ),
            _check(
                f"{capability_id}_secret_refs_metadata_only",
                "boundary",
                isinstance(secret_refs, list),
                "secret refs are metadata-only list",
                "secret refs must be declared as references",
                "high",
            ),
            _check(
                f"{capability_id}_connector_refs_declared",
                "boundary",
                isinstance(connector_refs, list),
                "connector refs are declared as references",
                "connector refs must be declared as references",
                "high",
            ),
            _check(
                f"{capability_id}_runtime_permissions_explicit",
                "permissions",
                isinstance(runtime_permissions, list),
                "runtime permissions are explicit",
                "runtime permissions must be explicit",
                "high",
            ),
            _check(
                f"{capability_id}_no_wildcard_egress",
                "boundary",
                not _has_wildcard_egress(egress_rules),
                "wildcard egress is absent",
                "wildcard egress is denied",
                "critical",
            ),
            _check(
                f"{capability_id}_process_spawn_disabled",
                "runtime",
                not process_spawn,
                "process spawn is disabled",
                "process spawn is denied in v0.1",
                "critical",
            ),
            _check(
                f"{capability_id}_filesystem_write_controlled",
                "runtime",
                not filesystem_write,
                "filesystem write is not requested",
                "filesystem write requires explicit future approval path",
                "high",
            ),
        ]

    def _authorize(
        self,
        *,
        action_type: str,
        resource_id: str | None,
        risk_level: str,
        actor_id: str | None,
        workspace_id: str | None,
        owner_scope: list[str],
        context: dict[str, Any],
        raise_on_deny: bool = True,
    ) -> Any:
        authorize = cast(Any, self._policy_adapter).authorize
        decision = authorize(
            PolicyRequest(
                request_id=f"{action_type}-{uuid4().hex}",
                trace_id=None,
                actor_id=actor_id,
                workspace_id=workspace_id,
                action_type=action_type,
                resource_type="module_package",
                resource_id=resource_id,
                risk_level=risk_level,
                approval_present=True,
                requested_permissions=[action_type],
                security_scope=owner_scope,
                context={**context, "permissions": [action_type]},
            )
        )
        if raise_on_deny and not decision.allow:
            raise PermissionError(f"policy_denied:{decision.reason}")
        return decision

    def _emit(
        self,
        event_type: str,
        node_type: str,
        node_id: str,
        intensity: float,
        payload: dict[str, Any],
    ) -> None:
        emit = getattr(self._telemetry_service, "emit", None)
        if not callable(emit):
            return
        try:
            emit(
                VisualTelemetryEvent(
                    telemetry_id=f"telemetry-{event_type}-{uuid4().hex}",
                    trace_id=node_id,
                    event_type=cast(Any, event_type),
                    node_type=cast(Any, node_type),
                    node_id=node_id,
                    edge_from=None,
                    edge_to=node_id,
                    intensity=intensity,
                    payload=payload,
                    created_at=datetime.now(UTC),
                )
            )
        except Exception:
            return


def _capability_certification(
    package: ModulePackage,
    capability: dict[str, Any],
    checks: list[CapabilityCertificationCheck],
    *,
    certified_by: str | None,
) -> CapabilityCertification:
    return CapabilityCertification(
        certification_id=f"cap-cert-{uuid4().hex}",
        module_package_id=package.module_package_id,
        module_id=package.module_id,
        version=package.version,
        capability_id=str(capability.get("capability_id") or capability.get("name") or "unknown"),
        status=_status(checks),
        score=_score(checks),
        checks=checks,
        failures=[check.model_dump(mode="json") for check in checks if check.status == "failed"],
        warnings=[check.model_dump(mode="json") for check in checks if check.status == "warning"],
        certified_by=certified_by,
        created_at=datetime.now(UTC),
    )


def _has_required_failure(checks: list[CapabilityCertificationCheck]) -> bool:
    return any(
        check.status == "failed" and check.severity in {"high", "critical"} for check in checks
    )


def _status(checks: list[CapabilityCertificationCheck]) -> CertificationStatus:
    if _has_required_failure(checks):
        return "failed"
    if any(check.status == "warning" for check in checks) or any(
        check.status == "failed" for check in checks
    ):
        return "warning"
    return "passed"


def _score(checks: list[CapabilityCertificationCheck]) -> float:
    if not checks:
        return 0.0
    return sum(check.status == "passed" for check in checks) / len(checks)


def _warning(
    check_id: str,
    category: str,
    message: str,
) -> CapabilityCertificationCheck:
    return CapabilityCertificationCheck(
        check_id=check_id,
        name=check_id.replace("_", " "),
        category=cast(Any, category),
        status="warning",
        severity="medium",
        message=message,
        details={"module_code_executed": False},
    )


def _check(
    check_id: str,
    category: str,
    condition: bool,
    success_message: str,
    failure_message: str,
    severity: str,
    *,
    details: dict[str, Any] | None = None,
) -> CapabilityCertificationCheck:
    return CapabilityCertificationCheck(
        check_id=check_id,
        name=check_id.replace("_", " "),
        category=cast(Any, category),
        status="passed" if condition else "failed",
        severity=cast(Any, severity),
        message=success_message if condition else failure_message,
        details=details or {},
    )


def _has_wildcard_egress(value: object) -> bool:
    if isinstance(value, list):
        return any(
            isinstance(item, dict) and item.get("destination_type") == "wildcard" for item in value
        )
    return False
