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
