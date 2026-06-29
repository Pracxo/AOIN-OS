# Connector Egress Preview

## Purpose

The connector egress preview describes what would be blocked before connector
egress can exist. It never performs an external request.

## Guarantees

Every AION-108 egress preview returns:

- `egress_allowed=false`
- `external_call_allowed=false`
- `credentials_present=false`
- disabled-runtime blockers
- redacted payload summary

Payload summaries reject secrets, raw prompts, and hidden reasoning.

## Future Work

A future connector runtime would need policy, action authorization, operator
approval, rate-limit posture, redaction, provenance, rollback, and release
gates before any controlled egress could be considered.
