"""Capability Runtime Gateway for module bus invocation."""

from collections.abc import Mapping
from datetime import UTC, datetime
from time import perf_counter
from typing import Any, cast

from aion_brain.approvals.integration import evaluate_approval_gate
from aion_brain.capabilities.registry import CapabilityRegistry
from aion_brain.contracts.autonomy import AutonomyDecisionRequest
from aion_brain.contracts.modules import (
    CapabilityBindingRequest,
    CapabilityInvocationRequest,
    CapabilityInvocationResult,
    CapabilityInvocationResultStatus,
    CapabilityRuntimeBinding,
    ModuleHealthCheck,
    ModuleHealthCheckStatus,
    ModuleRuntime,
    ModuleRuntimeRegistrationRequest,
    ModuleRuntimeRegistrationResponse,
)
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.sandbox import SandboxRunRequest
from aion_brain.contracts.telemetry import VisualTelemetryEvent
from aion_brain.modules.http_runtime import HttpRuntimeAdapter
from aion_brain.modules.local_internal_runtime import LocalInternalRuntimeAdapter
from aion_brain.modules.local_stub_runtime import LocalStubRuntimeAdapter
from aion_brain.modules.mcp_runtime import MCPRuntimeAdapter
from aion_brain.modules.repository import ModuleRuntimeRepository
from aion_brain.modules.runtime_base import CapabilityRuntimeAdapter
from aion_brain.policy.base import PolicyAdapter


