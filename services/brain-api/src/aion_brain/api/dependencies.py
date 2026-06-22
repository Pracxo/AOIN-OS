"""Shared API dependencies."""

from functools import lru_cache

from aion_brain.api.approvals import get_cached_approval_service
from aion_brain.api.graph_memory import get_cached_graph_memory_service
from aion_brain.api.mcp import get_cached_mcp_service
from aion_brain.api.retrieval import get_cached_retrieval_router
from aion_brain.api.workflows import get_cached_workflow_service
from aion_brain.attention.context_budget import ContextBudgeter
from aion_brain.attention.controller import AttentionController
from aion_brain.attention.focus import FocusService
from aion_brain.attention.repository import AttentionRepository
from aion_brain.audit.ledger import AuditLedger
from aion_brain.audit.repository import AuditRepository
from aion_brain.capabilities.registry import CapabilityRegistry
from aion_brain.capabilities.service import CapabilityService
from aion_brain.config import get_settings
from aion_brain.context.compiler import ContextCompiler
from aion_brain.core.brain_loop import BrainLoopService
from aion_brain.evaluation.evaluator import Evaluator
from aion_brain.goals.repository import GoalRepository
from aion_brain.goals.service import GoalService
from aion_brain.identity.repository import IdentityRepository
from aion_brain.identity.service import IdentityService
from aion_brain.intent.engine import IntentEngine
from aion_brain.learning.engine import LearningEngine
from aion_brain.memory.repository import MemoryRepository
from aion_brain.memory.service import PostgresMemoryService
from aion_brain.modules.local_internal_runtime import LocalInternalRuntimeAdapter
from aion_brain.modules.local_stub_runtime import LocalStubRuntimeAdapter
from aion_brain.modules.mcp_runtime import MCPRuntimeAdapter
from aion_brain.modules.repository import ModuleRuntimeRepository
from aion_brain.modules.runtime_gateway import CapabilityRuntimeGateway
from aion_brain.observability.local_recorder import LocalObservabilityRecorder
from aion_brain.observability.repository import ObservabilityRepository
from aion_brain.planning.planner import Planner
from aion_brain.policy.opa_adapter import OPAAdapter
from aion_brain.reasoning.deterministic_adapter import DeterministicReasoningAdapter
from aion_brain.reasoning.mesh import ReasoningMesh
from aion_brain.reasoning.prompt_builder import PromptBuilder
from aion_brain.reasoning.repository import ReasoningRepository
from aion_brain.reasoning.router import ModelRouter
from aion_brain.reflection.engine import ReflectionEngine
from aion_brain.reflection.repository import ReflectionRepository
from aion_brain.runtime.langgraph_runtime import LangGraphRuntimeAdapter
from aion_brain.schedules.repository import ScheduleRepository
from aion_brain.schedules.service import ScheduleService
from aion_brain.scopes.repository import ScopeRepository
from aion_brain.scopes.resolver import ScopeResolver
from aion_brain.skills.matcher import SkillMatcher
from aion_brain.skills.repository import SkillRepository
from aion_brain.skills.service import SkillService
from aion_brain.tasks.publisher import NatsTaskLifecyclePublisher
from aion_brain.tasks.repository import TaskRepository
from aion_brain.tasks.runner import CognitiveTaskRunner
from aion_brain.tasks.service import TaskService
from aion_brain.telemetry.visual import VisualTelemetryBuilder
from aion_brain.visual.repository import VisualRepository
from aion_brain.working_memory.repository import WorkingMemoryRepository
from aion_brain.working_memory.service import WorkingMemoryService


def get_audit_repository() -> AuditRepository:
    """Create the configured audit repository."""
    settings = get_settings()
    return get_cached_audit_repository(settings.database_url)


@lru_cache
def get_cached_audit_repository(database_url: str) -> AuditRepository:
    """Return a cached audit repository."""
    return AuditRepository(database_url)


@lru_cache
def get_cached_observability_repository(database_url: str) -> ObservabilityRepository:
    """Return a cached local observability repository."""
    return ObservabilityRepository(database_url)


@lru_cache
def get_cached_visual_repository(database_url: str) -> VisualRepository:
    """Return a cached Visual Brain Projection repository."""
    return VisualRepository(database_url)


def get_capability_registry() -> CapabilityRegistry:
    """Return the process-local capability registry."""
    return get_cached_capability_registry()


@lru_cache
def get_cached_capability_registry() -> CapabilityRegistry:
    """Return a cached capability registry."""
    return CapabilityRegistry()


def get_capability_service() -> CapabilityService:
    """Return the process-local capability service."""
    return CapabilityService(get_capability_registry())


