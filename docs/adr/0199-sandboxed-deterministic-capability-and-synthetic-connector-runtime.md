# ADR 0199: Sandboxed Deterministic Capability and Synthetic Connector Runtime

## Status
Accepted for AION-235 implementation pending AION-236 evaluation and closeout.

## Context
AION-234-SRI-0003 authorized AION-235 to implement a sandboxed capability runtime after AION-SRIPE-002 passed. Model output remains untrusted proposal material and cannot trigger execution or authorize capabilities.

## Decision
Implement a closed deterministic in-memory runtime with explicit operator capability selection, immutable capability and connector manifests, restricted input and output schemas, deterministic execution plans, policy/risk/guardrail/approval bindings, zero-external-effect budgets, parent kill-switch composition, in-memory sandbox admission, static dispatch, immutable receipts, provenance, audit, observability, health, integrity and rollback.

The runtime may execute only six reference capabilities and two synthetic reference connector operations. The synthetic connector is fixture-backed and in-memory. Write preview applies no mutation.

## Consequences
AION OS can execute closed schema-validated reference operations locally under authenticated operator control. No external connector, real tool, network, filesystem, process, shell, subprocess, browser, dynamic import, eval, exec, credential, token, production memory, production policy, belief mutation, source rewrite, deployment or model training capability is enabled. AION-234-SRI-0003 remains active pending AION-236.
