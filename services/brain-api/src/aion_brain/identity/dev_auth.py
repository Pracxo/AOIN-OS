"""Header-based development identity boundary."""

from typing import Annotated

from fastapi import Depends, Request

from aion_brain.config import Settings, get_settings
from aion_brain.contracts.actor_context_resolution import (
    ActorContextResolutionBundle,
    ActorContextResolutionInput,
)
from aion_brain.contracts.api import RequestContext
from aion_brain.contracts.request_identity import RequestIdentityContext
from aion_brain.contracts.scopes import ActorContext
from aion_brain.production_auth.actor_context import ProductionAuthActorContextResolver

DEV_PERMISSIONS = [
    "brain.think",
    "brain.plan",
    "event.ingest",
    "memory.read",
    "memory.write",
    "graph.read",
    "graph.write",
    "capability.read",
    "capability.register",
    "capability.invoke",
    "module.runtime.register",
    "module.runtime.read",
    "module.runtime.invoke",
    "module.package.submit",
    "module.package.read",
    "module.package.disable",
    "module.package.certify",
    "module.contract_test.run",
    "module.scaffold.create",
    "module.compatibility.check",
    "sandbox.profile.create",
    "sandbox.profile.read",
    "sandbox.profile.disable",
    "sandbox.profile.validate",
    "sandbox.run",
    "runtime_permission.grant",
    "runtime_permission.read",
    "runtime_permission.revoke",
    "secret_ref.create",
    "secret_ref.read",
    "secret_ref.disable",
    "secret_ref.rotate",
    "connector.create",
    "connector.read",
    "connector.disable",
    "connector.validate",
    "plan.create",
    "execution.run",
    "goal.create",
    "goal.read",
    "task.create",
    "task.run",
    "skill.read",
    "skill.promote",
    "trace.read",
    "policy.authorize",
    "policy.catalog.create",
    "policy.catalog.read",
    "policy.catalog.update",
    "policy.permission.create",
    "policy.permission.read",
    "policy.permission.update",
    "policy.role_template.create",
    "policy.role_template.read",
    "policy.role_template.update",
    "policy.simulate",
    "policy.test_case.create",
    "policy.test_case.read",
    "policy.test.run",
    "policy.coverage.read",
    "policy.bundle.export",
    "policy.opa.status",
    "telemetry.read",
    "visual.map.read",
    "visual.telemetry.read",
    "visual.stream.read",
    "visual.snapshot.create",
    "visual.snapshot.read",
    "visual.timeline.read",
    "observability.read",
    "observability.event.create",
    "run_supervision.create",
    "run_supervision.read",
    "run_supervision.update",
    "run_supervision.delete",
    "run_supervision.sample",
    "run_supervision.control.request",
    "run_supervision.control.read",
    "run_supervision.control.handoff",
    "run_supervision.timeout_policy.create",
    "run_supervision.timeout_policy.read",
    "run_supervision.timeout_policy.update",
    "run_supervision.compensation.create",
    "run_supervision.compensation.read",
    "run_supervision.compensation.update",
    "run_supervision.compensation.convert",
    "run_supervision.report.create",
    "run_supervision.report.read",
    "notification.topic.create",
    "notification.topic.read",
    "notification.topic.update",
    "notification.subscription.create",
    "notification.subscription.read",
    "notification.subscription.update",
    "notification.publish",
    "notification.read",
    "notification.update",
    "alert.create",
    "alert.read",
    "alert.update",
    "escalation.policy.create",
    "escalation.policy.read",
    "escalation.policy.update",
    "escalation.evaluate",
    "escalation.read",
    "escalation.update",
    "notification.digest.create",
    "notification.digest.read",
    "incident.signal.create",
    "incident.signal.read",
    "incident.signal.update",
    "incident.rule.create",
    "incident.rule.read",
    "incident.rule.update",
    "incident.create",
    "incident.read",
    "incident.update",
    "incident.delete",
    "incident.correlate",
    "incident.root_cause.create",
    "incident.root_cause.read",
    "incident.root_cause.update",
    "incident.recovery_review.create",
    "incident.recovery_review.read",
    "registry.resource.create",
    "registry.resource.read",
    "registry.resource.update",
    "registry.link.create",
    "registry.link.read",
    "registry.link.update",
    "registry.link.delete",
    "registry.backlink.read",
    "registry.validate",
    "registry.rebuild",
    "registry.snapshot.create",
    "registry.snapshot.read",
    "registry.broken_reference.read",
    "registry.broken_reference.update",
    "registry.orphaned_resource.read",
    "registry.orphaned_resource.update",
    "contract_registry.resource.create",
    "contract_registry.resource.read",
    "contract_registry.resource.update",
    "contract_registry.interface.read",
    "contract_registry.snapshot.create",
    "contract_registry.snapshot.read",
    "contract_registry.rule.create",
    "contract_registry.rule.read",
    "contract_registry.rule.update",
    "contract_registry.compatibility.scan",
    "contract_registry.finding.read",
    "contract_registry.finding.update",
    "contract_registry.migration_note.create",
    "contract_registry.migration_note.read",
    "contract_registry.migration_note.update",
    "contract_registry.report.create",
    "contract_registry.report.read",
    "extension.package.create",
    "extension.package.read",
    "extension.package.update",
    "extension.package.delete",
    "extension.manifest.validate",
    "extension.dependency.read",
    "extension.capability_declaration.read",
    "extension.compatibility.check",
    "extension.intake",
    "extension.review",
    "extension.install_plan.create",
    "extension.install_plan.read",
    "extension.install_plan.update",
    "extension.query",
    "module_slot.create",
    "module_slot.read",
    "module_slot.update",
    "module_slot.delete",
    "capability_binding.create",
    "capability_binding.read",
    "capability_binding.update",
    "module_binding.validate",
    "module_binding.conflict.read",
    "module_binding.conflict.update",
    "module_mount_plan.create",
    "module_mount_plan.read",
    "module_mount_plan.update",
    "route_binding_preview.create",
    "route_binding_preview.read",
    "module_binding.query",
    "conformance.profile.create",
    "conformance.profile.read",
    "conformance.profile.update",
    "conformance.test_vector.create",
    "conformance.test_vector.read",
    "conformance.test_vector.update",
    "conformance.run",
    "conformance.finding.read",
    "conformance.finding.update",
    "conformance.readiness.assess",
    "conformance.readiness.read",
    "conformance.query",
    "golden_path.scenario.create",
    "golden_path.scenario.read",
    "golden_path.fixture.create",
    "golden_path.fixture.read",
    "golden_path.run",
    "golden_path.run.read",
    "golden_path.assertion.evaluate",
    "golden_path.report.create",
    "golden_path.report.read",
    "golden_path.release_smoke.run",
    "golden_path.query",
    "bootstrap.profile.create",
    "bootstrap.profile.read",
    "bootstrap.profile.update",
    "bootstrap.seed_bundle.create",
    "bootstrap.seed_bundle.read",
    "bootstrap.seed_bundle.update",
    "bootstrap.seed.execute",
    "bootstrap.doctor.run",
    "bootstrap.finding.read",
    "bootstrap.finding.update",
    "bootstrap.run",
    "bootstrap.run.read",
    "bootstrap.report.create",
    "bootstrap.report.read",
    "bootstrap.query",
    "release_candidate.create",
    "release_candidate.read",
    "release_candidate.update",
    "release_candidate.matrix.create",
    "release_candidate.matrix.read",
    "release_candidate.matrix.update",
    "release_candidate.gate.run",
    "release_candidate.run.read",
    "release_candidate.finding.read",
    "release_candidate.finding.update",
    "release_candidate.evidence_pack.create",
    "release_candidate.evidence_pack.read",
    "release_candidate.report.create",
    "release_candidate.report.read",
    "release_candidate.query",
    "release_candidate.write",
    "lifecycle.read",
    "lifecycle.write",
    "lifecycle.policy.create",
    "lifecycle.policy.read",
    "lifecycle.policy.update",
    "lifecycle.classify",
    "lifecycle.classification.read",
    "lifecycle.evaluate",
    "lifecycle.archive_candidate.create",
    "lifecycle.archive_candidate.read",
    "lifecycle.archive_candidate.update",
    "lifecycle.redaction_candidate.create",
    "lifecycle.redaction_candidate.read",
    "lifecycle.redaction_candidate.update",
    "lifecycle.purge_preview.create",
    "lifecycle.purge_preview.read",
    "lifecycle.review.create",
    "lifecycle.review.read",
    "lifecycle.report.create",
    "lifecycle.report.read",
    "scheduler.schedule.create",
    "scheduler.schedule.read",
    "scheduler.schedule.update",
    "scheduler.schedule.delete",
    "scheduler.due_item.read",
    "scheduler.due_item.update",
    "scheduler.reminder.create",
    "scheduler.reminder.read",
    "scheduler.reminder.update",
    "scheduler.tick",
    "scheduler.policy.create",
    "scheduler.policy.read",
    "scheduler.policy.update",
    "scheduler.report.create",
    "scheduler.report.read",
    "prompt.template.create",
    "prompt.template.read",
    "prompt.template.update",
    "prompt.fragment.create",
    "prompt.fragment.read",
    "prompt.fragment.update",
    "prompt.compile",
    "prompt.packet.read",
    "prompt.packet.delete",
    "prompt.boundary.check",
    "prompt.injection.read",
    "prompt.preview",
    "prompt.manifest.create",
    "prompt.manifest.read",
    "instruction.create",
    "instruction.read",
    "instruction.update",
    "instruction.resolve",
    "instruction.conflict.read",
    "instruction.conflict.update",
    "instruction.constraint.create",
    "instruction.constraint.read",
    "instruction.constraint.update",
    "instruction.style_profile.create",
    "instruction.style_profile.read",
    "instruction.style_profile.update",
    "preference.create",
    "preference.read",
    "preference.update",
    "preference.candidate.create",
    "preference.candidate.read",
    "preference.candidate.update",
    "explanation.create",
    "explanation.read",
    "explanation.verify",
    "explanation.feedback.create",
    "explanation.feedback.read",
    "explanation.why_not",
    "explanation.trace_narrative.create",
    "explanation.trace_narrative.read",
    "risk.assess",
    "guardrail.rule.create",
    "guardrail.rule.read",
    "guardrail.rule.disable",
    "guardrail.evaluate",
    "approval.request.create",
    "approval.request.read",
    "approval.decision.create",
    "approval.request.cancel",
    "approval.expire",
    "model.provider.register",
    "model.provider.read",
    "model.provider.disable",
    "model.provider.health_check",
    "model.profile.register",
    "model.profile.read",
    "model.profile.disable",
    "model.gateway.complete",
    "model.route",
    "model.complete",
    "model.usage.read",
    "model.budget.create",
    "model.budget.read",
    "model.budget.update",
    "model.external.use",
    "model_output.create",
    "model_output.read",
    "model_output.delete",
    "model_output.parse",
    "model_output.govern",
    "model_output.structured_validate",
    "model_output.response_candidate.create",
    "model_output.response_candidate.read",
    "model_output.response_candidate.update",
    "model_output.tool_intent.create",
    "model_output.tool_intent.read",
    "model_output.tool_intent.update",
    "action_proposal.create",
    "action_proposal.read",
    "action_proposal.update",
    "action_proposal.delete",
    "action_proposal.review",
    "action_proposal.handoff",
    "action_proposal.blocker.read",
    "action_proposal.blocker.update",
    "action_proposal.tool_intent.review",
    "action_proposal.handoff.read",
    "run_supervision.create",
    "run_supervision.read",
    "run_supervision.update",
    "run_supervision.delete",
    "run_supervision.sample",
    "run_supervision.control.request",
    "run_supervision.control.read",
    "run_supervision.control.handoff",
    "run_supervision.timeout_policy.create",
    "run_supervision.timeout_policy.read",
    "run_supervision.timeout_policy.update",
    "run_supervision.compensation.create",
    "run_supervision.compensation.read",
    "run_supervision.compensation.update",
    "run_supervision.compensation.convert",
    "run_supervision.report.create",
    "run_supervision.report.read",
    "notification.topic.create",
    "notification.topic.read",
    "notification.topic.update",
    "notification.subscription.create",
    "notification.subscription.read",
    "notification.subscription.update",
    "notification.publish",
    "notification.read",
    "notification.update",
    "alert.create",
    "alert.read",
    "alert.update",
    "escalation.policy.create",
    "escalation.policy.read",
    "escalation.policy.update",
    "escalation.evaluate",
    "escalation.read",
    "escalation.update",
    "notification.digest.create",
    "notification.digest.read",
    "registry.resource.create",
    "registry.resource.read",
    "registry.resource.update",
    "registry.link.create",
    "registry.link.read",
    "registry.link.update",
    "registry.link.delete",
    "registry.backlink.read",
    "registry.validate",
    "registry.rebuild",
    "registry.snapshot.create",
    "registry.snapshot.read",
    "registry.broken_reference.read",
    "registry.broken_reference.update",
    "registry.orphaned_resource.read",
    "registry.orphaned_resource.update",
    "contract_registry.resource.create",
    "contract_registry.resource.read",
    "contract_registry.resource.update",
    "contract_registry.interface.read",
    "contract_registry.snapshot.create",
    "contract_registry.snapshot.read",
    "contract_registry.rule.create",
    "contract_registry.rule.read",
    "contract_registry.rule.update",
    "contract_registry.compatibility.scan",
    "contract_registry.finding.read",
    "contract_registry.finding.update",
    "contract_registry.migration_note.create",
    "contract_registry.migration_note.read",
    "contract_registry.migration_note.update",
    "contract_registry.report.create",
    "contract_registry.report.read",
    "snapshot.create",
    "snapshot.read",
    "replay.run",
    "replay.read",
    "regression.case.create",
    "regression.case.read",
    "regression.case.update",
    "regression.run",
    "regression.read",
    "eval.adapter.run",
    "identity.actor.create",
    "identity.actor.read",
    "identity.actor.disable",
    "identity.workspace.create",
    "identity.workspace.read",
    "identity.workspace.archive",
    "identity.membership.create",
    "identity.membership.read",
    "identity.membership.revoke",
    "identity.permission.create",
    "identity.permission.read",
    "identity.permission.revoke",
    "scope.resolve",
    "kernel.status.read",
    "kernel.boot.read",
    "kernel.services.read",
    "kernel.self_test.run",
    "kernel.contracts.export",
    "kernel.boundary_check.run",
    "api.request.read",
    "api.openapi_hygiene.read",
    "api.error_codes.read",
    "scenario.create",
    "scenario.read",
    "scenario.disable",
    "scenario.run",
    "scenario.seed_defaults",
    "demo_fixture.read",
    "demo_fixture.load",
    "release_baseline.run",
    "release_baseline.read",
    "version.manifest.create",
    "version.manifest.read",
    "version.manifest.freeze",
    "version.feature.create",
    "version.feature.read",
    "version.feature.deprecate",
    "compatibility.matrix.generate",
    "compatibility.matrix.read",
    "migration.baseline.generate",
    "release.artifact.generate",
    "freeze_gate.run",
    "freeze_gate.read",
    "release.package.create",
    "release.package.read",
    "release.package.validate",
    "release.handoff.read",
    "backup.create",
    "backup.read",
    "backup.validate",
    "backup.restore.preview",
    "backup.restore.apply",
    "performance.benchmark.create",
    "performance.benchmark.read",
    "performance.benchmark.run",
    "performance.baseline.create",
    "performance.baseline.read",
    "performance.budget.create",
    "performance.budget.read",
    "performance.summary.read",
    "performance.regression.read",
    "sdk.compatibility.check",
    "security.scan.run",
    "security.scan.read",
    "security.threat_model.create",
    "security.threat_model.read",
    "security.threat_model.update",
    "security.control.create",
    "security.control.read",
    "security.control.update",
    "security.hardening.run",
    "security.hardening.read",
    "runtime_config.profile.create",
    "runtime_config.profile.read",
    "runtime_config.profile.update",
    "runtime_config.feature_override.create",
    "runtime_config.feature_override.read",
    "runtime_config.feature_override.update",
    "runtime_config.snapshot.create",
    "runtime_config.snapshot.read",
    "runtime_config.validate",
    "runtime_config.status.read",
    "runtime_config.change.read",
    "resilience.status.read",
    "resilience.dependency.check",
    "resilience.dependency.read",
    "resilience.retry_policy.create",
    "resilience.retry_policy.read",
    "resilience.retry_policy.update",
    "resilience.circuit_breaker.create",
    "resilience.circuit_breaker.read",
    "resilience.circuit_breaker.update",
    "resilience.degraded.read",
    "resilience.degraded.resolve",
    "resilience.fault_rule.create",
    "resilience.fault_rule.read",
    "resilience.fault_rule.update",
    "resilience.test.run",
    "resilience.test.read",
    "local_auth.roles.read",
    "local_auth.identity.simulate",
    "local_auth.console.filter",
    "local_auth.audit.run",
    "local_auth.status.read",
]