def get_module_runtime_repository() -> ModuleRuntimeRepository:
    """Create the configured module runtime repository."""
    settings = get_settings()
    return get_cached_module_runtime_repository(settings.database_url)


@lru_cache
def get_cached_module_runtime_repository(database_url: str) -> ModuleRuntimeRepository:
    """Return a cached module runtime repository."""
    return ModuleRuntimeRepository(database_url)


def get_capability_runtime_gateway() -> CapabilityRuntimeGateway:
    """Create the configured capability runtime gateway."""
    settings = get_settings()
    return get_cached_capability_runtime_gateway(settings.database_url, settings.opa_url)


@lru_cache
def get_cached_capability_runtime_gateway(
    database_url: str,
    opa_url: str,
) -> CapabilityRuntimeGateway:
    """Return a cached capability runtime gateway."""
    settings = get_settings()
    approval_service = get_cached_approval_service(
        database_url,
        opa_url,
        settings.risk_engine_enabled,
        settings.guardrails_enabled,
        settings.approvals_enabled,
        settings.approval_default_expiry_hours,
        settings.high_risk_requires_approval,
        settings.critical_risk_blocks_by_default,
    )
    mcp_service = get_cached_mcp_service(
        database_url,
        opa_url,
        settings.mcp_enabled,
        settings.mcp_allow_network,
        settings.mcp_allow_stdio,
        settings.mcp_timeout_seconds,
        settings.mcp_default_risk_level,
        settings.mcp_auto_register_capabilities,
    )
    return CapabilityRuntimeGateway(
        module_runtime_repository=get_cached_module_runtime_repository(database_url),
        capability_registry=get_capability_registry(),
        policy_adapter=OPAAdapter(opa_url),
        telemetry_service=None,
        runtime_adapters={
            "local_internal": LocalInternalRuntimeAdapter(),
            "local_stub": LocalStubRuntimeAdapter(),
            "mcp": MCPRuntimeAdapter(mcp_service),
        },
        approval_service=approval_service,
    )


def get_goal_repository() -> GoalRepository:
    """Create the configured goal repository."""
    settings = get_settings()
    return get_cached_goal_repository(settings.database_url)


@lru_cache
def get_cached_goal_repository(database_url: str) -> GoalRepository:
    """Return a cached goal repository."""
    return GoalRepository(database_url)


def get_task_repository() -> TaskRepository:
    """Create the configured task repository."""
    settings = get_settings()
    return get_cached_task_repository(settings.database_url)


@lru_cache
def get_cached_task_repository(database_url: str) -> TaskRepository:
    """Return a cached task repository."""
    return TaskRepository(database_url)


def get_schedule_repository() -> ScheduleRepository:
    """Create the configured schedule repository."""
    settings = get_settings()
    return get_cached_schedule_repository(settings.database_url)


@lru_cache
def get_cached_schedule_repository(database_url: str) -> ScheduleRepository:
    """Return a cached schedule repository."""
    return ScheduleRepository(database_url)


def get_lifecycle_publisher() -> NatsTaskLifecyclePublisher:
    """Create the configured lifecycle publisher."""
    settings = get_settings()
    return NatsTaskLifecyclePublisher(settings.nats_url)


def get_reflection_repository() -> ReflectionRepository:
    """Create the configured reflection repository."""
    settings = get_settings()
    return get_cached_reflection_repository(settings.database_url)


@lru_cache
def get_cached_reflection_repository(database_url: str) -> ReflectionRepository:
    """Return a cached reflection repository."""
    return ReflectionRepository(database_url)


def get_skill_repository() -> SkillRepository:
    """Create the configured skill repository."""
    settings = get_settings()
    return get_cached_skill_repository(settings.database_url)


@lru_cache
def get_cached_skill_repository(database_url: str) -> SkillRepository:
    """Return a cached skill repository."""
    return SkillRepository(database_url)


def get_reflection_engine() -> ReflectionEngine:
    """Create the configured reflection engine."""
    settings = get_settings()
    policy_adapter = OPAAdapter(settings.opa_url)
    return ReflectionEngine(
        reflection_repository=get_cached_reflection_repository(settings.database_url),
        learning_engine=LearningEngine(),
        policy_adapter=policy_adapter,
        telemetry_service=get_cached_audit_repository(settings.database_url),
    )


