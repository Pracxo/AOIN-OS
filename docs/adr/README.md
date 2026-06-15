# Architecture Decision Records

Every architecture-changing Codex task must add or update an ADR.

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
