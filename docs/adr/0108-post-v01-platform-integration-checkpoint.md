# ADR 0108: Post-v0.1 Platform Integration Checkpoint

## Status

Accepted

## Context

AION-094 through AION-116 established local auth contracts, read-only local
session previews, role-aware static console filtering, dry-run authorization,
disabled production auth evidence, operator platform checkpoint and
stabilization gates, module activation design review gates, connector boundary
design, connector runtime review, connector simulator hardening, connector
policy catalog, connector sandbox design, connector credential architecture,
connector release gates, connector checkpoint gates, and connector
stabilization gates.

The post-v0.1 platform now needs one integration checkpoint that ties operator
and connector evidence together without enabling runtime capabilities.

## Decision

Decision: add a post-v0.1 platform integration checkpoint.

Decision: compose operator platform, local auth review, module activation
design review, connector release, connector checkpoint, connector stabilization,
static console, docs, domain drift, and boundary checks into one platform
checkpoint.

Decision: keep all implementation approvals false.

Decision: freeze future runtime boundaries until explicit future ADRs and
release gates approve a narrower implementation scope.

Decision: preserve direct full validation for manual freeze checks while
deferring nested full repository checks under pytest, CI aggregate gates, or
other outer gates.

Decision: keep `aion-v0.1.0` untouched and treat tag movement as out of scope.

## Reason

A single platform integration checkpoint reduces ambiguity between the operator
platform and connector platform lanes. It makes the current safe state explicit
and gives future runtime work a clear starting boundary without treating
existing evidence as implementation approval.

## Consequences

The platform checkpoint becomes a release blocker for future implementation
work. Future tasks must not infer approval from operator, connector, auth,
module, SDK, CLI, static console, docs, examples, or evidence artifacts.

Direct local execution of the freeze script still performs the full repository
check. Nested execution under pytest or an aggregate gate can defer the full
repository check to the outer gate to avoid recursive long-running checks.

## Constraints

Constraint: no production auth implementation.

Constraint: no connector runtime implementation.

Constraint: no operator write execution.

Constraint: no module activation.

Constraint: no external calls.

Constraint: no credential storage.

Constraint: no token storage.

Constraint: no OAuth, OIDC, or SAML runtime.

Constraint: no sandbox execution.

Constraint: no code loading, runtime registration, or capability activation.

Constraint: no API runtime execution route.

Constraint: no SDK resource or CLI command implementation.

Constraint: no package files, lockfiles, migrations, frontend dependencies, or
package installation instructions.

Constraint: no direct push to main.

Constraint: no move, delete, or recreation of `aion-v0.1.0`.

## Verification

The accepted verification surface is:

```bash
./scripts/platform-integration-checkpoint.sh
./scripts/platform-integration-freeze-check.sh
./scripts/platform-integration-no-go-regression.sh
./scripts/check.sh
git diff --check
```
