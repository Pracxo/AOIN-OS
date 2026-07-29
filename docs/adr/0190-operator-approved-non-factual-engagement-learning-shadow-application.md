# ADR 0190: Operator-Approved Non-Factual Engagement-Learning Shadow Application

## Status

Accepted for AION-226 implementation pending AION-227 closeout.

## Decision

AION OS implements a deterministic, operator-approved, non-factual engagement-learning application plane as an isolated in-memory shadow session. The plane may validate engagement candidates and approvals, plan bounded overlays, replay redacted counterfactual fixtures, compare baseline and candidate behaviour, and emit redacted operator-review evidence.

## Boundaries

Engagement is not factual evidence. It cannot increase confidence, knowledge, source independence, citation coverage, provenance completeness, or belief state. Approved overlays apply only in explicit bounded in-memory sessions, expire or roll back before close, and create no persistent overlay, AION-224 write, production policy mutation, cognitive-memory write, belief mutation, model-weight change, network call, background worker, scheduler, API route, installed CLI command, v0.2 tag, or v0.2 release.

## Consequences

AION-225-GLM-0003 remains active and unconsumed until AION-227 independently evaluates AION-226 and closes the authorization. AION-228 remains unapproved and AION-229 remains the final planned GLM closeout.
