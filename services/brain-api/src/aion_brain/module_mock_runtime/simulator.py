"""Deterministic module mock runtime simulator."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.api_support.errors import AIONNotFoundException
from aion_brain.audit_integrity.ledger import record_audit_event
from aion_brain.config import Settings, get_settings
from aion_brain.contracts.capability_bindings import CapabilityBinding
from aion_brain.contracts.module_mock_runtime import (
    ModuleMockFinding,
    ModuleMockInvocationCreateRequest,
    ModuleMockInvocationRequest,
    ModuleMockOutput,
    ModuleMockRun,
)
from aion_brain.module_mock_runtime.hash import hash_mock_output, hash_mock_payload
from aion_brain.module_mock_runtime.policy import authorize_module_mock_action
from aion_brain.module_mock_runtime.redaction import redact_module_mock_payload
from aion_brain.module_mock_runtime.repository import ModuleMockRuntimeRepository
from aion_brain.module_mock_runtime.schema_adapter import ModuleMockSchemaAdapter
from aion_brain.versioning.compatibility import emit_versioning_telemetry

_SAFE_TARGET_RUNTIMES = {"metadata_only", "noop", "sandbox"}


class ModuleMockSimulator:
    """Produce synthetic dry-run records without loading or executing module code."""

    def __init__(
        self,
        repository: ModuleMockRuntimeRepository,
        policy_adapter: object,
        *,
        module_binding_repository: object | None = None,
        schema_adapter: ModuleMockSchemaAdapter | None = None,
        telemetry_service: object | None = None,
        audit_sink: object | None = None,
        provenance_service: object | None = None,
        notification_router: object | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._module_binding_repository = module_binding_repository
        self._schema_adapter = schema_adapter or ModuleMockSchemaAdapter()
        self._telemetry_service = telemetry_service
        self._audit_sink = audit_sink
        self._provenance_service = provenance_service
        self._notification_router = notification_router
        self._settings = settings or get_settings()

    def invoke(self, request: ModuleMockInvocationCreateRequest) -> ModuleMockRun:
        """Persist a deterministic dry-run invocation record."""

        self._guard_settings()
        authorize_module_mock_action(
            self._policy_adapter,
            "module_mock.invoke",
            request.owner_scope,
            actor_id=request.actor_id or request.created_by,
            workspace_id=request.workspace_id,
            trace_id=request.trace_id,
            resource_type="module_mock_invocation",
            risk_level="medium",
            context={
                "mode": request.mode,
                "metadata_only": True,
                "activation_allowed": False,
                "execution_allowed": False,
            },
        )
        now = datetime.now(UTC)
        run_id = f"module-mock-run-{uuid4().hex}"
        request_id = request.mock_invocation_request_id or f"module-mock-request-{uuid4().hex}"
        self._emit(
            "module_mock_invocation_started",
            request_id,
            request.owner_scope,
            0.3,
            {"capability_binding_id": request.capability_binding_id},
        )
        binding = self._load_binding(request.capability_binding_id)
        profile = self._load_profile(request.mock_profile_id)
        redacted_input = cast(dict[str, Any], redact_module_mock_payload(request.input_payload))
        schema_check = self._schema_adapter.validate_input(redacted_input, binding)
        output_shape = self._schema_adapter.normalize_output_shape(
            request.expected_output_shape,
            binding,
        )
        output_shape_check = self._schema_adapter.validate_output_shape(output_shape, binding)
        findings = self._findings_for(request, binding, profile, schema_check, output_shape_check)
        request_record = ModuleMockInvocationRequest(
            mock_invocation_request_id=request_id,
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            mock_profile_id=request.mock_profile_id,
            extension_package_id=request.extension_package_id
            or getattr(binding, "extension_package_id", None),
            module_slot_id=request.module_slot_id or getattr(binding, "module_slot_id", None),
            capability_binding_id=request.capability_binding_id,
            capability_key=request.capability_key,
            invocation_type=request.invocation_type,
            mode="dry_run",
            owner_scope=request.owner_scope,
            input_payload_hash=hash_mock_payload(request.input_payload),
            redacted_input_payload=redacted_input,
            expected_output_shape=output_shape,
            evidence_refs=request.evidence_refs,
            policy_refs=request.policy_refs,
            sandbox_refs=request.sandbox_refs,
            metadata={
                **request.metadata,
                "metadata_only": True,
                "activation_allowed": False,
                "execution_allowed": False,
            },
            created_by=request.created_by,
            created_at=now,
        )
        output_payload = self._synthetic_output_payload(request, binding, profile, output_shape)
        output = ModuleMockOutput(
            module_mock_output_id=f"module-mock-output-{uuid4().hex}",
            trace_id=request.trace_id,
            module_mock_run_id=run_id,
            capability_binding_id=request.capability_binding_id,
            capability_key=request.capability_key,
            output_type=cast(Any, _output_type_for(request.invocation_type)),
            status="warning" if findings else "created",
            output_payload_hash=hash_mock_output(output_payload),
            redacted_output_payload=output_payload,
            output_summary="Synthetic deterministic module mock output.",
            confidence=0.65 if findings else 0.9,
            evidence_refs=request.evidence_refs,
            metadata={"synthetic": True, "metadata_only": True},
            created_by=request.created_by,
            created_at=now,
        )
        saved_request = self._repository.save_request(request_record)
        saved_output = self._repository.save_output(output)
        saved_findings = [
            self._repository.save_finding(
                finding.model_copy(
                    update={
                        "module_mock_run_id": run_id,
                        "mock_invocation_request_id": request_id,
                    }
                )
            )
            for finding in findings
        ]
        blocking = [
            item
            for item in saved_findings
            if item.severity in {"high", "critical"} and item.status == "open"
        ]
        status = "blocked" if blocking else "warning" if saved_findings else "passed"
        run = ModuleMockRun(
            module_mock_run_id=run_id,
            trace_id=request.trace_id,
            mock_invocation_request_id=saved_request.mock_invocation_request_id,
            mock_profile_id=request.mock_profile_id,
            extension_package_id=saved_request.extension_package_id,
            module_slot_id=saved_request.module_slot_id,
            capability_binding_id=request.capability_binding_id,
            status=cast(Any, status),
            mode="dry_run",
            owner_scope=request.owner_scope,
            checks_run=[
                "policy_authorized",
                "binding_metadata_loaded",
                "profile_metadata_loaded",
                "input_redacted",
                "input_shape_validated",
                "output_shape_validated",
                "synthetic_output_created",
                "execution_flags_blocked",
            ],
            output=saved_output,
            findings=saved_findings,
            score=0.0 if blocking else 0.7 if saved_findings else 1.0,
            schema_valid=bool(schema_check["valid"] and output_shape_check["valid"]),
            policy_valid=True,
            sandbox_valid=True,
            activation_allowed=False,
            execution_allowed=False,
            external_calls_made=False,
            code_loaded=False,
            warnings=[item.model_dump(mode="json") for item in saved_findings],
            failures=[item.model_dump(mode="json") for item in blocking],
            result={
                "synthetic": True,
                "metadata_only": True,
                "activation_allowed": False,
                "execution_allowed": False,
                "external_calls_made": False,
                "code_loaded": False,
                "capability_executed": False,
                "source_records_mutated": False,
            },
            metadata={
                **request.metadata,
                "profile_key": getattr(profile, "profile_key", None),
                "binding_status": getattr(binding, "status", None),
            },
            created_by=request.created_by,
            created_at=now,
            completed_at=now,
        )
        saved = self._repository.save_run(run)
        self._record_audit(saved)
        self._record_provenance(saved)
        self._maybe_notify(saved, request.create_notifications)
        self._emit(
            "module_mock_output",
            saved_output.module_mock_output_id,
            saved.owner_scope,
            saved_output.confidence,
            {"status": saved_output.status},
            node_type="module_mock_output",
        )
        self._emit(
            "module_mock_invocation_completed",
            saved.module_mock_run_id,
            saved.owner_scope,
            saved.score,
            {"status": saved.status, "finding_count": len(saved.findings)},
        )
        return saved

    def get_run(self, module_mock_run_id: str, scope: list[str]) -> ModuleMockRun:
        """Return one run inside scope."""

        authorize_module_mock_action(
            self._policy_adapter,
            "module_mock.run.read",
            scope,
            resource_type="module_mock_run",
            resource_id=module_mock_run_id,
            risk_level="low",
        )
        run = self._repository.get_run(module_mock_run_id)
        if run is None or not _in_scope(run.owner_scope, scope):
            raise AIONNotFoundException("module_mock_run_not_found")
        return run

    def list_runs(
        self,
        scope: list[str],
        *,
        status: str | None = None,
        capability_binding_id: str | None = None,
        limit: int = 100,
    ) -> list[ModuleMockRun]:
        """List dry-run records inside scope."""

        authorize_module_mock_action(
            self._policy_adapter,
            "module_mock.run.read",
            scope,
            resource_type="module_mock_run",
            risk_level="low",
        )
        return [
            item
            for item in self._repository.list_runs(
                capability_binding_id=capability_binding_id,
                status=status,
                limit=limit,
            )
            if _in_scope(item.owner_scope, scope)
        ]

    def _guard_settings(self) -> None:
        if not self._settings.module_mock_runtime_enabled:
            raise RuntimeError("module_mock_runtime_disabled")
        if not self._settings.module_mock_invocation_enabled:
            raise RuntimeError("module_mock_invocation_disabled")
        unsafe = {
            "module_mock_controlled_execution_enabled": (
                self._settings.module_mock_controlled_execution_enabled
            ),
            "module_mock_code_loading_enabled": self._settings.module_mock_code_loading_enabled,
            "module_mock_external_calls_enabled": self._settings.module_mock_external_calls_enabled,
        }
        enabled = [key for key, value in unsafe.items() if value]
        if enabled:
            raise RuntimeError(f"module_mock_unsafe_settings_enabled:{','.join(enabled)}")

    def _load_binding(self, capability_binding_id: str) -> CapabilityBinding | None:
        get_binding = getattr(self._module_binding_repository, "get_binding", None)
        if callable(get_binding):
            return cast(CapabilityBinding | None, get_binding(capability_binding_id))
        return None

    def _load_profile(self, mock_profile_id: str | None) -> object | None:
        if not mock_profile_id:
            return None
        return self._repository.get_profile(mock_profile_id)

    def _findings_for(
        self,
        request: ModuleMockInvocationCreateRequest,
        binding: CapabilityBinding | None,
        profile: object | None,
        schema_check: dict[str, Any],
        output_shape_check: dict[str, Any],
    ) -> list[ModuleMockFinding]:
        findings: list[ModuleMockFinding] = []
        if binding is None:
            findings.append(
                _finding(
                    request,
                    "missing_binding",
                    "Capability binding metadata was not found.",
                    "Create or validate a capability binding before mock invocation.",
                    severity="high",
                )
            )
        elif binding.target_runtime not in _SAFE_TARGET_RUNTIMES:
            findings.append(
                _finding(
                    request,
                    "execution_enabled",
                    "Capability binding references an executable target runtime.",
                    "Keep mock runtime bindings metadata-only, noop, or sandbox-declared.",
                    severity="critical",
                )
            )
        if request.mock_profile_id and profile is None:
            findings.append(
                _finding(
                    request,
                    "missing_mock_profile",
                    "Requested mock profile metadata was not found.",
                    "Create a mock profile or omit mock_profile_id.",
                    severity="medium",
                )
            )
        for error in schema_check.get("errors", []):
            findings.append(
                _finding(
                    request,
                    "invalid_input_shape",
                    str(error),
                    "Adjust the synthetic input shape.",
                    severity="medium",
                )
            )
        for error in output_shape_check.get("errors", []):
            findings.append(
                _finding(
                    request,
                    "invalid_output_shape",
                    str(error),
                    "Adjust the expected output shape.",
                    severity="medium",
                )
            )
        return findings

    def _synthetic_output_payload(
        self,
        request: ModuleMockInvocationCreateRequest,
        binding: CapabilityBinding | None,
        profile: object | None,
        output_shape: dict[str, Any],
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "synthetic": True,
            "output_kind": "module_mock_runtime",
            "capability_binding_id": request.capability_binding_id,
            "capability_key": request.capability_key,
            "invocation_type": request.invocation_type,
            "generated_by": "aion.module_mock_runtime",
            "mock_profile_id": request.mock_profile_id,
            "profile_key": getattr(profile, "profile_key", None),
            "binding_status": getattr(binding, "status", None),
            "shape": output_shape,
            "activation_allowed": False,
            "execution_allowed": False,
            "external_calls_made": False,
            "code_loaded": False,
            "records_created": ["request", "output", "run", "findings"],
        }
        if request.capability_key == "generic.knowledge.retrieve":
            payload.update({"synthetic_refs": [], "retrieved_count": 0})
        elif request.capability_key == "generic.knowledge.summarize":
            payload["summary"] = "Synthetic summary from metadata-only module mock runtime."
        elif request.capability_key == "generic.knowledge.ground":
            payload.update(
                {"grounding_status": "synthetic", "evidence_refs": list(request.evidence_refs)}
            )
        elif request.capability_key == "generic.knowledge.explain":
            payload["explanation"] = "Synthetic explanation from declared schema."
        elif request.capability_key == "generic.knowledge.answer":
            payload["answer"] = "Synthetic answer from metadata-only module mock runtime."
        return payload

    def _record_audit(self, run: ModuleMockRun) -> None:
        record_audit_event(
            self._audit_sink,
            action_type="module_mock.invoke",
            resource_type="module_mock_run",
            resource_id=run.module_mock_run_id,
            event_type="module_mock_run_created",
            outcome="completed" if run.status in {"passed", "warning"} else "blocked",
            source_component="module_mock_runtime",
            trace_id=run.trace_id,
            actor_id=run.created_by,
            risk_level="medium",
            payload={
                "status": run.status,
                "metadata_only": True,
                "activation_allowed": False,
                "execution_allowed": False,
            },
        )

    def _record_provenance(self, run: ModuleMockRun) -> None:
        record = getattr(self._provenance_service, "record", None)
        if not callable(record):
            return
        try:
            record(
                "module_mock_run",
                run.module_mock_run_id,
                run.owner_scope,
                metadata={"synthetic": True, "module_mock_runtime": True},
            )
        except Exception:
            return

    def _maybe_notify(self, run: ModuleMockRun, create_notifications: bool) -> None:
        if not (create_notifications and self._settings.module_mock_create_notifications_default):
            return
        publish = getattr(self._notification_router, "publish", None)
        if not callable(publish):
            return
        try:
            publish(
                {
                    "event_type": "module_mock_run_completed",
                    "source_id": run.module_mock_run_id,
                    "status": run.status,
                }
            )
        except Exception:
            return

    def _emit(
        self,
        event_type: str,
        node_id: str,
        scope: list[str],
        intensity: float,
        payload: dict[str, Any],
        *,
        node_type: str = "module_mock_run",
    ) -> None:
        emit_versioning_telemetry(
            self._telemetry_service,
            event_type=event_type,
            node_type=node_type,
            node_id=node_id,
            scope=scope,
            intensity=intensity,
            payload={**payload, "metadata_only": True, "synthetic": True},
        )


def _finding(
    request: ModuleMockInvocationCreateRequest,
    finding_type: str,
    title: str,
    recommended_action: str,
    *,
    severity: str,
) -> ModuleMockFinding:
    return ModuleMockFinding(
        module_mock_finding_id=f"module-mock-finding-{uuid4().hex}",
        trace_id=request.trace_id,
        module_slot_id=request.module_slot_id,
        capability_binding_id=request.capability_binding_id,
        finding_type=cast(Any, finding_type),
        severity=cast(Any, severity),
        status="open",
        title=title,
        description=title,
        recommended_action=recommended_action,
        refs=[request.capability_binding_id],
        metadata={"metadata_only": True, "synthetic": True},
        created_at=datetime.now(UTC),
    )


def _output_type_for(invocation_type: str) -> str:
    if invocation_type == "mock_knowledge":
        return "synthetic_knowledge"
    if invocation_type == "mock_summary":
        return "synthetic_summary"
    if invocation_type == "mock_grounding":
        return "synthetic_grounding"
    if invocation_type == "mock_explanation":
        return "synthetic_explanation"
    if invocation_type == "mock_answer":
        return "synthetic_answer"
    if invocation_type == "schema_simulation":
        return "synthetic_schema"
    return "generic"


def _in_scope(owner_scope: list[str], requested_scope: list[str]) -> bool:
    requested = set(requested_scope or [])
    return not requested or bool(set(owner_scope) & requested)


__all__ = ["ModuleMockSimulator"]
