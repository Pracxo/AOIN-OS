# ADR 0049: Decision Frame Manager and Counterfactual Simulator

## Status

Accepted for AION Brain v0.1.

## Decision

AION Brain adds a Decision Frame Manager, Option Evaluator, Tradeoff Matrix,
Counterfactual Simulator, and Decision Journal.

Decisions never execute selected options. They recommend, evaluate, project,
and record. Execution remains owned by explicit execution APIs guarded by
policy, risk, approval, and autonomy.

v0.1 uses deterministic utility scoring. Counterfactual simulation projects
only declared generic option effects and never mutates source records.

## Reason

AION needs a generic way to choose between possible next actions before
stronger planning and autonomy layers can rely on those choices.

## Consequences

Planner and Dialogue can request decision frames without owning decision
semantics. Operator surfaces can inspect open frames, recommendations, and
failed projections. Future external decision engines can be added behind
adapters without changing AION public contracts.

## Constraints

No external calls. No model evaluation. No automatic execution. No automatic
approval. No domain-specific utility weights or option types in Brain core.