def get_actor_context(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
) -> ActorContext:
    """Return the current request actor context for route dependencies."""
    resolver = _resolver_from_request(request)
    bundle = resolve_actor_context_bundle(request, settings, resolver=resolver)
    _attach_resolution_bundle(request, bundle)
    return bundle.actor_context


def actor_context_from_headers(request: Request, settings: Settings) -> ActorContext:
    """Compatibility wrapper for existing route and test imports."""
    return resolve_actor_context_bundle(request, settings).actor_context


def resolve_actor_context_bundle(
    request: Request,
    settings: Settings,
    *,
    resolver: ProductionAuthActorContextResolver | None = None,
) -> ActorContextResolutionBundle:
    """Resolve actor context from structured safe request state."""
    effective_resolver = resolver or ProductionAuthActorContextResolver()
    return effective_resolver.resolve(_resolution_input_from_request(request, settings))


def development_identity_simulation_enabled(settings: Settings) -> bool:
    """Return true only for the exact local development identity simulation gate."""
    return settings.env == "development" and settings.dev_auth_enabled is True


def _resolution_input_from_request(
    request: Request,
    settings: Settings,
) -> ActorContextResolutionInput:
    request_context = _safe_request_context(request)
    identity_present = _state_has(request, "aion_request_identity_context")
    identity_context = _safe_request_identity_context(request)
    identity_valid = identity_context is not None and _request_identity_is_disabled(
        identity_context
    )
    dev_enabled = development_identity_simulation_enabled(settings)
    trace_id = request_context.trace_id if request_context is not None else None
    correlation_id = (
        request_context.correlation_id if request_context is not None else None
    )
    if dev_enabled:
        actor_id = _header(request, "X-AION-Actor-ID") or settings.default_dev_actor_id
        workspace_id = (
            _header(request, "X-AION-Workspace-ID") or settings.default_dev_workspace_id
        )
        roles = tuple(_csv_header(request, "X-AION-Roles") or ["owner"])
        permissions = tuple(_csv_header(request, "X-AION-Permissions") or DEV_PERMISSIONS)
        security_scope = tuple(
            _csv_header(request, "X-AION-Security-Scope")
            or [f"workspace:{workspace_id}", f"actor:{actor_id}"]
        )
        if request_context is None:
            trace_id = _header(request, "X-AION-Trace-ID")
            correlation_id = _header(request, "X-AION-Correlation-ID")
    else:
        actor_id = None
        workspace_id = None
        roles = ()
        permissions = ()
        security_scope = ()
    return ActorContextResolutionInput(
        request_id=request_context.request_id if request_context is not None else None,
        trace_id=trace_id,
        correlation_id=correlation_id,
        request_identity_context_present=identity_present,
        request_identity_context_valid=identity_valid,
        development_simulation_enabled=dev_enabled,
        development_actor_id=actor_id,
        development_workspace_id=workspace_id,
        development_roles=roles,
        development_permissions=permissions,
        development_security_scope=security_scope,
        metadata={
            "request_context_actor_ignored": True,
            "request_context_workspace_ignored": True,
            "raw_headers_in_resolver_input": False,
        },
    )


