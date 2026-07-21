# Cognitive Architecture Security Boundary

The cognitive architecture uses strict contracts and explicit repositories. Cognitive services may exchange immutable records but must not directly import Git controllers, pull-request controllers, merge controllers, deployment controllers, production canary controllers, credential stores, unrestricted connector adapters, or unrestricted provider clients.

## Permitted Data

- synthetic records
- redacted operator-approved records
- opaque memory references
- evidence fingerprints
- bounded numerical metrics
- explicitly approved local files
- in-memory adapters
- explicit local SQLite adapters when authorized

## Rejected Data

- arbitrary URLs
- arbitrary filesystem discovery
- hidden paths
- repository-path output
- symlink escape
- path traversal
- raw operator prompts in learning evidence
- hidden reasoning
- secrets
- private keys
- unredacted personal data
- production event streams without later authorization

## Invariants

Every cognitive service must keep these fields false unless a later exact authorization changes one bounded field:

- `runtime_effect`
- `source_modified`
- `git_mutated`
- `pull_request_created`
- `approval_created`
- `merged`
- `production_exposure`
- `model_weights_changed`

## AION-183 Boundary

AION-183 is governance-only. It creates no runtime source, no API route, no scheduler, no background loop, no startup hook, and no production adapter.
