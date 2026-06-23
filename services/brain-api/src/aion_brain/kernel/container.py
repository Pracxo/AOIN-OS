"""Single composition root for AION Brain."""

from datetime import UTC, datetime
from pathlib import Path
from typing import TypeVar, cast

from aion_brain.action_proposals.blockers import ActionBlockerService
from aion_brain.action_proposals.handoffs import ExecutionHandoffService
from aion_brain.action_proposals.proposals import ActionProposalService
from aion_brain.action_proposals.query import ActionProposalQueryService
from aion_brain.action_proposals.repository import ActionProposalRepository
from aion_brain.action_proposals.reviews import ActionReviewService
from aion_brain.action_proposals.tool_intent_review import ToolIntentReviewService
from aion_brain.api_support.openapi_hygiene import OpenAPIHygieneChecker
from aion_brain.api_support.request_audit import APIRequestAuditService
from aion_brain.approvals.repository import ApprovalRepository
from aion_brain.approvals.service import ApprovalService
from aion_brain.attention.context_budget import ContextBudgeter
from aion_brain.attention.controller import AttentionController
from aion_brain.attention.focus import FocusService
from aion_brain.attention.interrupts import InterruptRouter
from aion_brain.attention.repository import AttentionRepository
from aion_brain.audit.ledger import AuditLedger
from aion_brain.audit.repository import AuditRepository
from aion_brain.audit_integrity.checkpoints import AuditCheckpointService
from aion_brain.audit_integrity.exporter import AuditExporter
from aion_brain.audit_integrity.ledger import AuditIntegrityLedger
from aion_brain.audit_integrity.provenance import ProvenanceService
from aion_brain.audit_integrity.repository import AuditIntegrityRepository
from aion_brain.audit_integrity.verifier import AuditVerifier
from aion_brain.autonomy.delegation import DelegationService
from aion_brain.autonomy.governor import AutonomyGovernor
from aion_brain.autonomy.repository import AutonomyRepository
from aion_brain.autonomy.run_level import RunLevelService
from aion_brain.backups.exporter import BackupExporter
from aion_brain.backups.repository import BackupRepository
from aion_brain.backups.resource_readers import ResourceReaderRegistry
from aion_brain.backups.restore_preview import RestorePreviewService
from aion_brain.backups.restore_service import RestoreService
from aion_brain.backups.validator import BackupValidator
from aion_brain.beliefs.claim_extractor import ClaimExtractor
from aion_brain.beliefs.contradictions import BeliefContradictionService
from aion_brain.beliefs.query import BeliefQueryService
from aion_brain.beliefs.repository import BeliefRepository
from aion_brain.beliefs.service import BeliefService
from aion_brain.beliefs.supports import BeliefSupportService
from aion_brain.beliefs.truth_maintenance import TruthMaintenanceService
from aion_brain.bootstrap import (
    BootstrapProfileService,
    BootstrapQueryService,
    BootstrapRepository,
    BootstrapRunner,
    SeedBundleService,
    SeedExecutor,
    SetupDoctor,
    SetupReportService,
)
from aion_brain.capabilities.mcp_adapter import MCPAdapter
from aion_brain.capabilities.registry import CapabilityRegistry
from aion_brain.capabilities.service import CapabilityService
from aion_brain.commands.bus import CommandBus
from aion_brain.commands.handlers import CommandHandlerRegistry
from aion_brain.commands.repository import CommandRepository
from aion_brain.concepts.repository import ConceptRepository
from aion_brain.concepts.service import ConceptService
from aion_brain.config import Settings, get_settings
from aion_brain.conformance import (
    CapabilityTestVectorService,
    ConformanceFindingService,
    ConformanceProfileService,
    ConformanceQueryService,
    ConformanceRepository,
    ConformanceRunner,
    MockInvocationSimulator,
    ReadinessAssessmentService,
    SchemaConformanceChecker,
)
from aion_brain.connectors.repository import ConnectorRepository
from aion_brain.connectors.service import ConnectorService
from aion_brain.consistency.checker import ConsistencyChecker
from aion_brain.consistency.leases import ProcessingLeaseService
from aion_brain.consistency.repository import ConsistencyRepository
from aion_brain.context.compiler import ContextCompiler
from aion_brain.contract_registry import (
    CompatibilityRuleService,
    ContractRegistryQueryService,
    ContractRegistryReportService,
    ContractRegistryRepository,
    ContractScanner,
    ContractSnapshotService,
    InterfaceInventoryService,
    MigrationNoteService,
)
from aion_brain.contract_registry import (
    CompatibilityScanner as ContractCompatibilityScanner,
)
from aion_brain.contracts.kernel import (
    KernelAdapterConfig,
    KernelBootRecord,
    KernelServiceType,
    KernelStatus,
)
from aion_brain.core.brain_loop import BrainLoopService
from aion_brain.cycles.maintenance import MaintenanceService
from aion_brain.cycles.orchestrator import CognitiveCycleOrchestrator
from aion_brain.cycles.repository import CognitiveCycleRepository
from aion_brain.cycles.sleep import SleepConsolidationService
from aion_brain.decisions.counterfactuals import CounterfactualSimulator
from aion_brain.decisions.evaluator import OptionEvaluator
from aion_brain.decisions.frames import DecisionFrameService
from aion_brain.decisions.journal import DecisionJournalService
from aion_brain.decisions.options import DecisionOptionService
from aion_brain.decisions.recommendations import DecisionRecommendationService
from aion_brain.decisions.repository import DecisionRepository
from aion_brain.decisions.tradeoffs import TradeoffMatrixService
from aion_brain.decisions.utility import UtilityProfileService
from aion_brain.dialogue.clarification import ClarificationManager
from aion_brain.dialogue.memory_handoff import DialogueMemoryHandoffService
from aion_brain.dialogue.message_service import DialogueMessageService
from aion_brain.dialogue.repository import DialogueRepository
from aion_brain.dialogue.session_service import DialogueSessionService
from aion_brain.dialogue.turn_service import DialogueTurnService
from aion_brain.embeddings.hash_embedding import HashEmbeddingAdapter
from aion_brain.entities.aliases import EntityAliasService
from aion_brain.entities.mention_extractor import EntityMentionExtractor
from aion_brain.entities.merge import EntityMergeService
from aion_brain.entities.query import EntityQueryService
from aion_brain.entities.references import ReferenceLinkService
from aion_brain.entities.repository import EntityRepository
from aion_brain.entities.resolver import EntityResolver
from aion_brain.entities.service import EntityService
from aion_brain.entities.split import EntitySplitService
from aion_brain.evaluation.evaluator import Evaluator
from aion_brain.event_reactions.actions import EventReactionActionRunner
from aion_brain.event_reactions.dead_letters import EventDeadLetterService
from aion_brain.event_reactions.matcher import EventTriggerMatcher
from aion_brain.event_reactions.replay import EventReactionReplayService
from aion_brain.event_reactions.repository import EventReactionRepository
from aion_brain.event_reactions.router import EventReactionRouter
from aion_brain.events.repository import EventRepository
from aion_brain.evidence.repository import EvidenceRepository
from aion_brain.evidence.service import EvidenceService
from aion_brain.execution.capability_invoker import CapabilityInvoker
from aion_brain.execution.orchestrator import ExecutionOrchestrator
from aion_brain.execution.repository import ExecutionRepository
from aion_brain.explanations.builder import ExplanationBuilder
from aion_brain.explanations.feedback import ExplanationFeedbackService
from aion_brain.explanations.repository import ExplanationRepository
from aion_brain.explanations.trace_narrative import TraceNarrativeBuilder
from aion_brain.explanations.verifier import ExplanationVerifier
from aion_brain.explanations.why_not import WhyNotService
from aion_brain.extensions import (
    CapabilityDeclarationService,
    DependencyDeclarationService,
    ExtensionCompatibilityGate,
    ExtensionIntakeService,
    ExtensionPackageService,
    ExtensionQueryService,
    ExtensionRegistryRepository,
    ExtensionReviewService,
    InstallPlanService,
    ManifestValidator,
)
from aion_brain.freeze.gate import FreezeGateService
from aion_brain.goals.repository import GoalRepository
from aion_brain.goals.service import GoalService
from aion_brain.golden_path import (
    AssertionEngine,
    FixturePackService,
    GoldenPathQueryService,
    GoldenPathReportService,
    GoldenPathRepository,
    GoldenPathRunner,
    ReleaseSmokeMatrix,
    ScenarioCatalogService,
)
from aion_brain.grounding.citation_mapper import CitationMapper
from aion_brain.grounding.citations import CitationService
from aion_brain.grounding.coverage import SourceCoverageService
from aion_brain.grounding.query import GroundingQueryService
from aion_brain.grounding.repository import GroundingRepository
from aion_brain.grounding.sources import GroundingSourceService
from aion_brain.grounding.statement_splitter import StatementSplitter
from aion_brain.grounding.support_checker import SupportChecker
from aion_brain.grounding.verifier import GroundingVerifier
from aion_brain.guardrails.engine import GuardrailEngine
from aion_brain.guardrails.repository import GuardrailRepository
from aion_brain.idempotency.repository import IdempotencyRepository
from aion_brain.idempotency.service import IdempotencyService
from aion_brain.identity.repository import IdentityRepository
from aion_brain.identity.service import IdentityService
from aion_brain.inbox.repository import InboxRepository
from aion_brain.inbox.service import InboxService
from aion_brain.incidents.correlation import IncidentCorrelationEngine
from aion_brain.incidents.query import IncidentQueryService
from aion_brain.incidents.recovery import RecoveryReviewService
from aion_brain.incidents.repository import IncidentRepository
from aion_brain.incidents.root_cause import RootCauseCandidateService
from aion_brain.incidents.rules import CorrelationRuleService
from aion_brain.incidents.service import IncidentService
from aion_brain.incidents.signals import IncidentSignalService
from aion_brain.instructions.conflicts import InstructionConflictDetector
from aion_brain.instructions.constraints import ConstraintService
from aion_brain.instructions.learning import PreferenceLearningService
from aion_brain.instructions.preferences import PreferenceService
from aion_brain.instructions.query import InstructionQueryService
from aion_brain.instructions.repository import InstructionRepository
from aion_brain.instructions.resolver import InstructionResolver
from aion_brain.instructions.service import InstructionService
from aion_brain.instructions.styles import StyleProfileService
from aion_brain.intent.engine import IntentEngine
from aion_brain.kernel.boot import KernelBootService
from aion_brain.kernel.bootstrap import build_dev_bootstrap
from aion_brain.kernel.boundary_check import ArchitectureBoundaryChecker
from aion_brain.kernel.contract_export import ContractExportService
from aion_brain.kernel.diagnostics import KernelDiagnostics
from aion_brain.kernel.repository import KernelRepository
from aion_brain.kernel.self_test import KernelSelfTestService
from aion_brain.kernel.service_registry import KernelServiceRegistry
from aion_brain.learning.engine import LearningEngine
from aion_brain.learning_synthesis.experience import ExperienceService
from aion_brain.learning_synthesis.lessons import LessonService
from aion_brain.learning_synthesis.miner import PatternMiner
from aion_brain.learning_synthesis.query import LearningQueryService
from aion_brain.learning_synthesis.regression_suggestions import RegressionSuggestionService
from aion_brain.learning_synthesis.repository import LearningSynthesisRepository
from aion_brain.learning_synthesis.skill_suggestions import SkillSuggestionService
from aion_brain.learning_synthesis.synthesizer import LearningSynthesizer
from aion_brain.lifecycle import (
    ArchivePlanner,
    LifecycleEvaluator,
    LifecyclePolicyService,
    LifecycleQueryService,
    LifecycleReportService,
    LifecycleRepository,
    LifecycleReviewService,
    PurgePreviewService,
    RedactionPlanner,
    RetentionClassifier,
)
from aion_brain.logging import configure_logging
from aion_brain.mcp.compat import MCPCompat
from aion_brain.mcp.repository import MCPRepository
from aion_brain.mcp.service import MCPService
from aion_brain.memory.graph_service import GraphMemoryService
from aion_brain.memory.graphiti_adapter import GraphitiGraphMemoryAdapter
from aion_brain.memory.graphiti_compat import GraphitiCompat
from aion_brain.memory.graphiti_repository import GraphitiRepository
from aion_brain.memory.in_memory_graph_adapter import InMemoryGraphAdapter
from aion_brain.memory.in_memory_semantic_adapter import InMemorySemanticMemoryAdapter
from aion_brain.memory.pgvector_adapter import PgVectorSemanticMemoryAdapter
from aion_brain.memory.postgres_graph_adapter import PostgresGraphAdapter
from aion_brain.memory.repository import MemoryRepository
from aion_brain.memory.semantic_service import SemanticMemoryService
from aion_brain.memory.service import PostgresMemoryService
from aion_brain.memory.turbovec_adapter import TurboVecSemanticMemoryAdapter
from aion_brain.memory.turbovec_compat import TurboVecCompat
from aion_brain.memory.turbovec_repository import TurboVecRepository
from aion_brain.memory_governance.compaction import MemoryCompactionService
from aion_brain.memory_governance.conflicts import MemoryConflictService
from aion_brain.memory_governance.decay import MemoryDecayService
from aion_brain.memory_governance.engine import MemoryGovernanceEngine
from aion_brain.memory_governance.forgetting import MemoryForgettingService
from aion_brain.memory_governance.repository import MemoryGovernanceRepository
from aion_brain.memory_governance.retention import MemoryRetentionService
from aion_brain.model_gateway.budget import ModelBudgetGuard
from aion_brain.model_gateway.profile_registry import ModelProfileRegistry
from aion_brain.model_gateway.provider_registry import ModelProviderRegistry
from aion_brain.model_gateway.redaction import PromptRedactor
from aion_brain.model_gateway.repository import ModelGatewayRepository
from aion_brain.model_gateway.router import ModelGatewayRouter
from aion_brain.model_gateway.service import ModelGatewayService
from aion_brain.model_gateway.usage import ModelUsageLedger
from aion_brain.model_outputs.governance import OutputGovernanceService
from aion_brain.model_outputs.parser import OutputParser
from aion_brain.model_outputs.query import ModelOutputQueryService
from aion_brain.model_outputs.repository import ModelOutputRepository
from aion_brain.model_outputs.response_candidates import ResponseCandidateService
from aion_brain.model_outputs.structured_validator import StructuredOutputValidator
from aion_brain.model_outputs.tool_intents import ToolIntentCaptureService
from aion_brain.model_outputs.unsafe_detector import UnsafeOutputDetector
from aion_brain.model_provider_hardening import (
    ModelProviderBlockerService,
    ModelProviderHardeningRepository,
    ModelProviderProfileService,
    ModelProviderReadinessService,
    ModelProviderSimulator,
    PromptEgressGuard,
    ProviderHardeningQueryService,
)
from aion_brain.module_activation import (
    ActivationBlockerService,
    ActivationGateService,
    ActivationPlanService,
    ActivationReviewService,
    ModuleActivationQueryService,
    ModuleActivationRepository,
    ModuleActivationRequestService,
    RuntimeRegistrationPreviewService,
)
from aion_brain.module_bindings import (
    BindingConflictService,
    BindingValidator,
    CapabilityBindingService,
    ModuleBindingQueryService,
    ModuleBindingRepository,
    ModuleMountPlanService,
    ModuleSlotService,
    RouteBindingPreviewService,
)
from aion_brain.module_developer.certifier import ModuleCertifier
from aion_brain.module_developer.compatibility import ModuleCompatibilityChecker
from aion_brain.module_developer.contract_tests import ModuleContractTestHarness
from aion_brain.module_developer.repository import ModuleDeveloperRepository
from aion_brain.module_developer.scaffold import ModuleScaffoldGenerator
from aion_brain.module_developer.validator import ModulePackageValidator
from aion_brain.module_mock_runtime import (
    ModuleMockFindingService,
    ModuleMockPlanService,
    ModuleMockProfileService,
    ModuleMockQueryService,
    ModuleMockRuntimeRepository,
    ModuleMockSchemaAdapter,
    ModuleMockSimulator,
)
from aion_brain.modules.local_internal_runtime import LocalInternalRuntimeAdapter
from aion_brain.modules.local_stub_runtime import LocalStubRuntimeAdapter
from aion_brain.modules.mcp_runtime import MCPRuntimeAdapter
from aion_brain.modules.repository import ModuleRuntimeRepository
from aion_brain.modules.runtime_gateway import CapabilityRuntimeGateway
from aion_brain.notifications.alerts import AlertService
from aion_brain.notifications.digests import NotificationDigestService
from aion_brain.notifications.escalations import EscalationService
from aion_brain.notifications.query import NotificationQueryService
from aion_brain.notifications.repository import NotificationRepository
from aion_brain.notifications.router import NotificationRouter
from aion_brain.notifications.subscriptions import NotificationSubscriptionService
from aion_brain.notifications.topics import NotificationTopicService
from aion_brain.observability.local_recorder import LocalObservabilityRecorder
from aion_brain.observability.repository import ObservabilityRepository
from aion_brain.operator.action_center import ActionCenterService
from aion_brain.operator.control_tower import OperatorControlTowerService
from aion_brain.operator.queues import QueueSummaryBuilder
from aion_brain.operator.readiness import ReadinessAggregator
from aion_brain.operator.repository import OperatorRepository
from aion_brain.operator.runbooks import RunbookRegistry
from aion_brain.operator.snapshots import OperatorSnapshotService
from aion_brain.operator.status_cards import StatusCardBuilder
from aion_brain.outbox.repository import OutboxRepository
from aion_brain.outbox.service import OutboxService
from aion_brain.outcomes.attribution import CausalAttributionService
from aion_brain.outcomes.collector import ObservedEffectCollector
from aion_brain.outcomes.effects import ExpectedEffectService
from aion_brain.outcomes.feedback import OutcomeFeedbackService
from aion_brain.outcomes.query import OutcomeQueryService
from aion_brain.outcomes.repository import OutcomeRepository
from aion_brain.outcomes.service import OutcomeService
from aion_brain.outcomes.verifier import EffectVerifier
from aion_brain.performance.baseline import CapacityBaselineService
from aion_brain.performance.budgets import ResourceBudgetService
from aion_brain.performance.regression import PerformanceRegressionComparator
from aion_brain.performance.repository import PerformanceRepository
from aion_brain.performance.runner import BenchmarkRunner
from aion_brain.performance.summary import PerformanceSummaryService
from aion_brain.planning.planner import Planner
from aion_brain.policy.base import PolicyAdapter
from aion_brain.policy.opa_adapter import OPAAdapter
from aion_brain.policy_catalog.bundles import PolicyBundleService
from aion_brain.policy_catalog.catalog import PolicyCatalogService
from aion_brain.policy_catalog.coverage import PolicyCoverageAnalyzer
from aion_brain.policy_catalog.permissions import PermissionMatrixService
from aion_brain.policy_catalog.repository import PolicyCatalogRepository
from aion_brain.policy_catalog.simulation import PolicySimulationService
from aion_brain.policy_catalog.test_harness import PolicyTestHarness
from aion_brain.prompts.boundary import PromptBoundaryChecker
from aion_brain.prompts.compiler import PromptPacketCompiler
from aion_brain.prompts.fragments import PromptFragmentService
from aion_brain.prompts.injection_detector import PromptInjectionDetector
from aion_brain.prompts.manifest import ModelInputManifestService
from aion_brain.prompts.preview import PromptPreviewService
from aion_brain.prompts.repository import PromptRepository
from aion_brain.prompts.sectioner import PromptSectioner
from aion_brain.prompts.service import PromptGovernanceService
from aion_brain.prompts.templates import PromptTemplateService
from aion_brain.reasoning.deterministic_adapter import DeterministicReasoningAdapter
from aion_brain.reasoning.litellm_adapter import LiteLLMHTTPAdapter
from aion_brain.reasoning.mesh import ReasoningMesh
from aion_brain.reasoning.openai_compatible_adapter import OpenAICompatibleHTTPAdapter
from aion_brain.reasoning.prompt_builder import PromptBuilder
from aion_brain.reasoning.repository import ReasoningRepository
from aion_brain.reasoning.router import ModelRouter
from aion_brain.reflection.engine import ReflectionEngine
from aion_brain.reflection.repository import ReflectionRepository
from aion_brain.regression.report import RegressionReportBuilder
from aion_brain.regression.repository import RegressionRepository
from aion_brain.regression.service import RegressionService
from aion_brain.release_baseline.repository import ReleaseBaselineRepository
from aion_brain.release_baseline.service import ReleaseBaselineService
from aion_brain.release_candidate import (
    RCEvidencePackService,
    RCFindingService,
    RCGateService,
    RCQueryService,
    RCReportService,
    ReleaseCandidateRepository,
    ReleaseCandidateService,
    VerificationCheckCollector,
    VerificationMatrixService,
)
from aion_brain.release_package.handoff import ReleaseHandoffService
from aion_brain.release_package.packager import ReleasePackager
from aion_brain.release_package.repository import ReleasePackageRepository
from aion_brain.release_package.sbom import SBOMPlaceholderService
from aion_brain.release_package.source_manifest import SourceManifestService
from aion_brain.release_package.validator import ReleasePackageValidator
from aion_brain.replay.comparator import TraceComparator
from aion_brain.replay.repository import ReplayRepository
from aion_brain.replay.service import ReplayService
from aion_brain.replay.snapshot import SnapshotService
from aion_brain.resilience.circuit_breakers import CircuitBreakerService
from aion_brain.resilience.degraded_mode import DegradedModeService
from aion_brain.resilience.dependency_health import DependencyHealthService
from aion_brain.resilience.fault_injection import FaultInjectionService
from aion_brain.resilience.repository import ResilienceRepository
from aion_brain.resilience.retry_policies import RetryPolicyService
from aion_brain.resilience.test_runner import ResilienceTestRunner
from aion_brain.resource_registry import (
    BacklinkService,
    ReferenceValidator,
    RegistryQueryService,
    RegistryRebuilder,
    RegistrySnapshotService,
    ResourceDescriptorFactory,
    ResourceLinkService,
    ResourceRegistryRepository,
    ResourceRegistryService,
    ResourceScanner,
)
from aion_brain.responses.composer import ResponseComposer
from aion_brain.responses.delivery import ResponseDeliveryService
from aion_brain.responses.feedback import DialogueFeedbackService
from aion_brain.responses.verifier import ResponseVerifier
from aion_brain.retrieval.router import RetrievalRouter
from aion_brain.risk.engine import RiskEngine
from aion_brain.risk.repository import RiskRepository
from aion_brain.run_supervision.compensation import CompensationPlanner
from aion_brain.run_supervision.control import RunControlService
from aion_brain.run_supervision.query import RunSupervisionQueryService
from aion_brain.run_supervision.reports import RunSupervisionReportService
from aion_brain.run_supervision.repository import RunSupervisionRepository
from aion_brain.run_supervision.service import RunSupervisionService
from aion_brain.run_supervision.status_sampler import RunStatusSampler
from aion_brain.run_supervision.targets import RunTargetStatusAdapter
from aion_brain.run_supervision.timeouts import TimeoutPolicyService
from aion_brain.runtime.langgraph_runtime import LangGraphRuntimeAdapter
from aion_brain.runtime_config.feature_flags import FeatureFlagOverrideService
from aion_brain.runtime_config.profiles import ConfigProfileService
from aion_brain.runtime_config.repository import RuntimeConfigRepository
from aion_brain.runtime_config.snapshots import ConfigSnapshotService
from aion_brain.runtime_config.status import RuntimeConfigStatusService
from aion_brain.runtime_config.validator import ConfigValidator
from aion_brain.sandbox.docker_adapter import DockerSandboxAdapter
from aion_brain.sandbox.firecracker_adapter import FirecrackerSandboxAdapter
from aion_brain.sandbox.local_noop_adapter import LocalNoopSandboxAdapter
from aion_brain.sandbox.repository import SandboxRepository
from aion_brain.sandbox.service import SandboxService
from aion_brain.sandbox.validator import SandboxValidator
from aion_brain.scenarios.comparator import ScenarioComparator
from aion_brain.scenarios.fixtures import DemoFixtureService
from aion_brain.scenarios.repository import ScenarioRepository
from aion_brain.scenarios.runner import ScenarioRunner
from aion_brain.scheduler.due_items import DueItemService
from aion_brain.scheduler.policies import SchedulePolicyService
from aion_brain.scheduler.query import SchedulerQueryService
from aion_brain.scheduler.recurrence import RecurrenceEvaluator
from aion_brain.scheduler.reminders import ReminderService
from aion_brain.scheduler.reports import SchedulerReportService
from aion_brain.scheduler.repository import SchedulerRepository
from aion_brain.scheduler.service import ScheduleService as LocalSchedulerScheduleService
from aion_brain.scheduler.tick import SchedulerTickOrchestrator
from aion_brain.schedules.repository import ScheduleRepository
from aion_brain.schedules.service import ScheduleService
from aion_brain.scopes.repository import ScopeRepository
from aion_brain.scopes.resolver import ScopeResolver
from aion_brain.secrets.repository import SecretRefRepository
from aion_brain.secrets.service import SecretRefService
from aion_brain.security_baseline.adapter_risk import AdapterRiskChecker
from aion_brain.security_baseline.api_exposure import APIExposureChecker
from aion_brain.security_baseline.config_checker import ConfigHardeningChecker
from aion_brain.security_baseline.control_catalog import SecurityControlCatalog
from aion_brain.security_baseline.dependency_metadata import DependencyMetadataScanner
from aion_brain.security_baseline.hardening_gate import HardeningGateService
from aion_brain.security_baseline.repository import SecurityBaselineRepository
from aion_brain.security_baseline.secret_scanner import SecretScanner
from aion_brain.security_baseline.threat_model import ThreatModelService
from aion_brain.self_model.assessment import SelfAssessmentService
from aion_brain.self_model.capability_awareness import CapabilityAwarenessService
from aion_brain.self_model.confidence import ConfidenceCalibrator
from aion_brain.self_model.description import SelfDescriptionService
from aion_brain.self_model.introspection import IntrospectionSnapshotService
from aion_brain.self_model.limitations import LimitationLedgerService
from aion_brain.self_model.profile import SelfModelProfileService
from aion_brain.self_model.repository import SelfModelRepository
from aion_brain.situations.continuity import ContextContinuityService
from aion_brain.situations.normalizer import SituationNormalizer
from aion_brain.situations.projector import SituationProjector
from aion_brain.situations.query import SituationQueryService
from aion_brain.situations.repository import SituationRepository
from aion_brain.situations.service import SituationService
from aion_brain.situations.state_atoms import StateAtomService
from aion_brain.situations.temporal_windows import TemporalStateWindowService
from aion_brain.situations.transitions import StateTransitionDetector
from aion_brain.skills.matcher import SkillMatcher
from aion_brain.skills.repository import SkillRepository
from aion_brain.skills.service import SkillService
from aion_brain.storage.local_store import LocalObjectStore
from aion_brain.tasks.publisher import NoopTaskLifecyclePublisher
from aion_brain.tasks.repository import TaskRepository
from aion_brain.tasks.service import TaskService
from aion_brain.telemetry.visual import VisualTelemetryBuilder
from aion_brain.versioning.artifacts import ReleaseArtifactService
from aion_brain.versioning.compatibility import (
    CompatibilityMatrixService,
    SDKCompatibilityService,
)
from aion_brain.versioning.features import FeatureRegistryService
from aion_brain.versioning.manifest import VersionManifestService
from aion_brain.versioning.migrations import MigrationBaselineService
from aion_brain.versioning.repository import VersioningRepository
from aion_brain.visual.map_builder import BrainMapBuilder
from aion_brain.visual.repository import VisualRepository
from aion_brain.visual.service import VisualProjectionService, VisualTelemetryQueryService
from aion_brain.workflows.local_engine import LocalWorkflowEngine
from aion_brain.workflows.local_worker import LocalWorkflowWorker
from aion_brain.workflows.repository import WorkflowRepository
from aion_brain.workflows.scheduler import LocalScheduler
from aion_brain.workflows.service import WorkflowService
from aion_brain.workflows.temporal_adapter import TemporalAdapter
from aion_brain.workflows.temporal_compat import TemporalCompat
from aion_brain.working_memory.repository import WorkingMemoryRepository
from aion_brain.working_memory.service import WorkingMemoryService

