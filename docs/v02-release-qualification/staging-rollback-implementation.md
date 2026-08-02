# AION-241 Rollback

Defines the Redis degradation and rollback drill. The drill stops only the run-owned Redis fixture, observes degraded readiness, restarts Redis and requires ready recovery.

## Release Boundary

- program: `AION-V02-RELEASE-QUALIFICATION-001`
- authorization: `AION-240-V02RQ-0002`
- implementation task: `AION-241`
- formal closeout: `AION-242`
- final planned decision: `AION-244`
- local staging artifact is not a release candidate
- production runtime, public network, DNS, registry login, registry pull, registry push, production deployment, v0.2 tag and v0.2 release remain disabled or absent

## Evidence

Canonical example payloads live under `examples/v02-release-qualification/`. Static console evidence lives under `operator-console-static/demo-data/` and remains read-only, redacted and synthetic.
