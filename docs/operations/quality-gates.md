# Quality Gates

## Tests

`scripts/test-all.sh` runs Brain API and SDK tests.

## Lint

`scripts/lint.sh` runs ruff checks for both Python packages.

## Typecheck

`scripts/typecheck.sh` runs mypy for both Python packages.

## Docker Build

`scripts/docker-build.sh` builds the core Brain API image.

## Migration Check

`scripts/migration-check.sh` validates migration files without a database.

## Boundary Check

`scripts/boundary-check.sh` uses the live API when available, otherwise local
tests.

## Policy Coverage

`scripts/policy-coverage.sh` uses the live API when available, otherwise local
policy tests.

## OpenAPI Hygiene

`scripts/openapi-hygiene.sh` uses the live API when available, otherwise local
OpenAPI hygiene tests.

## Kernel Self-Test

`scripts/kernel-self-test.sh` requires a running local Brain API.

## Scenario Harness

The scenario harness runs deterministic, generic, side-effect-safe Brain
scenarios. Default scenarios cover the golden path, memory and evidence
retrieval, policy and autonomy gates, module certification, sandbox validation,
event reactions, workflow dry-runs, cycles, replay, regression, and visual
projection.

Scenario runs must remain dry-run by default and must not require Docker,
external providers, optional adapters, full autonomy, or domain scenario packs.

## Release Baseline Report

The release baseline report combines selected scenario runs with quality gate
summaries. It records pass rate, failed scenarios, failed steps, gate results,
readiness status, and generic recommendations.

Use the release baseline before tagging v0.1 readiness so scenario failures and
quality gate failures are reviewed in one place.

## No-Domain-Drift

`scripts/verify-no-domain-drift.sh` blocks forbidden vertical source paths,
route prefixes, and example module IDs.

## Release Candidate Check

`scripts/release-candidate-check.sh` runs local gates and prints follow-up
manual checks.
