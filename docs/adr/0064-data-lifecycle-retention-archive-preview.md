# 0064: Data Lifecycle Retention and Archive Preview

## Status

Accepted

## Context

AION Brain needs a generic way to evaluate retention posture across local
Brain-owned records and registry-indexed resources before any real archival,
redaction, or purge path exists.

## Decision

AION adds a Data Lifecycle Manager as an advisory Brain layer. It owns generic
lifecycle policies, retention classifications, archive candidates, redaction
candidates, purge previews, review records, and lifecycle reports.

Lifecycle evaluation reads safe descriptors through the Global Resource
Registry and writes lifecycle-owned records only. Purge preview is a report
contract and must keep `hard_delete_allowed=false` in v0.1.

Archive and redaction candidates may be converted into action proposals for
review. Conversion does not execute archive or redaction.

## Constraints

- No source record mutation.
- No hard delete.
- No automatic archive, redaction, or purge.
- No external object storage or external lifecycle service calls.
- No domain-specific retention or classification logic.
- No raw headers, hidden reasoning, raw prompts, or secrets in lifecycle
  payloads.

## Consequences

Operators and future automation can inspect lifecycle posture safely through
Brain-owned contracts, SDK methods, CLI commands, operator queues, visual
telemetry, audit, and policy gates. A future task can add execution adapters
behind separate governance boundaries without changing the public advisory
contracts.
