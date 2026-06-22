"""Deterministic conformance runner."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.audit_integrity.ledger import record_audit_event
from aion_brain.config import Settings, get_settings
from aion_brain.conformance.mock_invocations import MockInvocationSimulator
from aion_brain.conformance.policy import authorize_conformance_action
from aion_brain.conformance.repository import ConformanceRepository
from aion_brain.conformance.schema_checks import SchemaConformanceChecker
from aion_brain.conformance.telemetry import emit_conformance_telemetry
from aion_brain.contracts.capability_bindings import CapabilityBinding
from aion_brain.contracts.conformance import (
    ConformanceFinding,
    ConformanceRun,
    ConformanceRunRequest,
)
from aion_brain.contracts.notifications import NotificationPublishRequest
from aion_brain.module_bindings.repository import ModuleBindingRepository
from aion_brain.policy_catalog.defaults import DEFAULT_ACTION_SPECS


class ConformanceRunner:
    """Run metadata-only conformance checks."""

    def __init__(
        self,
        repository: ConformanceRepository,
        policy_adapter: object,
        *,
        schema_checker: SchemaConformanceChecker,
        mock_simulator: MockInvocationSimulator,
        module_binding_repository: ModuleBindingRepository | None = None,
        contract_repository: object | None = None,
        policy_catalog_repository: object | None = None,
        autonomy_governor: object | None = None,
        notification_router: object | None = None,
        telemetry_service: object | None = None,
        audit_sink: object | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._schema_checker = schema_checker
        self._mock_simulator = mock_simulator
        self._module_binding_repository = module_binding_repository
        self._contract_repository = contract_repository
        self._policy_catalog_repository = policy_catalog_repository
        self._autonomy_governor = autonomy_governor
        self._notification_router = notification_router
        self._telemetry_service = telemetry_service
        self._audit_sink = audit_sink
        self._settings = settings or get_settings()

    def run(self, request: ConformanceRunRequest) -> ConformanceRun:
        if not self._settings.conformance_enabled:
            raise RuntimeError("conformance_disabled")
        authorize_conformance_action(
            self._policy_adapter,
            "conformance.run",
            request.owner_scope,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            trace_id=request.trace_id,
            resource_type="conformance_run",
            risk_level="medium",
            context={"mode": request.mode, "metadata_only": True},
        )
        self._check_autonomy(request)
        run_id = request.conformance_run_id or f"conformance-run-{uuid4().hex}"
        emit_conformance_telemetry(
            self._telemetry_service,
            event_type="conformance_run_started",
            node_type="conformance_run",
            node_id=run_id,
            scope=request.owner_scope,
            intensity=0.4,
            payload={"mode": request.mode},
        )
        profile = (
            self._repository.get_profile(request.conformance_profile_id)
            if request.conformance_profile_id
            else None
        )
        binding = self._load_binding(request)
        checks, findings = self._run_checks(request, binding)
        vectors = self._vectors(request, binding)
        mock_invocations = [
            self._mock_simulator.simulate(vector, binding, request.created_by) for vector in vectors
        ]
        for mock in mock_invocations:
            if mock.status in {"failed", "blocked"}:
                findings.append(
                    _finding(
                        "mock_invocation_failed",
                        "Mock invocation did not pass metadata checks.",
                        refs=[mock.mock_invocation_id],
                    )
                )
        findings = [
            item.model_copy(
                update={
                    "trace_id": request.trace_id,
                    "conformance_run_id": run_id,
                    "module_slot_id": request.module_slot_id
                    or (binding.module_slot_id if binding else None),
                    "capability_binding_id": request.capability_binding_id,
                    "extension_package_id": request.extension_package_id
                    or (binding.extension_package_id if binding else None),
                }
            )
            for item in findings
        ]
        blockers = [
            item.model_dump(mode="json")
            for item in findings
            if item.severity in {"high", "critical"}
        ]
        warnings = [
            item.model_dump(mode="json") for item in findings if item.severity in {"low", "medium"}
        ]
        minimum_score = profile.minimum_score if profile else 0.8
        score = max(0.0, min(1.0, 1.0 - (0.2 * len(blockers)) - (0.05 * len(warnings))))
        passed = score >= minimum_score and not blockers
        status = "dry_run" if request.mode == "dry_run" else "passed" if passed else "blocked"
        for finding in findings:
            self._repository.save_finding(finding)
        for mock in mock_invocations:
            self._repository.save_mock_invocation(mock)
        run = ConformanceRun(
            conformance_run_id=run_id,
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            status=cast(Any, status),
            mode=request.mode,
            owner_scope=request.owner_scope,
            conformance_profile_id=request.conformance_profile_id,
            module_slot_id=request.module_slot_id or (binding.module_slot_id if binding else None),
            capability_binding_id=request.capability_binding_id,
            extension_package_id=request.extension_package_id
            or (binding.extension_package_id if binding else None),
            checks_run=checks,
            test_vector_ids=[item.test_vector_id for item in vectors],
            mock_invocations=mock_invocations,
            findings=findings,
            score=score,
            passed=passed,
            blockers=blockers,
            warnings=warnings,
            result={
                "metadata_only": True,
                "source_records_mutated": False,
                "capability_executed": False,
                "extension_code_loaded": False,
                "activation_ready": False,
                "conformance_records_persisted": True,
            },
            metadata={**request.metadata, "source_mutated": False},
            created_by=request.created_by,
            created_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
        )
        saved = self._repository.save_run(run)
        self._record_audit(saved)
        self._maybe_notify(request, saved)
        emit_conformance_telemetry(
            self._telemetry_service,
            event_type="conformance_run_completed",
            node_type="conformance_run",
            node_id=saved.conformance_run_id,
            scope=saved.owner_scope,
            intensity=saved.score,
            payload={"status": saved.status, "score": saved.score},
        )
        return saved

    def get_run(self, conformance_run_id: str) -> ConformanceRun | None:
        return self._repository.get_run(conformance_run_id)

    def _run_checks(
        self,
        request: ConformanceRunRequest,
        binding: CapabilityBinding | None,
    ) -> tuple[list[str], list[ConformanceFinding]]:
        checks = [
            "required_contracts_present",
            "required_policy_actions_present",
            "required_settings_present",
            "sandbox_declared",
            "input_schema_valid",
            "output_schema_valid",
            "no_activation_enabled",
            "no_code_loading",
            "no_external_source",
            "no_domain_logic",
        ]
        findings: list[ConformanceFinding] = []
        if bool(getattr(self._settings, "conformance_code_execution_enabled", False)):
            findings.append(
                _finding("code_loading_enabled", "Conformance code execution is enabled.")
            )
        if bool(getattr(self._settings, "conformance_external_calls_enabled", False)):
            findings.append(
                _finding("external_source_enabled", "Conformance external calls are enabled.")
            )
        if bool(getattr(self._settings, "readiness_activation_enabled", False)):
            findings.append(
                _finding("activation_enabled", "Readiness activation must remain disabled.")
            )
        if bool(getattr(self._settings, "dynamic_route_registration_enabled", False)):
            findings.append(
                _finding("route_registration_enabled", "Dynamic route registration is enabled.")
            )
        if binding is not None:
            findings.extend(self._binding_findings(binding))
            for check in (
                self._schema_checker.validate_input_schema(binding),
                self._schema_checker.validate_output_schema(binding),
            ):
                for item in check.get("findings", []):
                    findings.append(
                        _finding(
                            cast(str, item.get("finding_type", "unsafe_metadata")),
                            cast(str, item.get("description", "Schema conformance failed.")),
                            severity=cast(str, item.get("severity", "high")),
                            refs=[binding.capability_binding_id],
                        )
                    )
        elif request.capability_binding_id:
            findings.append(_finding("generic", "Capability binding was not found."))
        return checks, findings

    def _binding_findings(self, binding: CapabilityBinding) -> list[ConformanceFinding]:
        findings: list[ConformanceFinding] = []
        for contract_key in binding.required_contracts:
            if not self._contract_exists(contract_key):
                findings.append(
                    _finding(
                        "missing_contract",
                        "Required contract is missing.",
                        refs=[binding.capability_binding_id, contract_key],
                    )
                )
        for action_type in binding.required_policy_actions:
            if not self._policy_action_exists(action_type):
                findings.append(
                    _finding(
                        "missing_policy_action",
                        "Required policy action is missing.",
                        refs=[binding.capability_binding_id, action_type],
                    )
                )
        for setting_key in binding.required_settings:
            if not hasattr(self._settings, setting_key):
                findings.append(
                    _finding(
                        "missing_setting",
                        "Required runtime setting is missing.",
                        severity="medium",
                        refs=[binding.capability_binding_id, setting_key],
                    )
                )
        if binding.requires_sandbox and not binding.sandbox_profile_id:
            findings.append(
                _finding(
                    "missing_sandbox",
                    "Required sandbox profile is missing.",
                    refs=[binding.capability_binding_id],
                )
            )
        return findings

    def _vectors(
        self,
        request: ConformanceRunRequest,
        binding: CapabilityBinding | None,
    ) -> list[Any]:
        vectors = [
            vector
            for vector_id in request.test_vector_ids
            if (vector := self._repository.get_vector(vector_id)) is not None
        ]
        if vectors:
            return vectors
        if binding is not None:
            existing = self._repository.list_vectors(
                capability_binding_id=binding.capability_binding_id,
                limit=20,
            )
            if existing:
                return existing
        return []

    def _load_binding(self, request: ConformanceRunRequest) -> CapabilityBinding | None:
        if self._module_binding_repository is None:
            return None
        if request.capability_binding_id:
            return self._module_binding_repository.get_binding(request.capability_binding_id)
        if request.module_slot_id:
            bindings = self._module_binding_repository.list_bindings(
                module_slot_id=request.module_slot_id,
                limit=1,
            )
            return bindings[0] if bindings else None
        return None

    def _contract_exists(self, contract_key: str) -> bool:
        list_contracts = getattr(self._contract_repository, "list_contracts", None)
        if not callable(list_contracts):
            return False
        return any(
            getattr(record, "contract_key", None) == contract_key
            for record in list_contracts(limit=1000)
        )

    def _policy_action_exists(self, action_type: str) -> bool:
        get_action = getattr(self._policy_catalog_repository, "get_action", None)
        if callable(get_action):
            action = get_action(action_type)
            if action is not None:
                return True
        return action_type in {spec[0] for spec in DEFAULT_ACTION_SPECS}

    def _check_autonomy(self, request: ConformanceRunRequest) -> None:
        authorize = getattr(self._autonomy_governor, "authorize", None)
        if callable(authorize):
            try:
                authorize("conformance.run", request.owner_scope)
            except TypeError:
                return

    def _record_audit(self, run: ConformanceRun) -> None:
        record_audit_event(
            self._audit_sink,
            action_type="conformance.run",
            resource_type="conformance_run",
            resource_id=run.conformance_run_id,
            event_type="conformance_run_completed",
            outcome="completed" if run.status not in {"failed", "blocked"} else "blocked",
            source_component="conformance_harness",
            trace_id=run.trace_id,
            actor_id=run.actor_id,
            workspace_id=run.workspace_id,
            risk_level="medium",
            payload={"status": run.status, "score": run.score, "metadata_only": True},
        )

    def _maybe_notify(self, request: ConformanceRunRequest, run: ConformanceRun) -> None:
        if not (
            request.create_notifications
            or bool(getattr(self._settings, "conformance_create_notifications_default", False))
        ):
            return
        publish = getattr(self._notification_router, "publish", None)
        if not callable(publish):
            return
        try:
            publish(
                NotificationPublishRequest(
                    trace_id=request.trace_id,
                    actor_id=request.actor_id,
                    workspace_id=request.workspace_id,
                    topic_key="generic.info",
                    severity="medium" if run.blockers else "info",
                    title="Conformance run completed",
                    message=f"Conformance run {run.conformance_run_id} completed.",
                    source_type="generic",
                    source_id=run.conformance_run_id,
                    target_type="operator",
                    target_id="operator",
                    owner_scope=run.owner_scope,
                    refs=[run.conformance_run_id],
                    metadata={"status": run.status, "metadata_only": True},
                    created_by=request.created_by,
                )
            )
        except Exception:
            return


def _finding(
    finding_type: str,
    description: str,
    *,
    severity: str = "high",
    refs: list[str] | None = None,
) -> ConformanceFinding:
    return ConformanceFinding(
        conformance_finding_id=f"conformance-finding-{uuid4().hex}",
        finding_type=cast(Any, finding_type),
        severity=cast(Any, severity),
        status="open",
        title=finding_type.replace("_", " "),
        description=description,
        recommended_action="Review and update staged metadata before future activation.",
        refs=refs or [],
        metadata={"metadata_only": True},
        created_at=datetime.now(UTC),
    )


__all__ = ["ConformanceRunner"]
