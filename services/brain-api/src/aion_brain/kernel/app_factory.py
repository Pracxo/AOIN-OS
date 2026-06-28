"""FastAPI application factory backed by the AION kernel container."""

from fastapi import FastAPI, Request

from aion_brain.api.action_authorization import router as action_authorization_router
from aion_brain.api.action_proposals import router as action_proposals_router
from aion_brain.api.approvals import router as approvals_router
from aion_brain.api.attention import router as attention_router
from aion_brain.api.audit_integrity import router as audit_integrity_router
from aion_brain.api.auth_runtime import router as auth_runtime_router
from aion_brain.api.autonomy import router as autonomy_router
from aion_brain.api.backups import router as backups_router
from aion_brain.api.beliefs import router as beliefs_router
from aion_brain.api.bootstrap import router as bootstrap_router
from aion_brain.api.brain import router as brain_router
from aion_brain.api.capabilities import router as capabilities_router
from aion_brain.api.commands import router as commands_router
from aion_brain.api.concepts import router as concepts_router
from aion_brain.api.conformance import router as conformance_router
from aion_brain.api.connectors import router as connectors_router
from aion_brain.api.consistency import router as consistency_router
from aion_brain.api.contract_registry import router as contract_registry_router
from aion_brain.api.cycles import router as cycles_router
from aion_brain.api.decisions import router as decisions_router
from aion_brain.api.dialogue import router as dialogue_router
from aion_brain.api.entities import router as entities_router
from aion_brain.api.event_reactions import router as event_reactions_router
from aion_brain.api.events import router as events_router
from aion_brain.api.evidence import router as evidence_router
from aion_brain.api.execution import router as execution_router
from aion_brain.api.explanations import router as explanations_router
from aion_brain.api.extensions import router as extensions_router
from aion_brain.api.freeze import router as freeze_router
from aion_brain.api.goals import router as goals_router
from aion_brain.api.golden_path import router as golden_path_router
from aion_brain.api.graph_memory import router as graph_memory_router
from aion_brain.api.grounding import router as grounding_router
from aion_brain.api.guardrails import router as guardrails_router
from aion_brain.api.health import router as health_router
from aion_brain.api.idempotency import router as idempotency_router
from aion_brain.api.identity import router as identity_router
from aion_brain.api.inbox import router as inbox_router
from aion_brain.api.incidents import router as incidents_router
from aion_brain.api.instructions import router as instructions_router
from aion_brain.api.kernel import api_router as api_support_router
from aion_brain.api.kernel import router as kernel_router
from aion_brain.api.learning import router as learning_router
from aion_brain.api.learning_synthesis import router as learning_synthesis_router
from aion_brain.api.lifecycle import router as lifecycle_router
from aion_brain.api.local_auth import router as local_auth_router
from aion_brain.api.local_session import router as local_session_router
from aion_brain.api.mcp import router as mcp_router
from aion_brain.api.memory import router as memory_router
from aion_brain.api.memory_governance import router as memory_governance_router
from aion_brain.api.model_gateway import router as model_gateway_router
from aion_brain.api.model_outputs import router as model_outputs_router
from aion_brain.api.model_provider_hardening import router as model_provider_hardening_router
from aion_brain.api.module_activation import router as module_activation_router
from aion_brain.api.module_bindings import router as module_bindings_router
from aion_brain.api.module_developer import router as module_developer_router
from aion_brain.api.module_mock_runtime import router as module_mock_runtime_router
from aion_brain.api.modules import router as modules_router
from aion_brain.api.notifications import router as notifications_router
from aion_brain.api.observability import router as observability_router
from aion_brain.api.operator import router as operator_router
from aion_brain.api.operator_actions import router as operator_actions_router
from aion_brain.api.operator_console import router as operator_console_router
from aion_brain.api.outbox import router as outbox_router
from aion_brain.api.outcomes import router as outcomes_router
from aion_brain.api.performance import router as performance_router
from aion_brain.api.policy import router as policy_router
from aion_brain.api.policy_catalog import router as policy_catalog_router
from aion_brain.api.prompts import router as prompts_router
from aion_brain.api.reasoning import router as reasoning_router
from aion_brain.api.reflection import router as reflection_router
from aion_brain.api.regression import router as regression_router
from aion_brain.api.release_baseline import router as release_baseline_router
from aion_brain.api.release_candidate import router as release_candidate_router
from aion_brain.api.release_package import router as release_package_router
from aion_brain.api.replay import router as replay_router
from aion_brain.api.resilience import router as resilience_router
from aion_brain.api.resource_registry import router as resource_registry_router
from aion_brain.api.responses import router as responses_router
from aion_brain.api.retrieval import router as retrieval_router
from aion_brain.api.risk import router as risk_router
from aion_brain.api.run_supervision import router as run_supervision_router
from aion_brain.api.runtime_config import router as runtime_config_router
from aion_brain.api.sandbox import router as sandbox_router
from aion_brain.api.scenarios import router as scenarios_router
from aion_brain.api.scheduler import router as scheduler_router
from aion_brain.api.schedules import router as schedules_router
from aion_brain.api.scopes import router as scopes_router
from aion_brain.api.secrets import router as secrets_router
from aion_brain.api.security_baseline import router as security_baseline_router
from aion_brain.api.self_model import router as self_model_router
from aion_brain.api.situations import router as situations_router
from aion_brain.api.skills import router as skills_router
from aion_brain.api.tasks import router as tasks_router
from aion_brain.api.telemetry import router as telemetry_router
from aion_brain.api.traces import router as traces_router
from aion_brain.api.versioning import router as versioning_router
from aion_brain.api.visual import router as visual_router
from aion_brain.api.workflows import router as workflows_router
from aion_brain.api.working_memory import router as working_memory_router
from aion_brain.api.workspaces import router as workspaces_router
from aion_brain.api_support.exception_handlers import register_exception_handlers
from aion_brain.api_support.middleware import RequestContextMiddleware
from aion_brain.kernel.container import KernelContainer

