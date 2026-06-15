# ADR 0004: LangGraph Runtime Adapter

## Decision

AION Brain v0.1 uses LangGraph behind `BrainRuntimeAdapter` for the first
deterministic runtime graph.

## Reason

The Brain loop is naturally stateful: event, intent, context, plan, policy
decisions, and trace are produced in order. LangGraph provides a small graph
runtime for coordinating those transitions without introducing model calls or
tool execution.

## Constraint

AION public contracts remain independent. LangGraph imports, graph builders,
compiled graph objects, and node internals must stay inside
`runtime/langgraph_runtime.py`.

## Consequence

LangGraph can be replaced later by another runtime implementation without
changing public AION APIs. The runtime boundary remains:

```text
AIONEvent -> DecisionTrace
```
