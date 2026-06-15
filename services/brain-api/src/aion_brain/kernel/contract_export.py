"""OpenAPI and AION-owned contract export."""

from datetime import UTC, datetime
from uuid import uuid4

from fastapi import FastAPI
from pydantic import BaseModel

from aion_brain.contracts.api import (
    AIONError,
    AIONErrorResponse,
    AIONFilter,
    AIONPage,
    AIONPageInfo,
    AIONPageRequest,
    AIONSort,
    AIONSuccessEnvelope,
    APIRequestRecord,
    OpenAPIHygieneReport,
    RequestContext,
)
from aion_brain.contracts.approvals import (
    ApprovalCreateRequest,
    ApprovalDecision,
    ApprovalDecisionRequest,
    ApprovalInboxQuery,
    ApprovalLifecycleEvent,
    ApprovalRequest,
)
from aion_brain.contracts.capabilities import CapabilityManifest
from aion_brain.contracts.compatibility import (
    CompatibilityMatrix,
    MigrationBaseline,
    ReleaseArtifactManifest,
    SDKCompatibilityReport,
)
from aion_brain.contracts.context import ContextPacket
from aion_brain.contracts.events import AIONEvent
from aion_brain.contracts.evidence import EvidenceRecord
from aion_brain.contracts.execution import ExecutionRequest
from aion_brain.contracts.freeze import FreezeGateCheck, FreezeGateRun, FreezeGateRunRequest
from aion_brain.contracts.goals import GoalRecord
from aion_brain.contracts.graph import (
    GraphitiConfigStatus,
    GraphitiEpisodeRequest,
    GraphitiEpisodeResponse,
    GraphitiSyncRequest,
    GraphitiSyncResponse,
    GraphMemoryAdapterStatus,
    GraphNode,
    GraphQueryResult,
)
from aion_brain.contracts.guardrails import (
    GuardrailDecision,
    GuardrailRule,
    RiskGuardrailEvaluation,
    RiskGuardrailEvaluationRequest,
)
from aion_brain.contracts.identity import ActorRecord, WorkspaceRecord
from aion_brain.contracts.intent import IntentFrame
from aion_brain.contracts.kernel import ContractExport, KernelStatus
from aion_brain.contracts.mcp import (
    MCPAdapterStatus,
    MCPCapabilityMapping,
    MCPInvocationRequest,
    MCPInvocationResult,
    MCPServerHealth,
    MCPServerRecord,
    MCPServerRegistrationRequest,
    MCPSyncRequest,
    MCPSyncResponse,
    MCPToolDescriptor,
)
from aion_brain.contracts.memory import (
    MemoryRecord,
    SemanticAdapterStatus,
    SemanticMemoryQuery,
    TurboVecIndexStatus,
    TurboVecRebuildRequest,
    TurboVecRebuildResponse,
)
from aion_brain.contracts.memory_governance import (
    ForgetMemoryRequest,
    ForgetMemoryResult,
    MemoryCompactionRequest,
    MemoryCompactionResult,
    MemoryConflict,
    MemoryConflictScanRequest,
    MemoryDecayRecord,
    MemoryGovernanceDecision,
    MemoryGovernanceRule,
    MemoryRetentionSweepRequest,
    MemoryRetentionSweepResult,
)
from aion_brain.contracts.model_gateway import (
    ModelBudgetRecord,
    ModelGatewayRequest,
    ModelGatewayResponse,
    ModelProfile,
    ModelProvider,
    ModelProviderHealth,
    ModelUsageRecord,
    PromptRedactionRecord,
)
from aion_brain.contracts.modules import ModuleRuntime
from aion_brain.contracts.planning import PlanGraph
from aion_brain.contracts.reasoning import ReasoningRequest
from aion_brain.contracts.reflection import ReflectionRecord
from aion_brain.contracts.regression import RegressionCase
from aion_brain.contracts.release_baseline import (
    ReleaseBaselineReport,
    ReleaseBaselineRequest,
)
from aion_brain.contracts.release_package import (
    ReleaseHandoffReport,
    ReleasePackage,
    ReleasePackageFile,
    ReleasePackageManifest,
    ReleasePackageRequest,
    ReleasePackageValidation,
    SBOMPlaceholder,
)
from aion_brain.contracts.replay import ReplayRequest
from aion_brain.contracts.retrieval import RetrievalRequest
from aion_brain.contracts.risk import RiskAssessment, RiskAssessmentRequest
from aion_brain.contracts.scenarios import (
    DemoFixture,
    DemoFixtureLoadRequest,
    DemoFixtureLoadResult,
    ScenarioCreateRequest,
    ScenarioDefinition,
    ScenarioRun,
    ScenarioRunRequest,
    ScenarioStep,
    ScenarioStepRun,
)
from aion_brain.contracts.skills import SkillRecord
from aion_brain.contracts.tasks import CognitiveTask
from aion_brain.contracts.versioning import (
    DeprecationPolicy,
    FeatureRegistryEntry,
    VersionManifest,
)
from aion_brain.contracts.visual import BrainMap
from aion_brain.contracts.workflows import (
    TemporalAdapterStatus,
    WorkflowDefinition,
    WorkflowEngineStatus,
    WorkflowRun,
)

