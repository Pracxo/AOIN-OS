# 0040: Security Baseline, Threat Model, and Hardening Gate

## Status

Accepted

## Decision

AION Brain v0.1 adds a local security baseline and hardening gate.

The baseline uses local static checks only in v0.1. It does not call external
scanner integrations, does not require internet access, and does not introduce
a domain-specific compliance layer.

The baseline owns AION security contracts, threat model semantics, attack
surface metadata, control catalog metadata, local secret scanning, and the
hardening gate result format.

## Reason

AION needs repeatable local posture checks before broader use. The Brain must
stay fail-closed, avoid raw secrets, avoid provider object leakage, avoid
uncontrolled execution, and keep optional adapters disabled by default.

## Consequence

Freeze and release packaging can include local security posture. The SDK and
CLI can trigger local scans and hardening checks through public APIs.

External security tools may be added later behind adapters, but they do not
define the AION core security baseline.

## Constraints

- No internet dependency.
- No external scanner calls.
- No raw secrets in findings or reports.
- No production auth claims.
- No domain-specific visualization, workflow, or compliance logic.
