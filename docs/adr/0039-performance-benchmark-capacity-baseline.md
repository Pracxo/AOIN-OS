# 0039: Performance Benchmark and Capacity Baseline

## Status

Accepted.

## Decision

AION Brain adds a local performance benchmark harness for v0.1.

AION Brain adds capacity baseline records derived from local benchmark runs.

AION Brain adds resource budget profiles in `report_only` mode by default.

AION Brain does not perform cloud load testing in v0.1.

## Reason

AION needs measurable local performance before future modules expand the system.
The Brain should be able to prove that generic local operations still fit within
known timing and capacity expectations.

## Consequences

Future changes can compare benchmark runs against a baseline and detect local
regressions. Operators can inspect benchmark reports, capacity records, and
budget evaluations through AION contracts, SDK calls, and `aionctl`.

## Constraints

- No external services.
- No provider calls.
- No cloud load testing.
- No request or response body storage in performance samples.
- No domain-specific benchmarks.
- Resource budget enforcement remains report-only by default.