def get_skill_service() -> SkillService:
    """Create the configured skill registry service."""
    settings = get_settings()
    policy_adapter = OPAAdapter(settings.opa_url)
    skill_repository = get_cached_skill_repository(settings.database_url)
    return SkillService(
        skill_repository=skill_repository,
        reflection_repository=get_cached_reflection_repository(settings.database_url),
        policy_adapter=policy_adapter,
        telemetry_service=get_cached_audit_repository(settings.database_url),
        matcher=SkillMatcher(skill_repository),
        approval_service=get_cached_approval_service(
            settings.database_url,
            settings.opa_url,
            settings.risk_engine_enabled,
            settings.guardrails_enabled,
            settings.approvals_enabled,
            settings.approval_default_expiry_hours,
            settings.high_risk_requires_approval,
            settings.critical_risk_blocks_by_default,
        ),
    )


def get_identity_repository() -> IdentityRepository:
    """Create the configured identity repository."""
    settings = get_settings()
    return get_cached_identity_repository(settings.database_url)


@lru_cache
def get_cached_identity_repository(database_url: str) -> IdentityRepository:
    """Return a cached identity repository."""
    return IdentityRepository(database_url)


def get_scope_repository() -> ScopeRepository:
    """Create the configured scope repository."""
    settings = get_settings()
    return get_cached_scope_repository(settings.database_url)


@lru_cache
def get_cached_scope_repository(database_url: str) -> ScopeRepository:
    """Return a cached scope repository."""
    return ScopeRepository(database_url)


def get_identity_service() -> IdentityService:
    """Create the configured identity service."""
    settings = get_settings()
    return IdentityService(
        repository=get_cached_identity_repository(settings.database_url),
        policy_adapter=OPAAdapter(settings.opa_url),
        telemetry_service=get_cached_audit_repository(settings.database_url),
    )


def get_scope_resolver() -> ScopeResolver:
    """Create the configured scope resolver."""
    settings = get_settings()
    return ScopeResolver(
        identity_repository=get_cached_identity_repository(settings.database_url),
        scope_repository=get_cached_scope_repository(settings.database_url),
        policy_adapter=OPAAdapter(settings.opa_url),
        telemetry_service=get_cached_audit_repository(settings.database_url),
    )


def get_goal_service() -> GoalService:
    """Create the configured goal service."""
    settings = get_settings()
    return GoalService(
        repository=get_cached_goal_repository(settings.database_url),
        policy_adapter=OPAAdapter(settings.opa_url),
        publisher=get_lifecycle_publisher(),
        telemetry_service=None,
    )


def get_task_service() -> TaskService:
    """Create the configured task service."""
    settings = get_settings()
    return TaskService(
        repository=get_cached_task_repository(settings.database_url),
        policy_adapter=OPAAdapter(settings.opa_url),
        publisher=get_lifecycle_publisher(),
        telemetry_service=None,
    )


def get_schedule_service() -> ScheduleService:
    """Create the configured schedule service."""
    settings = get_settings()
    return ScheduleService(
        repository=get_cached_schedule_repository(settings.database_url),
        policy_adapter=OPAAdapter(settings.opa_url),
        publisher=get_lifecycle_publisher(),
        telemetry_service=None,
    )


def get_task_runner() -> CognitiveTaskRunner:
    """Create the configured cognitive task runner."""
    settings = get_settings()
    repository = get_cached_task_repository(settings.database_url)
    policy_adapter = OPAAdapter(settings.opa_url)
    task_service = TaskService(
        repository=repository,
        policy_adapter=policy_adapter,
        publisher=get_lifecycle_publisher(),
        telemetry_service=None,
    )
    return CognitiveTaskRunner(
        task_service=task_service,
        task_repository=repository,
        policy_adapter=policy_adapter,
        execution_orchestrator=None,
        brain_runtime=None,
        workflow_service=get_cached_workflow_service(
            settings.database_url,
            settings.opa_url,
            settings.workflow_engine_adapter,
            settings.workflow_local_worker_enabled,
            settings.temporal_enabled,
            settings.temporal_endpoint_ref,
            settings.temporal_namespace,
            settings.temporal_task_queue,
        ),
        telemetry_service=None,
        approval_service=get_cached_approval_service(
            settings.database_url,
            settings.opa_url,
            settings.risk_engine_enabled,
            settings.guardrails_enabled,
            settings.approvals_enabled,
            settings.approval_default_expiry_hours,
            settings.high_risk_requires_approval,
            settings.critical_risk_blocks_by_default,
        ),
    )


def get_evaluator() -> Evaluator:
    """Return the deterministic evaluator."""
    return Evaluator()


def get_learning_engine() -> LearningEngine:
    """Return the deterministic learning signal engine."""
    return LearningEngine()


def get_brain_loop_service() -> BrainLoopService:
    """Create the configured full Brain loop service."""
    settings = get_settings()
    return get_cached_brain_loop_service(settings.database_url, settings.opa_url)


