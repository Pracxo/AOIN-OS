# Local Security Baseline

AION v0.1 security baseline is a local, deterministic posture layer for Brain
core. It gives developers a repeatable view of unsafe defaults, raw secret
leakage, adapter risk, API exposure, dependency metadata, threat model records,
and hardening gate status.

It does not call external scanners, does not require internet access, and does
not claim production security certification.

## Secret Scanner

The local scanner reads selected repository paths and emits redacted findings
only. It checks obvious API-key-like strings, bearer-token-like strings,
private-key blocks, password assignments, token assignments, `.env` files, and
credential-named files.

Findings never store raw matches. Lines can opt out with
`AION_SECRET_SCAN_IGNORE` when the local setting allows ignore comments.

## Config Hardening

The config checker verifies local hardening defaults:

- `.env` is not committed.
- `.env.example` exists.
- external model use is disabled by default.
- MCP is disabled by default.
- sandbox execution is disabled by default.
- restore apply is disabled by default.
- full autonomy is disabled by default.
- stack traces are not exposed.
- optional adapters are disabled by default.

## API Exposure

The API exposure checker inspects OpenAPI metadata locally. It checks for
forbidden vertical route prefixes, stacktrace exposure, raw provider schema
leakage, missing route tags where practical, and destructive routes that lack
policy category metadata.

## Adapter Risk

The adapter risk checker confirms that TurboVec, Graphiti, MCP, Temporal,
LiteLLM, MinIO, Langfuse, Docker sandbox, and Firecracker sandbox remain
optional or disabled by default. It also checks that public contracts do not
expose provider SDK objects.

## Dependency Metadata

The dependency scanner reads local `pyproject.toml` files only. It flags
required provider SDKs, cloud SDKs, Docker SDKs, secret-manager SDKs, and
domain-specific SDK dependencies. Optional adapter dependencies are recorded as
metadata, not failures.

## Hardening Gate

The hardening gate combines selected checks into a persisted run. It fails on
high or critical secret findings when configured, stacktrace exposure, full
autonomy defaults, sandbox execution defaults, restore apply defaults, external
models by default, `.env` inclusion, or provider object leakage.

Warnings are used for optional unavailable posture inputs such as an unseeded
threat model or control catalog.

## Known Limits

The v0.1 baseline is a local static and metadata checker. It is not production
auth, cloud posture management, a vulnerability scanner, or a compliance
certification layer. External scanners may be added later behind adapters, but
they do not define AION's core baseline.
