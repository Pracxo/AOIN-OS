# Release Candidate Gate Runbook

The Release Candidate Gate is the local AION v0.1 readiness aggregator. It
collects normalized verification checks, applies a verification matrix, records
findings, creates a redacted evidence pack, and writes an RC report.

## Local Commands

```bash
./scripts/rc-check.sh --offline-ok
./scripts/rc-evidence.sh --offline-ok
```

`rc-check.sh` runs local verification commands and, when the Brain API is
reachable, posts normalized checks to `/brain/rc/gate/run`. `rc-evidence.sh`
reads the latest RC report and evidence pack when the API is reachable.

## Operator Review

Review open findings first:

```bash
aionctl rc findings
aionctl rc reports
aionctl rc evidence
```

Dismiss a finding only after the underlying issue is understood:

```bash
aionctl rc dismiss-finding --id <finding-id> --reason "reviewed"
```

## Boundaries

The RC gate is local-only. It does not deploy, publish, tag releases
automatically, mutate source code, enable disabled features, call external
services, expose raw prompts, expose hidden reasoning, or add domain-specific
release logic.

## Release Handoff Usage

For v0.1 release handoff, run:

```bash
./scripts/rc-check.sh --offline-ok
./scripts/rc-evidence.sh --offline-ok
```

Any RC blocker is a no-go condition.
