# 0085: Local Auth Contract and Dev Identity Simulation

## Status

Accepted

## Context

The future Operator Console needs identity and role semantics before production login exists. AION-093 defined the design only. AION-094 adds a safe local contract and simulation layer.

## Decision

Add local auth contracts, dev-only identity simulation, role-aware console filtering, local auth status, and a local auth safety audit.

Decision: no production auth.

Decision: no credentials.

Decision: no sessions.

Decision: no external identity provider.

Decision: role-aware console filtering is read-only.

## Constraints

No login. No credential storage. No production auth claim. No privileged bypass.

The local auth context cannot grant write, execution, activation, external call, provider enablement, or hard-delete behavior.

## Consequences

Later auth work can build from explicit contracts, policy vocabulary, audit checks, SDK access, and CLI read-only status commands without changing the frozen v0.1 release baseline.