T = TypeVar("T")
_PLACEHOLDER_ADAPTERS = {
    "litellm",
    "langfuse",
    "minio",
    "temporal",
    "http",
}


def _resolve_repo_root(settings: Settings) -> Path:
    configured = str(settings.repo_root or "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    return Path(__file__).parents[5].resolve()


class KernelContainer:
    """Central composition root that owns the assembled Brain service graph."""

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        kernel_repository: KernelRepository | None = None,
        policy_adapter: PolicyAdapter | None = None,
        telemetry_service: object | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        configure_logging(self.settings)
        self.started_at = datetime.now(UTC)
        self.root_dir = _resolve_repo_root(self.settings)
        self.adapter_config = self._adapter_config()
        self.dev_bootstrap = build_dev_bootstrap(self.settings)
        self._reject_placeholder_selection()
        self.kernel_repository = kernel_repository or KernelRepository(self.settings.database_url)
        self.policy_adapter = policy_adapter or OPAAdapter(self.settings.opa_url)

        self.audit_repository = AuditRepository(self.settings.database_url)
        self.telemetry_service = telemetry_service or self.audit_repository
        self.audit_integrity_repository = AuditIntegrityRepository(self.settings.database_url)
        self.audit_checkpoint_service = AuditCheckpointService(self.audit_integrity_repository)
        self.audit_integrity_ledger = AuditIntegrityLedger(
            self.audit_integrity_repository,
            self.policy_adapter,
            self.telemetry_service,
            self.settings,
        )
        self.audit_integrity_ledger.set_checkpoint_service(self.audit_checkpoint_service)
        set_audit_sink = getattr(self.policy_adapter, "set_audit_sink", None)
        if callable(set_audit_sink):
            set_audit_sink(self.audit_integrity_ledger)
        self.audit_verifier = AuditVerifier(
            self.audit_integrity_repository,
            telemetry_service=self.telemetry_service,
        )
        self.provenance_service = ProvenanceService(
            self.audit_integrity_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
            audit_sink=self.audit_integrity_ledger,
        )
        self.policy_catalog_repository = PolicyCatalogRepository(self.settings.database_url)
        policy_file = self.root_dir / "infra/opa/policies/brain.rego"
        self.policy_catalog_service = PolicyCatalogService(
            repository=self.policy_catalog_repository,
            policy_adapter=self.policy_adapter,
            telemetry_service=self.telemetry_service,
        )
        self.permission_matrix_service = PermissionMatrixService(
            repository=self.policy_catalog_repository,
            policy_adapter=self.policy_adapter,
            telemetry_service=self.telemetry_service,
        )
        self.policy_simulation_service = PolicySimulationService(
            repository=self.policy_catalog_repository,
            policy_adapter=self.policy_adapter,
            telemetry_service=self.telemetry_service,
        )
        self.policy_test_harness = PolicyTestHarness(
            repository=self.policy_catalog_repository,
            simulation_service=self.policy_simulation_service,
            policy_adapter=self.policy_adapter,
            telemetry_service=self.telemetry_service,
        )
        self.policy_coverage_analyzer = PolicyCoverageAnalyzer(
            repository=self.policy_catalog_repository,
            policy_adapter=self.policy_adapter,
            telemetry_service=self.telemetry_service,
            policy_files=[policy_file],
        )
        self.policy_bundle_service = PolicyBundleService(
            repository=self.policy_catalog_repository,
            policy_adapter=self.policy_adapter,
            telemetry_service=self.telemetry_service,
            version=self.settings.version,
            rego_policy_path=policy_file,
        )
        self.visual_repository = VisualRepository(self.settings.database_url)
        self.observability_repository = ObservabilityRepository(self.settings.database_url)
        self.observability_service = LocalObservabilityRecorder(
            self.observability_repository,
            self.visual_repository,
        )
        self.instruction_repository = InstructionRepository(self.settings.database_url)
        self.instruction_query_service = InstructionQueryService(self.instruction_repository)
        self.instruction_service = InstructionService(
            self.instruction_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
            audit_sink=self.audit_integrity_ledger,
            settings=self.settings,
        )
        self.preference_service = PreferenceService(
            self.instruction_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
        )
        self.constraint_service = ConstraintService(
            self.instruction_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
        )
        self.style_profile_service = StyleProfileService(
            self.instruction_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
        )
        self.instruction_conflict_detector = InstructionConflictDetector(
            self.instruction_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
        )
        self.instruction_service.set_conflict_detector(self.instruction_conflict_detector)
        self.instruction_resolver = InstructionResolver(
            self.instruction_repository,
            self.policy_adapter,
            conflict_detector=self.instruction_conflict_detector,
            style_service=self.style_profile_service,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
        )
        self.preference_learning_service = PreferenceLearningService(
            self.instruction_repository,
            self.policy_adapter,
            preference_service=self.preference_service,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
        )
        self.api_request_audit_service = APIRequestAuditService(self.settings.database_url)
        self.openapi_hygiene_checker = OpenAPIHygieneChecker()
        self.risk_repository = RiskRepository(self.settings.database_url)
        self.guardrail_repository = GuardrailRepository(self.settings.database_url)
        self.approval_repository = ApprovalRepository(self.settings.database_url)
        self.risk_engine = RiskEngine(
            repository=self.risk_repository,
            policy_adapter=self.policy_adapter,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
            audit_sink=self.audit_integrity_ledger,
        )
        self.guardrail_engine = GuardrailEngine(
            repository=self.guardrail_repository,
            policy_adapter=self.policy_adapter,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
        )
        self.approval_service = ApprovalService(
            repository=self.approval_repository,
            risk_engine=self.risk_engine,
            guardrail_engine=self.guardrail_engine,
            policy_adapter=self.policy_adapter,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
            audit_sink=self.audit_integrity_ledger,
        )
        self.autonomy_repository = AutonomyRepository(self.settings.database_url)
        self.delegation_service = DelegationService(
            self.autonomy_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
        )
        self.run_level_service = RunLevelService(
            self.autonomy_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
        )
        self.autonomy_governor = AutonomyGovernor(
            self.autonomy_repository,
            self.policy_adapter,
            delegation_service=self.delegation_service,
            run_level_service=self.run_level_service,
            risk_engine=self.risk_engine,
            approval_service=self.approval_service,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
        )
        self.audit_exporter = AuditExporter(
            self.audit_integrity_repository,
            self.policy_adapter,
            autonomy_governor=self.autonomy_governor,
            telemetry_service=self.telemetry_service,
            audit_sink=self.audit_integrity_ledger,
        )
        self.memory_governance_repository = MemoryGovernanceRepository(self.settings.database_url)
        self.memory_governance_engine = MemoryGovernanceEngine(
            governance_repository=self.memory_governance_repository,
            risk_engine=self.risk_engine,
            approval_service=self.approval_service,
            policy_adapter=self.policy_adapter,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
        )

        self.capability_registry = CapabilityRegistry()
        self.capability_service = CapabilityService(self.capability_registry)
        self.event_repository = EventRepository(self.settings.database_url)
        self.event_repository.set_audit_sink(self.audit_integrity_ledger)
        self.identity_repository = IdentityRepository(self.settings.database_url)
        self.scope_repository = ScopeRepository(self.settings.database_url)
        self.identity_service = IdentityService(
            repository=self.identity_repository,
            policy_adapter=self.policy_adapter,
            telemetry_service=self.telemetry_service,
        )
        self.scope_service = ScopeResolver(
            identity_repository=self.identity_repository,
            scope_repository=self.scope_repository,
            policy_adapter=self.policy_adapter,
            telemetry_service=self.telemetry_service,
        )
        self.object_store = LocalObjectStore(self.settings.local_object_root)
        self.belief_repository = BeliefRepository(self.settings.database_url)
        self.claim_extractor = ClaimExtractor()
        self.belief_service = BeliefService(
            self.belief_repository,
            self.policy_adapter,
            audit_ledger=self.audit_integrity_ledger,
            provenance_service=self.provenance_service,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
        )
        self.belief_contradiction_service = BeliefContradictionService(
            self.belief_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
        )
        self.belief_support_service = BeliefSupportService(
            self.belief_repository,
            self.policy_adapter,
            contradiction_service=self.belief_contradiction_service,
            telemetry_service=self.telemetry_service,
        )
        self.belief_query_service = BeliefQueryService(
            self.belief_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
        )
        self.truth_maintenance_service = TruthMaintenanceService(
            self.belief_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
        )
        self.concept_repository = ConceptRepository(self.settings.database_url)
        self.concept_service = ConceptService(
            self.concept_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
        )
        self.entity_repository = EntityRepository(self.settings.database_url)
        self.entity_service = EntityService(
            self.entity_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
        )
        self.entity_query_service = EntityQueryService(self.entity_service)
        self.entity_alias_service = EntityAliasService(
            self.entity_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
        )
        self.reference_link_service = ReferenceLinkService(
            self.entity_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
            provenance_service=self.provenance_service,
        )
        self.entity_mention_extractor = EntityMentionExtractor()
        self.entity_resolver = EntityResolver(
            self.entity_repository,
            self.policy_adapter,
            mention_extractor=self.entity_mention_extractor,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
        )
        self.entity_merge_service = EntityMergeService(
            self.entity_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
        )
        self.entity_split_service = EntitySplitService(
            self.entity_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
        )
        self.situation_repository = SituationRepository(self.settings.database_url)
        self.situation_service = SituationService(
            self.situation_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
        )
        self.state_atom_service = StateAtomService(
            self.situation_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
        )
        self.situation_normalizer = SituationNormalizer()
        self.state_transition_detector = StateTransitionDetector()
        self.situation_projector = SituationProjector(
            self.situation_repository,
            self.policy_adapter,
            situation_service=self.situation_service,
            state_atom_service=self.state_atom_service,
            normalizer=self.situation_normalizer,
            transition_detector=self.state_transition_detector,
            autonomy_governor=self.autonomy_governor,
            telemetry_service=self.telemetry_service,
        )
        self.temporal_state_window_service = TemporalStateWindowService(
            self.situation_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
        )
        self.context_continuity_service = ContextContinuityService(
            self.situation_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
        )
        self.situation_query_service = SituationQueryService(self.situation_service)
        self.outcome_repository = OutcomeRepository(self.settings.database_url)
        self.expected_effect_service = ExpectedEffectService(
            self.outcome_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
            audit_sink=self.audit_integrity_ledger,
            provenance_service=self.provenance_service,
        )
        self.observed_effect_collector = ObservedEffectCollector(
            self.outcome_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
        )
        self.outcome_service = OutcomeService(
            self.outcome_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
            audit_sink=self.audit_integrity_ledger,
            provenance_service=self.provenance_service,
            settings=self.settings,
        )
        self.effect_verifier = EffectVerifier(
            self.outcome_repository,
            self.policy_adapter,
            observed_effect_collector=self.observed_effect_collector,
            telemetry_service=self.telemetry_service,
            audit_sink=self.audit_integrity_ledger,
            provenance_service=self.provenance_service,
            settings=self.settings,
        )
        self.causal_attribution_service = CausalAttributionService(
            self.outcome_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
            audit_sink=self.audit_integrity_ledger,
            provenance_service=self.provenance_service,
        )
        self.learning_synthesis_repository = LearningSynthesisRepository(self.settings.database_url)
        self.experience_service = ExperienceService(
            self.learning_synthesis_repository,
            self.policy_adapter,
            outcome_repository=self.outcome_repository,
            telemetry_service=self.telemetry_service,
            audit_sink=self.audit_integrity_ledger,
            provenance_service=self.provenance_service,
        )
        self.pattern_miner = PatternMiner(
            self.learning_synthesis_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
            audit_sink=self.audit_integrity_ledger,
        )
        self.lesson_service = LessonService(
            self.learning_synthesis_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
            audit_sink=self.audit_integrity_ledger,
        )
        self.skill_suggestion_service = SkillSuggestionService(
            self.learning_synthesis_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
            audit_sink=self.audit_integrity_ledger,
            settings=self.settings,
        )
        self.regression_suggestion_service = RegressionSuggestionService(
            self.learning_synthesis_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
            audit_sink=self.audit_integrity_ledger,
        )
        self.learning_query_service = LearningQueryService(self.experience_service)
        self.learning_synthesizer = LearningSynthesizer(
            self.learning_synthesis_repository,
            self.policy_adapter,
            experience_service=self.experience_service,
            pattern_miner=self.pattern_miner,
            lesson_service=self.lesson_service,
            skill_suggestion_service=self.skill_suggestion_service,
            regression_suggestion_service=self.regression_suggestion_service,
            outcome_repository=self.outcome_repository,
            autonomy_governor=self.autonomy_governor,
            preference_learning_service=self.preference_learning_service,
            telemetry_service=self.telemetry_service,
            audit_sink=self.audit_integrity_ledger,
            settings=self.settings,
        )
        self.outcome_feedback_service = OutcomeFeedbackService(
            self.outcome_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
            audit_sink=self.audit_integrity_ledger,
            experience_service=self.experience_service,
            learning_synthesizer=self.learning_synthesizer,
        )
        self.outcome_query_service = OutcomeQueryService(self.outcome_service)
        self.self_model_repository = SelfModelRepository(self.settings.database_url)
        self.capability_awareness_service = CapabilityAwarenessService(
            self.self_model_repository,
            self.policy_adapter,
            settings=self.settings,
            telemetry_service=self.telemetry_service,
        )
        self.limitation_ledger_service = LimitationLedgerService(
            self.self_model_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
            audit_sink=self.audit_integrity_ledger,
        )
        self.self_model_profile_service = SelfModelProfileService(
            self.self_model_repository,
            self.policy_adapter,
            capability_awareness_service=self.capability_awareness_service,
            limitation_service=self.limitation_ledger_service,
            settings=self.settings,
            telemetry_service=self.telemetry_service,
        )
        self.self_description_service = SelfDescriptionService(self.self_model_profile_service)
        self.confidence_calibrator = ConfidenceCalibrator(
            self.self_model_repository,
            self.policy_adapter,
            settings=self.settings,
            telemetry_service=self.telemetry_service,
            audit_sink=self.audit_integrity_ledger,
        )
        self.self_assessment_service = SelfAssessmentService(
            self.self_model_repository,
            self.policy_adapter,
            profile_service=self.self_model_profile_service,
            capability_awareness_service=self.capability_awareness_service,
            limitation_service=self.limitation_ledger_service,
            settings=self.settings,
            telemetry_service=self.telemetry_service,
            audit_sink=self.audit_integrity_ledger,
            provenance_service=self.provenance_service,
        )
        self.introspection_snapshot_service = IntrospectionSnapshotService(
            self.self_model_repository,
            self.policy_adapter,
            profile_service=self.self_model_profile_service,
            capability_awareness_service=self.capability_awareness_service,
            limitation_service=self.limitation_ledger_service,
            confidence_calibrator=self.confidence_calibrator,
            settings=self.settings,
            telemetry_service=self.telemetry_service,
        )
        self.decision_repository = DecisionRepository(self.settings.database_url)
        self.decision_frame_service = DecisionFrameService(
            self.decision_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
            audit_sink=self.audit_integrity_ledger,
            provenance_service=self.provenance_service,
        )
        self.decision_option_service = DecisionOptionService(
            self.decision_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
            provenance_service=self.provenance_service,
            expected_effect_service=self.expected_effect_service,
        )
        self.utility_profile_service = UtilityProfileService(
            self.decision_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
        )
        self.tradeoff_matrix_service = TradeoffMatrixService(
            self.decision_repository,
            telemetry_service=self.telemetry_service,
        )
        self.option_evaluator = OptionEvaluator(
            self.decision_repository,
            self.policy_adapter,
            self.utility_profile_service,
            self.tradeoff_matrix_service,
            risk_engine=self.risk_engine,
            autonomy_governor=self.autonomy_governor,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
        )
        self.counterfactual_simulator = CounterfactualSimulator(
            self.decision_repository,
            self.policy_adapter,
            autonomy_governor=self.autonomy_governor,
            state_atom_service=self.state_atom_service,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
            expected_effect_service=self.expected_effect_service,
        )
        self.decision_journal_service = DecisionJournalService(
            self.decision_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
            audit_sink=self.audit_integrity_ledger,
            provenance_service=self.provenance_service,
        )
        self.decision_recommendation_service = DecisionRecommendationService(
            self.decision_repository,
            self.decision_option_service,
            self.option_evaluator,
            self.counterfactual_simulator,
            settings=self.settings,
        )
        self.evidence_repository = EvidenceRepository(self.settings.database_url)
        self.evidence_service = EvidenceService(
            evidence_repository=self.evidence_repository,
            policy_adapter=self.policy_adapter,
            telemetry_service=self.telemetry_service,
            object_store=self.object_store,
            claim_extractor=self.claim_extractor,
            belief_service=self.belief_service,
            entity_resolver=self.entity_resolver,
            settings=self.settings,
        )
        self.memory_repository = MemoryRepository(self.settings.database_url)
        self.memory_service = PostgresMemoryService(
            self.memory_repository,
            self.policy_adapter,
            governance_engine=self.memory_governance_engine,
        )
        self.grounding_repository = GroundingRepository(self.settings.database_url)
        self.grounding_source_service = GroundingSourceService(
            self.grounding_repository,
            self.policy_adapter,
            evidence_service=self.evidence_service,
            belief_service=self.belief_service,
            memory_service=self.memory_service,
            telemetry_service=self.telemetry_service,
            audit_sink=self.audit_integrity_ledger,
        )
        self.citation_service = CitationService(
            self.grounding_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
            audit_sink=self.audit_integrity_ledger,
            provenance_service=self.provenance_service,
        )
        self.statement_splitter = StatementSplitter()
        self.support_checker = SupportChecker()
        self.attention_repository = AttentionRepository(self.settings.database_url)
        self.working_memory_repository = WorkingMemoryRepository(self.settings.database_url)
        self.focus_service = FocusService(
            self.attention_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
        )
        self.working_memory_service = WorkingMemoryService(
            self.working_memory_repository,
            self.policy_adapter,
            settings=self.settings,
            telemetry_service=self.telemetry_service,
        )
        self.attention_controller = AttentionController(
            self.attention_repository,
            self.policy_adapter,
            working_memory_service=self.working_memory_service,
            focus_service=self.focus_service,
            settings=self.settings,
            telemetry_service=self.telemetry_service,
        )
        self.interrupt_router = InterruptRouter(
            self.attention_repository,
            self.policy_adapter,
            settings=self.settings,
            telemetry_service=self.telemetry_service,
        )
        self.context_budgeter = ContextBudgeter(
            self.attention_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
        )
        self.memory_decay_service = MemoryDecayService(
            governance_repository=self.memory_governance_repository,
            memory_service=self.memory_service,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
        )
        self.memory_retention_service = MemoryRetentionService(
            memory_service=self.memory_service,
            governance_engine=self.memory_governance_engine,
            decay_service=self.memory_decay_service,
            policy_adapter=self.policy_adapter,
            telemetry_service=self.telemetry_service,
        )
        self.memory_conflict_service = MemoryConflictService(
            memory_service=self.memory_service,
            governance_repository=self.memory_governance_repository,
            policy_adapter=self.policy_adapter,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
            attention_controller=self.attention_controller,
        )
        self.memory_compaction_service = MemoryCompactionService(
            memory_service=self.memory_service,
            governance_repository=self.memory_governance_repository,
            policy_adapter=self.policy_adapter,
            approval_service=self.approval_service,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
        )
        self.turbovec_repository = TurboVecRepository(self.settings.database_url)
        self.turbovec_semantic_adapter = self._turbovec_adapter()
        self.semantic_adapter_fallback_reason: str | None = None
        self.semantic_memory_adapter = self._semantic_adapter()
        self.semantic_memory_service = SemanticMemoryService(
            adapter=self.semantic_memory_adapter,
            policy_adapter=self.policy_adapter,
            telemetry_repository=self.audit_repository,
            configured_adapter=self.settings.default_semantic_adapter,
            fallback_reason=self.semantic_adapter_fallback_reason,
            turbovec_adapter=self.turbovec_semantic_adapter,
        )
        self.graphiti_repository = GraphitiRepository(self.settings.database_url)
        self.graphiti_graph_adapter = self._graphiti_adapter()
        self.graph_adapter_fallback_reason: str | None = None
        self.graph_memory_adapter = self._graph_adapter()
        self.graph_memory_service = GraphMemoryService(
            adapter=self.graph_memory_adapter,
            policy_adapter=self.policy_adapter,
            configured_adapter=self.settings.default_graph_memory_adapter,
            fallback_reason=self.graph_adapter_fallback_reason,
            graphiti_adapter=self.graphiti_graph_adapter,
        )
        self.retrieval_router = self._retrieval_router()
        self.context_compiler = ContextCompiler(
            policy_adapter=self.policy_adapter,
            memory_service=self.memory_service,
            graph_service=self.graph_memory_service,
            capability_catalog=self.capability_registry,
            retrieval_router=self.retrieval_router,
            belief_query_service=self.belief_query_service,
            attention_controller=self.attention_controller,
            context_budgeter=self.context_budgeter,
            instruction_resolver=self.instruction_resolver,
            settings=self.settings,
        )
        self.reasoning_repository = ReasoningRepository(self.settings.database_url)
        self.model_gateway_repository = ModelGatewayRepository(self.settings.database_url)
        self.prompt_repository = PromptRepository(self.settings.database_url)
        self.model_output_repository = ModelOutputRepository(self.settings.database_url)
        self.unsafe_output_detector = UnsafeOutputDetector()
        self.output_parser = OutputParser(self.unsafe_output_detector)
        self.structured_output_validator = StructuredOutputValidator(
            self.model_output_repository,
            self.unsafe_output_detector,
            telemetry_service=self.telemetry_service,
        )
        self.model_provider_registry = ModelProviderRegistry(
            self.model_gateway_repository,
            self.policy_adapter,
        )
        self.model_profile_registry = ModelProfileRegistry(
            self.model_gateway_repository,
            self.policy_adapter,
        )
        self.model_provider_registry.ensure_defaults()
        self.model_profile_registry.ensure_defaults(
            max_input_tokens=self.settings.model_gateway_max_input_tokens_default,
            max_output_tokens=self.settings.model_gateway_max_output_tokens_default,
        )
        self.prompt_redactor = PromptRedactor(
            block_on_secret=self.settings.prompt_redaction_block_on_secret,
        )
        self.prompt_injection_detector = PromptInjectionDetector()
        self.prompt_sectioner = PromptSectioner()
        self.prompt_template_service = PromptTemplateService(
            self.prompt_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
            audit_sink=self.audit_integrity_ledger,
        )
        self.prompt_fragment_service = PromptFragmentService(
            self.prompt_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
            audit_sink=self.audit_integrity_ledger,
        )
        self.prompt_boundary_checker = PromptBoundaryChecker(
            self.prompt_repository,
            self.policy_adapter,
            detector=self.prompt_injection_detector,
            telemetry_service=self.telemetry_service,
            audit_sink=self.audit_integrity_ledger,
            settings=self.settings,
        )
        self.model_input_manifest_service = ModelInputManifestService(
            self.prompt_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
            audit_sink=self.audit_integrity_ledger,
        )
        self.prompt_compiler = PromptPacketCompiler(
            self.prompt_repository,
            self.policy_adapter,
            sectioner=self.prompt_sectioner,
            boundary_checker=self.prompt_boundary_checker,
            manifest_service=self.model_input_manifest_service,
            telemetry_service=self.telemetry_service,
            audit_sink=self.audit_integrity_ledger,
            provenance_service=self.provenance_service,
            autonomy_governor=self.autonomy_governor,
            settings=self.settings,
        )
        self.prompt_governance_service = PromptGovernanceService(self.prompt_compiler)
        self.prompt_preview_service = PromptPreviewService(
            self.prompt_compiler,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
        )
        self.model_budget_guard = ModelBudgetGuard(
            self.model_gateway_repository,
            default_daily_budget=self.settings.model_gateway_daily_budget_default,
        )
        self.model_usage_ledger = ModelUsageLedger(self.model_gateway_repository)
        self.model_gateway_router = ModelGatewayRouter()
        self.model_gateway_service = ModelGatewayService(
            provider_registry=self.model_provider_registry,
            profile_registry=self.model_profile_registry,
            router=self.model_gateway_router,
            redactor=self.prompt_redactor,
            budget_guard=self.model_budget_guard,
            adapters={
                "deterministic": DeterministicReasoningAdapter(),
                "litellm_http": LiteLLMHTTPAdapter(
                    base_url=self.settings.litellm_base_url,
                    timeout_seconds=self.settings.model_gateway_timeout_seconds,
                ),
                "openai_compatible_http": OpenAICompatibleHTTPAdapter(
                    base_url=self.settings.openai_compatible_base_url,
                    auth_token=None,
                    timeout_seconds=self.settings.model_gateway_timeout_seconds,
                ),
            },
            policy_adapter=self.policy_adapter,
            repository=self.model_gateway_repository,
            telemetry_service=self.telemetry_service,
            observability_service=self.observability_service,
            model_gateway_enabled=self.settings.model_gateway_enabled,
            approval_service=self.approval_service,
            autonomy_governor=self.autonomy_governor,
            audit_sink=self.audit_integrity_ledger,
            prompt_governance_service=self.prompt_governance_service,
        )
        self.reasoning_mesh = ReasoningMesh(
            model_router=ModelRouter(),
            prompt_builder=PromptBuilder(),
            model_gateway_adapter=DeterministicReasoningAdapter(),
            model_gateway_service=self.model_gateway_service,
            policy_adapter=self.policy_adapter,
            reasoning_repository=self.reasoning_repository,
            telemetry_service=self.telemetry_service,
        )
        self.planner = Planner(
            decision_frame_service=self.decision_frame_service,
            expected_effect_service=self.expected_effect_service,
        )
        self.module_runtime_repository = ModuleRuntimeRepository(self.settings.database_url)
        self.mcp_repository = MCPRepository(self.settings.database_url)
        self.sandbox_repository = SandboxRepository(self.settings.database_url)
        self.secret_ref_repository = SecretRefRepository(self.settings.database_url)
        self.connector_repository = ConnectorRepository(self.settings.database_url)
        self.sandbox_validator = SandboxValidator(self.settings)
        self.local_noop_sandbox_adapter = LocalNoopSandboxAdapter(self.settings)
        self.docker_sandbox_adapter = DockerSandboxAdapter()
        self.firecracker_sandbox_adapter = FirecrackerSandboxAdapter()
        self.secret_ref_service = SecretRefService(
            repository=self.secret_ref_repository,
            policy_adapter=self.policy_adapter,
            telemetry_service=self.telemetry_service,
        )
        self.connector_service = ConnectorService(
            repository=self.connector_repository,
            policy_adapter=self.policy_adapter,
            secret_ref_service=self.secret_ref_service,
            telemetry_service=self.telemetry_service,
        )
        self.sandbox_service = SandboxService(
            sandbox_repository=self.sandbox_repository,
            sandbox_validator=self.sandbox_validator,
            risk_engine=self.risk_engine,
            approval_service=self.approval_service,
            autonomy_governor=self.autonomy_governor,
            policy_adapter=self.policy_adapter,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
            adapters={
                "local_noop": self.local_noop_sandbox_adapter,
                "docker": self.docker_sandbox_adapter,
                "firecracker": self.firecracker_sandbox_adapter,
            },
        )
        self.mcp_service = MCPService(
            mcp_repository=self.mcp_repository,
            capability_service=self.capability_service,
            policy_adapter=self.policy_adapter,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
            compat=MCPCompat(),
            approval_service=self.approval_service,
            autonomy_governor=self.autonomy_governor,
            sandbox_service=self.sandbox_service,
        )
        self.mcp_runtime_adapter = MCPRuntimeAdapter(self.mcp_service)
        self.mcp_capability_adapter = MCPAdapter(self.mcp_service)
        self.module_runtime_gateway = CapabilityRuntimeGateway(
            module_runtime_repository=self.module_runtime_repository,
            capability_registry=self.capability_registry,
            policy_adapter=self.policy_adapter,
            telemetry_service=self.telemetry_service,
            runtime_adapters={
                "local_internal": LocalInternalRuntimeAdapter(),
                "local_stub": LocalStubRuntimeAdapter(),
                "mcp": self.mcp_runtime_adapter,
            },
            approval_service=self.approval_service,
            autonomy_governor=self.autonomy_governor,
            sandbox_service=self.sandbox_service,
        )
        self.module_developer_repository = ModuleDeveloperRepository(self.settings.database_url)
        self.module_package_validator = ModulePackageValidator()
        self.module_compatibility_checker = ModuleCompatibilityChecker(self.settings)
        self.module_scaffold_generator = ModuleScaffoldGenerator()
        self.module_contract_test_harness = ModuleContractTestHarness(
            self.module_developer_repository
        )
        self.module_certifier = ModuleCertifier(
            repository=self.module_developer_repository,
            validator=self.module_package_validator,
            capability_service=self.capability_service,
            runtime_gateway=self.module_runtime_gateway,
            policy_adapter=self.policy_adapter,
            autonomy_governor=self.autonomy_governor,
            risk_engine=self.risk_engine,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
            sandbox_service=self.sandbox_service,
            observed_effect_collector=self.observed_effect_collector,
            outcome_service=self.outcome_service,
        )
        self.brain_runtime = LangGraphRuntimeAdapter(
            intent_engine=IntentEngine(),
            context_compiler=self.context_compiler,
            planner=self.planner,
            policy_adapter=self.policy_adapter,
            reasoning_mesh=self.reasoning_mesh,
        )
        self.execution_repository = ExecutionRepository(self.settings.database_url)
        self.execution_orchestrator = ExecutionOrchestrator(
            policy_adapter=self.policy_adapter,
            capability_invoker=CapabilityInvoker(
                capability_registry=self.capability_registry,
                policy_adapter=self.policy_adapter,
                execution_repository=self.execution_repository,
                telemetry_service=self.telemetry_service,
                runtime_gateway=self.module_runtime_gateway,
            ),
            execution_repository=self.execution_repository,
            telemetry_service=self.telemetry_service,
            approval_service=self.approval_service,
            autonomy_governor=self.autonomy_governor,
        )
        lifecycle_publisher = NoopTaskLifecyclePublisher()
        self.goal_repository = GoalRepository(self.settings.database_url)
        self.goal_service = GoalService(
            repository=self.goal_repository,
            policy_adapter=self.policy_adapter,
            publisher=lifecycle_publisher,
            telemetry_service=self.telemetry_service,
        )
        self.task_repository = TaskRepository(self.settings.database_url)
        self.task_service = TaskService(
            repository=self.task_repository,
            policy_adapter=self.policy_adapter,
            publisher=lifecycle_publisher,
            telemetry_service=self.telemetry_service,
        )
        self.schedule_repository = ScheduleRepository(self.settings.database_url)
        self.schedule_service = ScheduleService(
            repository=self.schedule_repository,
            policy_adapter=self.policy_adapter,
            publisher=lifecycle_publisher,
            telemetry_service=self.telemetry_service,
        )
        self.workflow_repository = WorkflowRepository(self.settings.database_url)
        self.temporal_adapter = TemporalAdapter(
            enabled=self.settings.temporal_enabled,
            endpoint_ref=self.settings.temporal_endpoint_ref,
            namespace=self.settings.temporal_namespace,
            task_queue=self.settings.temporal_task_queue,
            compat=TemporalCompat(),
        )
        temporal_status = self.temporal_adapter.temporal_status()
        self.local_workflow_engine = LocalWorkflowEngine(
            repository=self.workflow_repository,
            policy_adapter=self.policy_adapter,
            telemetry_service=self.telemetry_service,
            execution_orchestrator=self.execution_orchestrator,
            task_runner=None,
            capability_runtime_gateway=self.module_runtime_gateway,
            temporal_available=temporal_status.package_available,
            temporal_enabled=self.settings.temporal_enabled,
            local_worker_enabled=self.settings.workflow_local_worker_enabled,
            approval_service=self.approval_service,
            autonomy_governor=self.autonomy_governor,
            observed_effect_collector=self.observed_effect_collector,
            outcome_service=self.outcome_service,
            settings=self.settings,
        )
        self.workflow_service = WorkflowService(
            local_engine=self.local_workflow_engine,
            temporal_adapter=self.temporal_adapter,
            workflow_engine_adapter=self.settings.workflow_engine_adapter,
            temporal_enabled=self.settings.temporal_enabled,
        )
        self.workflow_scheduler = LocalScheduler(
            schedule_service=self.schedule_service,
            schedule_repository=self.schedule_repository,
            workflow_service=self.workflow_service,
            enabled=self.settings.workflow_scheduler_enabled,
            telemetry_service=self.telemetry_service,
            autonomy_governor=self.autonomy_governor,
        )
        self.workflow_worker = LocalWorkflowWorker(
            repository=self.workflow_repository,
            engine=self.local_workflow_engine,
            enabled=self.settings.workflow_local_worker_enabled,
            max_runs_per_tick=self.settings.workflow_local_worker_max_runs_per_tick,
            policy_adapter=self.policy_adapter,
            telemetry_service=self.telemetry_service,
            autonomy_governor=self.autonomy_governor,
        )
        self.reflection_repository = ReflectionRepository(self.settings.database_url)
        self.reflection_service = ReflectionEngine(
            reflection_repository=self.reflection_repository,
            learning_engine=LearningEngine(),
            policy_adapter=self.policy_adapter,
            telemetry_service=self.telemetry_service,
        )
        self.skill_repository = SkillRepository(self.settings.database_url)
        self.skill_service = SkillService(
            skill_repository=self.skill_repository,
            reflection_repository=self.reflection_repository,
            policy_adapter=self.policy_adapter,
            telemetry_service=self.telemetry_service,
            matcher=SkillMatcher(self.skill_repository),
            approval_service=self.approval_service,
            autonomy_governor=self.autonomy_governor,
        )
        self.memory_forgetting_service = MemoryForgettingService(
            memory_service=self.memory_service,
            semantic_memory_service=self.semantic_memory_service,
            graph_memory_service=self.graph_memory_service,
            evidence_service=self.evidence_service,
            skill_service=self.skill_service,
            trace_repository=self.audit_repository,
            risk_engine=self.risk_engine,
            approval_service=self.approval_service,
            policy_adapter=self.policy_adapter,
            governance_repository=self.memory_governance_repository,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
            autonomy_governor=self.autonomy_governor,
        )
        self.brain_loop_service = BrainLoopService(
            runtime=self.brain_runtime,
            audit_ledger=AuditLedger(self.audit_repository),
            evaluator=Evaluator(),
            learning_engine=LearningEngine(),
            telemetry_builder=VisualTelemetryBuilder(),
            goal_service=self.goal_service,
            task_service=self.task_service,
            reflection_engine=self.reflection_service,
            skill_service=self.skill_service,
            observability_adapter=self.observability_service,
            focus_service=self.focus_service,
            attention_controller=self.attention_controller,
            working_memory_service=self.working_memory_service,
            autonomy_governor=self.autonomy_governor,
        )
        self.dialogue_repository = DialogueRepository(self.settings.database_url)
        self.dialogue_session_service = DialogueSessionService(
            self.dialogue_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
            focus_service=self.focus_service,
        )
        self.dialogue_message_service = DialogueMessageService(
            self.dialogue_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
        )
        self.clarification_manager = ClarificationManager(
            self.dialogue_repository,
            self.dialogue_message_service,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
        )
        self.response_composer = ResponseComposer(
            self.dialogue_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
            confidence_calibrator=self.confidence_calibrator,
            prompt_compiler=self.prompt_governance_service,
        )
        self.response_verifier = ResponseVerifier(
            self.dialogue_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
            belief_service=self.belief_service,
            entity_service=self.entity_service,
            situation_service=self.situation_service,
            state_atom_service=self.state_atom_service,
            capability_awareness_service=self.capability_awareness_service,
        )
        self.response_delivery_service = ResponseDeliveryService(
            self.dialogue_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
        )
        self.citation_mapper = CitationMapper(
            self.grounding_repository,
            self.policy_adapter,
            citation_service=self.citation_service,
            source_service=self.grounding_source_service,
            response_service=self.response_composer,
            splitter=self.statement_splitter,
            support_checker=self.support_checker,
            telemetry_service=self.telemetry_service,
            audit_sink=self.audit_integrity_ledger,
            provenance_service=self.provenance_service,
            settings=self.settings,
        )
        self.source_coverage_service = SourceCoverageService(
            self.grounding_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
            audit_sink=self.audit_integrity_ledger,
        )
        self.grounding_verifier = GroundingVerifier(
            self.grounding_repository,
            self.policy_adapter,
            citation_mapper=self.citation_mapper,
            coverage_service=self.source_coverage_service,
            source_service=self.grounding_source_service,
            telemetry_service=self.telemetry_service,
            audit_sink=self.audit_integrity_ledger,
            provenance_service=self.provenance_service,
            settings=self.settings,
        )
        self.grounding_query_service = GroundingQueryService(
            self.grounding_repository,
            self.policy_adapter,
        )
        set_grounding_services = getattr(self.response_composer, "set_grounding_services", None)
        if callable(set_grounding_services):
            set_grounding_services(self.citation_mapper, self.grounding_verifier)
        set_response_prompt_compiler = getattr(self.response_composer, "set_prompt_compiler", None)
        if callable(set_response_prompt_compiler):
            set_response_prompt_compiler(self.prompt_governance_service)
        set_response_grounding = getattr(self.response_verifier, "set_grounding_verifier", None)
        if callable(set_response_grounding):
            set_response_grounding(self.grounding_verifier)
        self.response_candidate_service = ResponseCandidateService(
            self.model_output_repository,
            self.policy_adapter,
            response_repository=self.dialogue_repository,
            response_verifier=self.response_verifier,
            grounding_verifier=self.grounding_verifier,
            telemetry_service=self.telemetry_service,
        )
        self.tool_intent_capture_service = ToolIntentCaptureService(
            self.model_output_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
        )
        self.model_output_query_service = ModelOutputQueryService(
            self.model_output_repository,
            self.policy_adapter,
        )
        self.output_governance_service = OutputGovernanceService(
            self.model_output_repository,
            self.policy_adapter,
            parser=self.output_parser,
            unsafe_detector=self.unsafe_output_detector,
            structured_validator=self.structured_output_validator,
            response_candidate_service=self.response_candidate_service,
            tool_intent_service=self.tool_intent_capture_service,
            telemetry_service=self.telemetry_service,
            audit_sink=self.audit_integrity_ledger,
            provenance_service=self.provenance_service,
            settings=self.settings,
        )
        set_output_governance = getattr(
            self.model_gateway_service, "set_output_governance_service", None
        )
        if callable(set_output_governance):
            set_output_governance(self.output_governance_service)
        self.explanation_repository = ExplanationRepository(self.settings.database_url)
        self.explanation_verifier = ExplanationVerifier(self.telemetry_service)
        self.explanation_builder = ExplanationBuilder(
            self.explanation_repository,
            self.policy_adapter,
            audit_ledger=self.audit_integrity_ledger,
            provenance_service=self.provenance_service,
            policy_service=self.audit_repository,
            risk_service=self.risk_engine,
            approval_service=self.approval_service,
            autonomy_service=self.autonomy_governor,
            evidence_service=self.evidence_service,
            memory_service=self.memory_service,
            belief_service=self.belief_service,
            decision_service=self.decision_repository,
            outcome_service=self.outcome_service,
            response_service=self.response_composer,
            self_model_service=self.capability_awareness_service,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
            verifier=self.explanation_verifier,
            citation_mapper=self.citation_mapper,
            grounding_verifier=self.grounding_verifier,
        )
        self.why_not_service = WhyNotService(
            self.explanation_repository,
            self.policy_adapter,
            policy_service=self.audit_repository,
            autonomy_service=self.autonomy_governor,
            approval_service=self.approval_service,
            risk_service=self.risk_engine,
            capability_awareness_service=self.capability_awareness_service,
            limitation_service=self.limitation_ledger_service,
            response_service=self.response_composer,
            outcome_service=self.outcome_service,
            telemetry_service=self.telemetry_service,
            audit_ledger=self.audit_integrity_ledger,
            settings=self.settings,
        )
        self.trace_narrative_builder = TraceNarrativeBuilder(
            self.explanation_repository,
            self.policy_adapter,
            audit_ledger=self.audit_integrity_ledger,
            provenance_service=self.provenance_service,
            event_repository=self.event_repository,
            command_service=None,
            policy_service=self.audit_repository,
            approval_service=self.approval_service,
            decision_service=self.decision_repository,
            outcome_service=self.outcome_service,
            response_service=self.response_composer,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
        )
        self.explanation_feedback_service = ExplanationFeedbackService(
            self.explanation_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
            audit_ledger=self.audit_integrity_ledger,
            settings=self.settings,
        )
        set_explanation_builder = getattr(self.response_composer, "set_explanation_builder", None)
        if callable(set_explanation_builder):
            set_explanation_builder(self.explanation_builder)
        set_explanation_services = getattr(self.response_verifier, "set_explanation_services", None)
        if callable(set_explanation_services):
            set_explanation_services(self.explanation_verifier, self.explanation_builder)
        self.dialogue_feedback_service = DialogueFeedbackService(
            self.dialogue_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
        )
        self.dialogue_memory_handoff_service = DialogueMemoryHandoffService(
            self.dialogue_repository,
            self.policy_adapter,
            self.memory_service,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
        )
        self.dialogue_turn_service = DialogueTurnService(
            session_service=self.dialogue_session_service,
            message_service=self.dialogue_message_service,
            clarification_manager=self.clarification_manager,
            response_composer=self.response_composer,
            response_verifier=self.response_verifier,
            response_delivery=self.response_delivery_service,
            brain_loop=self.brain_loop_service,
            attention_controller=self.attention_controller,
            working_memory_service=self.working_memory_service,
            memory_handoff_service=self.dialogue_memory_handoff_service,
            policy_adapter=self.policy_adapter,
            autonomy_governor=self.autonomy_governor,
            audit_ledger=self.audit_integrity_ledger,
            provenance_service=self.provenance_service,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
            claim_extractor=self.claim_extractor,
            belief_service=self.belief_service,
            entity_resolver=self.entity_resolver,
            context_continuity_service=self.context_continuity_service,
            self_description_service=self.self_description_service,
            explanation_builder=self.explanation_builder,
            why_not_service=self.why_not_service,
            instruction_resolver=self.instruction_resolver,
            preference_learning_service=self.preference_learning_service,
        )
        set_response_composer = getattr(self.brain_loop_service, "set_response_composer", None)
        if callable(set_response_composer):
            set_response_composer(self.response_composer)
        self.visual_projection_service = VisualProjectionService(
            BrainMapBuilder(self.visual_repository, self.settings),
            self.visual_repository,
            self.policy_adapter,
        )
        self.visual_telemetry_query_service = VisualTelemetryQueryService(
            self.visual_repository,
            self.policy_adapter,
        )

        self.replay_repository = ReplayRepository(self.settings.database_url)
        self.snapshot_service = SnapshotService(
            self.replay_repository,
            self.policy_adapter,
            self.telemetry_service,
            trace_repository=self.audit_repository,
            event_repository=self.event_repository,
        )
        self.replay_comparator = TraceComparator()
        self.replay_service = ReplayService(
            self.replay_repository,
            self.snapshot_service,
            self.audit_repository,
            self.event_repository,
            self.brain_loop_service,
            self.replay_comparator,
            self.policy_adapter,
            self.telemetry_service,
            self.observability_service,
        )
        self.regression_service = RegressionService(
            RegressionRepository(self.settings.database_url),
            self.replay_service,
            self.snapshot_service,
            self.policy_adapter,
            self.telemetry_service,
            RegressionReportBuilder(),
        )

        self.service_registry = KernelServiceRegistry(
            self.kernel_repository,
            self.telemetry_service,
        )
        self.diagnostics = KernelDiagnostics(self)
        self.boot_service = KernelBootService(
            container=self,
            repository=self.kernel_repository,
            registry=self.service_registry,
            diagnostics=self.diagnostics,
            telemetry_service=self.telemetry_service,
        )
        self.self_test_service = KernelSelfTestService(
            repository=self.kernel_repository,
            policy_adapter=self.policy_adapter,
            diagnostics=self.diagnostics,
            registry=self.service_registry,
            telemetry_service=self.telemetry_service,
        )
        self.cognitive_cycle_repository = CognitiveCycleRepository(self.settings.database_url)
        self.maintenance_service = MaintenanceService(
            attention_controller=self.attention_controller,
            focus_service=self.focus_service,
            working_memory_service=self.working_memory_service,
            memory_decay_service=self.memory_decay_service,
            memory_conflict_service=self.memory_conflict_service,
            memory_compaction_service=self.memory_compaction_service,
            reflection_engine=self.reflection_service,
            regression_service=self.regression_service,
            replay_service=self.replay_service,
            visual_service=self.visual_projection_service,
            observability_service=self.observability_service,
            approval_service=self.approval_service,
            workflow_worker=self.workflow_worker,
            kernel_self_test_service=self.self_test_service,
            settings=self.settings,
        )
        self.sleep_consolidation_service = SleepConsolidationService(
            working_memory_service=self.working_memory_service,
            memory_decay_service=self.memory_decay_service,
            memory_conflict_service=self.memory_conflict_service,
            memory_compaction_service=self.memory_compaction_service,
            reflection_engine=self.reflection_service,
            skill_service=self.skill_service,
            regression_service=self.regression_service,
            replay_service=self.replay_service,
            visual_service=self.visual_projection_service,
            observability_service=self.observability_service,
            situation_projector=self.situation_projector,
            telemetry_service=self.telemetry_service,
            cycle_repository=self.cognitive_cycle_repository,
            settings=self.settings,
        )
        self.cognitive_cycle_orchestrator = CognitiveCycleOrchestrator(
            cycle_repository=self.cognitive_cycle_repository,
            autonomy_governor=self.autonomy_governor,
            risk_engine=self.risk_engine,
            approval_service=self.approval_service,
            policy_adapter=self.policy_adapter,
            telemetry_service=self.telemetry_service,
            sleep_consolidation_service=self.sleep_consolidation_service,
            maintenance_service=self.maintenance_service,
            settings=self.settings,
        )
        self.event_reaction_repository = EventReactionRepository(self.settings.database_url)
        self.event_trigger_matcher = EventTriggerMatcher()
        self.event_reaction_action_runner = EventReactionActionRunner(
            attention_controller=self.attention_controller,
            interrupt_router=self.interrupt_router,
            task_service=self.task_service,
            workflow_service=self.workflow_service,
            cognitive_cycle_orchestrator=self.cognitive_cycle_orchestrator,
            memory_governance_engine=self.memory_governance_engine,
            memory_conflict_service=self.memory_conflict_service,
            capability_runtime_gateway=self.module_runtime_gateway,
            trace_service=self.audit_repository,
        )
        self.event_dead_letter_service = EventDeadLetterService(
            repository=self.event_reaction_repository,
            event_repository=self.event_repository,
            policy_adapter=self.policy_adapter,
            settings=self.settings,
            telemetry_service=self.telemetry_service,
        )
        self.event_reaction_router = EventReactionRouter(
            repository=self.event_reaction_repository,
            event_repository=self.event_repository,
            matcher=self.event_trigger_matcher,
            action_runner=self.event_reaction_action_runner,
            dead_letter_service=self.event_dead_letter_service,
            policy_adapter=self.policy_adapter,
            settings=self.settings,
            autonomy_governor=self.autonomy_governor,
            risk_engine=self.risk_engine,
            approval_service=self.approval_service,
            telemetry_service=self.telemetry_service,
        )
        self.event_dead_letter_service.set_router(self.event_reaction_router)
        self.event_reaction_replay_service = EventReactionReplayService(
            self.event_dead_letter_service
        )
        self.command_repository = CommandRepository(self.settings.database_url)
        self.idempotency_repository = IdempotencyRepository(self.settings.database_url)
        self.outbox_repository = OutboxRepository(self.settings.database_url)
        self.inbox_repository = InboxRepository(self.settings.database_url)
        self.consistency_repository = ConsistencyRepository(self.settings.database_url)
        self.idempotency_service = IdempotencyService(
            self.idempotency_repository,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
        )
        self.outbox_service = OutboxService(
            self.outbox_repository,
            settings=self.settings,
            telemetry_service=self.telemetry_service,
        )
        self.event_reaction_action_runner.set_outbox_service(self.outbox_service)
        self.inbox_service = InboxService(
            self.inbox_repository,
            telemetry_service=self.telemetry_service,
        )
        self.processing_lease_service = ProcessingLeaseService(
            self.consistency_repository,
            settings=self.settings,
            telemetry_service=self.telemetry_service,
        )
        self.command_handler_registry = CommandHandlerRegistry(
            brain_loop_service=self.brain_loop_service,
            event_reaction_router=self.event_reaction_router,
            workflow_service=self.workflow_service,
            cognitive_cycle_orchestrator=self.cognitive_cycle_orchestrator,
            memory_governance_engine=self.memory_governance_engine,
            capability_runtime_gateway=self.module_runtime_gateway,
            model_gateway_service=self.model_gateway_service,
        )
        self.command_bus = CommandBus(
            command_repository=self.command_repository,
            command_handlers=self.command_handler_registry,
            idempotency_service=self.idempotency_service,
            policy_adapter=self.policy_adapter,
            autonomy_governor=self.autonomy_governor,
            risk_engine=self.risk_engine,
            approval_service=self.approval_service,
            outbox_service=self.outbox_service,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
            sandbox_service=self.sandbox_service,
            observed_effect_collector=self.observed_effect_collector,
            outcome_service=self.outcome_service,
        )
        self.action_proposal_repository = ActionProposalRepository(self.settings.database_url)
        self.action_blocker_service = ActionBlockerService(
            self.action_proposal_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
        )
        self.action_proposal_service = ActionProposalService(
            self.action_proposal_repository,
            self.policy_adapter,
            blocker_service=self.action_blocker_service,
            tool_intent_repository=self.model_output_repository,
            telemetry_service=self.telemetry_service,
            audit_sink=self.audit_integrity_ledger,
            provenance_service=self.provenance_service,
            settings=self.settings,
        )
        self.tool_intent_review_service = ToolIntentReviewService(
            self.action_proposal_repository,
            self.model_output_repository,
            self.policy_adapter,
            action_proposal_service=self.action_proposal_service,
            blocker_service=self.action_blocker_service,
            telemetry_service=self.telemetry_service,
            audit_sink=self.audit_integrity_ledger,
            provenance_service=self.provenance_service,
            settings=self.settings,
        )
        self.action_review_service = ActionReviewService(
            self.action_proposal_repository,
            self.policy_adapter,
            blocker_service=self.action_blocker_service,
            risk_engine=self.risk_engine,
            autonomy_governor=self.autonomy_governor,
            approval_service=self.approval_service,
            telemetry_service=self.telemetry_service,
            audit_sink=self.audit_integrity_ledger,
            provenance_service=self.provenance_service,
        )
        self.execution_handoff_service = ExecutionHandoffService(
            self.action_proposal_repository,
            self.policy_adapter,
            blocker_service=self.action_blocker_service,
            command_bus=self.command_bus,
            workflow_service=self.workflow_service,
            execution_orchestrator=self.execution_orchestrator,
            capability_runtime=self.module_runtime_gateway,
            mcp_service=self.mcp_service,
            cycle_orchestrator=self.cognitive_cycle_orchestrator,
            sandbox_service=self.sandbox_service,
            risk_engine=self.risk_engine,
            autonomy_governor=self.autonomy_governor,
            approval_service=self.approval_service,
            telemetry_service=self.telemetry_service,
            audit_sink=self.audit_integrity_ledger,
            provenance_service=self.provenance_service,
            settings=self.settings,
        )
        self.action_proposal_query_service = ActionProposalQueryService(
            self.action_proposal_repository,
            self.policy_adapter,
        )
        self.run_supervision_repository = RunSupervisionRepository(self.settings.database_url)
        self.run_target_status_adapter = RunTargetStatusAdapter(
            command_bus=self.command_bus,
            workflow_service=self.workflow_service,
            execution_orchestrator=self.execution_orchestrator,
            capability_runtime=self.module_runtime_gateway,
            mcp_service=self.mcp_service,
            cycle_orchestrator=self.cognitive_cycle_orchestrator,
            sandbox_service=self.sandbox_service,
        )
        self.run_supervision_service = RunSupervisionService(
            self.run_supervision_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
            audit_sink=self.audit_integrity_ledger,
            provenance_service=self.provenance_service,
            settings=self.settings,
        )
        self.run_status_sampler = RunStatusSampler(
            self.run_supervision_repository,
            self.run_target_status_adapter,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
            audit_sink=self.audit_integrity_ledger,
            provenance_service=self.provenance_service,
            settings=self.settings,
        )
        self.timeout_policy_service = TimeoutPolicyService(
            self.run_supervision_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
        )
        self.run_control_service = RunControlService(
            self.run_supervision_repository,
            self.run_target_status_adapter,
            self.policy_adapter,
            approval_service=self.approval_service,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
        )
        self.compensation_planner = CompensationPlanner(
            self.run_supervision_repository,
            self.policy_adapter,
            action_proposal_service=self.action_proposal_service,
            telemetry_service=self.telemetry_service,
            audit_sink=self.audit_integrity_ledger,
            provenance_service=self.provenance_service,
            settings=self.settings,
        )
        self.run_supervision_report_service = RunSupervisionReportService(
            self.run_supervision_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
        )
        self.run_supervision_query_service = RunSupervisionQueryService(
            self.run_supervision_service
        )
        self.notification_repository = NotificationRepository(self.settings.database_url)
        self.alert_service = AlertService(
            self.notification_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
        )
        self.notification_router = NotificationRouter(
            self.notification_repository,
            self.policy_adapter,
            alert_service=self.alert_service,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
        )
        self.notification_topic_service = NotificationTopicService(
            self.notification_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
        )
        self.notification_subscription_service = NotificationSubscriptionService(
            self.notification_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
        )
        self.escalation_service = EscalationService(
            self.notification_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
        )
        self.notification_digest_service = NotificationDigestService(
            self.notification_repository,
            self.policy_adapter,
            notification_router=self.notification_router,
            alert_service=self.alert_service,
            telemetry_service=self.telemetry_service,
        )
        self.notification_query_service = NotificationQueryService(self.notification_router)
        self.incident_repository = IncidentRepository(self.settings.database_url)
        self.incident_signal_service = IncidentSignalService(
            self.incident_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
            audit_sink=self.audit_integrity_ledger,
            provenance_service=self.provenance_service,
        )
        self.alert_service._incident_signal_service = self.incident_signal_service
        self.incident_rule_service = CorrelationRuleService(
            self.incident_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
        )
        self.incident_service = IncidentService(
            self.incident_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
        )
        self.incident_query_service = IncidentQueryService(
            self.incident_repository,
            self.policy_adapter,
        )
        self.incident_correlation_engine = IncidentCorrelationEngine(
            self.incident_repository,
            self.policy_adapter,
            incident_service=self.incident_service,
            autonomy_governor=self.autonomy_governor,
            notification_router=self.notification_router,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
        )
        self.root_cause_candidate_service = RootCauseCandidateService(
            self.incident_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
        )
        self.recovery_review_service = RecoveryReviewService(
            self.incident_repository,
            self.policy_adapter,
            root_cause_service=self.root_cause_candidate_service,
            action_proposal_service=self.action_proposal_service,
            compensation_planner=self.compensation_planner,
            notification_router=self.notification_router,
            telemetry_service=self.telemetry_service,
        )
        self.scheduler_repository = SchedulerRepository(self.settings.database_url)
        self.scheduler_recurrence_evaluator = RecurrenceEvaluator()
        self.scheduler_schedule_service = LocalSchedulerScheduleService(
            self.scheduler_repository,
            self.policy_adapter,
            recurrence_evaluator=self.scheduler_recurrence_evaluator,
            telemetry_service=self.telemetry_service,
            audit_sink=self.audit_integrity_ledger,
            provenance_service=self.provenance_service,
            settings=self.settings,
        )
        self.scheduler_due_item_service = DueItemService(
            self.scheduler_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
        )
        self.scheduler_reminder_service = ReminderService(
            self.scheduler_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
        )
        self.schedule_policy_service = SchedulePolicyService(
            self.scheduler_repository,
            self.policy_adapter,
        )
        self.scheduler_report_service = SchedulerReportService(
            self.scheduler_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
        )
        self.scheduler_query_service = SchedulerQueryService(self.scheduler_repository)
        self.scheduler_tick_orchestrator = SchedulerTickOrchestrator(
            self.scheduler_repository,
            self.policy_adapter,
            due_item_service=self.scheduler_due_item_service,
            reminder_service=self.scheduler_reminder_service,
            recurrence_evaluator=self.scheduler_recurrence_evaluator,
            notification_router=self.notification_router,
            action_proposal_service=self.action_proposal_service,
            operator_repository=None,
            telemetry_service=self.telemetry_service,
            audit_sink=self.audit_integrity_ledger,
            provenance_service=self.provenance_service,
            settings=self.settings,
        )
        for supervised_service in (
            self.execution_handoff_service,
            self.command_bus,
            self.workflow_service,
            self.execution_orchestrator,
            self.module_runtime_gateway,
            self.mcp_service,
            self.sandbox_service,
            self.cognitive_cycle_orchestrator,
            self.outcome_service,
        ):
            set_run_supervision = getattr(
                supervised_service,
                "set_run_supervision_service",
                None,
            )
            if callable(set_run_supervision):
                set_run_supervision(self.run_supervision_service)
        set_tool_intent_review = getattr(
            self.output_governance_service,
            "set_tool_intent_review_service",
            None,
        )
        if callable(set_tool_intent_review):
            set_tool_intent_review(self.tool_intent_review_service)
        set_decision_action_proposals = getattr(
            self.decision_journal_service,
            "set_action_proposal_service",
            None,
        )
        if callable(set_decision_action_proposals):
            set_decision_action_proposals(self.action_proposal_service)
        set_planner_action_proposals = getattr(
            self.planner,
            "set_action_proposal_service",
            None,
        )
        if callable(set_planner_action_proposals):
            set_planner_action_proposals(self.action_proposal_service)
        self.contract_export_service = ContractExportService(self.settings.version)
        self.boundary_checker = ArchitectureBoundaryChecker(Path(__file__).parents[1])
        self.consistency_checker = ConsistencyChecker(
            repository=self.consistency_repository,
            lease_service=self.processing_lease_service,
            command_repository=self.command_repository,
            outbox_service=self.outbox_service,
            inbox_service=self.inbox_service,
            idempotency_service=self.idempotency_service,
            boundary_checker=self.boundary_checker,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
        )
        self.scenario_repository = ScenarioRepository(self.settings.database_url)
        self.scenario_comparator = ScenarioComparator()
        self.scenario_runner = ScenarioRunner(
            repository=self.scenario_repository,
            comparator=self.scenario_comparator,
            policy_adapter=self.policy_adapter,
            autonomy_governor=self.autonomy_governor,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
        )
        self.demo_fixture_service = DemoFixtureService(
            self.scenario_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
        )
        self.performance_repository = PerformanceRepository(self.settings.database_url)
        self.performance_regression_comparator = PerformanceRegressionComparator(
            self.performance_repository,
            telemetry_service=self.telemetry_service,
        )
        self.capacity_baseline_service = CapacityBaselineService(
            self.performance_repository,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
        )
        self.resource_budget_service = ResourceBudgetService(
            self.performance_repository,
            telemetry_service=self.telemetry_service,
        )
        self.performance_summary_service = PerformanceSummaryService(self.performance_repository)
        self.benchmark_runner = BenchmarkRunner(
            self.performance_repository,
            self.policy_adapter,
            autonomy_governor=self.autonomy_governor,
            telemetry_service=self.telemetry_service,
            regression_comparator=self.performance_regression_comparator,
            settings=self.settings,
        )
        root_dir = self.root_dir
        self.versioning_repository = VersioningRepository(self.settings.database_url)
        self.feature_registry_service = FeatureRegistryService(
            self.versioning_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
        )
        self.runtime_config_repository = RuntimeConfigRepository(self.settings.database_url)
        self.config_profile_service = ConfigProfileService(
            self.runtime_config_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
        )
        self.feature_flag_override_service = FeatureFlagOverrideService(
            self.runtime_config_repository,
            self.policy_adapter,
            feature_registry=self.feature_registry_service,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
        )
        self.config_snapshot_service = ConfigSnapshotService(
            self.runtime_config_repository,
            self.policy_adapter,
            feature_override_service=self.feature_flag_override_service,
            settings=self.settings,
            telemetry_service=self.telemetry_service,
        )
        self.config_validator = ConfigValidator(
            self.runtime_config_repository,
            self.policy_adapter,
            feature_override_service=self.feature_flag_override_service,
            settings=self.settings,
            telemetry_service=self.telemetry_service,
        )
        self.runtime_config_status_service = RuntimeConfigStatusService(
            self.runtime_config_repository,
            self.policy_adapter,
            feature_override_service=self.feature_flag_override_service,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
        )
        self.resilience_repository = ResilienceRepository(self.settings.database_url)
        self.dependency_health_service = DependencyHealthService(
            self.resilience_repository,
            settings=self.settings,
            telemetry_service=self.telemetry_service,
        )
        self.retry_policy_service = RetryPolicyService(
            self.resilience_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
        )
        self.circuit_breaker_service = CircuitBreakerService(
            self.resilience_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
        )
        self.fault_injection_service = FaultInjectionService(
            self.resilience_repository,
            self.policy_adapter,
            settings=self.settings,
            telemetry_service=self.telemetry_service,
        )
        self.degraded_mode_service = DegradedModeService(
            self.resilience_repository,
            dependency_health_service=self.dependency_health_service,
            circuit_breaker_service=self.circuit_breaker_service,
            fault_injection_service=self.fault_injection_service,
            telemetry_service=self.telemetry_service,
        )
        self.resilience_test_runner = ResilienceTestRunner(
            self.resilience_repository,
            self.policy_adapter,
            dependency_health_service=self.dependency_health_service,
            retry_policy_service=self.retry_policy_service,
            circuit_breaker_service=self.circuit_breaker_service,
            degraded_mode_service=self.degraded_mode_service,
            fault_injection_service=self.fault_injection_service,
            telemetry_service=self.telemetry_service,
        )
        self.outbox_service.set_retry_policy_service(self.retry_policy_service)
        self.command_bus.set_retry_policy_service(self.retry_policy_service)
        self.model_gateway_service.set_circuit_breaker_service(self.circuit_breaker_service)
        self.semantic_memory_service.set_degraded_mode_service(self.degraded_mode_service)
        self.graph_memory_service.set_degraded_mode_service(self.degraded_mode_service)
        self.security_baseline_repository = SecurityBaselineRepository(self.settings.database_url)
        self.config_hardening_checker = ConfigHardeningChecker(
            self.settings,
            root_dir=root_dir,
            config_validator=self.config_validator,
        )
        self.api_exposure_checker = APIExposureChecker()
        self.adapter_risk_checker = AdapterRiskChecker(self.settings, root_dir=root_dir)
        self.dependency_metadata_scanner = DependencyMetadataScanner(root_dir=root_dir)
        self.secret_scanner = SecretScanner(
            self.security_baseline_repository,
            self.policy_adapter,
            settings=self.settings,
            telemetry_service=self.telemetry_service,
            root_dir=root_dir,
        )
        self.threat_model_service = ThreatModelService(
            self.security_baseline_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
        )
        self.security_control_catalog = SecurityControlCatalog(
            self.security_baseline_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
        )
        self.hardening_gate_service = HardeningGateService(
            self.security_baseline_repository,
            self.policy_adapter,
            secret_scanner=self.secret_scanner,
            config_checker=self.config_hardening_checker,
            api_exposure_checker=self.api_exposure_checker,
            adapter_risk_checker=self.adapter_risk_checker,
            dependency_metadata_scanner=self.dependency_metadata_scanner,
            threat_model_service=self.threat_model_service,
            security_control_catalog=self.security_control_catalog,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
            audit_sink=self.audit_integrity_ledger,
        )
        self.release_baseline_repository = ReleaseBaselineRepository(self.settings.database_url)
        self.release_baseline_service = ReleaseBaselineService(
            scenario_runner=self.scenario_runner,
            repository=self.release_baseline_repository,
            policy_adapter=self.policy_adapter,
            kernel_self_test=self.self_test_service,
            policy_coverage=self.policy_coverage_analyzer,
            openapi_hygiene=self.openapi_hygiene_checker,
            boundary_checker=self.boundary_checker,
            contract_export=self.contract_export_service,
            performance_summary_service=self.performance_summary_service,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
        )
        self.version_manifest_service = VersionManifestService(
            self.versioning_repository,
            self.feature_registry_service,
            self.policy_adapter,
            contract_export_service=self.contract_export_service,
            runtime_config_status_service=self.runtime_config_status_service,
            config_snapshot_service=self.config_snapshot_service,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
        )
        self.compatibility_matrix_service = CompatibilityMatrixService(
            self.versioning_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
        )
        self.migration_baseline_service = MigrationBaselineService(
            self.versioning_repository,
            self.policy_adapter,
            migrations_dir=root_dir / "infra/postgres/migrations",
            telemetry_service=self.telemetry_service,
            settings=self.settings,
        )
        self.release_artifact_service = ReleaseArtifactService(
            self.versioning_repository,
            self.policy_adapter,
            root_dir=root_dir,
            contract_export_service=self.contract_export_service,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
        )
        self.sdk_compatibility_service = SDKCompatibilityService(
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
            root_dir=root_dir,
        )
        self.freeze_gate_service = FreezeGateService(
            self.versioning_repository,
            self.policy_adapter,
            version_manifest_service=self.version_manifest_service,
            feature_registry_service=self.feature_registry_service,
            compatibility_matrix_service=self.compatibility_matrix_service,
            migration_baseline_service=self.migration_baseline_service,
            release_artifact_service=self.release_artifact_service,
            sdk_compatibility_service=self.sdk_compatibility_service,
            release_baseline_service=self.release_baseline_service,
            kernel_self_test=self.self_test_service,
            policy_coverage=self.policy_coverage_analyzer,
            openapi_hygiene=self.openapi_hygiene_checker,
            boundary_checker=self.boundary_checker,
            contract_export_service=self.contract_export_service,
            benchmark_runner=self.benchmark_runner,
            capacity_baseline_service=self.capacity_baseline_service,
            hardening_gate_service=self.hardening_gate_service,
            config_validator=self.config_validator,
            config_snapshot_service=self.config_snapshot_service,
            runtime_config_status_service=self.runtime_config_status_service,
            resilience_test_runner=self.resilience_test_runner,
            audit_integrity_ledger=self.audit_integrity_ledger,
            audit_verifier=self.audit_verifier,
            telemetry_service=self.telemetry_service,
            root_dir=root_dir,
            settings=self.settings,
            audit_sink=self.audit_integrity_ledger,
        )
        self.release_package_repository = ReleasePackageRepository(self.settings.database_url)
        self.release_candidate_repository = ReleaseCandidateRepository(self.settings.database_url)
        self.release_package_source_manifest_service = SourceManifestService(
            max_file_size_mb=self.settings.release_package_max_file_size_mb
        )
        self.release_package_sbom_service = SBOMPlaceholderService(root_dir)
        self.release_package_validator = ReleasePackageValidator(
            max_file_size_mb=self.settings.release_package_max_file_size_mb
        )
        self.release_handoff_service = ReleaseHandoffService()
        self.release_packager = ReleasePackager(
            self.release_package_repository,
            self.policy_adapter,
            version_manifest_service=self.version_manifest_service,
            contract_export_service=self.contract_export_service,
            policy_bundle_service=self.policy_bundle_service,
            migration_baseline_service=self.migration_baseline_service,
            release_baseline_service=self.release_baseline_service,
            freeze_gate_service=self.freeze_gate_service,
            hardening_gate_service=self.hardening_gate_service,
            compatibility_matrix_service=self.compatibility_matrix_service,
            release_artifact_service=self.release_artifact_service,
            source_manifest_service=self.release_package_source_manifest_service,
            sbom_service=self.release_package_sbom_service,
            validator=self.release_package_validator,
            handoff_service=self.release_handoff_service,
            release_candidate_repository=self.release_candidate_repository,
            telemetry_service=self.telemetry_service,
            root_dir=root_dir,
            settings=self.settings,
        )
        self.backup_repository = BackupRepository(self.settings.database_url)
        self.backup_resource_readers = ResourceReaderRegistry()
        self.backup_exporter = BackupExporter(
            self.backup_repository,
            self.backup_resource_readers,
            self.policy_adapter,
            autonomy_governor=self.autonomy_governor,
            risk_engine=self.risk_engine,
            approval_service=self.approval_service,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
            root_dir=root_dir,
            audit_sink=self.audit_integrity_ledger,
        )
        self.restore_preview_service = RestorePreviewService(
            self.backup_repository,
            self.policy_adapter,
            self.backup_resource_readers,
            autonomy_governor=self.autonomy_governor,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
            root_dir=root_dir,
        )
        self.restore_service = RestoreService(
            self.backup_repository,
            self.policy_adapter,
            autonomy_governor=self.autonomy_governor,
            risk_engine=self.risk_engine,
            approval_service=self.approval_service,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
        )
        self.backup_validator = BackupValidator(
            self.backup_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
            root_dir=root_dir,
        )
        self.resource_registry_repository = ResourceRegistryRepository(self.settings.database_url)
        self.resource_descriptor_factory = ResourceDescriptorFactory()
        self.resource_scanner = ResourceScanner(
            self.resource_descriptor_factory,
            notification=self.notification_repository,
            incident=self.incident_repository,
            release_package=self.release_package_repository,
            release_candidate=self.release_candidate_repository,
            backup=self.backup_repository,
            freeze_gate=self.freeze_gate_service,
        )
        self.resource_registry_service = ResourceRegistryService(
            self.resource_registry_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
        )
        self.resource_link_service = ResourceLinkService(
            self.resource_registry_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
        )
        self.backlink_service = BacklinkService(
            self.resource_registry_repository,
            self.policy_adapter,
        )
        self.registry_query_service = RegistryQueryService(
            self.resource_registry_repository,
            self.policy_adapter,
        )
        self.reference_validator = ReferenceValidator(
            self.resource_registry_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
            notification_router=self.notification_router,
            incident_signal_service=self.incident_signal_service,
            settings=self.settings,
        )
        self.registry_snapshot_service = RegistrySnapshotService(
            self.resource_registry_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
        )
        self.registry_rebuilder = RegistryRebuilder(
            self.resource_registry_repository,
            self.policy_adapter,
            scanner=self.resource_scanner,
            registry_service=self.resource_registry_service,
            link_service=self.resource_link_service,
            snapshot_service=self.registry_snapshot_service,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
        )
        self.contract_registry_repository = ContractRegistryRepository(self.settings.database_url)
        self.contract_scanner = ContractScanner(settings=self.settings)
        self.interface_inventory_service = InterfaceInventoryService(
            self.contract_registry_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
        )
        self.contract_snapshot_service = ContractSnapshotService(
            self.contract_registry_repository,
            self.contract_scanner,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
            audit_sink=self.audit_integrity_ledger,
            provenance_service=self.provenance_service,
            settings=self.settings,
        )
        self.compatibility_rule_service = CompatibilityRuleService(
            self.contract_registry_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
        )
        self.migration_note_service = MigrationNoteService(
            self.contract_registry_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
        )
        self.compatibility_scanner = ContractCompatibilityScanner(
            self.contract_registry_repository,
            self.contract_snapshot_service,
            self.compatibility_rule_service,
            self.policy_adapter,
            migration_note_service=self.migration_note_service,
            notification_router=self.notification_router,
            telemetry_service=self.telemetry_service,
            audit_sink=self.audit_integrity_ledger,
            provenance_service=self.provenance_service,
        )
        self.contract_registry_report_service = ContractRegistryReportService(
            self.contract_registry_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
            audit_sink=self.audit_integrity_ledger,
        )
        self.contract_registry_query_service = ContractRegistryQueryService(
            self.contract_registry_repository,
            self.policy_adapter,
        )
        self.extension_registry_repository = ExtensionRegistryRepository(self.settings.database_url)
        self.extension_manifest_validator = ManifestValidator(settings=self.settings)
        self.extension_package_service = ExtensionPackageService(
            self.extension_registry_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
        )
        self.extension_capability_service = CapabilityDeclarationService(
            self.extension_registry_repository,
            self.policy_adapter,
        )
        self.extension_dependency_service = DependencyDeclarationService(
            self.extension_registry_repository,
            self.policy_adapter,
            contract_repository=self.contract_registry_repository,
            policy_catalog=self.policy_catalog_service,
            runtime_config_status=self.runtime_config_status_service,
            settings=self.settings,
        )
        self.extension_install_plan_service = InstallPlanService(
            self.extension_registry_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
        )
        self.extension_compatibility_gate = ExtensionCompatibilityGate(
            self.extension_registry_repository,
            self.policy_adapter,
            manifest_validator=self.extension_manifest_validator,
            dependency_service=self.extension_dependency_service,
            capability_service=self.extension_capability_service,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
        )
        self.module_binding_repository = ModuleBindingRepository(self.settings.database_url)
        self.module_slot_service = ModuleSlotService(
            self.module_binding_repository,
            self.policy_adapter,
            extension_registry_repository=self.extension_registry_repository,
            telemetry_service=self.telemetry_service,
            audit_sink=self.audit_integrity_ledger,
            settings=self.settings,
        )
        self.capability_binding_service = CapabilityBindingService(
            self.module_binding_repository,
            self.policy_adapter,
            extension_registry_repository=self.extension_registry_repository,
            telemetry_service=self.telemetry_service,
            audit_sink=self.audit_integrity_ledger,
            settings=self.settings,
        )
        self.binding_conflict_service = BindingConflictService(
            self.module_binding_repository,
            self.policy_adapter,
            contract_repository=self.contract_registry_repository,
            policy_catalog_repository=self.policy_catalog_repository,
            settings=self.settings,
            telemetry_service=self.telemetry_service,
        )
        self.binding_validator = BindingValidator(
            self.module_binding_repository,
            self.policy_adapter,
            conflict_service=self.binding_conflict_service,
            telemetry_service=self.telemetry_service,
            audit_sink=self.audit_integrity_ledger,
            notification_router=self.notification_router,
            settings=self.settings,
        )
        self.module_mount_plan_service = ModuleMountPlanService(
            self.module_binding_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
            audit_sink=self.audit_integrity_ledger,
            settings=self.settings,
        )
        self.route_binding_preview_service = RouteBindingPreviewService(
            self.module_binding_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
            audit_sink=self.audit_integrity_ledger,
            settings=self.settings,
        )
        self.module_binding_query_service = ModuleBindingQueryService(
            self.module_binding_repository,
            self.policy_adapter,
        )
        self.conformance_repository = ConformanceRepository(self.settings.database_url)
        self.conformance_schema_checker = SchemaConformanceChecker()
        self.conformance_profile_service = ConformanceProfileService(
            self.conformance_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
        )
        self.capability_test_vector_service = CapabilityTestVectorService(
            self.conformance_repository,
            self.policy_adapter,
            module_binding_repository=self.module_binding_repository,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
        )
        self.mock_invocation_simulator = MockInvocationSimulator(
            self.conformance_repository,
            schema_checker=self.conformance_schema_checker,
            module_binding_repository=self.module_binding_repository,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
        )
        self.conformance_runner = ConformanceRunner(
            self.conformance_repository,
            self.policy_adapter,
            schema_checker=self.conformance_schema_checker,
            mock_simulator=self.mock_invocation_simulator,
            module_binding_repository=self.module_binding_repository,
            contract_repository=self.contract_registry_repository,
            policy_catalog_repository=self.policy_catalog_repository,
            autonomy_governor=self.autonomy_governor,
            notification_router=self.notification_router,
            telemetry_service=self.telemetry_service,
            audit_sink=self.audit_integrity_ledger,
            settings=self.settings,
        )
        self.conformance_finding_service = ConformanceFindingService(
            self.conformance_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
        )
        self.readiness_assessment_service = ReadinessAssessmentService(
            self.conformance_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
        )
        self.conformance_query_service = ConformanceQueryService(
            self.conformance_repository,
            self.policy_adapter,
        )
        self.module_activation_repository = ModuleActivationRepository(self.settings.database_url)
        self.module_activation_request_service = ModuleActivationRequestService(
            self.module_activation_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
            audit_sink=self.audit_integrity_ledger,
            settings=self.settings,
        )
        self.activation_blocker_service = ActivationBlockerService(
            self.module_activation_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
        )
        self.activation_gate_service = ActivationGateService(
            self.module_activation_repository,
            self.policy_adapter,
            module_binding_repository=self.module_binding_repository,
            conformance_repository=self.conformance_repository,
            telemetry_service=self.telemetry_service,
            audit_sink=self.audit_integrity_ledger,
            settings=self.settings,
            blocker_service=self.activation_blocker_service,
        )
        self.activation_review_service = ActivationReviewService(
            self.module_activation_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
        )
        self.activation_plan_service = ActivationPlanService(
            self.module_activation_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
        )
        self.runtime_registration_preview_service = RuntimeRegistrationPreviewService(
            self.module_activation_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
        )
        self.module_activation_query_service = ModuleActivationQueryService(
            self.module_activation_repository,
            self.policy_adapter,
        )
        self.module_mock_repository = ModuleMockRuntimeRepository(self.settings.database_url)
        self.module_mock_schema_adapter = ModuleMockSchemaAdapter()
        self.module_mock_plan_service = ModuleMockPlanService()
        self.module_mock_profile_service = ModuleMockProfileService(
            self.module_mock_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
        )
        self.module_mock_simulator = ModuleMockSimulator(
            self.module_mock_repository,
            self.policy_adapter,
            module_binding_repository=self.module_binding_repository,
            schema_adapter=self.module_mock_schema_adapter,
            telemetry_service=self.telemetry_service,
            audit_sink=self.audit_integrity_ledger,
            provenance_service=self.provenance_service,
            notification_router=self.notification_router,
            settings=self.settings,
        )
        self.module_mock_finding_service = ModuleMockFindingService(
            self.module_mock_repository,
            self.policy_adapter,
        )
        self.module_mock_query_service = ModuleMockQueryService(
            self.module_mock_repository,
            self.policy_adapter,
        )
        self.model_provider_hardening_repository = ModelProviderHardeningRepository(
            self.settings.database_url
        )
        self.model_provider_profile_service = ModelProviderProfileService(
            self.model_provider_hardening_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
        )
        self.prompt_egress_guard = PromptEgressGuard(
            self.model_provider_hardening_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
            audit_sink=self.audit_integrity_ledger,
            notification_router=self.notification_router,
            settings=self.settings,
        )
        self.model_provider_simulator = ModelProviderSimulator(
            self.model_provider_hardening_repository,
            self.policy_adapter,
            output_governance_service=self.output_governance_service,
            telemetry_service=self.telemetry_service,
            audit_sink=self.audit_integrity_ledger,
            provenance_service=self.provenance_service,
            notification_router=self.notification_router,
            settings=self.settings,
        )
        self.model_provider_readiness_service = ModelProviderReadinessService(
            self.model_provider_hardening_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
            audit_sink=self.audit_integrity_ledger,
            settings=self.settings,
        )
        self.model_provider_blocker_service = ModelProviderBlockerService(
            self.model_provider_hardening_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
        )
        self.model_provider_query_service = ProviderHardeningQueryService(
            self.model_provider_hardening_repository,
            self.policy_adapter,
        )
        set_activation_module_mock_repository = getattr(
            self.activation_gate_service,
            "set_module_mock_repository",
            None,
        )
        if callable(set_activation_module_mock_repository):
            set_activation_module_mock_repository(self.module_mock_repository)
        set_conformance_module_mock_simulator = getattr(
            self.conformance_runner,
            "set_module_mock_simulator",
            None,
        )
        if callable(set_conformance_module_mock_simulator):
            set_conformance_module_mock_simulator(self.module_mock_simulator)
        set_gateway_provider_hardening = getattr(
            self.model_gateway_service,
            "set_provider_hardening_repository",
            None,
        )
        if callable(set_gateway_provider_hardening):
            set_gateway_provider_hardening(self.model_provider_hardening_repository)
        self.golden_path_repository = GoldenPathRepository(self.settings.database_url)
        self.golden_path_assertion_engine = AssertionEngine()
        self.golden_path_scenario_catalog = ScenarioCatalogService(
            self.golden_path_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
        )
        self.golden_path_fixture_service = FixturePackService(
            self.golden_path_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
        )
        self.golden_path_report_service = GoldenPathReportService(
            self.golden_path_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
        )
        self.golden_path_query_service = GoldenPathQueryService(
            self.golden_path_repository,
            self.policy_adapter,
        )
        self.bootstrap_repository = BootstrapRepository(self.settings.database_url)
        self.bootstrap_profile_service = BootstrapProfileService(
            self.bootstrap_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
        )
        self.seed_bundle_service = SeedBundleService(
            self.bootstrap_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
        )
        self.seed_executor = SeedExecutor(
            self.bootstrap_repository,
            self.seed_bundle_service,
            self.policy_adapter,
            service_dependencies={
                "kernel": self.diagnostics,
                "policy": self.policy_catalog_service,
                "operator": getattr(self, "operator_readiness_aggregator", self.policy_adapter),
                "notifications": self.notification_topic_service,
                "registry": self.resource_registry_service,
                "contract_registry": self.contract_registry_report_service,
                "lifecycle": getattr(self, "lifecycle_report_service", self.policy_adapter),
                "extensions": getattr(
                    self, "extension_query_service", self.extension_registry_repository
                ),
                "conformance": self.conformance_query_service,
                "golden_path_scenarios": self.golden_path_scenario_catalog,
                "golden_path_fixtures": self.golden_path_fixture_service,
                "self_model": self.self_model_profile_service,
                "limitations": self.limitation_ledger_service,
            },
            telemetry_service=self.telemetry_service,
            audit_sink=self.audit_integrity_ledger,
            provenance_service=self.provenance_service,
            settings=self.settings,
        )
        self.setup_report_service = SetupReportService(
            self.bootstrap_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
        )
        self.bootstrap_query_service = BootstrapQueryService(
            self.bootstrap_repository,
            self.policy_adapter,
        )
        self.extension_intake_service = ExtensionIntakeService(
            self.extension_registry_repository,
            self.policy_adapter,
            manifest_validator=self.extension_manifest_validator,
            package_service=self.extension_package_service,
            dependency_service=self.extension_dependency_service,
            capability_service=self.extension_capability_service,
            compatibility_gate=self.extension_compatibility_gate,
            install_plan_service=self.extension_install_plan_service,
            telemetry_service=self.telemetry_service,
            audit_sink=self.audit_integrity_ledger,
            notification_router=self.notification_router,
            module_slot_service=self.module_slot_service,
            settings=self.settings,
        )
        self.extension_review_service = ExtensionReviewService(
            self.extension_registry_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
            module_slot_service=self.module_slot_service,
        )
        self.extension_query_service = ExtensionQueryService(
            self.extension_registry_repository,
            self.policy_adapter,
        )
        self.seed_executor.set_service_dependency("extensions", self.extension_query_service)
        set_contract_registry_services = getattr(
            self.release_packager,
            "set_contract_registry_services",
            None,
        )
        if callable(set_contract_registry_services):
            set_contract_registry_services(
                repository=self.contract_registry_repository,
                report_service=self.contract_registry_report_service,
            )
        set_contract_registry_repository = getattr(
            self.freeze_gate_service,
            "set_contract_registry_repository",
            None,
        )
        if callable(set_contract_registry_repository):
            set_contract_registry_repository(self.contract_registry_repository)
        set_extension_registry_services = getattr(
            self.release_packager,
            "set_extension_registry_services",
            None,
        )
        if callable(set_extension_registry_services):
            set_extension_registry_services(repository=self.extension_registry_repository)
        set_module_binding_registry = getattr(
            self.release_packager,
            "set_module_binding_registry",
            None,
        )
        if callable(set_module_binding_registry):
            set_module_binding_registry(repository=self.module_binding_repository)
        set_conformance_repository = getattr(
            self.release_packager,
            "set_conformance_repository",
            None,
        )
        if callable(set_conformance_repository):
            set_conformance_repository(repository=self.conformance_repository)
        set_module_mock_repository = getattr(
            self.release_packager,
            "set_module_mock_repository",
            None,
        )
        if callable(set_module_mock_repository):
            set_module_mock_repository(repository=self.module_mock_repository)
        set_model_provider_hardening_repository = getattr(
            self.release_packager,
            "set_model_provider_hardening_repository",
            None,
        )
        if callable(set_model_provider_hardening_repository):
            set_model_provider_hardening_repository(
                repository=self.model_provider_hardening_repository
            )
        set_freeze_extension_registry = getattr(
            self.freeze_gate_service,
            "set_extension_registry_repository",
            None,
        )
        if callable(set_freeze_extension_registry):
            set_freeze_extension_registry(self.extension_registry_repository)
        set_freeze_module_binding_registry = getattr(
            self.freeze_gate_service,
            "set_module_binding_repository",
            None,
        )
        if callable(set_freeze_module_binding_registry):
            set_freeze_module_binding_registry(self.module_binding_repository)
        set_freeze_conformance_repository = getattr(
            self.freeze_gate_service,
            "set_conformance_repository",
            None,
        )
        if callable(set_freeze_conformance_repository):
            set_freeze_conformance_repository(self.conformance_repository)
        set_freeze_module_mock_repository = getattr(
            self.freeze_gate_service,
            "set_module_mock_repository",
            None,
        )
        if callable(set_freeze_module_mock_repository):
            set_freeze_module_mock_repository(self.module_mock_repository)
        set_freeze_model_provider_hardening = getattr(
            self.freeze_gate_service,
            "set_model_provider_hardening_repository",
            None,
        )
        if callable(set_freeze_model_provider_hardening):
            set_freeze_model_provider_hardening(self.model_provider_hardening_repository)
        set_hardening_extension_registry = getattr(
            self.hardening_gate_service,
            "set_extension_registry_repository",
            None,
        )
        if callable(set_hardening_extension_registry):
            set_hardening_extension_registry(self.extension_registry_repository)
        set_hardening_module_binding_registry = getattr(
            self.hardening_gate_service,
            "set_module_binding_repository",
            None,
        )
        if callable(set_hardening_module_binding_registry):
            set_hardening_module_binding_registry(self.module_binding_repository)
        set_hardening_conformance_repository = getattr(
            self.hardening_gate_service,
            "set_conformance_repository",
            None,
        )
        if callable(set_hardening_conformance_repository):
            set_hardening_conformance_repository(self.conformance_repository)
        set_hardening_module_mock_repository = getattr(
            self.hardening_gate_service,
            "set_module_mock_repository",
            None,
        )
        if callable(set_hardening_module_mock_repository):
            set_hardening_module_mock_repository(self.module_mock_repository)
        set_hardening_model_provider_hardening = getattr(
            self.hardening_gate_service,
            "set_model_provider_hardening_repository",
            None,
        )
        if callable(set_hardening_model_provider_hardening):
            set_hardening_model_provider_hardening(self.model_provider_hardening_repository)
        set_resource_provider = getattr(self.resource_scanner, "set_provider", None)
        if callable(set_resource_provider):
            set_resource_provider("contract_registry", self.contract_registry_repository)
            set_resource_provider("extension_registry", self.extension_registry_repository)
            set_resource_provider("module_binding_registry", self.module_binding_repository)
            set_resource_provider("conformance", self.conformance_repository)
            set_resource_provider("module_mock_runtime", self.module_mock_repository)
            set_resource_provider(
                "model_provider_hardening",
                self.model_provider_hardening_repository,
            )
        self.lifecycle_repository = LifecycleRepository(self.settings.database_url)
        self.lifecycle_policy_service = LifecyclePolicyService(
            self.lifecycle_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
        )
        self.retention_classifier = RetentionClassifier(
            self.lifecycle_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
        )
        self.archive_planner = ArchivePlanner(
            self.lifecycle_repository,
            self.policy_adapter,
            action_proposal_service=self.action_proposal_service,
            settings=self.settings,
            telemetry_service=self.telemetry_service,
        )
        self.redaction_planner = RedactionPlanner(
            self.lifecycle_repository,
            self.policy_adapter,
            action_proposal_service=self.action_proposal_service,
            telemetry_service=self.telemetry_service,
        )
        self.purge_preview_service = PurgePreviewService(
            self.lifecycle_repository,
            self.policy_adapter,
            registry_repository=self.resource_registry_repository,
            settings=self.settings,
            telemetry_service=self.telemetry_service,
        )
        self.lifecycle_review_service = LifecycleReviewService(
            self.lifecycle_repository,
            self.policy_adapter,
            archive_planner=self.archive_planner,
            redaction_planner=self.redaction_planner,
            telemetry_service=self.telemetry_service,
        )
        self.lifecycle_report_service = LifecycleReportService(
            self.lifecycle_repository,
            self.policy_adapter,
            registry_repository=self.resource_registry_repository,
            telemetry_service=self.telemetry_service,
        )
        self.lifecycle_query_service = LifecycleQueryService(self.lifecycle_repository)
        self.seed_executor.set_service_dependency("lifecycle", self.lifecycle_report_service)
        self.lifecycle_evaluator = LifecycleEvaluator(
            self.lifecycle_repository,
            self.policy_adapter,
            registry_repository=self.resource_registry_repository,
            policy_service=self.lifecycle_policy_service,
            classifier=self.retention_classifier,
            archive_planner=self.archive_planner,
            redaction_planner=self.redaction_planner,
            purge_preview_service=self.purge_preview_service,
            notification_router=self.notification_router,
            incident_signal_service=self.incident_signal_service,
            audit_sink=self.audit_integrity_ledger,
            provenance_service=self.provenance_service,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
        )
        self.operator_repository = OperatorRepository(self.settings.database_url)
        self.scheduler_tick_orchestrator._operator_repository = self.operator_repository
        self.operator_status_card_builder = StatusCardBuilder(
            kernel_service=self.diagnostics,
            resilience_service=self.resilience_test_runner,
            security_service=self.hardening_gate_service,
            runtime_config_service=self.runtime_config_status_service,
            audit_service=self.audit_integrity_ledger,
            policy_service=self.policy_coverage_analyzer,
            freeze_service=self.freeze_gate_service,
            release_service=self.release_baseline_service,
            performance_service=self.benchmark_runner,
            backup_service=self.backup_exporter,
            outbox_service=self.outbox_service,
            approval_service=self.approval_service,
            workflow_service=self.workflow_service,
            event_router_service=self.event_reaction_repository,
            situation_service=self.situation_service,
            decision_frame_service=self.decision_frame_service,
            decision_journal_service=self.decision_journal_service,
            outcome_service=self.outcome_service,
            outcome_feedback_service=self.outcome_feedback_service,
            effect_verifier=self.effect_verifier,
            learning_synthesizer=self.learning_synthesizer,
            learning_synthesis_repository=self.learning_synthesis_repository,
            skill_suggestion_service=self.skill_suggestion_service,
            regression_suggestion_service=self.regression_suggestion_service,
            self_model_service=self.self_model_profile_service,
            capability_awareness_service=self.capability_awareness_service,
            limitation_service=self.limitation_ledger_service,
            instruction_service=self.instruction_query_service,
            prompt_service=self.prompt_compiler,
            scheduler_service=self.scheduler_query_service,
            incident_service=self.incident_service,
            registry_service=self.registry_query_service,
            contract_registry_service=self.contract_registry_report_service,
            extension_registry_service=self.extension_registry_repository,
            module_binding_service=self.module_binding_repository,
            module_mock_runtime_service=self.module_mock_repository,
            model_provider_hardening_service=self.model_provider_hardening_repository,
            conformance_service=self.conformance_repository,
            golden_path_service=self.golden_path_repository,
            bootstrap_service=self.bootstrap_repository,
            release_candidate_service=self.release_candidate_repository,
            lifecycle_service=self.lifecycle_report_service,
        )
        self.operator_queue_summary_builder = QueueSummaryBuilder(
            approval_service=self.approval_repository,
            command_service=self.command_bus,
            outbox_service=self.outbox_repository,
            inbox_service=self.inbox_repository,
            workflow_service=self.workflow_repository,
            task_service=self.task_repository,
            event_router_service=self.event_reaction_repository,
            backup_service=self.backup_repository,
            release_service=self.release_package_repository,
            audit_service=self.audit_integrity_repository,
            resilience_service=self.resilience_repository,
            security_service=self.security_baseline_repository,
            scenario_service=self.scenario_repository,
            dialogue_service=self.clarification_manager,
            belief_contradiction_service=self.belief_contradiction_service,
            entity_repository=self.entity_repository,
            entity_merge_service=self.entity_merge_service,
            entity_split_service=self.entity_split_service,
            situation_projector=self.situation_projector,
            decision_frame_service=self.decision_frame_service,
            decision_journal_service=self.decision_journal_service,
            counterfactual_simulator=self.counterfactual_simulator,
            outcome_service=self.outcome_service,
            outcome_feedback_service=self.outcome_feedback_service,
            effect_verifier=self.effect_verifier,
            learning_synthesis_repository=self.learning_synthesis_repository,
            skill_suggestion_service=self.skill_suggestion_service,
            regression_suggestion_service=self.regression_suggestion_service,
            limitation_service=self.limitation_ledger_service,
            self_assessment_service=self.self_assessment_service,
            instruction_conflict_service=self.instruction_conflict_detector,
            preference_learning_service=self.preference_learning_service,
            grounding_repository=self.grounding_repository,
            grounding_verifier=self.grounding_verifier,
            prompt_repository=self.prompt_repository,
            model_output_repository=self.model_output_repository,
            response_candidate_service=self.response_candidate_service,
            tool_intent_service=self.tool_intent_capture_service,
            action_proposal_service=self.action_proposal_service,
            action_blocker_service=self.action_blocker_service,
            action_review_service=self.action_review_service,
            execution_handoff_service=self.execution_handoff_service,
            tool_intent_review_service=self.tool_intent_review_service,
            run_supervision_service=self.run_supervision_service,
            run_control_service=self.run_control_service,
            compensation_planner=self.compensation_planner,
            notification_query_service=self.notification_query_service,
            alert_service=self.alert_service,
            escalation_service=self.escalation_service,
            notification_digest_service=self.notification_digest_service,
            scheduler_service=self.scheduler_query_service,
            incident_service=self.incident_service,
            root_cause_service=self.root_cause_candidate_service,
            recovery_review_service=self.recovery_review_service,
            reference_validator=self.reference_validator,
            registry_rebuilder=self.registry_rebuilder,
            contract_registry_repository=self.contract_registry_repository,
            extension_registry_repository=self.extension_registry_repository,
            module_binding_repository=self.module_binding_repository,
            module_mock_repository=self.module_mock_repository,
            model_provider_hardening_repository=self.model_provider_hardening_repository,
            conformance_repository=self.conformance_repository,
            module_activation_repository=self.module_activation_repository,
            golden_path_repository=self.golden_path_repository,
            bootstrap_repository=self.bootstrap_repository,
            release_candidate_repository=self.release_candidate_repository,
            archive_planner=self.archive_planner,
            redaction_planner=self.redaction_planner,
            purge_preview_service=self.purge_preview_service,
            lifecycle_review_service=self.lifecycle_review_service,
        )
        self.operator_action_center_service = ActionCenterService(
            self.operator_repository,
            self.policy_adapter,
            self.telemetry_service,
            approval_service=self.approval_repository,
            command_service=self.command_bus,
            resilience_service=self.resilience_repository,
            audit_service=self.audit_integrity_repository,
            belief_contradiction_service=self.belief_contradiction_service,
            entity_repository=self.entity_repository,
            entity_merge_service=self.entity_merge_service,
            entity_split_service=self.entity_split_service,
            situation_service=self.situation_service,
            situation_projector=self.situation_projector,
            decision_frame_service=self.decision_frame_service,
            decision_journal_service=self.decision_journal_service,
            counterfactual_simulator=self.counterfactual_simulator,
            outcome_service=self.outcome_service,
            outcome_feedback_service=self.outcome_feedback_service,
            effect_verifier=self.effect_verifier,
            learning_synthesis_repository=self.learning_synthesis_repository,
            skill_suggestion_service=self.skill_suggestion_service,
            regression_suggestion_service=self.regression_suggestion_service,
            explanation_service=self.explanation_builder,
            instruction_conflict_service=self.instruction_conflict_detector,
            preference_learning_service=self.preference_learning_service,
            prompt_repository=self.prompt_repository,
            grounding_verifier=self.grounding_verifier,
            source_coverage_service=self.source_coverage_service,
            model_output_repository=self.model_output_repository,
            response_candidate_service=self.response_candidate_service,
            tool_intent_service=self.tool_intent_capture_service,
            action_proposal_service=self.action_proposal_service,
            action_blocker_service=self.action_blocker_service,
            execution_handoff_service=self.execution_handoff_service,
            tool_intent_review_service=self.tool_intent_review_service,
            run_supervision_service=self.run_supervision_service,
            run_control_service=self.run_control_service,
            compensation_planner=self.compensation_planner,
            notification_query_service=self.notification_query_service,
            alert_service=self.alert_service,
            escalation_service=self.escalation_service,
            notification_digest_service=self.notification_digest_service,
            scheduler_service=self.scheduler_query_service,
            incident_service=self.incident_service,
            contract_registry_repository=self.contract_registry_repository,
            extension_registry_repository=self.extension_registry_repository,
            module_binding_repository=self.module_binding_repository,
            module_mock_repository=self.module_mock_repository,
            conformance_repository=self.conformance_repository,
            golden_path_repository=self.golden_path_repository,
            bootstrap_repository=self.bootstrap_repository,
            release_candidate_repository=self.release_candidate_repository,
            archive_planner=self.archive_planner,
            redaction_planner=self.redaction_planner,
            purge_preview_service=self.purge_preview_service,
            lifecycle_review_service=self.lifecycle_review_service,
        )
        self.operator_readiness_aggregator = ReadinessAggregator(
            self.operator_status_card_builder,
            self.operator_action_center_service,
            telemetry_service=self.telemetry_service,
        )
        self.operator_runbook_registry = RunbookRegistry()
        self.operator_control_tower_service = OperatorControlTowerService(
            status_cards=self.operator_status_card_builder,
            queues=self.operator_queue_summary_builder,
            action_center=self.operator_action_center_service,
            readiness=self.operator_readiness_aggregator,
            runbooks=self.operator_runbook_registry,
            policy_adapter=self.policy_adapter,
            telemetry_service=self.telemetry_service,
        )
        self.introspection_snapshot_service.set_operator_service(
            self.operator_control_tower_service
        )
        self.operator_snapshot_service = OperatorSnapshotService(
            self.operator_repository,
            self.operator_control_tower_service,
            self.policy_adapter,
            self.telemetry_service,
        )
        self.golden_path_runner = GoldenPathRunner(
            self.golden_path_repository,
            self.golden_path_scenario_catalog,
            self.golden_path_fixture_service,
            self.golden_path_assertion_engine,
            self.golden_path_report_service,
            self.policy_adapter,
            autonomy_governor=self.autonomy_governor,
            notification_router=self.notification_router,
            operator_repository=self.operator_repository,
            telemetry_service=self.telemetry_service,
            audit_sink=self.audit_integrity_ledger,
            provenance_service=self.provenance_service,
            settings=self.settings,
            service_dependencies={
                "diagnostics": self.diagnostics,
                "health": self.diagnostics,
                "runtime_config": self.runtime_config_status_service,
                "self_description": self.self_description_service,
                "dialogue": self.dialogue_turn_service,
                "responses": self.response_composer,
                "instructions": self.instruction_resolver,
                "policy": self.policy_adapter,
                "autonomy": self.autonomy_governor,
                "context": self.context_compiler,
                "prompts": self.prompt_compiler,
                "model_outputs": self.output_governance_service,
                "grounding": self.grounding_verifier,
                "evidence": self.evidence_service,
                "action_proposals": self.action_proposal_service,
                "execution_handoff": self.execution_handoff_service,
                "run_supervision": self.run_supervision_service,
                "notifications": self.notification_router,
                "scheduler": self.scheduler_tick_orchestrator,
                "incidents": self.incident_correlation_engine,
                "resource_registry": self.resource_registry_service,
                "lifecycle": self.lifecycle_evaluator,
                "contract_registry": self.contract_registry_report_service,
                "extensions": self.extension_intake_service,
                "module_bindings": self.module_binding_query_service,
                "conformance": self.conformance_repository,
                "operator": self.operator_control_tower_service,
            },
        )
        self.golden_path_release_smoke = ReleaseSmokeMatrix(
            self.golden_path_repository,
            self.policy_adapter,
            diagnostics=self.diagnostics,
            freeze_gate_service=self.freeze_gate_service,
            release_packager=self.release_packager,
            registry_service=self.resource_registry_service,
            contract_registry=self.contract_registry_report_service,
            operator_service=self.operator_control_tower_service,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
        )
        self.setup_doctor = SetupDoctor(
            self.bootstrap_repository,
            self.policy_adapter,
            diagnostics=self.diagnostics,
            golden_path_repository=self.golden_path_repository,
            release_smoke=self.golden_path_release_smoke,
            operator_service=self.operator_control_tower_service,
            telemetry_service=self.telemetry_service,
            settings=self.settings,
            root_dir=root_dir,
        )
        self.bootstrap_runner = BootstrapRunner(
            self.bootstrap_repository,
            self.bootstrap_profile_service,
            self.seed_bundle_service,
            self.seed_executor,
            self.setup_doctor,
            self.setup_report_service,
            self.policy_adapter,
            golden_path_runner=self.golden_path_runner,
            release_smoke=self.golden_path_release_smoke,
            autonomy_governor=self.autonomy_governor,
            notification_router=self.notification_router,
            operator_repository=self.operator_repository,
            telemetry_service=self.telemetry_service,
            audit_sink=self.audit_integrity_ledger,
            provenance_service=self.provenance_service,
            settings=self.settings,
        )
        self.release_candidate_service = ReleaseCandidateService(
            self.release_candidate_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
            audit_sink=self.audit_integrity_ledger,
            provenance_service=self.provenance_service,
        )
        self.verification_matrix_service = VerificationMatrixService(
            self.release_candidate_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
            audit_sink=self.audit_integrity_ledger,
            settings=self.settings,
        )
        self.rc_check_collector = VerificationCheckCollector(
            setup_doctor=self.setup_doctor,
            golden_path_runner=self.golden_path_runner,
            release_smoke=self.golden_path_release_smoke,
            freeze_gate_service=self.freeze_gate_service,
            release_packager=self.release_packager,
            contract_registry_repository=self.contract_registry_repository,
            contract_registry_report_service=self.contract_registry_report_service,
            resource_registry_validator=self.reference_validator,
            lifecycle_service=self.lifecycle_query_service,
            extension_registry_repository=self.extension_registry_repository,
            module_binding_repository=self.module_binding_repository,
            conformance_repository=self.conformance_repository,
            hardening_gate_service=self.hardening_gate_service,
            runtime_config_status_service=self.runtime_config_status_service,
            operator_service=self.operator_control_tower_service,
            settings=self.settings,
        )
        self.rc_finding_service = RCFindingService(
            self.release_candidate_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
        )
        self.rc_evidence_pack_service = RCEvidencePackService(
            self.release_candidate_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
        )
        self.rc_report_service = RCReportService(
            self.release_candidate_repository,
            self.policy_adapter,
            telemetry_service=self.telemetry_service,
        )
        self.rc_gate_service = RCGateService(
            self.release_candidate_repository,
            self.policy_adapter,
            candidate_service=self.release_candidate_service,
            matrix_service=self.verification_matrix_service,
            check_collector=self.rc_check_collector,
            finding_service=self.rc_finding_service,
            evidence_pack_service=self.rc_evidence_pack_service,
            report_service=self.rc_report_service,
            autonomy_governor=self.autonomy_governor,
            notification_router=self.notification_router,
            operator_repository=self.operator_repository,
            telemetry_service=self.telemetry_service,
            audit_sink=self.audit_integrity_ledger,
            provenance_service=self.provenance_service,
            settings=self.settings,
        )
        self.rc_query_service = RCQueryService(
            self.release_candidate_repository,
            self.policy_adapter,
        )
        self.seed_executor.set_service_dependency("operator", self.operator_control_tower_service)
        set_freeze_golden_path_repository = getattr(
            self.freeze_gate_service,
            "set_golden_path_repository",
            None,
        )
        if callable(set_freeze_golden_path_repository):
            set_freeze_golden_path_repository(self.golden_path_repository)
        set_release_golden_path_repository = getattr(
            self.release_packager,
            "set_golden_path_repository",
            None,
        )
        if callable(set_release_golden_path_repository):
            set_release_golden_path_repository(self.golden_path_repository)
        set_freeze_bootstrap_repository = getattr(
            self.freeze_gate_service,
            "set_bootstrap_repository",
            None,
        )
        if callable(set_freeze_bootstrap_repository):
            set_freeze_bootstrap_repository(self.bootstrap_repository)
        set_release_bootstrap_repository = getattr(
            self.release_packager,
            "set_bootstrap_repository",
            None,
        )
        if callable(set_release_bootstrap_repository):
            set_release_bootstrap_repository(self.bootstrap_repository)
        set_golden_resource_provider = getattr(self.resource_scanner, "set_provider", None)
        if callable(set_golden_resource_provider):
            set_golden_resource_provider("golden_path", self.golden_path_repository)
        set_bootstrap_resource_provider = getattr(self.resource_scanner, "set_provider", None)
        if callable(set_bootstrap_resource_provider):
            set_bootstrap_resource_provider("bootstrap", self.bootstrap_repository)
        set_rc_resource_provider = getattr(self.resource_scanner, "set_provider", None)
        if callable(set_rc_resource_provider):
            set_rc_resource_provider("release_candidate", self.release_candidate_repository)
        set_operator_readiness = getattr(
            self.release_baseline_service,
            "set_operator_readiness_service",
            None,
        )
        if callable(set_operator_readiness):
            set_operator_readiness(self.operator_readiness_aggregator)
        self._services: dict[str, object] = {}
        self._register_services()
        self._latest_boot: KernelBootRecord | None = None

    def get(self, name: str, expected_type: type[T] | None = None) -> T | object:
        """Return one named assembled service."""
        service = self._services[name]
        if expected_type is not None and not isinstance(service, expected_type):
            raise TypeError(f"kernel service {name!r} is not {expected_type.__name__}")
        return service

    def ensure_booted(self) -> KernelBootRecord:
        """Boot once per container process."""
        if self._latest_boot is None:
            self._latest_boot = self.boot_service.boot()
        return self._latest_boot

    def status(self) -> KernelStatus:
        """Return current assembled kernel status."""
        latest_boot = self.ensure_booted()
        return KernelStatus(
            service_name=self.settings.service_name,
            version=self.settings.version,
            env=self.settings.env,
            status=latest_boot.status,
            uptime_seconds=int((datetime.now(UTC) - self.started_at).total_seconds()),
            adapter_config=self.adapter_config,
            services=self.service_registry.list_services(),
            latest_boot=latest_boot,
            latest_self_test=self.self_test_service.get_latest(),
            generated_at=datetime.now(UTC),
        )

    def _adapter_config(self) -> KernelAdapterConfig:
        return KernelAdapterConfig(
            runtime_adapter=getattr(self.settings, "runtime_adapter", "langgraph"),
            semantic_memory_adapter=self.settings.default_semantic_adapter,
            graph_memory_adapter=getattr(
                self.settings,
                "default_graph_memory_adapter",
                "postgres_graph",
            ),
            model_gateway_adapter=getattr(self.settings, "model_gateway_adapter", "deterministic"),
            policy_adapter=getattr(self.settings, "policy_adapter", "opa"),
            object_store_adapter=self.settings.default_object_store,
            observability_adapter=self.settings.observability_adapter,
            module_runtime_adapters=["local_internal", "local_stub", "mcp"],
            evaluation_adapters=["local"],
            metadata={
                "assembly": "aion-kernel-v0.1",
                "workflow_engine_adapter": self.settings.workflow_engine_adapter,
            },
        )

    def _reject_placeholder_selection(self) -> None:
        selected = {
            self.adapter_config.runtime_adapter,
            self.adapter_config.semantic_memory_adapter,
            self.adapter_config.graph_memory_adapter,
            self.adapter_config.model_gateway_adapter,
            self.adapter_config.policy_adapter,
            self.adapter_config.object_store_adapter,
            self.adapter_config.observability_adapter,
        }
        invalid = sorted(selected & _PLACEHOLDER_ADAPTERS)
        if invalid:
            raise ValueError(
                f"placeholder adapters cannot be selected for live execution: {invalid}"
            )

    def _turbovec_adapter(self) -> TurboVecSemanticMemoryAdapter:
        return TurboVecSemanticMemoryAdapter(
            memory_repository=self.memory_repository,
            turbovec_repository=self.turbovec_repository,
            embedding_adapter=HashEmbeddingAdapter(self.settings.semantic_vector_dimensions),
            telemetry_service=self.audit_repository,
            compat=TurboVecCompat(),
            enabled=self.settings.turbovec_enabled,
            index_name=self.settings.turbovec_index_name,
            index_dir=self.settings.turbovec_index_dir,
            dimensions=self.settings.semantic_vector_dimensions,
            bit_width=self.settings.turbovec_bit_width,
            auto_persist=self.settings.turbovec_auto_persist,
        )

    def _semantic_adapter(
        self,
    ) -> (
        InMemorySemanticMemoryAdapter
        | PgVectorSemanticMemoryAdapter
        | TurboVecSemanticMemoryAdapter
    ):
        selected = self.adapter_config.semantic_memory_adapter.replace("-", "_")
        if self.adapter_config.semantic_memory_adapter in {"in_memory", "in-memory"}:
            return InMemorySemanticMemoryAdapter()
        if selected == "turbovec":
            status = self.turbovec_semantic_adapter.status(self.settings.turbovec_index_name)
            if status.available:
                return self.turbovec_semantic_adapter
            self.semantic_adapter_fallback_reason = status.reason or "turbovec_unavailable"
            if self.settings.turbovec_fail_open_to_pgvector:
                return PgVectorSemanticMemoryAdapter(
                    memory_repository=self.memory_repository,
                    database_url=self.settings.database_url,
                    dimensions=self.settings.semantic_vector_dimensions,
                )
            return self.turbovec_semantic_adapter
        if selected != "pgvector":
            raise ValueError("unsupported semantic memory adapter")
        return PgVectorSemanticMemoryAdapter(
            memory_repository=self.memory_repository,
            database_url=self.settings.database_url,
            dimensions=self.settings.semantic_vector_dimensions,
        )

    def _graphiti_adapter(self) -> GraphitiGraphMemoryAdapter:
        return GraphitiGraphMemoryAdapter(
            graphiti_repository=self.graphiti_repository,
            postgres_graph_adapter=PostgresGraphAdapter(database_url=self.settings.database_url),
            telemetry_service=self.audit_repository,
            compat=GraphitiCompat(),
            enabled=self.settings.graphiti_enabled,
            config_name=self.settings.graphiti_config_name,
            backend_type=self.settings.graphiti_backend_type,
            endpoint_ref=self.settings.graphiti_endpoint_ref,
            fail_open_to_postgres_graph=self.settings.graphiti_fail_open_to_postgres_graph,
            model_gateway_enabled=self.settings.model_gateway_enabled,
        )

    def _graph_adapter(
        self,
    ) -> InMemoryGraphAdapter | PostgresGraphAdapter | GraphitiGraphMemoryAdapter:
        selected = self.adapter_config.graph_memory_adapter.replace("-", "_")
        if selected == "in_memory":
            return InMemoryGraphAdapter()
        if selected == "graphiti":
            status = self.graphiti_graph_adapter.status(self.settings.graphiti_config_name)
            if status.available:
                return self.graphiti_graph_adapter
            self.graph_adapter_fallback_reason = status.reason or "graphiti_unavailable"
            if self.settings.graphiti_fail_open_to_postgres_graph:
                return PostgresGraphAdapter(database_url=self.settings.database_url)
            return self.graphiti_graph_adapter
        if selected != "postgres_graph":
            raise ValueError("unsupported graph memory adapter")
        return PostgresGraphAdapter(database_url=self.settings.database_url)

    def _retrieval_router(self) -> RetrievalRouter:
        return RetrievalRouter(
            policy_adapter=self.policy_adapter,
            memory_service=self.memory_service,
            semantic_memory_service=self.semantic_memory_service,
            graph_memory_service=self.graph_memory_service,
            capability_registry=self.capability_registry,
            trace_repository=self.audit_repository,
            evidence_service=self.evidence_service,
            telemetry_service=self.telemetry_service,
            memory_governance_engine=self.memory_governance_engine,
            memory_decay_service=self.memory_decay_service,
            working_memory_service=self.working_memory_service,
            belief_query_service=self.belief_query_service,
            entity_query_service=self.entity_query_service,
            concept_service=self.concept_service,
            situation_service=self.situation_service,
            state_atom_service=self.state_atom_service,
            temporal_state_window_service=self.temporal_state_window_service,
            decision_journal_service=self.decision_journal_service,
        )

    def _register_services(self) -> None:
        service_specs: tuple[tuple[str, object, str, str], ...] = (
            ("policy_adapter", self.policy_adapter, "policy", self.adapter_config.policy_adapter),
            (
                "audit_integrity_repository",
                self.audit_integrity_repository,
                "repository",
                "postgres",
            ),
            ("audit_integrity_ledger", self.audit_integrity_ledger, "service", "local"),
            ("audit_checkpoint_service", self.audit_checkpoint_service, "service", "local"),
            ("audit_verifier", self.audit_verifier, "service", "local"),
            ("audit_exporter", self.audit_exporter, "service", "local"),
            ("provenance_service", self.provenance_service, "service", "local"),
            ("memory_service", self.memory_service, "memory", "postgres"),
            (
                "semantic_memory_adapter",
                self.semantic_memory_adapter,
                "adapter",
                self.adapter_config.semantic_memory_adapter,
            ),
            (
                "turbovec_semantic_adapter",
                self.turbovec_semantic_adapter,
                "adapter",
                "turbovec",
            ),
            (
                "graph_memory_adapter",
                self.graph_memory_adapter,
                "adapter",
                self.adapter_config.graph_memory_adapter,
            ),
            (
                "graphiti_graph_adapter",
                self.graphiti_graph_adapter,
                "adapter",
                "graphiti",
            ),
            ("retrieval_router", self.retrieval_router, "service", "local"),
            ("focus_service", self.focus_service, "service", "local"),
            ("attention_controller", self.attention_controller, "service", "local"),
            ("working_memory_service", self.working_memory_service, "service", "local"),
            ("interrupt_router", self.interrupt_router, "service", "local"),
            ("context_budgeter", self.context_budgeter, "service", "local"),
            ("memory_governance_engine", self.memory_governance_engine, "service", "local"),
            ("memory_decay_service", self.memory_decay_service, "service", "local"),
            ("memory_retention_service", self.memory_retention_service, "service", "local"),
            ("memory_conflict_service", self.memory_conflict_service, "service", "local"),
            ("memory_compaction_service", self.memory_compaction_service, "service", "local"),
            ("memory_forgetting_service", self.memory_forgetting_service, "service", "local"),
            ("risk_engine", self.risk_engine, "service", "local"),
            ("guardrail_engine", self.guardrail_engine, "service", "local"),
            ("approval_service", self.approval_service, "service", "local"),
            ("context_compiler", self.context_compiler, "service", "local"),
            (
                "model_gateway_service",
                self.model_gateway_service,
                "service",
                self.adapter_config.model_gateway_adapter,
            ),
            ("model_output_repository", self.model_output_repository, "repository", "postgres"),
            (
                "output_governance_service",
                self.output_governance_service,
                "service",
                "local",
            ),
            ("model_output_query_service", self.model_output_query_service, "service", "local"),
            ("output_parser", self.output_parser, "service", "deterministic"),
            (
                "structured_output_validator",
                self.structured_output_validator,
                "service",
                "deterministic",
            ),
            ("unsafe_output_detector", self.unsafe_output_detector, "service", "deterministic"),
            (
                "response_candidate_service",
                self.response_candidate_service,
                "service",
                "local",
            ),
            (
                "tool_intent_capture_service",
                self.tool_intent_capture_service,
                "service",
                "local",
            ),
            (
                "action_proposal_repository",
                self.action_proposal_repository,
                "repository",
                "postgres",
            ),
            (
                "action_blocker_service",
                self.action_blocker_service,
                "service",
                "local",
            ),
            (
                "action_proposal_service",
                self.action_proposal_service,
                "service",
                "local",
            ),
            (
                "tool_intent_review_service",
                self.tool_intent_review_service,
                "service",
                "local",
            ),
            (
                "action_review_service",
                self.action_review_service,
                "service",
                "local",
            ),
            (
                "execution_handoff_service",
                self.execution_handoff_service,
                "service",
                "local",
            ),
            (
                "action_proposal_query_service",
                self.action_proposal_query_service,
                "service",
                "local",
            ),
            (
                "run_supervision_repository",
                self.run_supervision_repository,
                "repository",
                "postgres",
            ),
            (
                "run_target_status_adapter",
                self.run_target_status_adapter,
                "adapter",
                "local",
            ),
            (
                "run_supervision_service",
                self.run_supervision_service,
                "service",
                "local",
            ),
            (
                "run_status_sampler",
                self.run_status_sampler,
                "service",
                "local",
            ),
            (
                "run_control_service",
                self.run_control_service,
                "service",
                "local",
            ),
            (
                "timeout_policy_service",
                self.timeout_policy_service,
                "service",
                "local",
            ),
            (
                "compensation_planner",
                self.compensation_planner,
                "service",
                "local",
            ),
            (
                "run_supervision_report_service",
                self.run_supervision_report_service,
                "service",
                "local",
            ),
            (
                "run_supervision_query_service",
                self.run_supervision_query_service,
                "service",
                "local",
            ),
            (
                "notification_repository",
                self.notification_repository,
                "repository",
                "postgres",
            ),
            (
                "notification_topic_service",
                self.notification_topic_service,
                "service",
                "local",
            ),
            (
                "notification_subscription_service",
                self.notification_subscription_service,
                "service",
                "local",
            ),
            (
                "notification_router",
                self.notification_router,
                "service",
                "local",
            ),
            (
                "alert_service",
                self.alert_service,
                "service",
                "local",
            ),
            (
                "escalation_service",
                self.escalation_service,
                "service",
                "local",
            ),
            (
                "notification_digest_service",
                self.notification_digest_service,
                "service",
                "local",
            ),
            (
                "notification_query_service",
                self.notification_query_service,
                "service",
                "local",
            ),
            ("incident_repository", self.incident_repository, "repository", "postgres"),
            (
                "incident_signal_service",
                self.incident_signal_service,
                "service",
                "local",
            ),
            (
                "incident_rule_service",
                self.incident_rule_service,
                "service",
                "local",
            ),
            ("incident_service", self.incident_service, "service", "local"),
            (
                "incident_correlation_engine",
                self.incident_correlation_engine,
                "service",
                "deterministic",
            ),
            ("incident_query_service", self.incident_query_service, "service", "local"),
            (
                "root_cause_candidate_service",
                self.root_cause_candidate_service,
                "service",
                "deterministic",
            ),
            (
                "recovery_review_service",
                self.recovery_review_service,
                "service",
                "local",
            ),
            ("scheduler_repository", self.scheduler_repository, "repository", "postgres"),
            (
                "scheduler_schedule_service",
                self.scheduler_schedule_service,
                "service",
                "local",
            ),
            (
                "scheduler_due_item_service",
                self.scheduler_due_item_service,
                "service",
                "local",
            ),
            (
                "scheduler_reminder_service",
                self.scheduler_reminder_service,
                "service",
                "local",
            ),
            (
                "scheduler_tick_orchestrator",
                self.scheduler_tick_orchestrator,
                "service",
                "local",
            ),
            ("schedule_policy_service", self.schedule_policy_service, "service", "local"),
            ("scheduler_report_service", self.scheduler_report_service, "service", "local"),
            ("scheduler_query_service", self.scheduler_query_service, "service", "local"),
            (
                "model_provider_registry",
                self.model_provider_registry,
                "service",
                "local",
            ),
            (
                "model_profile_registry",
                self.model_profile_registry,
                "service",
                "local",
            ),
            ("prompt_redactor", self.prompt_redactor, "service", "local"),
            ("prompt_repository", self.prompt_repository, "repository", "postgres"),
            ("prompt_template_service", self.prompt_template_service, "service", "local"),
            ("prompt_fragment_service", self.prompt_fragment_service, "service", "local"),
            ("prompt_sectioner", self.prompt_sectioner, "service", "deterministic"),
            (
                "prompt_injection_detector",
                self.prompt_injection_detector,
                "service",
                "deterministic",
            ),
            ("prompt_boundary_checker", self.prompt_boundary_checker, "service", "deterministic"),
            ("prompt_compiler", self.prompt_compiler, "service", "deterministic"),
            (
                "model_input_manifest_service",
                self.model_input_manifest_service,
                "service",
                "local",
            ),
            ("prompt_preview_service", self.prompt_preview_service, "service", "local"),
            ("prompt_governance_service", self.prompt_governance_service, "service", "local"),
            ("model_budget_guard", self.model_budget_guard, "service", "local"),
            ("model_usage_ledger", self.model_usage_ledger, "service", "local"),
            (
                "reasoning_mesh",
                self.reasoning_mesh,
                "reasoning",
                self.adapter_config.model_gateway_adapter,
            ),
            ("planner", self.planner, "service", "deterministic"),
            ("brain_runtime", self.brain_runtime, "runtime", self.adapter_config.runtime_adapter),
            ("dialogue_repository", self.dialogue_repository, "repository", "postgres"),
            ("dialogue_session_service", self.dialogue_session_service, "service", "local"),
            ("dialogue_message_service", self.dialogue_message_service, "service", "local"),
            ("clarification_manager", self.clarification_manager, "service", "local"),
            ("response_composer", self.response_composer, "service", "deterministic"),
            ("response_verifier", self.response_verifier, "service", "local"),
            (
                "response_delivery_service",
                self.response_delivery_service,
                "service",
                "local",
            ),
            ("explanation_repository", self.explanation_repository, "repository", "postgres"),
            ("explanation_builder", self.explanation_builder, "service", "deterministic"),
            ("trace_narrative_builder", self.trace_narrative_builder, "service", "deterministic"),
            ("why_not_service", self.why_not_service, "service", "deterministic"),
            ("explanation_verifier", self.explanation_verifier, "service", "deterministic"),
            (
                "explanation_feedback_service",
                self.explanation_feedback_service,
                "service",
                "local",
            ),
            ("dialogue_feedback_service", self.dialogue_feedback_service, "service", "local"),
            (
                "dialogue_memory_handoff_service",
                self.dialogue_memory_handoff_service,
                "service",
                "local",
            ),
            ("dialogue_turn_service", self.dialogue_turn_service, "service", "local"),
            ("execution_orchestrator", self.execution_orchestrator, "execution", "local"),
            ("visual_projection_service", self.visual_projection_service, "visual", "local"),
            (
                "observability_service",
                self.observability_service,
                "observability",
                self.adapter_config.observability_adapter,
            ),
            ("replay_service", self.replay_service, "service", "local"),
            ("regression_service", self.regression_service, "regression", "local"),
            ("capability_registry", self.capability_registry, "service", "local"),
            ("capability_service", self.capability_service, "service", "local"),
            ("mcp_service", self.mcp_service, "service", "mcp"),
            ("mcp_runtime_adapter", self.mcp_runtime_adapter, "adapter", "mcp"),
            ("mcp_capability_adapter", self.mcp_capability_adapter, "adapter", "mcp"),
            ("identity_service", self.identity_service, "service", "local"),
            ("scope_service", self.scope_service, "service", "local"),
            ("belief_repository", self.belief_repository, "repository", "postgres"),
            ("claim_extractor", self.claim_extractor, "service", "deterministic"),
            ("belief_service", self.belief_service, "service", "local"),
            ("belief_support_service", self.belief_support_service, "service", "local"),
            (
                "belief_contradiction_service",
                self.belief_contradiction_service,
                "service",
                "local",
            ),
            ("belief_query_service", self.belief_query_service, "service", "local"),
            (
                "truth_maintenance_service",
                self.truth_maintenance_service,
                "service",
                "deterministic",
            ),
            ("concept_repository", self.concept_repository, "repository", "postgres"),
            ("concept_service", self.concept_service, "service", "local"),
            ("entity_repository", self.entity_repository, "repository", "postgres"),
            ("entity_service", self.entity_service, "service", "local"),
            ("entity_query_service", self.entity_query_service, "service", "local"),
            ("entity_alias_service", self.entity_alias_service, "service", "local"),
            ("reference_link_service", self.reference_link_service, "service", "local"),
            (
                "entity_mention_extractor",
                self.entity_mention_extractor,
                "service",
                "deterministic",
            ),
            ("entity_resolver", self.entity_resolver, "service", "deterministic"),
            ("entity_merge_service", self.entity_merge_service, "service", "local"),
            ("entity_split_service", self.entity_split_service, "service", "local"),
            ("situation_repository", self.situation_repository, "repository", "postgres"),
            ("situation_service", self.situation_service, "service", "local"),
            ("state_atom_service", self.state_atom_service, "service", "local"),
            ("situation_normalizer", self.situation_normalizer, "service", "deterministic"),
            (
                "state_transition_detector",
                self.state_transition_detector,
                "service",
                "deterministic",
            ),
            ("situation_projector", self.situation_projector, "service", "deterministic"),
            (
                "temporal_state_window_service",
                self.temporal_state_window_service,
                "service",
                "local",
            ),
            ("context_continuity_service", self.context_continuity_service, "service", "local"),
            ("situation_query_service", self.situation_query_service, "service", "local"),
            ("outcome_repository", self.outcome_repository, "repository", "postgres"),
            ("expected_effect_service", self.expected_effect_service, "service", "local"),
            ("observed_effect_collector", self.observed_effect_collector, "service", "local"),
            ("outcome_service", self.outcome_service, "service", "local"),
            ("effect_verifier", self.effect_verifier, "service", "deterministic"),
            ("causal_attribution_service", self.causal_attribution_service, "service", "local"),
            ("outcome_feedback_service", self.outcome_feedback_service, "service", "local"),
            ("outcome_query_service", self.outcome_query_service, "service", "local"),
            ("self_model_repository", self.self_model_repository, "repository", "postgres"),
            ("self_model_profile_service", self.self_model_profile_service, "service", "local"),
            ("self_description_service", self.self_description_service, "service", "local"),
            (
                "capability_awareness_service",
                self.capability_awareness_service,
                "service",
                "local",
            ),
            (
                "limitation_ledger_service",
                self.limitation_ledger_service,
                "service",
                "local",
            ),
            ("confidence_calibrator", self.confidence_calibrator, "service", "deterministic"),
            ("self_assessment_service", self.self_assessment_service, "service", "local"),
            (
                "introspection_snapshot_service",
                self.introspection_snapshot_service,
                "service",
                "local",
            ),
            (
                "learning_synthesis_repository",
                self.learning_synthesis_repository,
                "repository",
                "postgres",
            ),
            ("experience_service", self.experience_service, "service", "local"),
            ("pattern_miner", self.pattern_miner, "service", "deterministic"),
            ("lesson_service", self.lesson_service, "service", "local"),
            ("learning_synthesizer", self.learning_synthesizer, "service", "deterministic"),
            ("skill_suggestion_service", self.skill_suggestion_service, "service", "local"),
            (
                "regression_suggestion_service",
                self.regression_suggestion_service,
                "service",
                "local",
            ),
            ("learning_query_service", self.learning_query_service, "service", "local"),
            ("decision_repository", self.decision_repository, "repository", "postgres"),
            ("decision_frame_service", self.decision_frame_service, "service", "local"),
            ("decision_option_service", self.decision_option_service, "service", "local"),
            ("utility_profile_service", self.utility_profile_service, "service", "local"),
            ("option_evaluator", self.option_evaluator, "service", "deterministic"),
            ("tradeoff_matrix_service", self.tradeoff_matrix_service, "service", "deterministic"),
            ("counterfactual_simulator", self.counterfactual_simulator, "service", "deterministic"),
            ("decision_journal_service", self.decision_journal_service, "service", "local"),
            (
                "decision_recommendation_service",
                self.decision_recommendation_service,
                "service",
                "deterministic",
            ),
            ("evidence_service", self.evidence_service, "service", "local"),
            ("grounding_repository", self.grounding_repository, "repository", "postgres"),
            ("grounding_source_service", self.grounding_source_service, "service", "local"),
            ("citation_service", self.citation_service, "service", "local"),
            ("statement_splitter", self.statement_splitter, "service", "deterministic"),
            ("support_checker", self.support_checker, "service", "deterministic"),
            ("citation_mapper", self.citation_mapper, "service", "deterministic"),
            ("grounding_verifier", self.grounding_verifier, "service", "deterministic"),
            ("source_coverage_service", self.source_coverage_service, "service", "local"),
            ("grounding_query_service", self.grounding_query_service, "service", "local"),
            ("module_runtime_gateway", self.module_runtime_gateway, "service", "local"),
            ("goal_service", self.goal_service, "service", "local"),
            ("task_service", self.task_service, "service", "local"),
            ("schedule_service", self.schedule_service, "service", "local"),
            (
                "workflow_service",
                self.workflow_service,
                "service",
                self.settings.workflow_engine_adapter,
            ),
            ("local_workflow_engine", self.local_workflow_engine, "service", "local"),
            ("workflow_scheduler", self.workflow_scheduler, "service", "local"),
            ("workflow_worker", self.workflow_worker, "service", "local"),
            ("temporal_adapter", self.temporal_adapter, "adapter", "temporal"),
            (
                "cognitive_cycle_repository",
                self.cognitive_cycle_repository,
                "repository",
                "postgres",
            ),
            ("maintenance_service", self.maintenance_service, "service", "local"),
            (
                "sleep_consolidation_service",
                self.sleep_consolidation_service,
                "service",
                "local",
            ),
            (
                "cognitive_cycle_orchestrator",
                self.cognitive_cycle_orchestrator,
                "service",
                "local",
            ),
            (
                "event_reaction_repository",
                self.event_reaction_repository,
                "repository",
                "postgres",
            ),
            ("event_trigger_matcher", self.event_trigger_matcher, "service", "local"),
            (
                "event_reaction_action_runner",
                self.event_reaction_action_runner,
                "service",
                "local",
            ),
            ("event_dead_letter_service", self.event_dead_letter_service, "service", "local"),
            ("event_reaction_router", self.event_reaction_router, "service", "local"),
            (
                "event_reaction_replay_service",
                self.event_reaction_replay_service,
                "service",
                "local",
            ),
            ("command_repository", self.command_repository, "repository", "postgres"),
            ("command_bus", self.command_bus, "service", "local"),
            ("command_handler_registry", self.command_handler_registry, "service", "local"),
            ("idempotency_service", self.idempotency_service, "service", "local"),
            ("outbox_service", self.outbox_service, "service", "local"),
            ("inbox_service", self.inbox_service, "service", "local"),
            ("processing_lease_service", self.processing_lease_service, "service", "local"),
            ("consistency_checker", self.consistency_checker, "service", "local"),
            ("api_request_audit_service", self.api_request_audit_service, "api", "local"),
            ("openapi_hygiene_checker", self.openapi_hygiene_checker, "api", "local"),
            ("scenario_runner", self.scenario_runner, "service", "local"),
            ("scenario_comparator", self.scenario_comparator, "service", "deterministic"),
            ("demo_fixture_service", self.demo_fixture_service, "service", "local"),
            ("release_baseline_service", self.release_baseline_service, "service", "local"),
            ("performance_repository", self.performance_repository, "repository", "postgres"),
            ("benchmark_runner", self.benchmark_runner, "service", "local"),
            (
                "capacity_baseline_service",
                self.capacity_baseline_service,
                "service",
                "local",
            ),
            ("resource_budget_service", self.resource_budget_service, "service", "local"),
            (
                "performance_regression_comparator",
                self.performance_regression_comparator,
                "service",
                "local",
            ),
            (
                "performance_summary_service",
                self.performance_summary_service,
                "service",
                "local",
            ),
            (
                "security_baseline_repository",
                self.security_baseline_repository,
                "repository",
                "postgres",
            ),
            (
                "runtime_config_repository",
                self.runtime_config_repository,
                "repository",
                "postgres",
            ),
            ("config_profile_service", self.config_profile_service, "service", "local"),
            (
                "feature_flag_override_service",
                self.feature_flag_override_service,
                "service",
                "local",
            ),
            ("config_snapshot_service", self.config_snapshot_service, "service", "local"),
            ("config_validator", self.config_validator, "service", "local"),
            (
                "runtime_config_status_service",
                self.runtime_config_status_service,
                "service",
                "local",
            ),
            ("resilience_repository", self.resilience_repository, "repository", "postgres"),
            ("dependency_health_service", self.dependency_health_service, "service", "local"),
            ("retry_policy_service", self.retry_policy_service, "service", "local"),
            ("circuit_breaker_service", self.circuit_breaker_service, "service", "local"),
            ("degraded_mode_service", self.degraded_mode_service, "service", "local"),
            ("fault_injection_service", self.fault_injection_service, "service", "local"),
            ("resilience_test_runner", self.resilience_test_runner, "service", "local"),
            ("secret_scanner", self.secret_scanner, "service", "local"),
            ("config_hardening_checker", self.config_hardening_checker, "service", "local"),
            ("api_exposure_checker", self.api_exposure_checker, "service", "local"),
            ("adapter_risk_checker", self.adapter_risk_checker, "service", "local"),
            (
                "dependency_metadata_scanner",
                self.dependency_metadata_scanner,
                "service",
                "local",
            ),
            ("threat_model_service", self.threat_model_service, "service", "local"),
            ("security_control_catalog", self.security_control_catalog, "service", "local"),
            ("hardening_gate_service", self.hardening_gate_service, "service", "local"),
            ("versioning_repository", self.versioning_repository, "repository", "postgres"),
            ("feature_registry_service", self.feature_registry_service, "service", "local"),
            ("version_manifest_service", self.version_manifest_service, "service", "local"),
            (
                "compatibility_matrix_service",
                self.compatibility_matrix_service,
                "service",
                "local",
            ),
            ("migration_baseline_service", self.migration_baseline_service, "service", "local"),
            ("release_artifact_service", self.release_artifact_service, "service", "local"),
            ("sdk_compatibility_service", self.sdk_compatibility_service, "service", "local"),
            ("freeze_gate_service", self.freeze_gate_service, "service", "local"),
            (
                "release_package_repository",
                self.release_package_repository,
                "repository",
                "postgres",
            ),
            (
                "release_package_source_manifest_service",
                self.release_package_source_manifest_service,
                "service",
                "local",
            ),
            (
                "release_package_sbom_service",
                self.release_package_sbom_service,
                "service",
                "local",
            ),
            ("release_package_validator", self.release_package_validator, "service", "local"),
            ("release_handoff_service", self.release_handoff_service, "service", "local"),
            ("release_packager", self.release_packager, "service", "local"),
            ("backup_repository", self.backup_repository, "repository", "postgres"),
            ("instruction_repository", self.instruction_repository, "repository", "postgres"),
            ("instruction_service", self.instruction_service, "service", "local"),
            ("instruction_resolver", self.instruction_resolver, "service", "local"),
            (
                "instruction_conflict_detector",
                self.instruction_conflict_detector,
                "service",
                "local",
            ),
            ("preference_service", self.preference_service, "service", "local"),
            (
                "preference_learning_service",
                self.preference_learning_service,
                "service",
                "local",
            ),
            ("constraint_service", self.constraint_service, "service", "local"),
            ("style_profile_service", self.style_profile_service, "service", "local"),
            ("backup_resource_readers", self.backup_resource_readers, "service", "local"),
            ("backup_exporter", self.backup_exporter, "service", "local"),
            ("restore_preview_service", self.restore_preview_service, "service", "local"),
            ("restore_service", self.restore_service, "service", "local"),
            ("backup_validator", self.backup_validator, "service", "local"),
            (
                "resource_registry_repository",
                self.resource_registry_repository,
                "repository",
                "postgres",
            ),
            (
                "resource_descriptor_factory",
                self.resource_descriptor_factory,
                "service",
                "deterministic",
            ),
            ("resource_scanner", self.resource_scanner, "service", "local"),
            (
                "resource_registry_service",
                self.resource_registry_service,
                "service",
                "local",
            ),
            ("resource_link_service", self.resource_link_service, "service", "local"),
            ("backlink_service", self.backlink_service, "service", "local"),
            ("registry_query_service", self.registry_query_service, "service", "local"),
            ("reference_validator", self.reference_validator, "service", "deterministic"),
            (
                "registry_snapshot_service",
                self.registry_snapshot_service,
                "service",
                "deterministic",
            ),
            ("registry_rebuilder", self.registry_rebuilder, "service", "deterministic"),
            (
                "contract_registry_repository",
                self.contract_registry_repository,
                "repository",
                "postgres",
            ),
            ("contract_scanner", self.contract_scanner, "service", "deterministic"),
            (
                "interface_inventory_service",
                self.interface_inventory_service,
                "service",
                "local",
            ),
            (
                "contract_snapshot_service",
                self.contract_snapshot_service,
                "service",
                "deterministic",
            ),
            (
                "compatibility_rule_service",
                self.compatibility_rule_service,
                "service",
                "local",
            ),
            ("compatibility_scanner", self.compatibility_scanner, "service", "deterministic"),
            ("migration_note_service", self.migration_note_service, "service", "local"),
            (
                "contract_registry_report_service",
                self.contract_registry_report_service,
                "service",
                "local",
            ),
            (
                "contract_registry_query_service",
                self.contract_registry_query_service,
                "service",
                "local",
            ),
            (
                "extension_registry_repository",
                self.extension_registry_repository,
                "repository",
                "postgres",
            ),
            (
                "extension_manifest_validator",
                self.extension_manifest_validator,
                "service",
                "deterministic",
            ),
            ("extension_package_service", self.extension_package_service, "service", "local"),
            (
                "extension_capability_service",
                self.extension_capability_service,
                "service",
                "local",
            ),
            (
                "extension_dependency_service",
                self.extension_dependency_service,
                "service",
                "local",
            ),
            (
                "extension_compatibility_gate",
                self.extension_compatibility_gate,
                "service",
                "deterministic",
            ),
            ("extension_intake_service", self.extension_intake_service, "service", "local"),
            ("extension_review_service", self.extension_review_service, "service", "local"),
            (
                "extension_install_plan_service",
                self.extension_install_plan_service,
                "service",
                "local",
            ),
            ("extension_query_service", self.extension_query_service, "service", "local"),
            (
                "module_binding_repository",
                self.module_binding_repository,
                "repository",
                "postgres",
            ),
            ("module_slot_service", self.module_slot_service, "service", "local"),
            (
                "capability_binding_service",
                self.capability_binding_service,
                "service",
                "local",
            ),
            (
                "binding_conflict_service",
                self.binding_conflict_service,
                "service",
                "deterministic",
            ),
            ("binding_validator", self.binding_validator, "service", "deterministic"),
            (
                "module_mount_plan_service",
                self.module_mount_plan_service,
                "service",
                "local",
            ),
            (
                "route_binding_preview_service",
                self.route_binding_preview_service,
                "service",
                "local",
            ),
            (
                "module_binding_query_service",
                self.module_binding_query_service,
                "service",
                "local",
            ),
            (
                "module_activation_repository",
                self.module_activation_repository,
                "repository",
                "postgres",
            ),
            (
                "module_activation_request_service",
                self.module_activation_request_service,
                "service",
                "local",
            ),
            ("activation_blocker_service", self.activation_blocker_service, "service", "local"),
            (
                "activation_gate_service",
                self.activation_gate_service,
                "service",
                "deterministic",
            ),
            ("activation_review_service", self.activation_review_service, "service", "local"),
            ("activation_plan_service", self.activation_plan_service, "service", "local"),
            (
                "runtime_registration_preview_service",
                self.runtime_registration_preview_service,
                "service",
                "local",
            ),
            (
                "module_activation_query_service",
                self.module_activation_query_service,
                "service",
                "local",
            ),
            (
                "module_mock_repository",
                self.module_mock_repository,
                "repository",
                "postgres",
            ),
            (
                "module_mock_schema_adapter",
                self.module_mock_schema_adapter,
                "service",
                "deterministic",
            ),
            (
                "module_mock_plan_service",
                self.module_mock_plan_service,
                "service",
                "deterministic",
            ),
            (
                "module_mock_profile_service",
                self.module_mock_profile_service,
                "service",
                "local",
            ),
            (
                "module_mock_simulator",
                self.module_mock_simulator,
                "service",
                "deterministic",
            ),
            (
                "module_mock_finding_service",
                self.module_mock_finding_service,
                "service",
                "local",
            ),
            (
                "module_mock_query_service",
                self.module_mock_query_service,
                "service",
                "local",
            ),
            (
                "model_provider_hardening_repository",
                self.model_provider_hardening_repository,
                "repository",
                "postgres",
            ),
            (
                "model_provider_profile_service",
                self.model_provider_profile_service,
                "service",
                "local",
            ),
            (
                "prompt_egress_guard",
                self.prompt_egress_guard,
                "service",
                "deterministic",
            ),
            (
                "model_provider_simulator",
                self.model_provider_simulator,
                "service",
                "deterministic",
            ),
            (
                "model_provider_readiness_service",
                self.model_provider_readiness_service,
                "service",
                "local",
            ),
            (
                "model_provider_blocker_service",
                self.model_provider_blocker_service,
                "service",
                "local",
            ),
            (
                "model_provider_query_service",
                self.model_provider_query_service,
                "service",
                "local",
            ),
            ("conformance_repository", self.conformance_repository, "repository", "postgres"),
            (
                "conformance_schema_checker",
                self.conformance_schema_checker,
                "service",
                "deterministic",
            ),
            (
                "conformance_profile_service",
                self.conformance_profile_service,
                "service",
                "local",
            ),
            (
                "capability_test_vector_service",
                self.capability_test_vector_service,
                "service",
                "local",
            ),
            (
                "mock_invocation_simulator",
                self.mock_invocation_simulator,
                "service",
                "deterministic",
            ),
            ("conformance_runner", self.conformance_runner, "service", "deterministic"),
            (
                "conformance_finding_service",
                self.conformance_finding_service,
                "service",
                "local",
            ),
            (
                "readiness_assessment_service",
                self.readiness_assessment_service,
                "service",
                "deterministic",
            ),
            (
                "conformance_query_service",
                self.conformance_query_service,
                "service",
                "local",
            ),
            ("golden_path_repository", self.golden_path_repository, "repository", "postgres"),
            (
                "golden_path_assertion_engine",
                self.golden_path_assertion_engine,
                "service",
                "deterministic",
            ),
            (
                "golden_path_scenario_catalog",
                self.golden_path_scenario_catalog,
                "service",
                "local",
            ),
            (
                "golden_path_fixture_service",
                self.golden_path_fixture_service,
                "service",
                "local",
            ),
            (
                "golden_path_report_service",
                self.golden_path_report_service,
                "service",
                "local",
            ),
            (
                "golden_path_query_service",
                self.golden_path_query_service,
                "service",
                "local",
            ),
            ("golden_path_runner", self.golden_path_runner, "service", "deterministic"),
            (
                "golden_path_release_smoke",
                self.golden_path_release_smoke,
                "service",
                "deterministic",
            ),
            ("bootstrap_repository", self.bootstrap_repository, "repository", "postgres"),
            (
                "bootstrap_profile_service",
                self.bootstrap_profile_service,
                "service",
                "local",
            ),
            ("seed_bundle_service", self.seed_bundle_service, "service", "local"),
            ("seed_executor", self.seed_executor, "service", "deterministic"),
            ("setup_doctor", self.setup_doctor, "service", "deterministic"),
            ("setup_report_service", self.setup_report_service, "service", "local"),
            ("bootstrap_runner", self.bootstrap_runner, "service", "deterministic"),
            ("bootstrap_query_service", self.bootstrap_query_service, "service", "local"),
            ("lifecycle_repository", self.lifecycle_repository, "repository", "postgres"),
            ("lifecycle_policy_service", self.lifecycle_policy_service, "service", "local"),
            ("retention_classifier", self.retention_classifier, "service", "deterministic"),
            ("lifecycle_evaluator", self.lifecycle_evaluator, "service", "deterministic"),
            ("archive_planner", self.archive_planner, "service", "local"),
            ("redaction_planner", self.redaction_planner, "service", "local"),
            ("purge_preview_service", self.purge_preview_service, "service", "local"),
            ("lifecycle_review_service", self.lifecycle_review_service, "service", "local"),
            ("lifecycle_report_service", self.lifecycle_report_service, "service", "local"),
            ("lifecycle_query_service", self.lifecycle_query_service, "service", "local"),
            ("operator_repository", self.operator_repository, "repository", "postgres"),
            (
                "operator_status_card_builder",
                self.operator_status_card_builder,
                "service",
                "local",
            ),
            (
                "operator_queue_summary_builder",
                self.operator_queue_summary_builder,
                "service",
                "local",
            ),
            (
                "operator_action_center_service",
                self.operator_action_center_service,
                "service",
                "local",
            ),
            (
                "operator_readiness_aggregator",
                self.operator_readiness_aggregator,
                "service",
                "local",
            ),
            ("operator_runbook_registry", self.operator_runbook_registry, "service", "local"),
            (
                "operator_control_tower_service",
                self.operator_control_tower_service,
                "service",
                "local",
            ),
            ("operator_snapshot_service", self.operator_snapshot_service, "service", "local"),
            ("reflection_service", self.reflection_service, "service", "local"),
            ("skill_service", self.skill_service, "service", "local"),
            ("snapshot_service", self.snapshot_service, "service", "local"),
        )
        for name, service, service_type, adapter in service_specs:
            self._services[name] = service
            self.service_registry.register_service(
                name,
                cast(KernelServiceType, service_type),
                adapter,
                status="healthy",
                health={"assembled": True},
            )