CORE_CONTRACTS: tuple[type[BaseModel], ...] = (
    AIONEvent,
    IntentFrame,
    ContextPacket,
    MemoryRecord,
    MemoryGovernanceRule,
    MemoryGovernanceDecision,
    MemoryDecayRecord,
    ForgetMemoryRequest,
    ForgetMemoryResult,
    MemoryConflict,
    MemoryConflictScanRequest,
    MemoryCompactionRequest,
    MemoryCompactionResult,
    MemoryRetentionSweepRequest,
    MemoryRetentionSweepResult,
    SemanticMemoryQuery,
    SemanticAdapterStatus,
    TurboVecIndexStatus,
    TurboVecRebuildRequest,
    TurboVecRebuildResponse,
    GraphNode,
    GraphQueryResult,
    GraphMemoryAdapterStatus,
    GraphitiConfigStatus,
    GraphitiSyncRequest,
    GraphitiSyncResponse,
    GraphitiEpisodeRequest,
    GraphitiEpisodeResponse,
    MCPServerRecord,
    MCPToolDescriptor,
    MCPCapabilityMapping,
    MCPServerRegistrationRequest,
    MCPSyncRequest,
    MCPSyncResponse,
    MCPInvocationRequest,
    MCPInvocationResult,
    MCPServerHealth,
    MCPAdapterStatus,
    RiskAssessment,
    RiskAssessmentRequest,
    GuardrailRule,
    GuardrailDecision,
    RiskGuardrailEvaluationRequest,
    RiskGuardrailEvaluation,
    ApprovalRequest,
    ApprovalCreateRequest,
    ApprovalDecisionRequest,
    ApprovalDecision,
    ApprovalInboxQuery,
    ApprovalLifecycleEvent,
    EvidenceRecord,
    RetrievalRequest,
    ReasoningRequest,
    ModelProvider,
    ModelProfile,
    ModelGatewayRequest,
    ModelGatewayResponse,
    PromptRedactionRecord,
    ModelBudgetRecord,
    ModelUsageRecord,
    ModelProviderHealth,
    PlanGraph,
    ExecutionRequest,
    CapabilityManifest,
    ModuleRuntime,
    GoalRecord,
    CognitiveTask,
    ReflectionRecord,
    SkillRecord,
    ActorRecord,
    WorkspaceRecord,
    BrainMap,
    WorkflowDefinition,
    WorkflowRun,
    WorkflowEngineStatus,
    TemporalAdapterStatus,
    ReplayRequest,
    RegressionCase,
    ScenarioStep,
    ScenarioDefinition,
    ScenarioCreateRequest,
    ScenarioRunRequest,
    ScenarioStepRun,
    ScenarioRun,
    DemoFixture,
    DemoFixtureLoadRequest,
    DemoFixtureLoadResult,
    ReleaseBaselineRequest,
    ReleaseBaselineReport,
    VersionManifest,
    FeatureRegistryEntry,
    DeprecationPolicy,
    CompatibilityMatrix,
    MigrationBaseline,
    ReleaseArtifactManifest,
    SDKCompatibilityReport,
    FreezeGateCheck,
    FreezeGateRunRequest,
    FreezeGateRun,
    ReleasePackageRequest,
    ReleasePackageFile,
    ReleasePackageManifest,
    ReleasePackageValidation,
    ReleaseHandoffReport,
    ReleasePackage,
    SBOMPlaceholder,
    KernelStatus,
    AIONError,
    AIONErrorResponse,
    AIONSuccessEnvelope,
    AIONPageRequest,
    AIONPageInfo,
    AIONPage,
    AIONFilter,
    AIONSort,
    RequestContext,
    APIRequestRecord,
    OpenAPIHygieneReport,
)


class ContractExportService:
    """Export frontend- and provider-neutral AION contracts."""

    def __init__(self, version: str) -> None:
        self._version = version

    def export_contracts(self, app: FastAPI) -> ContractExport:
        """Export OpenAPI and core Pydantic JSON schemas."""
        return ContractExport(
            export_id=f"contract-export-{uuid4().hex}",
            version=self._version,
            contracts={
                contract.__name__: contract.model_json_schema() for contract in CORE_CONTRACTS
            },
            openapi=app.openapi(),
            generated_at=datetime.now(UTC),
        )
