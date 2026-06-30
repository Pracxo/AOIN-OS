# Connector Policy Dry-Run Gate

The connector policy dry-run gate evaluates a requested connector policy action
without executing any connector behavior. It returns a decision, blockers,
warnings, audit posture, and provenance posture.

The gate can return `allow_read`, `allow_dry_run`, or `deny`. An allowed
dry-run means only that the preview request is safe to inspect locally. It does
not approve connector runtime or external calls.

Hard blockers remain active in every result:

- connector runtime disabled
- external calls disabled
- credentials and tokens disabled
- activation disabled
- route registration disabled
- tool and write execution disabled

The gate emits connector policy telemetry and audit evidence, but it never
stores connector material and never creates write paths.
