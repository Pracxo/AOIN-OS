# Cognitive Architecture Operator Model

The operator model keeps the program evidence-driven and approval-bound.

## Operator Responsibilities

- review authorization records before implementation tasks
- review evaluation evidence before the next authorization is created
- keep evaluation evidence separate from approval
- verify runtime-disabled fields remain false
- verify no direct main writes, source rewrite, deployment, production exposure, or model-weight change occurs without a later exact authorization

## Machine Responsibilities

- maintain append-only ledgers
- produce deterministic evidence
- flag contradictions, uncertainty, risk, and reversibility
- create operator review items
- preserve redaction and provenance
- stop on hard-gate failure

## Current Authorization

`AION-183-CA-0001` authorizes only AION-184 persistent cognitive state implementation. It does not authorize production cognitive runtime, network access, provider access, connector access, Git mutation through runtime, pull-request creation through runtime, approval creation, merge, deployment, production canary, or model-weight training.
