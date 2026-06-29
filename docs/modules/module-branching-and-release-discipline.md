# Module Branching and Release Discipline

## Branching

- `main` remains stable.
- `aion-v0.1.0` is the immutable release baseline.
- Post-v0.1 work uses feature branches.
- Modules use separate module branches.
- Brain core changes require architecture review.

Recommended branch command:

```bash
git switch main
git pull --ff-only origin main
git switch -c phase/post-v0.1-module-strategy
```

## Release

Every module must pass:

- manifest validation
- extension intake
- binding validation
- conformance
- readiness
- RC gate
- freeze gate
- no-domain drift
- boundary check
- docs audit

## Brain Core Protection

Modules must not modify Brain core. Module-specific implementation must live
outside the core until a future architecture-approved activation path exists.

Activation remains disabled. Code loading remains disabled.

## Module Pack Branch Rule

Every module pack starts in its own branch or approved phase branch. A module
pack cannot alter Brain core, add migrations, add API routes, add SDK
resources, add CLI commands, or enable runtime behavior without architecture
review.

The Generic Knowledge Intelligence pack is examples, docs, scripts, and tests
only. It must not move the `aion-v0.1.0` tag.

## AION-105 Branch Rule

AION-105 runs on `phase/module-activation-design-review` as a review and
evidence branch only. It may add docs, examples, scripts, and regression tests.
It must not add migrations, API routes, SDK resources, CLI command
implementations, package manager files, package installation, code loading,
runtime registration, capability activation, controlled execution, module
writes, or domain module logic.

The branch must pass:

```bash
./scripts/module-activation-design-review.sh
./scripts/module-activation-no-go-regression.sh
./scripts/check.sh
```
