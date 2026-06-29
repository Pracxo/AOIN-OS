# Future Connector Implementation Prerequisites

## Purpose

This document defines the prerequisites for any future connector implementation
work. AION-106 does not satisfy these prerequisites; it only defines them.

## Connector ADR

Future implementation needs a connector ADR that explicitly changes the current
runtime-absent state and defines disabled-by-default rollout behavior.

## Connector Threat Model

Future implementation needs an approved threat model covering credential
exfiltration, prompt injection, malicious metadata, overbroad scopes,
SSRF-style egress abuse, data exfiltration, stale data trust, rate-limit
exhaustion, audit tampering, policy bypass, action authorization bypass,
hidden external calls, provider impersonation, and dependency confusion.

## Sandbox Design

Future implementation needs sandbox posture for egress, ingress, credential
access, network boundaries, rate limits, resource limits, and audit capture.

## Credential Store Design

Future implementation needs a credential store design with metadata-only Brain
references, rotation, revocation, no plaintext logs, no browser storage, and
release-gate evidence.

## Egress Allowlist Design

Future implementation needs a destination allowlist, egress preview, payload
classification, redaction, policy decision, action authorization decision,
rate-limit posture, and operator approval path.

## Ingress Redaction Design

Future implementation needs response normalization, secret scanning, prompt
injection scanning, provenance tagging, source classification, stale data flags,
and operator review.

## Policy Action Catalogue

Future connector actions must use generic policy actions reviewed in the policy
catalogue. Connector metadata must not create active policy actions.

## Dry-Run Simulator

Future implementation needs a dry-run simulator before runtime. The simulator
must not call external systems, store credentials, issue tokens, or execute
tools.

## Disabled Prototype

Future connector prototype work must be disabled by default. It may expose
status and preview evidence only after ADR approval.

## Release Gate

Future implementation needs a release gate that proves no external call can
occur without policy, action authorization, operator review, audit/provenance,
egress guard, ingress guard, credential boundary, sandbox posture, and rollback
evidence.

## Rollback Plan

Future implementation needs a rollback plan that disables connector routing,
revokes credential references, stops future egress, preserves audit/provenance,
marks connector capabilities unavailable, and avoids hard delete.