class CapabilityRuntimeGateway:
    """Policy-gated capability runtime gateway."""

    def __init__(
        self,
        *,
        module_runtime_repository: ModuleRuntimeRepository | object,
        capability_registry: CapabilityRegistry | object,
        policy_adapter: PolicyAdapter,
        telemetry_service: object | None = None,
        runtime_adapters: Mapping[str, CapabilityRuntimeAdapter] | None = None,
        approval_service: object | None = None,
        autonomy_governor: object | None = None,
        sandbox_service: object | None = None,
    ) -> None:
        self._repository = module_runtime_repository
        self._capability_registry = capability_registry
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._runtime_adapters = dict(runtime_adapters or _default_runtime_adapters())
        self._approval_service = approval_service
        self._autonomy_governor = autonomy_governor
        self._sandbox_service = sandbox_service

    def register_runtime(
        self,
        request: ModuleRuntimeRegistrationRequest,
    ) -> ModuleRuntimeRegistrationResponse:
        """Register a module runtime and optional capability bindings."""
        decision = self._authorize(
            action_type="module.runtime.register",
            resource_type="module_runtime",
            resource_id=request.runtime.runtime_id,
            risk_level="medium",
            trace_id=None,
            actor_id=None,
            workspace_id=None,
            approval_present=True,
            context={
                "runtime_id": request.runtime.runtime_id,
                "runtime_type": request.runtime.runtime_type,
            },
        )
        if not decision.allow:
            return ModuleRuntimeRegistrationResponse(
                registered=False,
                runtime_id=request.runtime.runtime_id,
                module_id=request.runtime.module_id,
                version=request.runtime.version,
                binding_count=0,
                status="blocked_by_policy",
                reason=decision.reason,
            )
        if not _module_exists(
            self._capability_registry,
            request.runtime.module_id,
            request.runtime.version,
        ):
            return ModuleRuntimeRegistrationResponse(
                registered=False,
                runtime_id=request.runtime.runtime_id,
                module_id=request.runtime.module_id,
                version=request.runtime.version,
                binding_count=0,
                status="module_not_found",
                reason="capability_manifest_not_found",
            )

        status = "active" if request.activate else request.runtime.status
        saved_runtime = self._save_runtime(request.runtime.model_copy(update={"status": status}))
        binding_count = 0
        for capability_id in request.bind_capabilities:
            binding = self.bind_capability(
                CapabilityBindingRequest(
                    capability_id=capability_id,
                    module_id=saved_runtime.module_id,
                    runtime_id=saved_runtime.runtime_id,
                    invocation_mode="controlled",
                    status="active",
                )
            )
            if binding.status == "active":
                binding_count += 1
        self._emit_runtime_registered(saved_runtime)
        return ModuleRuntimeRegistrationResponse(
            registered=True,
            runtime_id=saved_runtime.runtime_id,
            module_id=saved_runtime.module_id,
            version=saved_runtime.version,
            binding_count=binding_count,
            status=saved_runtime.status,
            reason=None,
        )

    def bind_capability(self, request: CapabilityBindingRequest) -> CapabilityRuntimeBinding:
        """Bind a capability contract to a registered runtime."""
        decision = self._authorize(
            action_type="capability.bind_runtime",
            resource_type="capability",
            resource_id=request.capability_id,
            risk_level="medium",
            trace_id=None,
            actor_id=None,
            workspace_id=None,
            approval_present=True,
            context={"runtime_id": request.runtime_id, "mode": request.invocation_mode},
        )
        if not decision.allow:
            raise ValueError(f"policy_denied:{decision.reason}")
        if not _capability_exists(self._capability_registry, request.capability_id):
            raise ValueError("capability_not_found")
        if self.get_runtime(request.runtime_id) is None:
            raise ValueError("runtime_not_found")
        binding = CapabilityRuntimeBinding(
            binding_id=_binding_id(
                request.capability_id,
                request.runtime_id,
                request.invocation_mode,
            ),
            capability_id=request.capability_id,
            module_id=request.module_id,
            runtime_id=request.runtime_id,
            invocation_mode=request.invocation_mode,
            status=request.status,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        return self._save_binding(binding)

    def list_runtimes(self) -> list[ModuleRuntime]:
        """Return registered runtimes."""
        return _call_list_runtimes(self._repository)

    def get_runtime(self, runtime_id: str) -> ModuleRuntime | None:
        """Return a runtime by ID."""
        get_runtime = getattr(self._repository, "get_runtime", None)
        if callable(get_runtime):
            result = get_runtime(runtime_id)
            if isinstance(result, ModuleRuntime) or result is None:
                return result
        return None

    def health_check(self, runtime_id: str) -> ModuleHealthCheck:
        """Run and persist a runtime health check."""
        decision = self._authorize(
            action_type="module.runtime.health_check",
            resource_type="module_runtime",
            resource_id=runtime_id,
            risk_level="low",
            trace_id=None,
            actor_id=None,
            workspace_id=None,
            approval_present=False,
            context={},
        )
        runtime = self.get_runtime(runtime_id)
        if runtime is None:
            return _health(runtime_id, "unknown", "unhealthy", {"reason": "runtime_not_found"})
        if not decision.allow:
            health = _health(
                runtime.runtime_id,
                runtime.module_id,
                "unhealthy",
                {"reason": decision.reason},
            )
            return self._persist_health(health)

        adapter = self._runtime_adapters[runtime.runtime_type]
        try:
            health = adapter.health_check(runtime)
        except NotImplementedError as exc:
            health = _health(
                runtime.runtime_id,
                runtime.module_id,
                "degraded",
                {"reason": "runtime_not_implemented", "detail": str(exc)},
            )
        except Exception as exc:
            health = _health(
                runtime.runtime_id,
                runtime.module_id,
                "unhealthy",
                {"reason": "runtime_health_check_failed", "detail": str(exc)},
            )
        return self._persist_health(health)

    def certify_dry_run(self, capability_id: str) -> dict[str, Any]:
        """Return dry-run certification metadata without invoking a runtime."""

        return {
            "capability_id": capability_id,
            "dry_run": True,
            "module_code_executed": False,
            "external_calls": False,
            "runtime_invocation": "not_executed",
        }

    def invoke(self, request: CapabilityInvocationRequest) -> CapabilityInvocationResult:
        """Invoke a capability through policy, binding, runtime, and telemetry boundaries."""
        started = perf_counter()
        self._emit_capability_started(request)
        decision = self._authorize(
            action_type="capability.invoke",
            resource_type="capability",
            resource_id=request.capability_id,
            risk_level=_risk_level(request),
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            approval_present=request.approval_present,
            context={"mode": request.mode, "capability_id": request.capability_id},
        )
        if not decision.allow:
            return self._result(
                request,
                None,
                "blocked_by_policy",
                {"invoked": False, "reason": decision.reason},
                {},
                decision.decision_id,
                started,
            )
        autonomy = self._autonomy_decision(request)
        if autonomy is not None and not bool(getattr(autonomy, "allow", False)):
            return self._result(
                request,
                None,
                "blocked_by_policy",
                {},
                {
                    "reason": str(getattr(autonomy, "reason", "autonomy_denied")),
                    "autonomy_decision_id": getattr(autonomy, "autonomy_decision_id", None),
                },
                decision.decision_id,
                started,
            )
        if not _capability_exists(self._capability_registry, request.capability_id):
            return self._result(
                request,
                None,
                "capability_not_found",
                {"invoked": False},
                {"reason": "capability_not_found"},
                decision.decision_id,
                started,
            )
        sandbox_error = self._sandbox_boundary_error(request)
        if sandbox_error is not None:
            return self._result(
                request,
                None,
                "blocked_by_policy",
                {},
                sandbox_error,
                decision.decision_id,
                started,
            )
        if request.mode == "dry_run":
            return self._result(
                request,
                None,
                "dry_run",
                {
                    "dry_run": True,
                    "capability_id": request.capability_id,
                    "runtime_id": None,
                    "message": "Capability invocation validated but not executed.",
                },
                {},
                decision.decision_id,
                started,
            )

        if _requires_control_plane_approval(request):
            gate = evaluate_approval_gate(
                self._approval_service,
                trace_id=request.trace_id,
                actor_id=request.actor_id,
                workspace_id=request.workspace_id,
                action_type="capability.invoke",
                resource_type="capability",
                resource_id=request.capability_id,
                requested_risk_level=_risk_level(request),
                security_scope=_scope(request.metadata),
                payload={"capability_id": request.capability_id},
                context={
                    "mode": request.mode,
                    "approval_present": request.approval_present,
                    "invokes_capability": True,
                    "external_effect_possible": bool(
                        request.metadata.get("external_effect_possible")
                    ),
                    "controlled_execution": request.mode == "controlled",
                },
                metadata=request.metadata,
            )
            if gate is not None and gate.final_decision != "allow":
                return self._result(
                    request,
                    None,
                    "blocked_by_policy",
                    {},
                    {
                        "reason": (
                            gate.reason
                            if gate.final_decision == "block"
                            else "approval_required"
                        ),
                        "approval_request_id": gate.approval_request_id,
                    },
                    decision.decision_id,
                    started,
                )

        binding = _active_binding(self._repository, request.capability_id, request.mode)
        if binding is None:
            return self._result(
                request,
                None,
                "runtime_not_found",
                {"invoked": False},
                {"reason": "runtime_binding_not_found"},
                decision.decision_id,
                started,
            )
        runtime = self.get_runtime(binding.runtime_id)
        if runtime is None or runtime.status == "disabled":
            return self._result(
                request,
                binding.runtime_id,
                "runtime_not_found",
                {"invoked": False},
                {"reason": "runtime_not_found"},
                decision.decision_id,
                started,
            )
        if runtime.health_status == "unhealthy":
            return self._result(
                request,
                runtime.runtime_id,
                "runtime_unhealthy",
                {"invoked": False},
                {"reason": "runtime_unhealthy"},
                decision.decision_id,
                started,
            )
        try:
            result = self._runtime_adapters[runtime.runtime_type].invoke(request, runtime)
        except NotImplementedError as exc:
            result = self._result(
                request,
                runtime.runtime_id,
                "not_implemented",
                {"invoked": False},
                {"reason": "runtime_not_implemented", "detail": str(exc)},
                decision.decision_id,
                started,
                emit=False,
            )
        except Exception as exc:
            result = self._result(
                request,
                runtime.runtime_id,
                "failed",
                {"invoked": False},
                {"reason": "runtime_invocation_failed", "detail": str(exc)},
                decision.decision_id,
                started,
                emit=False,
            )
        if result.policy_decision_id is None:
            result = result.model_copy(update={"policy_decision_id": decision.decision_id})
        self._emit_capability_recorded(result)
        return result

    def _sandbox_boundary_error(
        self,
        request: CapabilityInvocationRequest,
    ) -> dict[str, Any] | None:
        sandbox_profile_id = request.metadata.get("sandbox_profile_id")
        if sandbox_profile_id is None:
            return None
        if self._sandbox_service is None:
            return {"reason": "sandbox_service_unavailable"}
        profile_id = str(sandbox_profile_id)
        has_grant = getattr(self._sandbox_service, "has_active_grant", None)
        if callable(has_grant) and not bool(
            has_grant(
                target_type="capability",
                target_id=request.capability_id,
                sandbox_profile_id=profile_id,
            )
        ):
            return {"reason": "runtime_permission_grant_required"}
        run = getattr(self._sandbox_service, "run", None)
        if not callable(run):
            return {"reason": "sandbox_service_unavailable"}
        result = run(
            SandboxRunRequest(
                trace_id=request.trace_id,
                actor_id=request.actor_id,
                workspace_id=request.workspace_id,
                sandbox_profile_id=profile_id,
                target_type="capability",
                target_id=request.capability_id,
                mode=request.mode,
                input={"capability_id": request.capability_id},
                approval_present=request.approval_present,
                metadata={"source": "module_runtime_gateway"},
            )
        )
        status = str(getattr(result, "status", "failed"))
        if status not in {"dry_run", "completed"}:
            return {
                "reason": "sandbox_validation_failed",
                "sandbox_run_id": getattr(result, "sandbox_run_id", None),
                "sandbox_status": status,
            }
        return None

    def _authorize(
        self,
        *,
        action_type: str,
        resource_type: str,
        resource_id: str | None,
        risk_level: str,
        trace_id: str | None,
        actor_id: str | None,
        workspace_id: str | None,
        approval_present: bool,
        context: dict[str, Any],
    ) -> PolicyDecision:
        return self._policy_adapter.authorize(
            PolicyRequest(
                request_id=f"{action_type}-{resource_id or 'module-bus'}",
                trace_id=trace_id,
                actor_id=actor_id,
                workspace_id=workspace_id,
                action_type=action_type,
                resource_type=resource_type,
                resource_id=resource_id,
                risk_level=risk_level,
                approval_present=approval_present,
                requested_permissions=[],
                security_scope=_scope(context),
                context=context,
            )
        )

    def _autonomy_decision(self, request: CapabilityInvocationRequest) -> object | None:
        decide = getattr(self._autonomy_governor, "decide", None)
        if not callable(decide):
            return None
        requested_mode = "dry_run" if request.mode == "dry_run" else "supervised_controlled"
        return cast(
            object,
            decide(
                AutonomyDecisionRequest(
                    trace_id=request.trace_id,
                    actor_id=request.actor_id,
                    workspace_id=request.workspace_id,
                    requested_mode=cast(Any, requested_mode),
                    action_type="capability.invoke",
                    resource_type="capability",
                    resource_id=request.capability_id,
                    risk_level=cast(Any, _risk_level(request)),
                    approval_present=request.approval_present,
                    delegation_id=_metadata_str(request.metadata, "delegation_id"),
                    context={
                        "mode": request.mode,
                        "security_scope": _scope(request.metadata),
                        "uses_external_tool": request.mode == "controlled",
                    },
                    metadata=request.metadata,
                )
            ),
        )

    def _save_runtime(self, runtime: ModuleRuntime) -> ModuleRuntime:
        save_runtime = getattr(self._repository, "save_runtime", None)
        if callable(save_runtime):
            result = save_runtime(runtime)
            if isinstance(result, ModuleRuntime):
                return result
        return runtime

    def _save_binding(self, binding: CapabilityRuntimeBinding) -> CapabilityRuntimeBinding:
        save_binding = getattr(self._repository, "save_binding", None)
        if callable(save_binding):
            result = save_binding(binding)
            if isinstance(result, CapabilityRuntimeBinding):
                return result
        return binding

    def _persist_health(self, health: ModuleHealthCheck) -> ModuleHealthCheck:
        save_health_check = getattr(self._repository, "save_health_check", None)
        if callable(save_health_check):
            save_health_check(health)
        update_health = getattr(self._repository, "update_runtime_health", None)
        if callable(update_health):
            update_health(health.runtime_id, health.status, health.created_at)
        self._emit_health_checked(health)
        return health

    def _result(
        self,
        request: CapabilityInvocationRequest,
        runtime_id: str | None,
        status: str,
        output: dict[str, Any],
        error: dict[str, Any],
        policy_decision_id: str | None,
        started: float,
        *,
        emit: bool = True,
    ) -> CapabilityInvocationResult:
        result = CapabilityInvocationResult(
            invocation_id=request.invocation_id,
            capability_id=request.capability_id,
            runtime_id=runtime_id,
            status=cast(CapabilityInvocationResultStatus, status),
            output=output,
            error=error,
            policy_decision_id=policy_decision_id,
            latency_ms=max(0, int((perf_counter() - started) * 1000)),
            created_at=datetime.now(UTC),
        )
        if emit:
            self._emit_capability_recorded(result)
        return result

    def _emit_runtime_registered(self, runtime: ModuleRuntime) -> None:
        self._emit(
            VisualTelemetryEvent(
                telemetry_id=f"telemetry-{runtime.runtime_id}-module-runtime-registered",
                trace_id=runtime.runtime_id,
                event_type="module_runtime_registered",
                node_type="runtime",
                node_id=runtime.runtime_id,
                edge_from=runtime.module_id,
                edge_to=runtime.runtime_id,
                intensity=0.5,
                payload={"module_id": runtime.module_id, "runtime_type": runtime.runtime_type},
                created_at=datetime.now(UTC),
            )
        )

    def _emit_health_checked(self, health: ModuleHealthCheck) -> None:
        intensities = {"healthy": 0.8, "degraded": 0.5, "unhealthy": 0.2}
        self._emit(
            VisualTelemetryEvent(
                telemetry_id=f"telemetry-{health.health_check_id}-module-health-checked",
                trace_id=health.runtime_id,
                event_type="module_health_checked",
                node_type="runtime",
                node_id=health.runtime_id,
                edge_from=health.module_id,
                edge_to=health.health_check_id,
                intensity=intensities[health.status],
                payload={"status": health.status, **health.details},
                created_at=health.created_at,
            )
        )

    def _emit_capability_started(self, request: CapabilityInvocationRequest) -> None:
        self._emit(
            VisualTelemetryEvent(
                telemetry_id=f"telemetry-{request.invocation_id}-capability-invocation-started",
                trace_id=request.trace_id or request.invocation_id,
                event_type="capability_invocation_started",
                node_type="capability",
                node_id=request.capability_id,
                edge_from=request.step_run_id,
                edge_to=request.invocation_id,
                intensity=0.6,
                payload={"mode": request.mode},
                created_at=datetime.now(UTC),
            )
        )

    def _emit_capability_recorded(self, result: CapabilityInvocationResult) -> None:
        intensities = {
            "completed": 1.0,
            "dry_run": 0.5,
            "not_implemented": 0.3,
            "blocked_by_policy": 0.8,
            "capability_not_found": 0.9,
            "runtime_not_found": 0.9,
            "runtime_unhealthy": 0.9,
            "failed": 0.9,
        }
        self._emit(
            VisualTelemetryEvent(
                telemetry_id=f"telemetry-{result.invocation_id}-capability-invocation-recorded",
                trace_id=result.invocation_id,
                event_type="capability_invocation_recorded",
                node_type="capability",
                node_id=result.capability_id,
                edge_from=result.runtime_id,
                edge_to=result.invocation_id,
                intensity=intensities[result.status],
                payload={"status": result.status, "runtime_id": result.runtime_id},
                created_at=result.created_at,
            )
        )

    def _emit(self, event: VisualTelemetryEvent) -> None:
        if self._telemetry_service is None:
            return
        try:
            emit = getattr(self._telemetry_service, "emit", None)
            if callable(emit):
                emit(event)
                return
            save = getattr(self._telemetry_service, "save_visual_telemetry", None)
            if callable(save):
                save(event.trace_id, [event])
        except Exception:
            return


def _default_runtime_adapters() -> dict[str, CapabilityRuntimeAdapter]:
    return {
        "local_internal": LocalInternalRuntimeAdapter(),
        "local_stub": LocalStubRuntimeAdapter(),
        "http": HttpRuntimeAdapter(),
        "mcp": MCPRuntimeAdapter(),
    }


def _module_exists(registry: object, module_id: str, version: str) -> bool:
    for manifest in _manifests(registry):
        module_matches = getattr(manifest, "module_id", None) == module_id
        version_matches = getattr(manifest, "version", None) == version
        if module_matches and version_matches:
            return True
    return False


def _capability_exists(registry: object, capability_id: str) -> bool:
    capability_exists = getattr(registry, "capability_exists", None)
    if callable(capability_exists) and bool(capability_exists(capability_id)):
        return True
    for manifest in _manifests(registry):
        for capability in getattr(manifest, "capabilities", []):
            if isinstance(capability, dict) and capability_id in {
                capability.get("capability_id"),
                capability.get("id"),
            }:
                return True
            if getattr(capability, "capability_id", None) == capability_id:
                return True
    return False


def _manifests(registry: object) -> list[object]:
    list_manifests = getattr(registry, "list_manifests", None)
    if not callable(list_manifests):
        return []
    result = list_manifests()
    if isinstance(result, list):
        return result
    return []


def _active_binding(
    repository: object,
    capability_id: str,
    mode: str,
) -> CapabilityRuntimeBinding | None:
    get_active_binding = getattr(repository, "get_active_binding", None)
    if callable(get_active_binding):
        result = get_active_binding(capability_id, mode)
        if isinstance(result, CapabilityRuntimeBinding) or result is None:
            return result
    return None


def _call_list_runtimes(repository: object) -> list[ModuleRuntime]:
    list_runtimes = getattr(repository, "list_runtimes", None)
    if callable(list_runtimes):
        result = list_runtimes()
        if isinstance(result, list):
            return [runtime for runtime in result if isinstance(runtime, ModuleRuntime)]
    return []


def _binding_id(capability_id: str, runtime_id: str, mode: str) -> str:
    safe_capability_id = capability_id.replace(".", "-").replace(":", "-")
    return f"binding-{safe_capability_id}-{runtime_id}-{mode}"


def _risk_level(request: CapabilityInvocationRequest) -> str:
    value = request.metadata.get("risk_level")
    if isinstance(value, str):
        return value
    return "low" if request.mode == "dry_run" else "medium"


def _requires_control_plane_approval(request: CapabilityInvocationRequest) -> bool:
    if request.approval_present or request.mode != "controlled":
        return False
    return _risk_level(request) in {"high", "critical"} or bool(
        request.metadata.get("external_effect_possible")
    )


def _scope(context: dict[str, Any]) -> list[str]:
    value = context.get("security_scope")
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return value
    return ["workspace:main"]


def _metadata_str(metadata: dict[str, Any], key: str) -> str | None:
    value = metadata.get(key)
    return value if isinstance(value, str) and value else None


def _health(
    runtime_id: str,
    module_id: str,
    status: str,
    details: dict[str, Any],
) -> ModuleHealthCheck:
    return ModuleHealthCheck(
        health_check_id=f"health-{runtime_id}-{datetime.now(UTC).strftime('%Y%m%d%H%M%S%f')}",
        runtime_id=runtime_id,
        module_id=module_id,
        status=cast(ModuleHealthCheckStatus, status),
        latency_ms=0,
        details=details,
        created_at=datetime.now(UTC),
    )
