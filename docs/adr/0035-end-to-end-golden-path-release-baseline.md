# 0035: End-to-End Golden Path and Release Baseline

## Status

Accepted

## Decision

AION Brain v0.1 adds an end-to-end scenario harness. The harness owns scenario
contracts, deterministic step execution, result comparison, scenario run
records, demo fixture loading, visual telemetry semantics, and release baseline
reporting.

Scenarios are generic and dry-run by default. They validate Brain behavior
without domain workflow logic, external services, live model providers, optional
adapters, full autonomy, external tools, or UI code.

The release baseline combines selected scenario runs with quality gate
summaries into one persisted readiness report. The report is the local v0.1
release artifact for reviewing failed scenarios, failed steps, quality gates,
and generic remediation recommendations.

No domain scenario packs belong in Brain core. Future modules may ship separate
scenario packs outside the core Brain boundary.

## Reason

AION needs deterministic proof of system behavior before the v0.1 release. The
Brain now has many cooperating subsystems, so isolated unit tests are not
enough to show that the whole generic control plane can boot, accept events,
retrieve context, reason deterministically, plan, apply governance, validate
modules, check sandbox metadata, project visual telemetry, and pass local
quality gates.

## Consequence

Release readiness can be checked through public APIs, SDK helpers, CLI
commands, and local tests. Future modules can add separate scenario packs
without changing Brain core contracts or introducing vertical logic into the
core repository.

The harness increases the amount of local validation code, but keeps it
deterministic and side-effect-safe so it can run in CI and developer machines
without Docker services by default.

## Constraints

- No external services.
- No full autonomy.
- No domain-specific logic.
- No domain scenario packs in Brain core.
- No external tool execution.
- No optional adapter requirement.