def _resolver_from_request(request: Request) -> ProductionAuthActorContextResolver:
    container = getattr(request.app.state, "kernel_container", None)
    resolver = getattr(container, "production_auth_actor_context_resolver", None)
    if isinstance(resolver, ProductionAuthActorContextResolver):
        return resolver
    return ProductionAuthActorContextResolver()


def _safe_request_context(request: Request) -> RequestContext | None:
    value = _state_get(request, "aion_request_context")
    return value if isinstance(value, RequestContext) else None


def _safe_request_identity_context(request: Request) -> RequestIdentityContext | None:
    value = _state_get(request, "aion_request_identity_context")
    return value if isinstance(value, RequestIdentityContext) else None


def _request_identity_is_disabled(context: RequestIdentityContext) -> bool:
    return (
        context.authentication_state == "disabled"
        and context.authenticated is False
        and context.actor_id is None
        and context.subject is None
        and tuple(context.roles) == ()
        and context.runtime_effect is False
    )


def _attach_resolution_bundle(
    request: Request,
    bundle: ActorContextResolutionBundle,
) -> None:
    state = getattr(request, "state", None)
    if state is None:
        return
    state.aion_actor_context_resolution = bundle
    state.aion_actor_context_resolution_audit_event = getattr(bundle, "audit_event", None)
    state.aion_actor_context_resolution_provenance = getattr(bundle, "provenance", None)
    state.aion_actor_context_resolution_source = getattr(bundle, "source", "anonymous_fail_closed")
    state.aion_actor_context_resolution_failed = bool(getattr(bundle, "resolution_failed", False))
    state.aion_actor_context_resolution_failure_reason = getattr(bundle, "failure_reason", None)


def _state_get(request: Request, name: str) -> object | None:
    state = getattr(request, "state", None)
    if state is None:
        return None
    return getattr(state, name, None)


def _state_has(request: Request, name: str) -> bool:
    state = getattr(request, "state", None)
    return bool(state is not None and hasattr(state, name))


def _header(request: Request, name: str) -> str | None:
    value = request.headers.get(name)
    if value is None or not value.strip():
        return None
    return value.strip()


def _csv_header(request: Request, name: str) -> list[str]:
    value = _header(request, name)
    if value is None:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]
