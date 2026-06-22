# 0062: Incident Correlation, Root Cause Candidates, and Recovery Review

## Status

Accepted

## Context

AION Brain now has local notifications, alerts, run supervision, scheduler
records, grounding checks, model output governance, audit records, and
operator surfaces. These systems can emit signals that need to be grouped for
operator review without giving Brain core authority to remediate, mutate source
records, or call external incident systems.

## Decision

Add a Brain-owned incident correlation layer with normalized incident signals,
local incident grouping records, deterministic correlation runs, root cause
candidate records, and recovery review records.

Incident correlation is local and generic. It may ingest local AION signals,
cluster them by trace, source, fingerprint, or correlation key, and create
AION-owned incident records only when explicitly requested through a controlled
mode. Dry-run remains the default.

Root cause records are candidates, not truth. Recovery reviews are summaries
and optional local record proposals, not remediation execution.

## Constraints

- No external incident-management integration in v0.1.
- No automatic remediation.
- No source record mutation.
- No domain-specific incident logic.
- No hidden reasoning, raw prompts, raw headers, provider payloads, or secrets.
- Public APIs return AION contracts only.

## Consequences

Operators can review correlated local incident state through the Brain API,
SDK, CLI, operator surfaces, and visual telemetry. Future external adapters can
be added behind governance boundaries without changing public AION contracts.