ROUTERS = (
    health_router,
    audit_integrity_router,
    identity_router,
    workspaces_router,
    scopes_router,
    instructions_router,
    events_router,
    event_reactions_router,
    commands_router,
    idempotency_router,
    outbox_router,
    inbox_router,
    consistency_router,
    capabilities_router,
    modules_router,
    sandbox_router,
    secrets_router,
    connectors_router,
    goals_router,
    tasks_router,
    schedules_router,
    scheduler_router,
    workflows_router,
    cycles_router,
    execution_router,
    beliefs_router,
    concepts_router,
    entities_router,
    evidence_router,
    grounding_router,
    memory_router,
    memory_governance_router,
    mcp_router,
    graph_memory_router,
    model_provider_hardening_router,
    model_gateway_router,
    model_outputs_router,
    action_proposals_router,
    run_supervision_router,
    notifications_router,
    incidents_router,
    contract_registry_router,
    extensions_router,
    module_bindings_router,
    module_activation_router,
    module_mock_runtime_router,
    conformance_router,
    golden_path_router,
    bootstrap_router,
    resource_registry_router,
    lifecycle_router,
    prompts_router,
    module_developer_router,
    retrieval_router,
    reasoning_router,
    reflection_router,
    skills_router,
    policy_router,
    policy_catalog_router,
    risk_router,
    guardrails_router,
    approvals_router,
    attention_router,
    working_memory_router,
    autonomy_router,
    dialogue_router,
    responses_router,
    situations_router,
    decisions_router,
    outcomes_router,
    explanations_router,
    brain_router,
    traces_router,
    learning_router,
    learning_synthesis_router,
    telemetry_router,
    scenarios_router,
    release_baseline_router,
    release_candidate_router,
    release_package_router,
    backups_router,
    performance_router,
    security_baseline_router,
    self_model_router,
    runtime_config_router,
    resilience_router,
    versioning_router,
    freeze_router,
    visual_router,
    observability_router,
    operator_router,
    operator_actions_router,
    action_authorization_router,
    auth_runtime_router,
    local_auth_router,
    local_session_router,
    operator_console_router,
    replay_router,
    regression_router,
    api_support_router,
    kernel_router,
)


def create_app(container: KernelContainer | None = None) -> FastAPI:
    """Create the AION Brain API around one process-wide composition root."""
    kernel = container or KernelContainer()
    app = FastAPI(title="AION Brain API", version=kernel.settings.version)
    app.state.kernel_container = kernel
    app.add_middleware(RequestContextMiddleware)
    app.state.aion_request_context_middleware_present = True
    register_exception_handlers(app)
    for router in ROUTERS:
        app.include_router(router)
    return app


def get_kernel_container(request: Request) -> KernelContainer:
    """Return the process-wide kernel composition root from app state."""
    container = getattr(request.app.state, "kernel_container", None)
    if not isinstance(container, KernelContainer):
        raise RuntimeError("AION kernel container is not configured")
    return container
