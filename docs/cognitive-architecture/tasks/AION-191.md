# AION-191 Consolidation Evaluation and Planning Authorization

## Task Purpose

AION-191 evaluates the AION-190 memory consolidation and replay implementation
under evaluation `AION-MCRE-001`. The evaluation closes implementation
authorization `AION-189-CA-0004` on PASS and creates the next bounded
implementation authorization, `AION-191-CA-0005`, for AION-192.

This task is an evaluation and authorization checkpoint only. It records
deterministic local evidence and does not implement planning source, add API
runtime paths, enable background loops, call external services, execute actions,
or change model weights.

## Evaluation

- Evaluation ID: `AION-MCRE-001`
- Evaluated task: `AION-190`
- Implementation PR: `101`
- Implementation merge commit:
  `a1dcd0826a48ebc2e953e61c4b5ed522da2bcdd1`
- Evidence artifact:
  `examples/cognitive-architecture/aion-191-memory-consolidation-evaluation.json`
- Result: `PASS`
- Decision:
  `MEMORY_CONSOLIDATION_EVALUATION_PASS_AUTHORIZE_COUNTERFACTUAL_PLANNING`

The evaluation uses local synthetic replay fixtures to validate episodic recall,
semantic generalization, duplicate reduction, contradiction preservation,
retention, policy-evidenced non-destructive forgetting, catastrophic-forgetting
avoidance, procedural candidate safety, replay determinism, and zero automatic
promotion.

## Closed Authorization

Authorization `AION-189-CA-0004` is closed by AION-191 after AION-190 merged
and passed evaluation. The closed authorization is consumed by AION-190,
expired, non-reusable, and retained in the authorization ledger for audit.

The closeout record binds AION-190 to PR `101` and merge commit
`a1dcd0826a48ebc2e953e61c4b5ed522da2bcdd1`.

## Hard PASS Conditions

- Retained critical memories rate: `1.0`
- Duplicate reduction rate: `1.0`
- Contradiction loss rate: `0.0`
- Catastrophic forgetting rate: `0.0`
- Provenance coverage: `1.0`
- Unauthorized promotion count: `0`
- Deterministic replay rate: `1.0`
- Forbidden side effects: `0`

## New Authorization

AION-191 creates active implementation authorization `AION-191-CA-0005`.

- Authorized task: `AION-192`
- Candidate ID: `hierarchical-counterfactual-planning-core`
- Scope:
  `hierarchical-counterfactual-goal-strategy-milestone-task-action-planning-core`
- Workstream: `counterfactual-planning`
- Closeout task: `AION-193`
- Parent evaluation: `AION-MCRE-001`
- Parent PR: `101`
- Parent commit: `a1dcd0826a48ebc2e953e61c4b5ed522da2bcdd1`

The authorization is active, not consumed, not expired, and not reusable.

## AION-192 Scope

AION-192 may implement only hierarchical counterfactual planning contracts and
local deterministic planning services. The required contracts are:

- `StrategicGoal`
- `StrategyOption`
- `MilestonePlan`
- `TaskPlan`
- `ActionProposal`
- `CounterfactualBranch`
- `ExpectedOutcome`
- `PlanRisk`
- `PlanResourceEstimate`
- `PlanReversibility`
- `HierarchicalPlan`
- `ReplanningDecision`
- `PlanEvidence`

The required services are:

- `StrategicPlanner`
- `TacticalPlanner`
- `ActionPlanner`
- `CounterfactualPlanEvaluator`
- `PlanRiskEvaluator`
- `ReversibilityEvaluator`
- `ResourceBudgetEvaluator`
- `ReplanningService`

The planner may use the existing world model for bounded rollouts. Plan scores
must include expected goal progress, expected information gain, confidence,
risk, resource cost, reversibility, policy eligibility, uncertainty, and time
horizon. Hard safety and policy failures always override utility gains.

The planner produces action proposals only. It performs no action.

## Source Boundaries

AION-192 may use:

- `services/brain-api/src/aion_brain/planning/`
- `services/brain-api/src/aion_brain/contracts/planning.py`
- `services/brain-api/tests/test_cognitive_counterfactual_planning.py`
- `services/brain-api/tests/test_cognitive_counterfactual_planning_no_runtime_effect.py`
- `docs/cognitive-architecture/`
- `examples/cognitive-architecture/`
- `scripts/cognitive-counterfactual-planning-check.sh`
- `scripts/cognitive-counterfactual-planning-no-go-regression.sh`
- `scripts/lib/cognitive_architecture_governance.py`

AION-192 may not add or change package files, migrations, workflows, production
API runtime execution routes, deployment code, connector runtime paths,
model-provider runtime paths, credential storage, pull-request automation, git
mutation paths, source-rewrite runtime paths, or action execution paths.

## Required Gates

- `scripts/cognitive-memory-consolidation-closeout-check.sh`
- `scripts/cognitive-memory-consolidation-closeout-no-go-regression.sh`
- `scripts/cognitive-memory-consolidation-check.sh`
- `scripts/cognitive-memory-consolidation-no-go-regression.sh`
- `scripts/cognitive-workspace-closeout-check.sh`
- `scripts/cognitive-global-workspace-check.sh`
- `scripts/auth-design-check.sh`
- `scripts/docs-check.sh`
- `scripts/final-docs-audit.sh`
- `scripts/verify-no-domain-drift.sh`
- `scripts/boundary-check.sh`
- `scripts/check.sh`

## Security Invariants

- No production cognitive runtime is enabled.
- No API runtime execution route is added.
- No kernel runtime registration is added.
- No background planning loop is enabled.
- No external action dispatch is enabled.
- No automatic semantic or procedural promotion is allowed.
- No source rewrite is allowed.
- No model-weight update is allowed.
- No hidden memory mutation is allowed.
- No credentials, tokens, or connector runtime calls are introduced.

## Completion Conditions

AION-191 is complete when:

- AION-190 is recorded as merged and evaluated with PASS.
- `AION-189-CA-0004` is closed, consumed, expired, and non-reusable.
- `AION-191-CA-0005` is the only active cognitive implementation
  authorization.
- AION-192 scope and source boundaries are recorded in both ledgers and the
  authorization artifact.
- AION-191 tests and governance scripts pass locally and in CI.
- No runtime activation or forbidden side effect is introduced.

## Next Task

AION-192 implements the authorized
`hierarchical-counterfactual-goal-strategy-milestone-task-action-planning-core`
scope under authorization `AION-191-CA-0005`. Its closeout task is AION-193.
