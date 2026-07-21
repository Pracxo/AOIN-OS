# AION-192 Hierarchical Counterfactual Planning

## Task Purpose

AION-192 implements a local, offline hierarchical counterfactual planning core for the AION Cognitive Architecture Program. It creates immutable planning records that decompose a goal into strategies, milestones, task plans, and proposal-only action references, then ranks bounded counterfactual branches using the existing predictive world model.

## Authorization

- Program ID: `AION-COGNITIVE-ARCHITECTURE-001`
- Authorization ID: `AION-191-CA-0005`
- Authorized task: `AION-192`
- Candidate ID: `hierarchical-counterfactual-planning-core`
- Scope: `hierarchical-counterfactual-goal-strategy-milestone-task-action-planning-core`
- Branch: `phase/cognitive-counterfactual-planning`
- Formal closeout task: `AION-193`
- Evaluation ID: `AION-HCPE-001`

## Role Comparison

AION-192 is an implementation task, not an evaluation or authorization task. It consumes the active planning authorization by adding proposal-only planning contracts, local deterministic planning services, tests, examples, and release gates. It does not close `AION-191-CA-0005`; AION-193 performs the formal evaluation and closeout.

## Source Boundaries

Allowed source paths are limited to:

- `services/brain-api/src/aion_brain/planning/`
- `services/brain-api/src/aion_brain/contracts/planning.py`
- `services/brain-api/tests/test_cognitive_counterfactual_planning.py`
- `services/brain-api/tests/test_cognitive_counterfactual_planning_no_runtime_effect.py`
- `docs/cognitive-architecture/`
- `examples/cognitive-architecture/`
- `scripts/cognitive-counterfactual-planning-check.sh`
- `scripts/cognitive-counterfactual-planning-no-go-regression.sh`
- `scripts/lib/cognitive_architecture_governance.py`

Prohibited paths remain `.github/workflows/`, migrations, package files and lockfiles, API routes, git automation, pull-request automation, deployment code, connectors, model providers, credentials, and SDK source.

## Required Contracts

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

## Required Services

- `StrategicPlanner`
- `TacticalPlanner`
- `ActionPlanner`
- `CounterfactualPlanEvaluator`
- `PlanRiskEvaluator`
- `ReversibilityEvaluator`
- `ResourceBudgetEvaluator`
- `ReplanningService`

## Algorithm

The planner evaluates candidate `StrategyOption` records by creating proposal-only `ActionProposal` entries, simulating bounded branches with the existing predictive world model, deriving expected outcomes, and scoring each branch across:

- `expected_goal_progress`
- `expected_information_gain`
- `confidence`
- `risk`
- `resource_cost`
- `reversibility`
- `policy_eligibility`
- `uncertainty`
- `time_horizon`

Hard policy failures, safety failures, irreversible unsafe proposals, budget overruns, and fail-closed rollouts override utility gain. Only an unblocked, policy-eligible branch may be selected.

## Required Tests

- `services/brain-api/tests/test_cognitive_counterfactual_planning.py`
- `services/brain-api/tests/test_cognitive_counterfactual_planning_no_runtime_effect.py`

The tests cover immutable fingerprints, proposal-only action records, deterministic replay, safe branch selection, policy and safety override behavior, replanning decisions, script execution under pytest context, and absence of runtime wiring.

## Required Gates

- `scripts/cognitive-counterfactual-planning-no-go-regression.sh`
- `scripts/cognitive-counterfactual-planning-check.sh`
- inherited memory-consolidation closeout gate
- docs check
- final docs audit
- domain-drift validation
- boundary check
- repository health
- full repository check
- `git diff --check`

## Security Invariants

- No API route is added.
- No kernel registration is added.
- No background planning loop is added.
- No action execution is enabled.
- No external action dispatch is performed.
- No network calls are introduced.
- No connector calls are introduced.
- No model-provider calls are introduced.
- No credential, token, prompt, hidden reasoning, raw user message, source patch, raw diff, or private data storage is introduced.
- No source rewrite, git mutation, deployment, production exposure, or model-weight change is introduced.
- The protected `aion-v0.1.0` tag remains unchanged.
- No v0.2 tag or release is created.

## Performance Limits

Planning remains deterministic and bounded to local in-memory data structures. Counterfactual rollouts use the existing world-model depth limit and do not run background work. Resource counters for network, connector, model-provider, git, source-rewrite, deployment, production exposure, and action execution remain zero.

## Completion Conditions

- AION-192 contracts and services exist under the allowed paths.
- The implementation evidence example validates.
- The program ledger records AION-192 as implemented pending AION-193 evaluation.
- The authorization ledger updates `AION-191-CA-0005` to implemented pending AION-193 evaluation while keeping it active, non-reusable, not expired, and not closed.
- Focused tests and no-go gates pass.
- Full repository validation passes before merge.

## Next Task

AION-193 evaluates AION-192 under `AION-HCPE-001`, closes `AION-191-CA-0005` if the planning implementation passes, and authorizes the next active information acquisition implementation only if all no-runtime and hard benchmark conditions hold.
