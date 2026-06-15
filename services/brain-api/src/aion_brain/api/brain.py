"""Brain runtime API."""

from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, ConfigDict

from aion_brain.api.dependencies import (
    get_brain_loop_service as get_cached_brain_loop_service_dependency,
)
from aion_brain.api.graph_memory import get_cached_graph_memory_service
from aion_brain.api.retrieval import get_cached_retrieval_router
from aion_brain.attention.context_budget import ContextBudgeter
from aion_brain.attention.controller import AttentionController
from aion_brain.attention.focus import FocusService
from aion_brain.attention.repository import AttentionRepository
from aion_brain.capabilities.registry import CapabilityRegistry
from aion_brain.config import get_settings
from aion_brain.context.compiler import ContextCompiler
from aion_brain.contracts.context import ContextPacket
from aion_brain.contracts.events import AIONEvent
from aion_brain.contracts.planning import PlanGraph
from aion_brain.contracts.scopes import ActorContext
from aion_brain.contracts.traces import DecisionTrace
from aion_brain.core.brain_loop import BrainLoopService
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.intent.engine import IntentEngine
from aion_brain.kernel.container import KernelContainer
from aion_brain.memory.repository import MemoryRepository
from aion_brain.memory.service import PostgresMemoryService
from aion_brain.planning.planner import Planner
from aion_brain.policy.opa_adapter import OPAAdapter
from aion_brain.reasoning.deterministic_adapter import DeterministicReasoningAdapter
from aion_brain.reasoning.mesh import ReasoningMesh
from aion_brain.reasoning.prompt_builder import PromptBuilder
from aion_brain.reasoning.repository import ReasoningRepository
from aion_brain.reasoning.router import ModelRouter
from aion_brain.runtime.base import BrainRuntimeAdapter
from aion_brain.runtime.langgraph_runtime import LangGraphRuntimeAdapter
from aion_brain.working_memory.repository import WorkingMemoryRepository
from aion_brain.working_memory.service import WorkingMemoryService

router = APIRouter(prefix="/brain", tags=["brain"])


class PlanRequest(BaseModel):
    """Plan creation request."""

    model_config = ConfigDict(extra="forbid")

    context: ContextPacket


def get_planner() -> Planner:
    """Return the deterministic planner."""
    return Planner()


def get_brain_loop_service(request: Request) -> BrainLoopService:
    """Return the kernel-composed Brain loop service when available."""
    container = getattr(request.app.state, "kernel_container", None)
    if isinstance(container, KernelContainer):
        return container.brain_loop_service
    return get_cached_brain_loop_service_dependency()


def get_brain_runtime() -> BrainRuntimeAdapter:
    """Create the configured deterministic Brain runtime."""
    settings = get_settings()
    return get_cached_brain_runtime(settings.database_url, settings.opa_url)


@lru_cache
def get_cached_brain_runtime(database_url: str, opa_url: str) -> BrainRuntimeAdapter:
    """Return a cached LangGraph runtime behind the Brain adapter boundary."""
    policy_adapter = OPAAdapter(opa_url)
    settings = get_settings()
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
    return LangGraphRuntimeAdapter(
        intent_engine=IntentEngine(),
        context_compiler=ContextCompiler(
            policy_adapter=policy_adapter,
            memory_service=memory_service,
            graph_service=graph_service,
            capability_catalog=CapabilityRegistry(),
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


@router.post("/plan", response_model=PlanGraph)
def create_plan(
    request: PlanRequest,
    planner: Annotated[Planner, Depends(get_planner)],
) -> PlanGraph:
    """Create a deterministic plan graph from a context packet."""
    return planner.create_plan(request.context)


@router.post("/think", response_model=DecisionTrace)
def think(
    event: AIONEvent,
    service: Annotated[BrainLoopService, Depends(get_brain_loop_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> DecisionTrace:
    """Run the deterministic Brain loop through planning and policy."""
    enriched_event = event.model_copy(
        update={
            "actor_id": event.actor_id or actor_context.actor_id,
            "workspace_id": event.workspace_id or actor_context.workspace_id,
            "security_scope": event.security_scope or actor_context.security_scope,
            "correlation_id": event.correlation_id or actor_context.correlation_id,
            "trace_id": event.trace_id or actor_context.trace_id,
        }
    )
    return service.think(enriched_event)
