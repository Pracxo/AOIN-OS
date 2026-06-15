# Resilience Control Plane

AION v0.1 resilience checks are local and deterministic. Fault injection is
disabled by default and does not start background workers.

The Resilience Control Plane records dependency health, bounded retry policies,
circuit breaker state, degraded mode events, fault injection rules, and local
resilience test runs. It is a Brain control plane, not an auto-remediation
system.

## Concepts

- `DependencyHealth` records one bounded dependency check.
- `RetryPolicy` defines max attempts, backoff, jitter, and retryable statuses.
- `CircuitBreaker` tracks closed, open, half-open, and disabled states.
- `DegradedModeEvent` records an explicit fallback posture for a component.
- `FaultInjectionRule` is local, deterministic, and inert unless enabled.
- `ResilienceTestRun` combines health, retry, breaker, fault, and degraded
  signals into a release-safe report.

Retry policies are metadata used by services such as the command bus and
outbox. They do not create background retry loops in v0.1.

Circuit breakers gate selected adapter boundaries. An open breaker blocks the
call locally and returns a contract-shaped failure where practical.

Degraded mode records fallback state only. It never repairs, restarts, deploys,
or changes external infrastructure.

Fault injection is disabled by default through
`AION_FAULT_INJECTION_ENABLED=false`. In v0.1, the harness returns deterministic
fault outcomes for tests and local drills without external side effects.

## Endpoints

- `GET /brain/resilience/status`
- `POST /brain/resilience/dependencies/check`
- `GET /brain/resilience/dependencies`
- `POST /brain/resilience/retry-policies`
- `GET /brain/resilience/retry-policies`
- `POST /brain/resilience/retry-policies/seed-defaults`
- `POST /brain/resilience/circuit-breakers`
- `GET /brain/resilience/circuit-breakers`
- `POST /brain/resilience/circuit-breakers/{name}/reset`
- `GET /brain/resilience/degraded`
- `POST /brain/resilience/degraded/{degraded_event_id}/resolve`
- `POST /brain/resilience/fault-rules`
- `GET /brain/resilience/fault-rules`
- `POST /brain/resilience/fault-rules/{fault_rule_id}/disable`
- `POST /brain/resilience/test/run`
- `GET /brain/resilience/test-runs/{resilience_test_run_id}`

## Local Commands

```bash
./scripts/aionctl.sh --scope workspace:main resilience status
./scripts/aionctl.sh --scope workspace:main resilience dependencies check
./scripts/aionctl.sh --scope workspace:main resilience retry-policies seed
./scripts/aionctl.sh --scope workspace:main resilience circuit-breakers list
./scripts/aionctl.sh --scope workspace:main resilience degraded list
./scripts/aionctl.sh --scope workspace:main resilience fault-rules list
./scripts/aionctl.sh --scope workspace:main resilience test run
./scripts/resilience-check.sh
./scripts/fault-injection-dry-run.sh
```

`./scripts/fault-injection-dry-run.sh` asks the resilience test runner to include
fault injection metadata. It does not enable fault injection globally.

## Release Gate

The freeze gate runs a dry-run resilience test when a runner is available.
Critical resilience failures fail the freeze gate when
`AION_RESILIENCE_FAIL_FREEZE_ON_CRITICAL=true`.

Missing optional adapters and disabled optional capabilities may produce
warnings, not automatic remediation.
