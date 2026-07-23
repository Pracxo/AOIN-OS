# ADR 0169: Controlled Research Acquisition and Immutable Source Snapshots

## Status

Accepted.

## Context

ADR 0168 authorized `AION-204-KI-0001` for AION-205 to implement controlled research acquisition without activating public internet research.

## Decision

Add immutable research contracts, URL and destination policy, explicit allowlists, disabled and in-memory adapters, explicit local fixtures, source snapshots, provenance, citation references, lineage, deduplication, incidents, diagnostics, and operator-review evidence. The HTTP policy adapter is present but its system transport remains unavailable and `public_network_fetch_available=false`.

## Consequences

Acquired source content remains untrusted evidence. AION-205 does not verify factual claims, promote knowledge, create beliefs, run crawlers, integrate search providers, use connectors, mutate source, operate Git, deploy, or train model weights. `AION-204-KI-0001` remains active pending AION-206 closeout.
