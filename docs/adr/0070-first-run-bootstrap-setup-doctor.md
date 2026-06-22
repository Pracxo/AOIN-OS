# 0070: First-Run Bootstrap and Setup Doctor

## Status

Accepted

## Decision

AION Brain v0.1 adds a local first-run bootstrap layer, seed bundle manager,
setup doctor, setup report records, SDK helpers, CLI commands, and local
scripts.

Bootstrap profiles and seed bundles are AION-owned contracts. Seed execution is
idempotent and dry-run by default. Setup Doctor reports inspect local readiness
and create findings for operator review.

## Reason

AION needs a clean local developer onboarding gate after golden path, release
smoke, operator control, contract registry, resource registry, conformance, and
freeze/release gates exist. The setup path must be inspectable and repeatable
without becoming production provisioning.

## Consequences

Future local setup flows can consume bootstrap reports and findings. Release
packages can include bootstrap readiness summaries. Freeze gates can require
bootstrap readiness only when explicitly requested.

## Constraints

Bootstrap must not install dependencies, call external services, create cloud
resources, create production secrets, enable production auth, enable external
model calls, enable full autonomy, load code, execute tools, hard-delete
records, mutate source code, or add domain-specific setup logic.
