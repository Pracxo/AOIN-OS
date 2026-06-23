# Architecture Decision Records

Every architecture-changing Codex task must add or update an ADR.

AION-079 is a release handoff and documentation audit task. It adds no new
runtime architecture decision and therefore has no dedicated ADR.

AION-080 freezes the local v0.1 release baseline and records that release
closure decision in ADR 0072.

## Index

- [0001: Brain-Only Scope](0001-brain-only-scope.md) - Defines Brain core scope and exclusions.
- [0002: Adapter-First Architecture](0002-adapter-first-architecture.md) - Establishes adapter boundaries for external systems.
- [0003: Adopted Intelligence Repos](0003-adopted-intelligence-repos.md) - Records adopted intelligence repository posture.
- [0004: LangGraph Runtime Adapter](0004-langgraph-runtime-adapter.md) - Keeps LangGraph behind Brain runtime boundaries.
- [0005: Semantic Memory pgvector Baseline](0005-semantic-memory-pgvector-baseline.md) - Defines initial semantic memory storage.
- [0006: Temporal Graph Memory Baseline](0006-temporal-graph-memory-baseline.md) - Defines graph memory baseline.
- [0007: Retrieval Router and Context Fusion](0007-retrieval-router-context-fusion.md) - Defines retrieval and context fusion boundaries.
- [0008: Reasoning Mesh and Model Gateway Boundary](0008-reasoning-mesh-model-gateway.md) - Defines reasoning and model routing boundaries.
- [0009: Execution Orchestrator and Plan Step State Machine](0009-execution-orchestrator-state-machine.md) - Defines generic execution state control.
- [0010: Module Bus and Capability Runtime Gateway](0010-module-bus-capability-runtime-gateway.md) - Defines module runtime gateway boundaries.
- [0011: Goal and Task Lifecycle Control Plane](0011-goal-task-lifecycle-control-plane.md) - Defines goal and task lifecycle controls.
- [0012: Reflection Engine, Skill Registry, and Learning Promotion Gates](0012-reflection-skill-registry-learning-promotion.md) - Defines reflection and skill promotion gates.
- [0013: Identity, Workspace, and Scope Control Plane](0013-identity-workspace-scope-control-plane.md) - Defines identity and scope boundaries.
- [0014: Evidence Vault and Source Grounding](0014-evidence-vault-source-grounding.md) - Defines evidence and grounding contracts.
- [0015: Visual Brain Projection and Observability Spine](0015-visual-brain-projection-observability.md) - Defines backend visual projection.
- [0016: Cognitive Replay and Regression Harness](0016-cognitive-replay-regression-harness.md) - Defines replay and regression controls.
- [0017: Kernel Assembly Composition Root](0017-kernel-assembly-composition-root.md) - Defines kernel composition root.
- [0018: Model Gateway Provider Registry and Budget Guard](0018-model-gateway-provider-registry-budget-guard.md) - Defines model provider governance.
- [0019: TurboVec Compressed Semantic Memory Adapter](0019-turbovec-compressed-semantic-memory.md) - Defines TurboVec adapter boundary.
- [0020: Graphiti Temporal Knowledge Graph Adapter](0020-graphiti-temporal-knowledge-graph-adapter.md) - Defines Graphiti adapter boundary.
- [0021: MCP Capability Protocol Adapter](0021-mcp-capability-protocol-adapter.md) - Defines MCP compatibility boundary.
- [0022: Durable Workflow Engine and Temporal Boundary](0022-durable-workflow-engine-temporal-boundary.md) - Defines workflow engine boundary.
- [0023: Risk, Guardrail, and Approval Control Plane](0023-risk-guardrail-approval-control-plane.md) - Defines risk and approval control plane.
- [0024: Memory Governance, Decay, Forgetting, and Compaction](0024-memory-governance-decay-forgetting-compaction.md) - Defines memory governance controls.
- [0025: Attention Controller, Working Memory, and Focus Manager](0025-attention-working-memory-focus-manager.md) - Defines attention and focus controls.
- [0026: Autonomy Governor Operating Modes](0026-autonomy-governor-operating-modes.md) - Defines autonomy operating modes.
- [0027: Cognitive Cycle Orchestrator](0027-cognitive-cycle-orchestrator.md) - Defines cognitive cycle orchestration.
- [0028: Event Reaction Router Subscription Control Plane](0028-event-reaction-router-subscription-control-plane.md) - Defines event reaction controls.
- [0029: Command Bus, Idempotency, Outbox, and Consistency Guard](0029-command-bus-idempotency-outbox-consistency.md) - Defines command consistency controls.
- [0030: API Contract Hardening and Error Taxonomy](0030-api-contract-hardening-error-taxonomy.md) - Defines API hardening rules.
- [0031: Python SDK and aionctl Developer Interface](0031-python-sdk-aionctl-developer-interface.md) - Defines SDK and CLI boundary.
- [0032: Module Developer Kit and Certification Harness](0032-module-developer-kit-certification-harness.md) - Defines module certification controls.
- [0033: Sandbox, Secret, and Connector Boundary](0033-sandbox-secret-connector-boundary.md) - Defines sandbox and connector boundaries.
- [0034: Policy Catalog, Permission Matrix, and Rego Test Harness](0034-policy-catalog-permission-matrix.md) - Defines policy catalog governance.
- [0035: End-to-End Golden Path and Release Baseline](0035-end-to-end-golden-path-release-baseline.md) - Defines release readiness scenarios.
- [0036: Version Manifest, Compatibility Matrix, and Freeze Gate](0036-version-manifest-compatibility-freeze-gate.md) - Defines release freeze metadata and local readiness checks.
- [0037: Local Release Package Handoff](0037-local-release-package-handoff.md) - Defines local package and handoff boundaries.
- [0038: Local State Backup and Restore Preview](0038-local-state-backup-restore-preview.md) - Defines local backup portability and restore-preview boundaries.
- [0039: Performance Benchmark and Capacity Baseline](0039-performance-benchmark-capacity-baseline.md) - Defines local performance measurement and capacity baselines.
- [0040: Security Baseline, Threat Model, and Hardening Gate](0040-security-baseline-threat-model-hardening-gate.md) - Defines local security posture checks.
- [0041: Runtime Configuration and Feature Flags](0041-runtime-configuration-feature-flags.md) - Defines safe runtime config metadata and feature override controls.
- [0042: Resilience Control Plane, Circuit Breakers, and Fault Injection](0042-resilience-circuit-breaker-fault-injection.md) - Defines local resilience posture controls.
- [0043: Tamper-Evident Audit and Provenance](0043-tamper-evident-audit-provenance.md) - Defines local audit integrity and provenance.
- [0044: Operator Control Tower and Action Center](0044-operator-control-tower-action-center.md) - Defines read-mostly operator aggregation.
- [0045: Dialogue Response and Clarification Layer](0045-dialogue-response-clarification-layer.md) - Defines backend dialogue and response contracts.
- [0046: Belief State and Truth Maintenance](0046-belief-state-truth-maintenance.md) - Defines explicit claim ledger and deterministic truth maintenance.
- [0047: Concept Registry and Entity Resolver](0047-concept-registry-entity-resolver.md) - Defines canonical references, deterministic resolution, and merge/split governance.
- [0048: Situation Model and Temporal State](0048-situation-model-temporal-state.md) - Defines generic state projection and temporal continuity.
- [0049: Decision Frame and Counterfactual Simulator](0049-decision-frame-counterfactual-simulator.md) - Defines decision records, options, and dry-run counterfactuals.
- [0050: Outcome Ledger, Effect Verification, and Learning Feedback Bridge](0050-outcome-ledger-effect-verification.md) - Defines expected effects, observed effects, verification, attribution, and feedback.
- [0051: Experience Ledger and Learning Synthesis](0051-experience-ledger-learning-synthesis.md) - Defines generic experience records, pattern mining, lessons, and review-only suggestions.
- [0052: Self Model and Capability Awareness](0052-self-model-capability-awareness.md) - Defines descriptive self-model, capability awareness, limitations, confidence calibration, and introspection.
- [0053: Explanation Engine and Trace Narratives](0053-explanation-engine-trace-narratives.md) - Defines deterministic public explanations, why-not answers, trace narratives, verification, and feedback.
- [0054: Instruction Hierarchy and Preference Ledger](0054-instruction-hierarchy-preference-ledger.md) - Defines instruction precedence, preference confirmation, style profiles, and deterministic conflict resolution.
- [0055: Grounding Citation and Source Attribution](0055-grounding-citation-source-attribution.md) - Defines deterministic source attribution, citations, verification, and coverage.
- [0056: Prompt Packet and Model Input Governance](0056-prompt-packet-model-input-governance.md) - Defines provider-neutral prompt packets, boundary checks, injection detection, and model input manifests.
- [0057: Model Output Governance](0057-model-output-governance.md) - Defines redacted model output intake, parsing, response candidates, and tool-intent capture.
- [0058: Action Proposal Broker and Execution Handoff Gate](0058-action-proposal-broker-execution-handoff.md) - Defines reviewed action proposals and explicit dry-run handoff gates.
- [0059: Run Supervision, Cancellation Gate, Timeout Policy, and Compensation Planner](0059-run-supervision-cancellation-compensation.md) - Defines generic run observation, manual control requests, timeout detection, and non-executing compensation plans.
- [0060: Internal Notification and Alert Routing](0060-internal-notification-alert-routing.md) - Defines local notification, alert, escalation, and digest boundaries.
- [0061: Temporal Scheduler, Reminder Queue, Due Item Ledger, and Local Tick Orchestrator](0061-temporal-scheduler-local-tick.md) - Defines local tick-driven scheduler records without background execution.
- [0062: Incident Correlation, Root Cause Candidates, and Recovery Review](0062-incident-correlation-root-cause-review.md) - Defines local incident grouping, candidates, and review boundaries.
- [0063: Global Resource Registry and Link Integrity](0063-global-resource-registry-link-integrity.md) - Defines the registry index, resource URI spine, and non-repairing integrity checks.
- [0064: Data Lifecycle Retention and Archive Preview](0064-data-lifecycle-retention-archive-preview.md) - Defines advisory retention classification, candidates, previews, and reports without source mutation.
- [0065: Contract Registry and Interface Drift Gate](0065-contract-registry-interface-drift.md) - Defines contract inventory, snapshots, compatibility scans, and advisory interface drift records.
- [0066: Extension Registry and Module Intake](0066-extension-registry-module-intake.md) - Defines metadata-only extension manifests, compatibility gates, reviews, and future install plans.
- [0067: Capability Binding Registry and Module Slot Manager](0067-capability-binding-module-slot-manager.md) - Defines inactive module slots, capability bindings, validation, mount plans, and route previews.
- [0068: Capability Conformance Harness and Readiness Gate](0068-capability-conformance-readiness-gate.md) - Defines schema-only conformance runs, mock invocation records, findings, and readiness assessments.
- [0069: Golden Path Scenario Harness](0069-golden-path-scenario-harness.md) - Defines local deterministic golden path runs, fixture packs, reports, and release smoke checks.
- [0070: First-Run Bootstrap and Setup Doctor](0070-first-run-bootstrap-setup-doctor.md) - Defines local first-run bootstrap, seed bundles, setup findings, and onboarding reports.
- [0071: Release Candidate Gate](0071-release-candidate-gate.md) - Defines local RC readiness matrices, gate runs, findings, evidence packs, and reports.
- [0072: v0.1 Release Freeze Baseline](0072-v0.1-release-freeze-baseline.md) - Freezes the local v0.1 release baseline and final release-closure gates.
- [0073: Post-v0.1 Module Ecosystem Strategy](0073-post-v0.1-module-ecosystem-strategy.md) - Defines post-v0.1 module strategy, activation design posture, and first metadata-only module selection.
- [0074: Module Activation Request Gate](0074-module-activation-request-gate.md) - Defines metadata-only activation requests, blockers, reviews, plans, and runtime registration previews.
- [0075: Generic Knowledge Intelligence Module Pack](0075-generic-knowledge-intelligence-module-pack.md) - Defines the first metadata-only governed module package and readiness trail.
- [0076: Deterministic Module Mock Runtime](0076-deterministic-module-mock-runtime.md) - Defines synthetic dry-run module invocation evidence and readiness boundaries.
- [0077: Model Provider Adapter Hardening](0077-model-provider-adapter-hardening.md) - Defines provider-readiness metadata, prompt egress previews, and dry-run provider simulation boundaries.
- [0078: Operator Console CLI/API-First Decision](0078-operator-console-cli-api-first-decision.md) - Defines operator console strategy before runtime UI work.