@lru_cache
def get_cached_brain_loop_service(database_url: str, opa_url: str) -> BrainLoopService:
    """Return a cached full Brain loop service."""
    settings = get_settings()
    policy_adapter = OPAAdapter(opa_url)
    attention_repository = AttentionRepository(database_url)
    focus_service = FocusService(attention_repository, policy_adapter)
    working_memory_service = WorkingMemoryService(
        WorkingMemoryRepository(database_url),
        policy_adapter,
        settings=settings,
    )
    attention_controller = AttentionController(
        attention_repository,
        policy_adapter,
        working_memory_service=working_memory_service,
        focus_service=focus_service,
        settings=settings,
    )
    context_budgeter = ContextBudgeter(attention_repository, policy_adapter)
    memory_service = PostgresMemoryService(
        memory_adapter=MemoryRepository(database_url),
        policy_adapter=policy_adapter,
    )
    graph_service = get_cached_graph_memory_service(
        database_url,
        opa_url,
        settings.default_graph_memory_adapter,
        settings.graphiti_enabled,
        settings.graphiti_config_name,
        settings.graphiti_backend_type,
        settings.graphiti_endpoint_ref,
        settings.graphiti_fail_open_to_postgres_graph,
        settings.model_gateway_enabled,
    )
    retrieval_router = get_cached_retrieval_router(
        database_url,
        opa_url,
        settings.default_semantic_adapter,
        settings.embedding_adapter,
        settings.semantic_vector_dimensions,
        settings.turbovec_enabled,
        settings.turbovec_index_name,
        settings.turbovec_index_dir,
        settings.turbovec_bit_width,
        settings.turbovec_auto_persist,
        settings.turbovec_fail_open_to_pgvector,
        settings.default_graph_memory_adapter,
        settings.graphiti_enabled,
        settings.graphiti_config_name,
        settings.graphiti_backend_type,
        settings.graphiti_endpoint_ref,
        settings.graphiti_fail_open_to_postgres_graph,
        settings.model_gateway_enabled,
    )
    runtime = LangGraphRuntimeAdapter(
        intent_engine=IntentEngine(),
        context_compiler=ContextCompiler(
            policy_adapter=policy_adapter,
            memory_service=memory_service,
            graph_service=graph_service,
            capability_catalog=get_capability_registry(),
            retrieval_router=retrieval_router,
            attention_controller=attention_controller,
            context_budgeter=context_budgeter,
            settings=settings,
        ),
        planner=Planner(),
        policy_adapter=policy_adapter,
        reasoning_mesh=ReasoningMesh(
            model_router=ModelRouter(),
            prompt_builder=PromptBuilder(),
            model_gateway_adapter=DeterministicReasoningAdapter(),
            policy_adapter=policy_adapter,
            reasoning_repository=ReasoningRepository(database_url),
            telemetry_service=None,
        ),
    )
    return BrainLoopService(
        runtime=runtime,
        audit_ledger=AuditLedger(get_cached_audit_repository(database_url)),
        evaluator=Evaluator(),
        learning_engine=LearningEngine(),
        telemetry_builder=VisualTelemetryBuilder(),
        goal_service=GoalService(
            repository=get_cached_goal_repository(database_url),
            policy_adapter=policy_adapter,
            publisher=get_lifecycle_publisher(),
            telemetry_service=None,
        ),
        task_service=TaskService(
            repository=get_cached_task_repository(database_url),
            policy_adapter=policy_adapter,
            publisher=get_lifecycle_publisher(),
            telemetry_service=None,
        ),
        reflection_engine=ReflectionEngine(
            reflection_repository=get_cached_reflection_repository(database_url),
            learning_engine=LearningEngine(),
            policy_adapter=policy_adapter,
            telemetry_service=get_cached_audit_repository(database_url),
        ),
        skill_service=SkillService(
            skill_repository=get_cached_skill_repository(database_url),
            reflection_repository=get_cached_reflection_repository(database_url),
            policy_adapter=policy_adapter,
            telemetry_service=get_cached_audit_repository(database_url),
            matcher=SkillMatcher(get_cached_skill_repository(database_url)),
            approval_service=get_cached_approval_service(
                database_url,
                opa_url,
                settings.risk_engine_enabled,
                settings.guardrails_enabled,
                settings.approvals_enabled,
                settings.approval_default_expiry_hours,
                settings.high_risk_requires_approval,
                settings.critical_risk_blocks_by_default,
            ),
        ),
        observability_adapter=LocalObservabilityRecorder(
            get_cached_observability_repository(database_url),
            get_cached_visual_repository(database_url),
        ),
        focus_service=focus_service,
        attention_controller=attention_controller,
        working_memory_service=working_memory_service,
    )
