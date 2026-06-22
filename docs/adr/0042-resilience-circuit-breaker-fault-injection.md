# 0042: Resilience Control Plane, Circuit Breakers, and Fault Injection

## Decision

AION Brain adds a local Resilience Control Plane for dependency health records,
bounded retry policy metadata, circuit breaker state, degraded mode events,
fault injection rules, and deterministic resilience test runs.

Fault injection is disabled by default and remains local. Circuit breakers and
retry policies are Brain-owned contracts. The freeze gate may consume the
resilience test report before a local release.

## Reason

AION needs explicit failure posture before adding more runtime surfaces. The
Brain must know when an adapter is unavailable, when a call should be blocked,
when a fallback is active, and whether the local stack is fit for release.

## Consequences

Services can consult retry and breaker metadata without owning resilience
policy. Optional adapter failures can mark degraded mode without crashing the
Brain loop. Local operators can run a deterministic resilience check through
HTTP, SDK, CLI, or script.

## Constraints

- No background retry workers are added in v0.1.
- No external failover, cloud remediation, or deployment behavior is added.
- Fault injection is disabled by default.
- Fault injection rules are local records and do not perform external calls.
- Degraded mode records state and constraints; it does not auto-remediate.
- Public APIs expose AION contracts only, not infrastructure client objects.
- Resilience logic remains Brain-generic and domain-neutral.
