# ADR 0205: Controlled Isolated Local Staging Artifact Build and Rollback Drill

## Status

Accepted for AION-241.

## Context

AION-240 authorized one controlled isolated local staging qualification under AION-240-V02RQ-0002 after AION-V02RQPE-001 passed. The work must exercise a local staging artifact without creating production runtime, production credentials, a release candidate, a v0.2 tag or a v0.2 release.

## Decision

Use Docker Desktop's existing local Linux daemon as the execution substrate. AION-241 creates an immutable Git archive from the implementation commit, builds two local staging images offline with `--pull=false` and `--network=none`, deploys one five-service Compose stack on an internal network, exposes Brain API only through `127.0.0.1`, validates health, readiness, identity, replay, redaction, drift and rollback controls, then removes every run-owned resource.

## Consequences

The staging artifact is local and is not a release candidate. The runner may invoke bounded Docker commands, but the runtime package remains pure and effect-free. AION-240-V02RQ-0002 remains active until AION-242 independently evaluates and closes it.
